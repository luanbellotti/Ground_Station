#!/bin/bash

echo "Iniciando a configuração do ambiente..."

# Verifica se o ambiente virtual já existe; se não, cria um
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual (venv)..."
    python3 -m venv venv
fi

# Ativa o ambiente virtual
source venv/bin/activate

# Atualiza o pip e instala as bibliotecas do requirements.txt
echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Ambiente configurado com sucesso!"
echo "Iniciando o programa principal..."

# Executa o seu código (substitua main.py pelo nome do seu arquivo principal)
python src\main.py