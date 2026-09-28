import sys
from PyQt6.QtWidgets import QApplication
import subprocess
from pathlib import Path

# Importa as nossas classes
from janela import Interface
from rocket import Leitor_stl
from update import GerenciadorMissao
from leitor_data import MODO_TESTE

def main():
    processo_simulador = None
    MODO_TELA_CHEIA = False

    # SE ESTIVER NO MODO TESTE, EXECUTA O SIMULADOR COM O ARQUIVO TXT (LEMBRAR DE ALTERAR O MODO TESTE PARA FALSE, CASO VIDA REAL)
    if MODO_TESTE:
        print("main: [K.I.R.A.] Identificado Modo Teste. Ligando o Simulador_SRAD automaticamente...")
        pasta_atual = Path(__file__).parent
        caminho_simulador = pasta_atual / "simulador_SRAD.py"
        processo_simulador = subprocess.Popen([sys.executable, str(caminho_simulador.resolve())])   

    # CRIA A APLICACAO Qt
    app = QApplication(sys.argv)
    # CARREGA O FOGUETE
    leitor = Leitor_stl("basic_rocket.stl")
    mesh_foguete = leitor.carregar_foguete()
    # CRIA A JANELA PRINCIPAL
    minha_interface = Interface(app,foguete_mesh=mesh_foguete)
    # MOSTRA A JANELA
    if MODO_TELA_CHEIA == True:
        minha_interface.showFullScreen()
    else:
        minha_interface.showMaximized()
    # CRIA A LOGICA E CONECTA A JANELA
    gerente = GerenciadorMissao(minha_interface)
    minha_interface.gerente = gerente # PERMITE QUE A JANELA DO CONSOLE ACESSE O GERENTE
    gerente.iniciar() # INICIA OS TIMERS

    try:
        exit_code = app.exec()
        sys.exit(exit_code)
    finally:
        if processo_simulador and processo_simulador.poll() is None:
            print("\nmain: K.I.R.A. fechada. Desligando...")
            processo_simulador.terminate() # DESLIGA O SIMULADOR EM SEGUNDO PLANO
            processo_simulador.wait() # LIBERA A PORTA 65432 DO COMPUTADOR

if __name__ == "__main__":
    main()