import math
import random
from pathlib import Path

def gerar_voo_longo():
    cabecalho = "Temperatura (°C),Pressão (Pa),Umidade (%),Altitude (m),ax (m/s^2),ay (m/s^2),az (m/s^2),gx (°/s),gy (°/s),gz (°/s),vib_x (m/s^2),vib_y (m/s^2),vib_z (m/s^2),Latitude,Longitude,Satélites Visíveis\n"
    linhas = [cabecalho]

    t = 0.0
    dt = 0.10 # 10Hz (Para bater com o time.sleep(0.10) do seu simulador)
    
    # Condições Iniciais
    z, x, y = 0.0, 0.0, 0.0
    vz, vx, vy = 0.0, 15.0, 5.0 # Já sai com um pequeno vento lateral
    
    lat_0, lon_0 = -27.600000, -48.520000
    fase = "PROPULSAO"

    print("Calculando física de voo suborbital...")

    while t <= 400.0: # 400 segundos de voo = 4.000 linhas!
        
        if fase == "PROPULSAO":
            az_base = 70.0 # Motor fortíssimo (Acelera a ~7G)
            vz += az_base * dt
            
            # Giroscópio tremendo muito por causa do motor
            gx, gy, gz = random.gauss(0, 5), random.gauss(0, 5), random.gauss(0, 10)
            
            if t > 6.0: # Motor desliga aos 6 segundos
                fase = "COAST"

        elif fase == "COAST":
            az_base = -9.81 # Apenas a gravidade freando o foguete
            vz += az_base * dt
            
            # Foguete começa a tombar (Gravity Turn)
            gx, gy, gz = random.gauss(0, 1), -4.0 + random.gauss(0, 1), random.gauss(0, 1)
            
            if vz < 0 and z > 100: # Chegou no Apogeu!
                fase = "DROGUE"

        elif fase == "DROGUE":
            az_base = 0.0
            vz = -35.0 # Cai rápido com o paraquedas piloto (drogue)
            vx, vy = 20.0, 10.0 # Vento empurra mais rápido lá no alto
            
            # Balanço do pêndulo agressivo
            gx = 30.0 * math.sin(t * 4) + random.gauss(0, 2)
            gy = 30.0 * math.cos(t * 4) + random.gauss(0, 2)
            gz = 10.0 * math.sin(t * 2) + random.gauss(0, 2)

            if z < 1000.0: # Aos 1000m de altitude, abre o principal
                fase = "MAIN"

        elif fase == "MAIN":
            az_base = 0.0
            vz = -6.0 # Queda muito suave (paraquedas principal)
            vx, vy = 5.0, 2.0 # Vento mais fraco perto do chão
            
            # Balanço suave
            gx = 10.0 * math.sin(t * 1.5) + random.gauss(0, 0.5)
            gy = 10.0 * math.cos(t * 1.5) + random.gauss(0, 0.5)
            gz = 2.0 * math.sin(t * 1) + random.gauss(0, 0.5)

            if z <= 0:
                z, vz, vx, vy = 0.0, 0.0, 0.0, 0.0
                gx, gy, gz, az_base = 0.0, 0.0, 0.0, 0.0
                fase = "POUSO"

        # Integração da Posição
        z += vz * dt
        x += vx * dt
        y += vy * dt

        # Conversão Metros -> Coordenadas GPS
        lat_atual = lat_0 + (y / 111320.0)
        lon_atual = lon_0 + (x / (111320.0 * math.cos(math.radians(lat_0))))

        # Sensores (Com ruído)
        ax = random.gauss(0, 0.5) if fase != "POUSO" else random.gauss(0, 0.05)
        ay = random.gauss(0, 0.5) if fase != "POUSO" else random.gauss(0, 0.05)
        az = az_base + random.gauss(0, 0.5) if fase != "POUSO" else random.gauss(0, 0.05)
        
        temp = max(-50.0, 28.0 - (0.0065 * z)) # Temperatura cai com a altitude
        pressao = 101325 * math.pow(max(0.1, 1 - (2.25577e-5 * z)), 5.25588)
        umidade = max(0.0, min(100.0, 70.0 - (0.008 * z) + random.gauss(0, 1.0))) # Cai com a altitude (aprox.)

        # RUIDO ARTIFICIAL DE VIBRACAO (ADXL375) - PARA VALIDAR O ALGORITMO DE MINIMOS
        # QUADRADOS DO update.py ANTES DO VOO REAL. AMPLITUDE/FREQUENCIA VARIAM POR FASE.
        if fase == "PROPULSAO":
            amplitude_vib, freq_vib = 12.0, 18.0   # Motor queimando = vibração forte
        elif fase == "COAST":
            amplitude_vib, freq_vib = 2.0, 6.0     # Voo balístico = vibração leve
        elif fase == "DROGUE":
            amplitude_vib, freq_vib = 6.0, 10.0    # Abertura do drogue = turbulência
        elif fase == "MAIN":
            amplitude_vib, freq_vib = 1.5, 4.0     # Descida sob o principal = suave
        else:
            amplitude_vib, freq_vib = 0.2, 1.0     # Pouso = quase parado

        vib_x = ax + amplitude_vib * math.sin(t * freq_vib) + random.gauss(0, amplitude_vib * 0.3)
        vib_y = ay + amplitude_vib * math.cos(t * freq_vib * 1.1) + random.gauss(0, amplitude_vib * 0.3)
        vib_z = az + amplitude_vib * math.sin(t * freq_vib * 0.9 + 1.0) + random.gauss(0, amplitude_vib * 0.3)

        # SATELITES GPS VISIVEIS - CAI UM POUCO NAS FASES DE MAIS VIBRACAO/ROTACAO (o receptor
        # perde lock com mais facilidade), MELHORA NAS FASES CALMAS. VALOR INTEIRO (0-12).
        if fase == "PROPULSAO":
            faixa_sat = (4, 8)     # motor vibrando forte = mais dificil manter o fix
        elif fase == "COAST":
            faixa_sat = (8, 12)    # voo balistico, fix bom
        elif fase == "DROGUE":
            faixa_sat = (6, 10)    # balanco do pendulo atrapalha um pouco
        elif fase == "MAIN":
            faixa_sat = (8, 12)    # descida suave, fix bom
        else:
            faixa_sat = (9, 12)    # pouso, parado, melhor fix possivel
        num_sat = random.randint(*faixa_sat)

        linha = f"{temp:.2f},{pressao:.2f},{umidade:.2f},{z:.2f},{ax:.2f},{ay:.2f},{az:.2f},{gx:.2f},{gy:.2f},{gz:.2f},{vib_x:.2f},{vib_y:.2f},{vib_z:.2f},{lat_atual:.6f},{lon_atual:.6f},{num_sat}\n"
        linhas.append(linha)
        t += dt

    # Salva o arquivo na mesma estrutura do seu projeto
    pasta_atual = Path(__file__).parent
    caminho_salvar = pasta_atual / ".." / "docs" / "dados_LoRa_fake.txt"
    caminho_salvar.parent.mkdir(parents=True, exist_ok=True)
    
    with open(caminho_salvar.resolve(), "w", encoding="utf-8") as f:
        f.writelines(linhas)
        
    print(f"Sucesso! Voo Épico gerado com {len(linhas)-1} linhas!")

if __name__ == "__main__":
    gerar_voo_longo()