import numpy as np
import json
import math
import time
from collections import deque
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QVector3D
from datetime import datetime, timedelta
import scipy.spatial.transform

from janela import *
from leitor_data import LeitorSerial

class GerenciadorMissao:
    def __init__(self, interface_grafica):
        # VARIAVEIS DE CONTROLE DE TEMPO E POSICAO
        self.tempo_anterior = time.time()
        self.lat_origem = None
        self.lng_origem = None
        self.aceleracao_controle_ruido = 15
        self.gravidade = 9.81
        self.modulo_da_aceleracao = 0.0

        # ANGULOS DE EULER ACUMULADOS, RECEBIDOS DIRETAMENTE DO GIROSCÓPIO
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

        # RECEBE A INTERFACE PARA CONTROLE
        self.interface = interface_grafica

        # INICIALIZA AS VARIAVEIS DE CONTROLE
        self.inicio_missao = None
        self.altitude_maxima = 0.0
        self.temperatura_maxima = None
        self.historico_posicao = []
        self.altitude = 0.0
        self.ultimo_tempo_amostra = None
        
        self.leitor_serial = LeitorSerial()
        if self.leitor_serial.modo_csv:
            self.interface.configurar_tempo_csv(self.leitor_serial)

        # CONFIGURA OS TIMERS
        self.timer_principal = QTimer()
        self.timer_principal.timeout.connect(self.atualizar_loop)
        self.timer_apogeu = QTimer()
        self.timer_apogeu.timeout.connect(self.atualizar_apogeu_display)

        # =====================================================
        # FILTRO PASSA-BAIXA (SUAVIZACAO DE RUIDO POR VIBRACAO)
        # =====================================================
        self.ax_filtrado = 0.0
        self.ay_filtrado = 0.0
        self.az_filtrado = 0.0
        self.alpha_filtro = 0.2 # FORÇA DO FILTRO

        # ==========================================================
        # PROCESSAMENTO DE VIBRACAO DO PAYLOAD PANDORA (ADXL375)
        # PROCESSADO AQUI NA GROUND STATION (NAO NO ESP32)
        # ==========================================================
        self.JANELA_MINIMOS_QUADRADOS = 15  # Nº DE AMOSTRAS NA JANELA MOVEL (1.5s A 10Hz)
        self.vib_referencia_max = 3.0  # m/s² -> PISO INICIAL; SOBE SOZINHO CONFORME O VOO ACONTECE
        self.buffer_vib_tempo = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        self.buffer_vib_bruto = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        # BUFFERS POR EIXO (PARA OS 3 GRAFICOS EMPILHADOS: X, Y, Z)
        self.buffer_vib_x = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        self.buffer_vib_y = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        self.buffer_vib_z = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)

        # ==========================================================
        # VIBRACAO DO MPU6050 (MESMA LOGICA DO ADXL375, SENSOR DIFERENTE)
        # ==========================================================
        self.mpu_referencia_max = 3.0  # m/s² -> PISO INICIAL; SOBE SOZINHO CONFORME O VOO ACONTECE
        self.buffer_mpu_tempo = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        self.buffer_mpu_bruto = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        # BUFFERS POR EIXO (PARA PLOTAR BRUTA x LINEARIZADA NOS 3 GRAFICOS, IGUAL AO ADXL)
        self.buffer_mpu_x = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        self.buffer_mpu_y = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)
        self.buffer_mpu_z = deque(maxlen=self.JANELA_MINIMOS_QUADRADOS)

    # CONFIGURACAO DOS TIMERS DA MISSAO (HORARIO LOCAL E TEMPO DE VOO)
    def iniciar(self):
        # INICIA O START NO LOOP DA MISSAO
        self.timer_principal.start(100) # 10 Hz para sincronia com Rádio
        self.timer_apogeu.start(1000)

    def processar_vibracao(self, tempo_amostra, vib_x, vib_y, vib_z):
        # (1) ACELERACAO BRUTA CAPTADA PELO ADXL375 (MODULO DOS 3 EIXOS, PARA O MEDIDOR DE INTENSIDADE)
        modulo_bruto = math.sqrt(vib_x**2 + vib_y**2 + vib_z**2)

        self.buffer_vib_tempo.append(tempo_amostra)
        self.buffer_vib_bruto.append(modulo_bruto)
        self.buffer_vib_x.append(vib_x)
        self.buffer_vib_y.append(vib_y)
        self.buffer_vib_z.append(vib_z)

        # (2) CURVA LINEARIZADA POR MINIMOS QUADRADOS (RETA) NA JANELA MOVEL MAIS RECENTE
        # FEITO PARA O MODULO (MEDIDOR) E PARA CADA EIXO SEPARADO (OS 3 GRAFICOS)
        if len(self.buffer_vib_tempo) >= 3:
            coef_modulo = np.polyfit(self.buffer_vib_tempo, self.buffer_vib_bruto, 1)
            linear_modulo = float(np.polyval(coef_modulo, tempo_amostra))

            coef_x = np.polyfit(self.buffer_vib_tempo, self.buffer_vib_x, 1)
            linear_x = float(np.polyval(coef_x, tempo_amostra))

            coef_y = np.polyfit(self.buffer_vib_tempo, self.buffer_vib_y, 1)
            linear_y = float(np.polyval(coef_y, tempo_amostra))

            coef_z = np.polyfit(self.buffer_vib_tempo, self.buffer_vib_z, 1)
            linear_z = float(np.polyval(coef_z, tempo_amostra))
        else:
            linear_modulo = modulo_bruto
            linear_x, linear_y, linear_z = vib_x, vib_y, vib_z

        # (3) VIBRACAO = DIFERENCA ENTRE A CURVA BRUTA E A CURVA LINEARIZADA (MODULO -> MEDIDOR DE %)
        vibracao = modulo_bruto - linear_modulo

        # ATUALIZA A REFERENCIA COM BASE NA VIBRACAO EM SI (NAO NO modulo_bruto!) - modulo_bruto
        # inclui o empuxo do motor e a gravidade, entao usar ele deixaria a referencia dominada
        # por aceleracao de verdade em vez de vibracao, e a % nunca chegaria perto de 100%
        if abs(vibracao) > self.vib_referencia_max:
            self.vib_referencia_max = abs(vibracao)

        intensidade_pct = min(100.0, (abs(vibracao) / self.vib_referencia_max) * 100.0)

        return (modulo_bruto, linear_modulo, intensidade_pct,
                vib_x, linear_x, vib_y, linear_y, vib_z, linear_z)

    def processar_vibracao_mpu(self, tempo_amostra, ax, ay, az):
        # MESMA LOGICA DE processar_vibracao(), MAS PRO MPU6050 EM VEZ DO ADXL375.
        # LINEARIZA POR EIXO TAMBEM AGORA, PRA PLOTAR BRUTA x LINEARIZADA IGUAL AO ADXL.

        # (1) MODULO DA ACELERACAO BRUTA DO MPU6050 (PARA O MEDIDOR DE INTENSIDADE)
        modulo_bruto_mpu = math.sqrt(ax**2 + ay**2 + az**2)

        self.buffer_mpu_tempo.append(tempo_amostra)
        self.buffer_mpu_bruto.append(modulo_bruto_mpu)
        self.buffer_mpu_x.append(ax)
        self.buffer_mpu_y.append(ay)
        self.buffer_mpu_z.append(az)

        # (2) CURVA LINEARIZADA POR MINIMOS QUADRADOS (RETA) - MODULO (MEDIDOR) E POR EIXO (GRAFICOS)
        if len(self.buffer_mpu_tempo) >= 3:
            coef_mpu = np.polyfit(self.buffer_mpu_tempo, self.buffer_mpu_bruto, 1)
            linear_mpu = float(np.polyval(coef_mpu, tempo_amostra))

            coef_x_mpu = np.polyfit(self.buffer_mpu_tempo, self.buffer_mpu_x, 1)
            linear_x_mpu = float(np.polyval(coef_x_mpu, tempo_amostra))

            coef_y_mpu = np.polyfit(self.buffer_mpu_tempo, self.buffer_mpu_y, 1)
            linear_y_mpu = float(np.polyval(coef_y_mpu, tempo_amostra))

            coef_z_mpu = np.polyfit(self.buffer_mpu_tempo, self.buffer_mpu_z, 1)
            linear_z_mpu = float(np.polyval(coef_z_mpu, tempo_amostra))
        else:
            linear_mpu = modulo_bruto_mpu
            linear_x_mpu, linear_y_mpu, linear_z_mpu = ax, ay, az

        # (3) VIBRACAO DO MPU = DIFERENCA ENTRE BRUTO E LINEARIZADO (MODULO -> MEDIDOR DE %)
        vibracao_mpu = modulo_bruto_mpu - linear_mpu

        # REFERENCIA AUTOMATICA, MESMA IDEIA DO ADXL (BASEADA NA VIBRACAO, NAO NO MODULO BRUTO)
        if abs(vibracao_mpu) > self.mpu_referencia_max:
            self.mpu_referencia_max = abs(vibracao_mpu)

        intensidade_mpu_pct = min(100.0, (abs(vibracao_mpu) / self.mpu_referencia_max) * 100.0)

        return (intensidade_mpu_pct, linear_x_mpu, linear_y_mpu, linear_z_mpu)

    def atualizar_loop(self):
        # ===========================================
        # LEITURA DE DADOS BRUTOS E CONTROLE DE TEMPO
        # ===========================================
        agora = datetime.now()
        if self.inicio_missao is None:
            self.inicio_missao = agora

        dados_raw = self.leitor_serial.readLine()
        if dados_raw is None:
            return
        dados = json.loads(dados_raw.decode())

        temperatura = dados.get('temp')
        if temperatura is not None:
            if self.temperatura_maxima is None or temperatura > self.temperatura_maxima:
                self.temperatura_maxima = temperatura
                if hasattr(self.interface, 'area_cabecalho'):
                    self.interface.area_cabecalho.atualizar_temperatura_maxima(temperatura)
        
        # CALCULO DOS DIFERENCIAIS DE TEMPO dt
        tempo_atual = time.time()
        dt = max(tempo_atual - self.tempo_anterior, 0.001)
        self.tempo_anterior = tempo_atual
        
        # ==========================
        # MATEMATICA E FISICA DO VOO
        # ==========================

        # (1) ACELERACAO DO MPU6050
        ax_raw, ay_raw, az_raw = dados.get('ax', 0.0), dados.get('ay', 0.0), dados.get('az', 0.0)

        # (2) ORIENTACAO (GIROSCOPIO)
        # INTEGRACAO DAS VELOCIDADES ANGULARES LIDAS DO RADIO
        gx, gy, gz = dados.get('gx',0.0), dados.get('gy',0.0), dados.get('gz',0.0)

        # (2.5) VIBRACAO DO PAYLOAD PANDORA (ADXL375 + MINIMOS QUADRADOS, MODULO + POR EIXO)
        vib_x, vib_y, vib_z = dados.get('vib_x', 0.0), dados.get('vib_y', 0.0), dados.get('vib_z', 0.0)
        tempo_amostra = dados.get('tempo_missao', tempo_atual)

        if (self.leitor_serial.modo_csv
                and self.ultimo_tempo_amostra is not None
                and tempo_amostra < self.ultimo_tempo_amostra):
            self.reiniciar_historico_tempo()

        self.ultimo_tempo_amostra = tempo_amostra

        total_segundos = max(0, int(tempo_amostra))
        horas, resto = divmod(total_segundos, 3600)
        minutos, segundos = divmod(resto, 60)
        texto_t = f"T+ {horas:02}:{minutos:02}:{segundos:02}"
        texto_hora = agora.strftime("%H:%M:%S")

        if hasattr(self.interface, 'area_cabecalho'):
            self.interface.area_cabecalho.atualizar_tempos(texto_t, texto_hora)

        (vib_bruto, vib_linearizado, vib_intensidade,
         vib_x_bruto, vib_x_linear, vib_y_bruto, vib_y_linear, vib_z_bruto, vib_z_linear) = self.processar_vibracao(tempo_amostra, vib_x, vib_y, vib_z)

        if hasattr(self.interface, 'painel_vibracao'):
            self.interface.painel_vibracao.atualizar_vibracao(
                tempo_amostra, vib_bruto, vib_linearizado, vib_intensidade,
                vib_x_bruto, vib_x_linear, vib_y_bruto, vib_y_linear, vib_z_bruto, vib_z_linear
            )

        # VIBRACAO DO MPU6050 (MESMA IDEIA, PAINEL SEPARADO EM ABA PROPRIA)
        intensidade_mpu, linear_x_mpu, linear_y_mpu, linear_z_mpu = self.processar_vibracao_mpu(tempo_amostra, ax_raw, ay_raw, az_raw)

        if hasattr(self.interface, 'painel_vibracao_mpu'):
            self.interface.painel_vibracao_mpu.atualizar_vibracao_mpu(
                tempo_amostra, ax_raw, linear_x_mpu, ay_raw, linear_y_mpu, az_raw, linear_z_mpu, intensidade_mpu
            )

        # APLICACAO DO FILTRO PASSA-BAIXA (PARA TIRAR "VIBRACOES")
        self.ax_filtrado = (self.alpha_filtro * ax_raw) + (1.0 - self.alpha_filtro)*self.ax_filtrado
        self.ay_filtrado = (self.alpha_filtro * ay_raw) + (1.0 - self.alpha_filtro)*self.ay_filtrado
        self.az_filtrado = (self.alpha_filtro * az_raw) + (1.0 - self.alpha_filtro)*self.az_filtrado
        
        # CRIACAO DE FILTRO COMPLEMENTAR PARA ANGULACAO DO FOGUETE
        pitch_acc = math.degrees(math.atan2(ax_raw, az_raw))
        roll_acc = math.degrees(math.atan2(ay_raw, az_raw))

        self.modulo_da_aceleracao = math.sqrt(self.ax_filtrado**2 + self.ay_filtrado**2 + self.az_filtrado**2)
 
        if self.modulo_da_aceleracao < self.aceleracao_controle_ruido: # ACELERACOES MUITO ALTAS DISTORCEM A LEITURA DE GRAVIDADE DO MPU
                self.pitch = 0.98 * (self.pitch + gy*dt) + 0.02*pitch_acc
                self.roll = 0.98 * (self.roll + gx*dt) + 0.02*roll_acc
        else: 
            self.roll += gx*dt
            self.pitch += gy*dt
        self.yaw += gz*dt

        # CRIACAO DA ROTACAO BASEADA NA SEQUENCIA 'XYZ' EM GRAUS
        rotacao_matriz = scipy.spatial.transform.Rotation.from_euler('xyz', [self.roll, self.pitch, self.yaw], degrees=True)
        acc_terra = rotacao_matriz.apply([self.ax_filtrado, self.ay_filtrado, self.az_filtrado])
        
        # VARIAVEL PARA ARMAZENAR ACELERACAO PARA CIMA
        acc_z_real = abs(acc_terra[2])

        # (3) POSICAO ESPACIAL (GPS E BAROMETRO)
        lat_atual, lng_atual = dados.get('lat', 0.0), dados.get('lng', 0.0)
        altitude_temporaria = self.altitude
        self.altitude = dados.get('alt', 0.0)

        # (4) VELOCIDADE (EXTREMAMENTE ESTIMADA, NAO DEVE SERVIR COMO PARAMETRO REAL DE VELOCIDADE)
        velocidade = (self.altitude - altitude_temporaria)/dt

        if self.altitude > self.altitude_maxima:
            self.altitude_maxima = self.altitude
        if self.lat_origem is None and (lat_atual != 0.0 or lng_atual != 0.0):
            self.lat_origem = lat_atual
            self.lng_origem = lng_atual
        
        x,y = 0.0,0.0

        if self.lat_origem is not None:
            RAIO_TERRA = 6371000 
            lat0, lng0 = math.radians(self.lat_origem), math.radians(self.lng_origem)
            lat_rad, lng_rad = math.radians(lat_atual), math.radians(lng_atual)

            # APROXIMAÇÃO DE TERRA PLANA (Corrigido para Multiplicação)
            x = RAIO_TERRA * (lng_rad - lng0) * math.cos(lat0)
            y = RAIO_TERRA * (lat_rad - lat0)

        # ================================
        # ATUALIZACAO DA INTERFACE GRAFICA
        # ================================

        # (1) FOGUETE 3D E CAMERA
        self.interface.foguete.resetTransform()

        # APLICACAO DAS ROTACOES SUCESSIVAS ATRAVES DIRETAMENTE NA MALHA 3D USANDO OS EIXOS
        self.interface.foguete.rotate(self.yaw, 0, 0, 1) # Guinada (Z)
        self.interface.foguete.rotate(self.pitch, 0, 1, 0) # Arfagem (Y)
        self.interface.foguete.rotate(self.roll, 1, 0, 0) # Rolamento (X)
        self.interface.foguete.translate(x, y, self.altitude)
        
        if self.interface.meus_botoes.seguindo:
            self.interface.view.setCameraPosition(pos=QVector3D(x, y, self.altitude), distance=2000, elevation=30, azimuth=45)

        # (3) ROCKET CONTROL (ANGULOS) - REMOVIDO JUNTO COM painel_controle

        # (4) STATUS DOS LEDS - REMOVIDO JUNTO COM painel_status
        # (contador_pouso/delta_para_apogeu/apogeu_minimo so existiam pra alimentar esse LED,
        # entao saíram junto; altitude_maxima continua em uso pelo header, nao foi afetado)

        # (5) TRILHA 3D
        self.historico_posicao.append([x, y, self.altitude])
        self.interface.trilha.setData(pos=np.array(self.historico_posicao))

        # (6) CONSOLE - REMOVIDO JUNTO COM painel_console

    def reiniciar_historico_tempo(self):
        self.buffer_vib_tempo.clear()
        self.buffer_vib_bruto.clear()
        self.buffer_vib_x.clear()
        self.buffer_vib_y.clear()
        self.buffer_vib_z.clear()
        self.buffer_mpu_tempo.clear()
        self.buffer_mpu_bruto.clear()
        self.buffer_mpu_x.clear()
        self.buffer_mpu_y.clear()
        self.buffer_mpu_z.clear()
        self.ax_filtrado = 0.0
        self.ay_filtrado = 0.0
        self.az_filtrado = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.historico_posicao.clear()

        if hasattr(self.interface, 'painel_vibracao'):
            self.interface.painel_vibracao.limpar_graficos()
        if hasattr(self.interface, 'painel_vibracao_mpu'):
            self.interface.painel_vibracao_mpu.limpar_graficos()
        self.interface.trilha.setData(pos=np.empty((0, 3)))

    def atualizar_apogeu_display(self):
        if hasattr(self.interface, 'area_cabecalho'):
            self.interface.area_cabecalho.atualizar_valor(self.altitude_maxima)
        
