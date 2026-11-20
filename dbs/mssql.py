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


def recuperarHistorialUnoAUno(usuario_actual: str, usuario_objetivo: str,)->list[dict]:
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # Consulta para obtener mensajes entre dos usuarios

    query = """
        SELECT m.id_mensaje, u_rem.nombre_usuario as remitente,
         u_des.nombre_usuario as destinatario,
          m.contenido,
           m.fecha_envio
        FROM Mensajes m
        INNER JOIN Usuarios u_rem on m.id_remitente = u_rem.id_usuario
        INNER JOIN Usuarios u_des on m.id_destinatario = u_des.id_usuario
        where
            (u_rem.nombre_usuario = ? AND u_des.nombre_usuario= ?)
            OR
            (u_rem.nombre_usuario = ? AND u_des.nombre_usuario =?)

        ORDER BY  m.fecha_envio ASC, m.id_mensaje ASC;
    """

    cursor.execute(query, (usuario_actual, usuario_objetivo, usuario_objetivo, usuario_actual),
                   )

    filas = cursor.fetchall()
    historial = []

    for fila in filas:
        historial.append({
            "id_mensaje": fila.id_mensaje,
            "remitente": fila.remitente,
            "destinatario":fila.destinatario,
            "contenido": fila.contenido,
            "fecha_envio": fila.fecha_envio.isoformat() if fila.fecha_envio else None,
        })

    return historial


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

def guardarMensajeUnoAUno(remitente: str, destinatario: str, contenido: str) -> bool:
    conn = obtener_conexion()  # usa tu función actual de conexión a SQL Server
    cursor = None
    try:
        cursor = conn.cursor()

        # 1. Resolver id_remitente e id_destinatario desde la tabla de usuarios
        cursor.execute(
            """
            SELECT id_usuario, nombre_usuario
            FROM Usuarios
            WHERE LOWER(nombre_usuario) IN (LOWER(?), LOWER(?))
            """,
            (remitente.strip(), destinatario.strip()),
        )
        filas = cursor.fetchall()

        ids_por_nombre = {
            row[1].strip().lower(): row[0] for row in filas
        }
        id_remitente = ids_por_nombre.get(remitente.strip().lower())
        id_destinatario = ids_por_nombre.get(destinatario.strip().lower())

        if not id_remitente or not id_destinatario:
            print(
                f"No se encontraron usuarios en BD: remitente={remitente}, destinatario={destinatario}"
            )
            return False

        # 2. Insertar usando solo id_remitente e id_destinatario
        cursor.execute(
            """
            INSERT INTO Mensajes (id_remitente, id_destinatario, contenido, fecha_envio)
            VALUES (?, ?, ?, GETDATE())
            """,
            (id_remitente, id_destinatario, contenido),
        )
        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error al guardar mensaje uno a uno en SQL Server: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()
