from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QShortcut, QKeySequence

class config_botoes:
    def __init__(self, janela_principal, view_3d, stack_central):
        self.janela = janela_principal
        self.view = view_3d
        self.stack = stack_central
        self.seguindo = False
        self.estilo_padrao_botoes = """
            QPushButton {
                background-color: rgba(255, 255, 255, 200); 
                color: red; 
                border: 1px solid #999
                padding: 5px; 
                font-weight: bold; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: white;
                border-color: #000
            }
            QPushButton:checked{
            background-color: #4CAF50; /* aparece uma cor verde quando ativado */
            color: white;
            }
            QPushButton: unchecked{
            background-color: red;
            color: black;
            }
        """
        self.criar_botoes()

        # ATALHO PARA O F3 (ALTERNA ENTRE A TELA DE VOO 3D E AS ABAS DE VIBRACAO)
        self.atalho_f3 = QShortcut(QKeySequence("F3"), self.janela)
        self.atalho_f3.activated.connect(self.alternar_tela)

        # ATALHO PARA O F12
        self.atalho_f12 = QShortcut(QKeySequence("F12"), self.janela)
        self.atalho_f12.activated.connect(self.bt_view.click)
        # FUNCAO PARA REDIMENSIONAMENTO DA VIEW
        self.resize_original_da_view = self.view.resizeEvent
        # SUBSTITUINDO PELA FUNCAO QUE ORGANIZA OS BOTOES
        self.view.resizeEvent = self.ao_redimensionar_view

    def criar_botoes(self):
        # CRIACAO DO BOTAO QUE TROCA A VISUALIZACAO
        self.bt_view = QPushButton("F12", self.view)
        self.bt_view.setFixedSize(90,30)
        self.bt_view.setStyleSheet(self.estilo_padrao_botoes)
        self.bt_view.setCheckable(True)
        self.bt_view.clicked.connect(self.trocar_camera)
        self.bt_view.raise_()
        self.bt_view.show()

        self.posicao_dos_botoes()

    def ao_redimensionar_view(self, event):
        # FUNCAO CHAMADA SEMPRE QUE A VIEW MUDA DE TAMANHO
        self.resize_original_da_view(event)
        # RECALCULA A POSICAO DOS BOTOES
        self.posicao_dos_botoes()

    def posicao_dos_botoes(self, event = None):
        largura = self.view.width()
        self.bt_view.move(largura - 100,10)

    def alternar_tela(self):
        # ALTERNA ENTRE INDICE 0 (TELA DE VOO 3D) E INDICE 1 (ABAS DE VIBRACAO)
        novo_indice = 1 if self.stack.currentIndex() == 0 else 0
        self.stack.setCurrentIndex(novo_indice)

    def trocar_camera(self):
        self.seguindo = self.bt_view.isChecked()
        if self.seguindo:
            self.bt_view.setText("Acompanhar")
        else:
            self.bt_view.setText("Panorâmica")
            self.view.setCameraPosition(distance = 3000, elevation = 30, azimuth = 45)
