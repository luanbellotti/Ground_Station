import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from medidor_circular import Medidor_Aceleracao

class PainelVibracaoMPU(QWidget):
    # TELA DE VIBRACAO DO MPU6050: 3 GRAFICOS EMPILHADOS (UM POR EIXO), CADA UM MOSTRA
    # A CURVA BRUTA x LINEARIZADA (MINIMOS QUADRADOS) - EXATAMENTE IGUAL AO PAINEL DO ADXL375 -
    # + MEDIDOR DE INTENSIDADE (%) DO MODULO.
    # E UMA ABA DENTRO DE self.abas_vibracao (ver janela.py), QUE POR SUA VEZ E A PAGINA 1
    # DA AREA CENTRAL, ALTERNADA COM A TELA 3D VIA F3 (ver botoes.py)
    def __init__(self, janela_mae=None):
        super().__init__(janela_mae)
        self.setMinimumHeight(560)

        layout_principal = QHBoxLayout()
        layout_principal.setContentsMargins(10,10,10,10)
        layout_principal.setSpacing(10)
        self.setLayout(layout_principal)

        # COLUNA DOS 3 GRAFICOS (X, Y, Z), UM EMBAIXO DO OUTRO
        coluna_graficos = QWidget()
        layout_graficos = QVBoxLayout()
        layout_graficos.setContentsMargins(0,0,0,0)
        layout_graficos.setSpacing(6)
        coluna_graficos.setLayout(layout_graficos)

        label_titulo = QLabel("PAYLOAD PANDORA — VIBRAÇÃO POR EIXO (MPU6050)")
        label_titulo.setStyleSheet("color: #FFFAFA; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_graficos.addWidget(label_titulo)

        self.grafico_x, self.curva_x_bruta, self.curva_x_linear = self._criar_grafico_eixo("Eixo X", com_legenda=True)
        self.grafico_y, self.curva_y_bruta, self.curva_y_linear = self._criar_grafico_eixo("Eixo Y")
        self.grafico_z, self.curva_z_bruta, self.curva_z_linear = self._criar_grafico_eixo("Eixo Z")

        # SO O ULTIMO GRAFICO GANHA ROTULO DO EIXO X (TEMPO) PRA ECONOMIZAR ESPACO VERTICAL
        self.grafico_z.setLabel('bottom', 'Tempo de missão', units='s')

        layout_graficos.addWidget(self.grafico_x)
        layout_graficos.addWidget(self.grafico_y)
        layout_graficos.addWidget(self.grafico_z)

        layout_principal.addWidget(coluna_graficos, stretch=3)

        # BLOCO DO MEDIDOR DE INTENSIDADE DO MPU6050
        coluna_medidor = QWidget()
        layout_medidor = QVBoxLayout()
        layout_medidor.setContentsMargins(0,0,0,0)
        layout_medidor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coluna_medidor.setLayout(layout_medidor)

        label_medidor = QLabel("INTENSIDADE (%)")
        label_medidor.setStyleSheet("color: #D478FF; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        label_medidor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_medidor.addWidget(label_medidor)

        self.medidor_vibracao_mpu = Medidor_Aceleracao("#D478FF", "Vibração MPU", 100)
        layout_medidor.addWidget(self.medidor_vibracao_mpu, alignment=Qt.AlignmentFlag.AlignCenter)

        layout_principal.addWidget(coluna_medidor, stretch=1)

        # BUFFERS PARA OS GRAFICOS EM TEMPO REAL (JANELA DESLIZANTE)
        self.tamanho_max_buffer = 300  # 30s DE HISTORICO A 10Hz
        self.buffer_tempo = []
        self.buffer_x_bruto, self.buffer_x_linear = [], []
        self.buffer_y_bruto, self.buffer_y_linear = [], []
        self.buffer_z_bruto, self.buffer_z_linear = [], []

    # CRIA UM MINI-GRAFICO PADRONIZADO PRA UM EIXO (BRUTA VERDE + LINEARIZADA LARANJA)
    # MESMAS CORES DO PAINEL DO ADXL375, DE PROPOSITO (pra ficar visualmente igual)
    def _criar_grafico_eixo(self, titulo_eixo, com_legenda=False):
        grafico = pg.PlotWidget()
        grafico.setBackground("#151515")
        grafico.showGrid(x=True, y=True, alpha=0.3)
        grafico.setLabel('left', titulo_eixo, units='m/s²')
        grafico.setMinimumHeight(140)
        if com_legenda:
            grafico.addLegend(offset=(5,5))
        curva_bruta = grafico.plot(pen=pg.mkPen('#D478FF', width=1), name="Bruta" if com_legenda else None)
        curva_linear = grafico.plot(pen=pg.mkPen('#82CFFF', width=2), name="Linearizada" if com_legenda else None)
        return grafico, curva_bruta, curva_linear

    def atualizar_vibracao_mpu(self, tempo, x_bruto, x_linear, y_bruto, y_linear, z_bruto, z_linear, intensidade_mpu_pct):
        # ATUALIZA OS BUFFERS DOS 3 GRAFICOS
        self.buffer_tempo.append(tempo)
        self.buffer_x_bruto.append(x_bruto)
        self.buffer_x_linear.append(x_linear)
        self.buffer_y_bruto.append(y_bruto)
        self.buffer_y_linear.append(y_linear)
        self.buffer_z_bruto.append(z_bruto)
        self.buffer_z_linear.append(z_linear)

        if len(self.buffer_tempo) > self.tamanho_max_buffer:
            self.buffer_tempo = self.buffer_tempo[-self.tamanho_max_buffer:]
            self.buffer_x_bruto = self.buffer_x_bruto[-self.tamanho_max_buffer:]
            self.buffer_x_linear = self.buffer_x_linear[-self.tamanho_max_buffer:]
            self.buffer_y_bruto = self.buffer_y_bruto[-self.tamanho_max_buffer:]
            self.buffer_y_linear = self.buffer_y_linear[-self.tamanho_max_buffer:]
            self.buffer_z_bruto = self.buffer_z_bruto[-self.tamanho_max_buffer:]
            self.buffer_z_linear = self.buffer_z_linear[-self.tamanho_max_buffer:]

        self.curva_x_bruta.setData(self.buffer_tempo, self.buffer_x_bruto)
        self.curva_x_linear.setData(self.buffer_tempo, self.buffer_x_linear)
        self.curva_y_bruta.setData(self.buffer_tempo, self.buffer_y_bruto)
        self.curva_y_linear.setData(self.buffer_tempo, self.buffer_y_linear)
        self.curva_z_bruta.setData(self.buffer_tempo, self.buffer_z_bruto)
        self.curva_z_linear.setData(self.buffer_tempo, self.buffer_z_linear)

        # ATUALIZA O MEDIDOR DE INTENSIDADE (%) DO MPU6050
        self.medidor_vibracao_mpu.atualizar_valor(intensidade_mpu_pct)

    def limpar_graficos(self):
        self.buffer_tempo.clear()
        self.buffer_x_bruto.clear()
        self.buffer_x_linear.clear()
        self.buffer_y_bruto.clear()
        self.buffer_y_linear.clear()
        self.buffer_z_bruto.clear()
        self.buffer_z_linear.clear()
        self.curva_x_bruta.clear()
        self.curva_x_linear.clear()
        self.curva_y_bruta.clear()
        self.curva_y_linear.clear()
        self.curva_z_bruta.clear()
        self.curva_z_linear.clear()
