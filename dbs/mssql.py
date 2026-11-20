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
