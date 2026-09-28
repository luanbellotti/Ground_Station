import pandas as pd
from pathlib import Path

src = Path("gravador_de_voo/Dados_pandora.csv")
df = pd.read_csv(src)

# Substitui a coluna Tempo por uma contagem de 0,5 s em 0,5 s.
if "Tempo" in df.columns:
    df["Tempo"] = [i * 0.5 for i in range(len(df))]
else:
    # Mantém o arquivo utilizável caso a coluna tenha outra capitalização.
    col = next((c for c in df.columns if c.strip().lower() == "tempo"), None)
    if col:
        df[col] = [i * 0.5 for i in range(len(df))]

out = Path("gravador_de_voo/Dados_pandora_tempo_0_5s.csv")
df.to_csv(out, index=False)
print(out)
