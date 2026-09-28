from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class PainelApogeu(QWidget):
    def __init__(self, parent= None):
        super().__init__(parent)

        # CRIACAO DA CAIXA DE CONTEUDO
        self.layout_conteudo = QVBoxLayout()
        self.layout_conteudo.setContentsMargins(0,0,0,0)
        self.layout_conteudo.setSpacing(5)
        self.setLayout(self.layout_conteudo)

        # LABEL DO TITULO
        self.label_titulo = QLabel("Altura Máxima")
        self.label_titulo.setStyleSheet("color: #FFFAFA; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        self.label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_conteudo.addWidget(self.label_titulo)

        # CRIACAO DO LABEL QUE MOSTRA O VALOR
        self.label_apogeu = QLabel("Apogeu: 0.00 m")
        self.label_apogeu.setFixedHeight(60)
        # ESTILIZACAO
        self.label_apogeu.setStyleSheet("""
            background-color: #151515;
            color: #00FF00;
            font-size: 24px; 
            font-family: 'Courier New'; 
            font-weight: bold;
            border: 2px solid #333;
            border-radius: 10px;
            """)
        self.label_apogeu.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_conteudo.addWidget(self.label_apogeu)


    def atualizar_valor(self,valor):
        # ESTA FUNCAO SERA CHAMADA EM UPDATE.PY PARA ATUALIZAR O VALOR
        self.label_apogeu.setText(f"Apogeu: {valor:.2f} m")