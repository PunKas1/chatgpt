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

### 1. Instalar dependencias del sistema y el driver ODBC 18 de SQL Server

Actualiza índices e instala las herramientas y cabeceras de desarrollo de `unixODBC`:

```bash
sudo apt-get update
sudo apt-get install -y unixodbc-dev curl gnupg


curl -sSL [https://packages.microsoft.com/keys/microsoft.asc](https://packages.microsoft.com/keys/microsoft.asc) | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc > /dev/null

curl -sSL "[https://packages.microsoft.com/config/ubuntu/$](https://packages.microsoft.com/config/ubuntu/$)(. /etc/os-release && echo "$VERSION_ID")/prod.list" | sudo tee /etc/apt/sources.list.d/mssql-release.list > /dev/null

sudo apt-get update

sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

#verificar registro

odbcinst -q -d

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python3 -c "import pyodbc; print(pyodbc.drivers())"```


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