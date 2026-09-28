from PyQt6.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt

from painel_tempo import PainelTempo
from painel_apogeu import PainelApogeu
from painel_temperatura import PainelTemperatura
from painel_logo import logo

class PainelHeader(QDockWidget):
    def __init__(self, janela_mae):
        super().__init__("Header", janela_mae)
        
        # CONFIGURACOES DA AREA UNICA
        self.setAllowedAreas(Qt.DockWidgetArea.TopDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget())
        self.setMinimumHeight(90)

        # AREA PRINCIPAL
        widget_principal = QWidget()
        layout_horizontal = QHBoxLayout()
        layout_horizontal.setContentsMargins(10,10,10,10)
        layout_horizontal.setSpacing(20) # ESPAÇO ENTRE OS PAINEIS
        layout_horizontal.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        widget_principal.setLayout(layout_horizontal)

        # INSTACIA OS PAINEIS
        self.modulo_tempo = PainelTempo()
        self.modulo_apogeu = PainelApogeu()
        self.modulo_temperatura = PainelTemperatura()
        self.modulo_logo = logo()
        self.controle_tempo_csv = None

        # ADICIONA AO LAYOUT HORIZONTAL
        layout_horizontal.addWidget(self.modulo_tempo,5)
        layout_horizontal.addWidget(self.modulo_apogeu, 3)
        layout_horizontal.addWidget(self.modulo_temperatura, 3)
        layout_horizontal.addWidget(self.modulo_logo, 1)
        self.setWidget(widget_principal)

    def atualizar_tempos(self, t_missao, hora_local):
        # FUNCAO DENTRO DO ARQUIVO PAINEL_TEMPO
        self.modulo_tempo.atualizar_tempos(t_missao, hora_local)

    def atualizar_valor(self, valor):
        # FUNCAO DENTRO DO ARQUIVO PAINEL_MAXIMOS
        self.modulo_apogeu.atualizar_valor(valor)

    def atualizar_temperatura_maxima(self, valor):
        self.modulo_temperatura.atualizar_valor(valor)

    def configurar_tempo_csv(self, leitor):
        intervalo = leitor.intervalo_tempo_csv()
        if intervalo is None:
            return

        inicio, fim = intervalo
        escala = 100
        self.controle_tempo_csv = QSlider(Qt.Orientation.Horizontal)
        self.controle_tempo_csv.setRange(round(inicio * escala), round(fim * escala))
        self.controle_tempo_csv.setValue(round(inicio * escala))
        self.controle_tempo_csv.setToolTip("Selecionar tempo da telemetria CSV")

        texto_tempo = QLabel()
        texto_tempo.setMinimumWidth(110)

        def atualizar_tempo(valor):
            tempo = valor / escala
            leitor.selecionar_tempo_csv(tempo)
            texto_tempo.setText(f"CSV: {tempo:.2f} s")

        self.controle_tempo_csv.valueChanged.connect(atualizar_tempo)
        atualizar_tempo(self.controle_tempo_csv.value())

        self.widget().layout().addWidget(texto_tempo)
        self.widget().layout().addWidget(self.controle_tempo_csv, 2)
