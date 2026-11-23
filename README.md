# chatgpt
Chat de gpt

Hola profesor para ejecutar la vista hay que instalar los Requerimientos: 

pip install -r requirements.txt

si lo va a ejecutar en una distro Ubunto o debian: 

sudo apt update
sudo apt install -y unixodbc-dev curl gnupg
pip install -r requirements.txt


Driver para el uso de pyodbc ODBC

curl -sSL [https://packages.microsoft.com/keys/microsoft.asc](https://packages.microsoft.com/keys/microsoft.asc) | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc > /dev/null

curl -sSL "[https://packages.microsoft.com/config/ubuntu/$](https://packages.microsoft.com/config/ubuntu/$)(. /etc/os-release && echo "$VERSION_ID")/prod.list" | sudo tee /etc/apt/sources.list.d/mssql-release.list > /dev/null

sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql18


ejecutar vista desde la carpeta raiz 

python -m chats.cliente