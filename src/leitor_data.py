import json
import os
import serial
from pathlib import Path
from serial.tools import list_ports
import time
import csv
from bisect import bisect_left


# ============================================================
# CONFIGURAÇÕES
# ============================================================

MODO_TESTE = False
MODO_CSV = False

ARQUIVO_CSV_TESTE = (
    r"C:\Users\LUAN BELLOTTI\Kosmos\Ground_Station_v2"
    r"\Ground-Station_2026-main\gravador_de_voo\dados_voo_20260904_163843.csv"
)



# ============================================================
# PROCURA AUTOMÁTICA PELO ESP32
# ============================================================

def find_esp():

    for p in list_ports.comports():

        desc = (p.description or "").lower()

        if "ch340" in desc or "cp210" in desc or "usb" in desc:

            if "bluetooth" not in desc:
                return p.device

    return None


# ============================================================
# LEITOR SERIAL / CSV
# ============================================================

class LeitorSerial:

    def __init__(self, porta="COM7", baudrate=9600):

        self.modo_teste = MODO_TESTE
        self.modo_csv = MODO_CSV

        # ----------------------------------------------------
        # TEMPO DE INÍCIO DA MISSÃO
        # ----------------------------------------------------

        self.tempo_inicio_missao = time.perf_counter()

        # ----------------------------------------------------
        # MODO CSV
        # ----------------------------------------------------

        if self.modo_csv:

            caminho_csv = Path(ARQUIVO_CSV_TESTE)

            if not caminho_csv.exists():
                raise Exception(
                    f"Arquivo CSV não encontrado: {caminho_csv.resolve()}"
                )

            print(
                f"Modo CSV ativado.\n"
                f"Lendo arquivo: {caminho_csv.resolve()}"
            )

            self.arquivo_csv = open(
                caminho_csv,
                "r",
                encoding="utf-8",
                newline=""
            )

            self.linhas_csv = list(csv.DictReader(self.arquivo_csv))
            self.tempos_csv = [float(linha["Tempo"]) for linha in self.linhas_csv]
            self.indice_csv = 0

            # Não precisamos de conexão serial
            self.conexao = None

            # ------------------------------------------------
            # CRIA NOVO ARQUIVO DE SAÍDA
            # ------------------------------------------------

            timestamp = time.strftime("%Y%m%d_%H%M%S")

            nome_arquivo = f"dados_processados_{timestamp}.csv"

            pasta_atual = Path(__file__).parent

            caminho_docs = (
                pasta_atual
                / ".."
                / "gravador_de_voo"
                / nome_arquivo
            )

            self.ficheiro_log = caminho_docs.resolve()

            self.ficheiro_log.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                self.ficheiro_log,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    "Temperatura,"
                    "Pressao,"
                    "Umidade,"
                    "Altitude,"
                    "ax,"
                    "ay,"
                    "az,"
                    "gx,"
                    "gy,"
                    "gz,"
                    "vib_x,"
                    "vib_y,"
                    "vib_z,"
                    "Latitude,"
                    "Longitude,"
                    "Tempo\n"
                )

            print(
                f"Arquivo de saída:\n"
                f"{self.ficheiro_log}"
            )

            return

        # ====================================================
        # MODO SERIAL NORMAL
        # ====================================================

        porta_detectada = find_esp()

        if porta_detectada is None:

            if not self.modo_teste:
                raise Exception("ESP32 não conectado")

            porta_detectada = porta

        try:

            if self.modo_teste:

                self.conexao = serial.serial_for_url(
                    "socket://127.0.0.1:65432",
                    timeout=0.1
                )

            else:

                print(
                    f"K.I.R.A ligada à porta física "
                    f"{porta_detectada} (MODO REAL)..."
                )

                self.conexao = serial.Serial(
                    porta_detectada,
                    baudrate,
                    timeout=0.1
                )

                self.conexao.reset_input_buffer()

        except Exception as e:

            print(f"ERRO DE CONEXAO: {e}")

            print(
                "Verifique se o ESP32 está conectado "
                "e se a porta serial está disponível!"
            )

            return

        # ----------------------------------------------------
        # ARQUIVO CSV
        # ----------------------------------------------------

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        nome_arquivo = f"dados_voo_{timestamp}.csv"

        pasta_atual = Path(__file__).parent

        caminho_docs = (
            pasta_atual
            / ".."
            / "gravador_de_voo"
            / nome_arquivo
        )

        self.ficheiro_log = caminho_docs.resolve()

        self.ficheiro_log.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not os.path.exists(self.ficheiro_log):

            with open(
                self.ficheiro_log,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    "Temperatura,"
                    "Pressao,"
                    "Umidade,"
                    "Altitude,"
                    "ax,"
                    "ay,"
                    "az,"
                    "gx,"
                    "gy,"
                    "gz,"
                    "vib_x,"
                    "vib_y,"
                    "vib_z,"
                    "Latitude,"
                    "Longitude,"
                    "Tempo\n"
                )


    # ========================================================
    # LEITURA
    # ========================================================

    def selecionar_tempo_csv(self, tempo):

        if not self.modo_csv or not self.tempos_csv:
            return

        indice = bisect_left(self.tempos_csv, float(tempo))
        self.indice_csv = min(indice, len(self.linhas_csv) - 1)

    def intervalo_tempo_csv(self):

        if not self.modo_csv or not self.tempos_csv:
            return None

        return self.tempos_csv[0], self.tempos_csv[-1]

    def readLine(self):

        # ====================================================
        # MODO CSV
        # ====================================================

        if self.modo_csv:

            if self.indice_csv >= len(self.linhas_csv):

                print("Fim do arquivo CSV.")

                return None

            linha = self.linhas_csv[self.indice_csv]
            self.indice_csv += 1

            try:

                temperatura = float(linha["Temperatura"])
                pressao = float(linha["Pressao"])
                umidade = float(linha["Umidade"])
                altitude = float(linha["Altitude"])

                ax = float(linha["ax"])
                ay = float(linha["ay"])
                az = float(linha["az"])

                gx = float(linha["gx"])
                gy = float(linha["gy"])
                gz = float(linha["gz"])

                vib_x = float(linha["vib_x"])
                vib_y = float(linha["vib_y"])
                vib_z = float(linha["vib_z"])

                latitude = float(linha["Latitude"])
                longitude = float(linha["Longitude"])

            except (ValueError, KeyError) as e:

                print(f"Erro ao ler linha do CSV: {e}")

                return None

            try:
                tempo_decorrido = float(linha.get("Tempo", ""))
            except ValueError:
                tempo_decorrido = (
                    time.perf_counter()
                    - self.tempo_inicio_missao
                )

            # ------------------------------------------------
            # TEMPO
            # ------------------------------------------------

            # ------------------------------------------------
            # GRAVA NOVO CSV
            # ------------------------------------------------

            with open(
                self.ficheiro_log,
                "a",
                encoding="utf-8"
            ) as f:

                f.write(
                    f"{temperatura:.2f},"
                    f"{pressao:.2f},"
                    f"{umidade:.2f},"
                    f"{altitude:.2f},"
                    f"{ax:.2f},"
                    f"{ay:.2f},"
                    f"{az:.2f},"
                    f"{gx:.3f},"
                    f"{gy:.3f},"
                    f"{gz:.3f},"
                    f"{vib_x:.2f},"
                    f"{vib_y:.2f},"
                    f"{vib_z:.2f},"
                    f"{latitude:.6f},"
                    f"{longitude:.6f},"
                    f"{tempo_decorrido:.2f}\n"
                )

            # ------------------------------------------------
            # PACOTE PARA A K.I.R.A.
            # ------------------------------------------------

            pacote = {

                "temp": temperatura,

                "pressao": pressao,

                "umidade": umidade,

                "alt": altitude,

                "ax": ax,
                "ay": ay,
                "az": az,

                "gx": gx,
                "gy": gy,
                "gz": gz,

                "vib_x": vib_x,
                "vib_y": vib_y,
                "vib_z": vib_z,

                "lat": latitude,
                "lng": longitude,

                "tempo_missao": tempo_decorrido
            }

            return json.dumps(pacote).encode()

        # ====================================================
        # MODO SERIAL NORMAL
        # ====================================================

        if not hasattr(self, "conexao"):

            return None

        try:

            linha_bytes = self.conexao.readline()

        except serial.SerialException:

            return None

        if not linha_bytes:

            return None

        linha_texto = linha_bytes.decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if not linha_texto:

            return None

        valores = linha_texto.split(",")

        if len(valores) != 15:

            return None

        try:

            temperatura = float(valores[0])
            pressao = float(valores[1])
            umidade = float(valores[2])
            altitude = float(valores[3])

            ax = float(valores[4])
            ay = float(valores[5])
            az = float(valores[6])

            gx = float(valores[7])
            gy = float(valores[8])
            gz = float(valores[9])

            vib_x = float(valores[10])
            vib_y = float(valores[11])
            vib_z = float(valores[12])

            latitude = float(valores[13])
            longitude = float(valores[14])

        except ValueError:

            return None

        tempo_decorrido = (
            time.perf_counter()
            - self.tempo_inicio_missao
        )

        with open(
            self.ficheiro_log,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                f"{temperatura:.2f},"
                f"{pressao:.2f},"
                f"{umidade:.2f},"
                f"{altitude:.2f},"
                f"{ax:.2f},"
                f"{ay:.2f},"
                f"{az:.2f},"
                f"{gx:.3f},"
                f"{gy:.3f},"
                f"{gz:.3f},"
                f"{vib_x:.2f},"
                f"{vib_y:.2f},"
                f"{vib_z:.2f},"
                f"{latitude:.6f},"
                f"{longitude:.6f},"
                f"{tempo_decorrido:.2f}\n"
            )

        pacote = {

            "temp": temperatura,
            "pressao": pressao,
            "umidade": umidade,
            "alt": altitude,

            "ax": ax,
            "ay": ay,
            "az": az,

            "gx": gx,
            "gy": gy,
            "gz": gz,

            "vib_x": vib_x,
            "vib_y": vib_y,
            "vib_z": vib_z,

            "lat": latitude,
            "lng": longitude,

            "tempo_missao": tempo_decorrido
        }

        return json.dumps(pacote).encode()


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    leitor = LeitorSerial()

    print("\n===== INICIANDO TESTE =====\n")

    while True:

        dados = leitor.readLine()

        if dados is None:
            break

        print(dados.decode())

        # Pequena pausa para simular a chegada dos dados
        time.sleep(0.1)

    print("\n===== TESTE FINALIZADO =====")