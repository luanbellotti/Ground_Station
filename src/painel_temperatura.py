from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class PainelTemperatura(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout_conteudo = QVBoxLayout()
        layout_conteudo.setContentsMargins(0, 0, 0, 0)
        layout_conteudo.setSpacing(5)
        self.setLayout(layout_conteudo)

        label_titulo = QLabel("Temperatura Máxima")
        label_titulo.setStyleSheet("color: #FFFAFA; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_conteudo.addWidget(label_titulo)

        self.label_temperatura = QLabel("Máxima: -- °C")
        self.label_temperatura.setFixedHeight(60)
        self.label_temperatura.setStyleSheet("""
            background-color: #151515;
            color: #FF9F43;
            font-size: 24px;
            font-family: 'Courier New';
            font-weight: bold;
            border: 2px solid #333;
            border-radius: 10px;
            """)
        self.label_temperatura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_conteudo.addWidget(self.label_temperatura)

    def atualizar_valor(self, valor):
        self.label_temperatura.setText(f"Máxima: {valor:.2f} °C")