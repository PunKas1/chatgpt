# chatgpt
Chat de gpt

##Configuraipn del entorno en Fedora

### 1. Instalar dependencias del sistema y el driver ODBC 18 de SQL Server

Instala las herramientas base y las cabeceras de desarrollo de `unixODBC`:

```bash

sudo dnf install -y unixODBC-devel curl gnupg2

sudo curl -fsSL [https://packages.microsoft.com/config/rhel/9/prod.repo](https://packages.microsoft.com/config/rhel/9/prod.repo) | sudo tee /etc/yum.repos.d/mssql-release.repo > /dev/null

sudo ACCEPT_EULA=Y dnf install -y msodbcsql18

#Verificar instalacion:

odbcinst -q -d

#crear entorno virtual

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

#verificar conexcion a sqlserver

python3 -c "import pyodbc; print(pyodbc.drivers())"



## Configuración del entorno en Ubuntu

# 1. Actualizar repositorios e instalar Python, venv y librerías gráficas de Qt
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 \
    libxcb-shape0 libxcb-xfixes0 libgl1 libegl1 libdbus-1-3 libfontconfig1

# 2. Entrar a la carpeta del proyecto cliente
# (Asegúrate de que solo estén: chats/, uis/, images/ y requirements.txt; sin dbs/)
cd /ruta/de/tu/proyecto_cliente

# 3. Generar el requirements.txt exclusivo del cliente
echo "PySide6" > requirements.txt

# 4. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 5. Actualizar pip e instalar PySide6
pip install --upgrade pip
pip install -r requirements.txt

# 6. Verificar que PySide6 cargue correctamente (debe imprimir la versión sin errores)
python3 -c "import PySide6; print('PySide6 listo:', PySide6.__version__)"

# 7. Ejecutar el cliente
python3 chats/main.py


##Configuración del entorno en macOS

Instalar Homebrew y el driver ODBC 18 de SQL Server

brew tap microsoft/mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools18 unixodbc

odbcinst -q -d

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python3 -c "import pyodbc; print(pyodbc.drivers())"