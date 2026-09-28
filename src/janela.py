import pyqtgraph.opengl as gl
import PyQt6

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStackedWidget, QTabWidget

from botoes import config_botoes
from painel_header import PainelHeader
from painel_vibracao import PainelVibracao
from painel_vibracao_mpu import PainelVibracaoMPU

class Interface(PyQt6.QtWidgets.QMainWindow):
    def __init__(self, app, foguete_mesh = None):
        super().__init__()
        self.app = app
        # CRIACAO DA JANELA PRINCIPAL
        self.setWindowTitle("K.I.R.A.")
        self.estilizar_janela()
        # TAMANHO MINIMO PRA GARANTIR QUE O HEADER + O PAINEL DE VIBRACAO SEMPRE CAIBAM
        # (SE A JANELA FOR REDIMENSIONADA MENOR QUE ISSO, O QT PODE "SUMIR" COM O DOCK QUE NAO COUBER)
        self.setMinimumSize(900, 720)
        # CRIA A VIEW 3D PRINCIPAL (TELA ANTIGA)
        self.view = gl.GLViewWidget()
        # CRIA AS AREAS DOS PAINEIS (HEADER + AS DUAS TELAS DE VIBRACAO, AINDA SEM LUGAR FIXO)
        self.setup_paineis()
        # AREA CENTRAL QUE ALTERNA ENTRE A TELA DE VOO 3D E AS ABAS DE VIBRACAO (TECLA F3)
        self.stack_central = QStackedWidget()
        self.stack_central.addWidget(self.view)           # INDICE 0: TELA DE VOO 3D (TELA ANTIGA)
        self.stack_central.addWidget(self.abas_vibracao)  # INDICE 1: ABAS ADXL375 / MPU6050
        self.setCentralWidget(self.stack_central)
        # ADICIONA OS ELEMENTOS DO CENARIO
        self.setup_cenario()

        # O FOGUETE (Respeita o mesh carregado pelo main.py)
        if foguete_mesh:
            self.foguete = foguete_mesh
        else:
            print("Interface: Criando cilindro reserva esguio para visualização realista.")
            # rows e cols definem a resolução. radius=[raio_base, raio_topo]. length=altura.
            md = gl.MeshData.cylinder(rows=20, cols=20, radius=[0.5, 0.5], length=8.0)
            self.foguete = gl.GLMeshItem(meshdata=md, smooth=True, color=(1, 0, 0, 1))
         
        self.view.addItem(self.foguete)
        # CONFIGURA A CAMERA INICIAL
        self.view.setCameraPosition(distance = 3000, elevation = 30, azimuth = 45)
        # BOTOES
        self.meus_botoes = config_botoes(self, self.view, self.stack_central)
        # EVENTO DE REDIMENSIONAMENTO
        self.resizeEvent = self.redimensionar
    
    # COLOCA BORDAS ENTRE AS JANELAS DA GROUND STATION
    def estilizar_janela(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QMainWindow::separator {
                background-color: #333333;
                width: 4px; height: 4px;
                border: 1px solid #000;
            }
            QMainWindow::separator:hover { background-color: #555; }
        """)

    def setup_paineis(self):
        # ADICIONANDO A AREA COM O HEADER
        self.area_cabecalho = PainelHeader(self)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.area_cabecalho)

        # PAINEL DO PAYLOAD (PANDORA - VIBRACAO). DOIS SENSORES, DUAS ABAS:
        # ADXL375 (painel_vibracao) E MPU6050 (painel_vibracao_mpu). ESSE QTabWidget
        # NAO E MAIS UM DOCK - VIRA A PAGINA 1 DA AREA CENTRAL (self.stack_central),
        # CRIADA LOGO ABAIXO, ALTERNADA COM A TELA 3D VIA F3.
        self.painel_vibracao = PainelVibracao(self)
        self.painel_vibracao_mpu = PainelVibracaoMPU(self)

        self.abas_vibracao = QTabWidget()
        self.abas_vibracao.setStyleSheet("""
            QTabWidget::pane { border: none; background-color: #1e1e1e; }
            QTabBar::tab {
                background-color: #2a2a2a; color: #DDDDDD;
                padding: 6px 16px; font-weight: bold;
            }
            QTabBar::tab:selected { background-color: #1e1e1e; color: #FFFAFA; }
        """)
        self.abas_vibracao.addTab(self.painel_vibracao, "ADXL375")
        self.abas_vibracao.addTab(self.painel_vibracao_mpu, "MPU6050")

    def setup_cenario(self):
        # GRID
        grid = gl.GLGridItem()
        grid.setSize(x=100000, y=100000, z=100000)
        grid.setSpacing(x=10000, y=10000, z=10000)
        self.view.addItem(grid)
        # TRILHA
        self.trilha = gl.GLLinePlotItem(color=(1,1,1,1))
        self.view.addItem(self.trilha)
        # EIXOS
        axis = gl.GLAxisItem()
        axis.setSize(x=500000, y = 500000, z = 500000)
        self.view.addItem(axis)

    def redimensionar(self, event):
        # MANUTENCAO DA LOGICA DE BOTOES AO REDIMENSIONAR
        if hasattr(self, 'meus_botoes'):
            self.meus_botoes.posicao_dos_botoes(event)
        super().resizeEvent(event)

    def configurar_tempo_csv(self, leitor):
        self.area_cabecalho.configurar_tempo_csv(leitor)
