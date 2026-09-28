import json
import os
import serial
from pathlib import Path
from serial.tools import list_ports
import datetime

MODO_TESTE = True

def find_esp():
    for p in list_ports.comports():
        desc = (p.description or "").lower()

        if "ch340" in desc or "cp210" in desc or "usb" in desc:
            if "bluetooth" not in desc:
                return p.device
            
    return None

class LeitorSerial:
    # PARA O CASO DO LINUX, TROCAR 'COM4' PELA PORTA ATUAL
    def __init__(self, porta = 'COM4', baudrate = 115200):
        # 1. DECIDE USAR A CONEXAO COM BASE NO MODO DE LEITURA (SIMULACAO POR DOC OU TESTE REAL)
        self.modo_teste = MODO_TESTE
        porta = find_esp()
        if porta is None:
            if not MODO_TESTE: 
                raise Exception("Esp nao conectado")
        try:
            if self.modo_teste:
                self.conexao = serial.serial_for_url('socket://127.0.0.1:65432', timeout = 0.1)
            else:
                print(f"K.I.R.A ligada à porta física {porta} (MODO REAL)...")
                self.conexao = serial.Serial(porta, baudrate, timeout = 0.1)
        except Exception as e:
            print(f"ERRO DE CONEXAO: {e}")
            print("Verifique se o simulador SRAD está funcionando ou se o LoRa está plugado!")
        
        # PREPARA O ARQUIVO CSV DE BACKUP
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.tempo_inicio_missao = datetime.datetime.now()
        nome_arquivo = f"dados_voo_{timestamp}.csv"
        pasta_atual = Path(__file__).parent
        caminho_docs = pasta_atual / ".." / "gravador_de_voo" / nome_arquivo
        self.ficheiro_log = caminho_docs.resolve()
        # SE O ARQUIVO NAO EXISTE, CRIA UM COM CABEÇALHO
        if not os.path.exists(self.ficheiro_log):
            with open(self.ficheiro_log, 'w', encoding = 'utf-8') as f:
                f.write("Temperatura,Pressao,Umidade,Altitude,ax,ay,az,gx,gy,gz,vib_x,vib_y,vib_z,Latitude,Longitude,Sat,Tempo\n")
 
    def readLine(self):
        # VERIFICA SE A CONEXAO FOI ESTABELECIDA COM SUCESSO
        if not hasattr(self, 'conexao'):
            return None
        
        # TENTATIVA DE LEITURA DA LINHA SEJA DO DOCS OU LORA
        try:
            linha_bytes = self.conexao.readline()
        except serial.SerialException:
            return None
        
        if linha_bytes:
            linha_texto = linha_bytes.decode('utf-8', errors = 'ignore').strip()

            # GUARDA OS DADOS NO FICHEIRO CSV IMEDIAMENTE
            if linha_texto:
                # CALCULA A VARIACAO DE TEMPO
                tempo_decorrido = (datetime.datetime.now() - self.tempo_inicio_missao).total_seconds()
                # ADICIONA O TEMPO AO FINAL DA STRING COMO UMA NOVA COLUNA
                linha_texto = f"{linha_texto},{tempo_decorrido:.2f}"
                # O WITH REALIZA O FECHAMENTO DO ARQUIVO, O PROTEGENDO
                with open(self.ficheiro_log, 'a', encoding = 'utf-8') as f:
                    f.write(linha_texto + '\n')

            # SEPARA OS DADOS POR VIRGULAS E PREPARA O PACOTE PARA USO DA GROUND STATION
            valores = linha_texto.split(',')

            # VERIFICA SE EXISTEM 17 VALORES (11 ORIGINAIS + UMIDADE, VIBRACAO/ADXL375 E SAT DO PAYLOAD PANDORA + TEMPO)
            if len(valores) >= 17:
                try:
                    pacote = {
                        # BME280 (TEMPERATURA, PRESSAO E UMIDADE DO PAYLOAD PANDORA)
                        "temp": float(valores[0]),
                        "pressao": float(valores[1]),
                        "umidade": float(valores[2]),
                        "alt": float(valores[3]),
                        # MPU6050 (ORIENTACAO: ACELEROMETRO + GIROSCOPIO)
                        "ax": float(valores[4]),
                        "ay": float(valores[5]),
                        "az": float(valores[6]),
                        "gx": float(valores[7]),
                        "gy": float(valores[8]),
                        "gz": float(valores[9]),
                        # ADXL375 (ACELERACAO DE VIBRACAO DO PAYLOAD PANDORA)
                        "vib_x": float(valores[10]),
                        "vib_y": float(valores[11]),
                        "vib_z": float(valores[12]),
                        # GPS
                        "lat": float(valores[13]),
                        "lng": float(valores[14]),
                        "sat": int(float(valores[15])),
                        "tempo_missao": float(valores[16])
                    }
                    return json.dumps(pacote).encode()
                except ValueError:
                    pass # SE HOUVER CORRUPCAO DOS DADOS, PASSA PARA A PRÓXIMA LEITURA
        return None
