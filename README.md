# chatgpt
Chat de gpt

Hola profesor para ejecutar la vista hay que instalar los Requerimientos: 

pip install -r Requerimientos.txt

si lo va a ejecutar en una distro Ubunto o debian: 

sudo apt update
sudo apt install -y unixodbc-dev
pip install -r requirements.txt


Driver para el uso de pyodbc ODBC

curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev