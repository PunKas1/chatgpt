# chatgpt
Chat de gpt

##Configuraipn del entorno en Linux, windows 



## Configuración del entorno en Ubuntu


# 1. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Actualizar pip e instalar PySide6
pip install --upgrade pip
pip install -r requirements.txt


# 3. Ejecutar el cliente
python3 -m chats.main

