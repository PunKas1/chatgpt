import pyodbc


def obtener_conexion():
    return pyodbc.connect(
        "DRIVER={SQL Server};"  # O 'ODBC Driver 18 for SQL Server'
        "SERVER=3.149.102.2;"  # O la IP de tu servidor
        "DATABASE=GANADORES;"  # El nombre de tu base de datos
        "UID=esteves;"  # Tu usuario de SQL Server
        "PWD=Punkas123;"
        "TrustServerCertificate=yes;"
    )


def guardar_mensaje(usuario, contenido):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # En SQL Server con pyodbc se usa '?' como marcador de parámetro
    cursor.execute(
        "INSERT INTO mensajes (usuario, contenido) VALUES (?, ?)",
        (usuario, contenido),
    )
    conexion.commit()
    conexion.close()


def obtener_historial():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT usuario, contenido FROM mensajes ORDER BY id ASC")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados