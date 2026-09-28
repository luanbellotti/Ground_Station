from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRectF

class Medidor_Aceleracao(QWidget):
    def __init__(self, cor, nome="Aceleração", valor_maximo = 100, parent = None):
        super().__init__(parent)
        self.titulo = nome
        self.valor_maximo = valor_maximo
        self.valor_atual = 0.0
        self.cor = cor
        # DEFININDO TAMANHO MINIMO PARA O GRAFICO NAO FICAR APERTADO
        self.setMinimumSize(120,150)

    def atualizar_valor(self, novo_valor):
        # ATUALIZA O VALOR E MANDA O PYQT ATUALIZAR A TELA
        # VALOR ENTRE O MAXIMO E 0
        self.valor_atual = max(0, min(novo_valor, self.valor_maximo))
        self.update() # REALIZA O DESENHO AUTOMATICAMENTE

    def paintEvent(self, event):
        # DESENHO DO COMPONENTE
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # REMOVE O SERRILHADO DO DESENHO
        # DEFINE A AREA DO CIRCULO
        rect = QRectF(15,15,self.width() - 30, self.width() - 30)

        # DESENHA O FUNDO DO CIRCULO (CINZA ESCURO)
        cor_fundo = QPen(QColor("#444444"))
        cor_fundo.setWidth(15) # ESPESSURA DA LINHA
        painter.setPen(cor_fundo)
        # drawArc usa ângulos multiplicados por 16 para desenhar o círculo (0 a 360*16 faz o círculo completo)
        painter.drawArc(rect, 0, 360*16)

        # DESENHANDO O PROGRESSO (ARCO VERDE)
        cor_progresso = QPen(QColor(self.cor))
        cor_progresso.setWidth(15)
        cor_progresso.setCapStyle(Qt.PenCapStyle.FlatCap) # PONTA RETA
        painter.setPen(cor_progresso)

        # CALCULANDO O TAMANHO DO ARCO
        proporcao = self.valor_atual / self.valor_maximo
        # ANGULO SPAN NEGATIVO PARA PREENCHER O CIRCULO NO SENTIDO HORARIO
        angulo_span = int(-360*proporcao*16)
        angulo_inicial = 90*16 # 90 GRAUS PARA QUE O ARCO COMECE DO TOPO DO CIRCULO
        painter.drawArc(rect,angulo_inicial,angulo_span)

        # DESENHAR O TEXTO
        painter.setPen(QColor(self.cor))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        texto = f"{self.titulo}: {int(self.valor_atual)}"

        # POSICIONA O TEXTO NA BASE DO WIDGET
        rect_texto = QRectF(0, self.height() - 25, self.width(), 25)
        painter.drawText(rect_texto, Qt.AlignmentFlag.AlignCenter, texto)
        
        painter.end()


