from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

class PainelTempo(QWidget):
    def __init__(self, parent= None):
        super().__init__(parent)

        self.layout_principal = QHBoxLayout()
        self.layout_principal.setContentsMargins(0,0,0,0)
        self.layout_principal.setSpacing(10)
        self.setLayout(self.layout_principal)

        # BLOCO DO TEMPO DE MISSAO
        self.area_timer_missao = self.criar_area("T (MISSÃO)", "#00FFFF")
        self.label_timer_missao = self.area_timer_missao.findChild(QLabel, "valor")
        self.layout_principal.addWidget(self.area_timer_missao)

        # BLOCO DO HORARIO LOCAL
        self.area_timer_local = self.criar_area("Horário Local", "#FFFFFF")
        self.label_timer_local = self.area_timer_local.findChild(QLabel, "valor")
        self.layout_principal.addWidget(self.area_timer_local)

    def criar_area(self, titulo, cor):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)
        widget.setLayout(layout)

        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet("color: #FFFAFA; font-size: 12px; font-weight: bold; letter-spacing: 2px;")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_titulo)

        label_valor = QLabel("00:00:00")
        label_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_valor.setObjectName("valor")
        label_valor.setFixedHeight(60)
        label_valor.setStyleSheet(f"""
            background-color: #151515; 
            color: {cor}; 
            font-size: 24px; 
            font-family: 'Courier New'; 
            font-weight: bold;
            border: 2px solid #333;
            border-radius: 10px;
        """)
        layout.addWidget(label_valor)

        return widget
    
    def atualizar_tempos(self, t_mais, hora_local):
        self.label_timer_missao.setText(t_mais)
        self.label_timer_local.setText(hora_local)
