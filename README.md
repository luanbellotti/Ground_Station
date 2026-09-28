Ground Station - K.I.R.A.

Olá! Este repositório contém os arquivos e ambiente necesssários para rodar a interface gráfica de análise e visualização de dados durante competições. Logo abaixo, explicarei o objetivo de cada arquivo necessário para rodar a interface.

<img width="1919" height="1019" alt="image" src="https://github.com/user-attachments/assets/ceda6857-2615-47bd-b287-6f6fe70244ba" />

** Imagem antiga da Interface da K.I.R.A.

<img width="1918" height="1013" alt="image" src="https://github.com/user-attachments/assets/3a472ca0-05f6-44e2-a644-2841a6efab5f" />

** Imagem atual do desenvolvimento da Interface da K.I.R.A.

## Antes de tudo

Para rodar este programa em um Linux Debian, é preciso antes instalar algumas biblitecas gráficas.

**Terminal:**
1. sudo apt update
2. sudo apt install libxcb-cursor0 libx11-xcb1 libgl1-mesa-glx libqt6gui6 -y


## Como rodar o projeto

Este projeto utiliza um script de automação para criar o ambiente e instalar as dependências necessárias.

**Linux:**
1. Abra o terminal na pasta do projeto.
2. Dê permissão de execução ao script: `chmod +x setup.sh`
3. Execute: `./setup.sh`

**Windows:**
1. Dê um duplo clique no arquivo `setup.bat` ou rode `setup.bat` no terminal.

## Reproduzir um voo salvo

Para reconstruir a telemetria recebida a partir de qualquer CSV compatível com
os campos do gravador, execute:

```text
python src/main.py --csv gravador_de_voo/dados_voo_20260904_163843.csv
```

O leitor usa a coluna `Tempo` quando ela existe e também aceita CSVs sem
cabeçalho contendo os 15 valores de sensores.
"# Ground_Station" 
