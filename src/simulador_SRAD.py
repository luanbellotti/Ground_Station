import socket 
import time
from pathlib import Path

# ENCONTRANDO O ARQUIVO PRESENTE EM OUTRA PASTA
arquivo = Path(__file__).parent
caminho_traj = arquivo / ".." / "docs" / "dados_LoRa_fake.txt"
HOST = '127.0.0.1'
PORTA = 65432

def radar_voo_real():
    print("---Iniciando Transmissor de Telemetria em Tempo Real (fake)---")

    # ESTA PARTE ESTABELECE A CONEXAO DE PORTAS VIRTUAIS
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind((HOST,PORTA))
        servidor.listen()
        print(f"---Antena SRAD ligada! Aguardando Ground Station na Porta {PORTA}---")

        conexao, endereco = servidor.accept()

        with conexao:
            print("---Ground Station conectada! Reproduzindo voo---")
            try: 
                with open(caminho_traj, 'r', encoding='utf-8') as arquivo_txt:

                    cabecalho = arquivo_txt.readline() # IGNORA A PRIMEIRA LINHA DE TEXTO

                    for linha in arquivo_txt:
                        if not linha.strip():
                            continue

                        # ENVIO DA LINHA DO TXT PELO SOCKET
                        conexao.sendall(linha.encode('utf-8'))
                        """print(f"Enviando: {linha.strip()}")
                        ---------------PARA FICAR PRINTANDO NO TERMINAL O QUE SERÁ ENVIADO PARA O DOCUMENTO-------------
                        """
                        # 10 Hz de atraso 
                        time.sleep(0.10)
            except FileNotFoundError:
                    print(f"ERRO: Arquivo {caminho_traj} não encontrado")
            except Exception as e:
                        print(f"A conexão caiu: {e}")

if __name__ == "__main__":
    radar_voo_real()