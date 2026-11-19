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

def crear_usuario(nombre_usuario, contrasena):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        # Verificar si el usuario ya existe
        cursor.execute(
            "SELECT id_usuario FROM dbo.Usuarios WHERE nombre_usuario = ?",
            (nombre_usuario,),
        )
        if cursor.fetchone():
            return False

        cursor.execute(
            "INSERT INTO dbo.Usuarios (nombre_usuario, contrasena) VALUES (?, ?)",
            (nombre_usuario, contrasena),
        )
        conexion.commit()
        return True
    finally:
        conexion.close()

def autenticar_usuario(nombre_usuario, contrasena):
    """Retorna (id_usuario, nombre_usuario) si las credenciales son válidas, o None."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id_usuario, nombre_usuario FROM dbo.Usuarios WHERE nombre_usuario = ? AND contrasena = ?",
            (nombre_usuario, contrasena),
        )
        return cursor.fetchone()
    finally:
        conexion.close()