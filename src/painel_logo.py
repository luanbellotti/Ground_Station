from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from pathlib import Path

class logo(QWidget):
    def __init__(self, parent= None):
        super().__init__(parent)

        # CRIACAO DA CAIXA DE CONTEUDO
        self.layout_principal = QVBoxLayout()
        self.layout_principal.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout_principal)

        # CONFIGURACAO DA IMAGEM
        self.label_imagem = QLabel()
        self.label_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_imagem.setStyleSheet("background-color: black; border-radius: 10px;")

        # BLOCO DA IMAGEM
        pasta_atual = Path(__file__).parent
        caminho_imagem = pasta_atual / ".." / "imgs" / "logo-groundstation.png"

        # CARREGA A IMAGEM
        if caminho_imagem.exists():
            pixmap = QPixmap(str(caminho_imagem))
            pixmap_redimensionado = pixmap.scaledToHeight(80, Qt.TransformationMode.SmoothTransformation)
            self.label_imagem.setPixmap(pixmap_redimensionado)
        else:
            print("Infelizmente a imagem não pôde ser carregada")
            # CASO A IMAGEM NAO FOR ENCONTRADA, CARREGA O SEGUINTE TEXTO
            self.label_imagem.setText("Kosmos \n Rocketry")
            self.label_imagem.setStyleSheet("color: white; font-weight: bold; font-size: 14px; background-color: #151515;")

        self.layout_principal.addWidget(self.label_imagem)

