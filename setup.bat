@echo off
echo Iniciando a configuracao do ambiente...

IF NOT EXIST venv (
    echo Criando ambiente virtual...
    python -m venv venv
)

call venv\Scripts\activate

echo Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Ambiente configurado com sucesso!
echo Iniciando o programa principal...

python src\main.py
pause