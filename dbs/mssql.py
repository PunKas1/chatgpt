import pyodbc

import os
import platform
import pyodbc


def _resolver_driver() -> str:
    instalados = pyodbc.drivers()
    sistema = platform.system()

    if sistema == "Windows":
        candidatos = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server",
        ]
    else:
        # Linux y macOS
        candidatos = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
        ]

    for candidato in candidatos:
        if candidato in instalados:
            return candidato

    for drv in instalados:
        if "SQL Server" in drv:
            return drv

    raise RuntimeError(
        f"No se encontró un driver ODBC de SQL Server en {sistema}. "
        f"Drivers detectados: {instalados or 'ninguno'}."
    )

def obtener_conexion():
    return pyodbc.connect(
        "DRIVER=" + _resolver_driver() + ";"  # O 'ODBC Driver 18 for SQL Server'
        "SERVER=3.149.102.2;"  # O la IP de tu servidor
        "DATABASE=GANADORES;"  # El nombre de tu base de datos
        "UID=esteves;"  # Tu usuario de SQL Server
        "TrustServerCertificate=yes;"
    )


def guardar_mensaje(usuario, contenido):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO mensajes (usuario, contenido) VALUES (?, ?)",
            (usuario, contenido),
        )
        conexion.commit()
    finally:
        conexion.close()


def recuperarHistorialUnoAUno(
    usuario_actual: str, usuario_objetivo: str
) -> list[dict]:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        query = """
            SELECT m.id_mensaje, u_rem.nombre_usuario as remitente,
                   u_des.nombre_usuario as destinatario,
                   m.contenido,
                   m.fecha_envio
            FROM Mensajes m
            INNER JOIN Usuarios u_rem on m.id_remitente = u_rem.id_usuario
            INNER JOIN Usuarios u_des on m.id_destinatario = u_des.id_usuario
            WHERE
                (u_rem.nombre_usuario = ? AND u_des.nombre_usuario = ?)
                OR
                (u_rem.nombre_usuario = ? AND u_des.nombre_usuario = ?)
            ORDER BY m.fecha_envio ASC, m.id_mensaje ASC;
        """

        cursor.execute(
            query,
            (
                usuario_actual,
                usuario_objetivo,
                usuario_objetivo,
                usuario_actual,
            ),
        )

        filas = cursor.fetchall()
        historial = []

        for fila in filas:
            historial.append(
                {
                    "id_mensaje": fila.id_mensaje,
                    "remitente": fila.remitente,
                    "destinatario": fila.destinatario,
                    "contenido": fila.contenido,
                    "fecha_envio": (
                        fila.fecha_envio.isoformat()
                        if fila.fecha_envio
                        else None
                    ),
                }
            )

        return historial
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()

def _obtener_id_imagen_aleatoria(cursor) -> int | None:
    """Selecciona un id_imagen aleatorio de dbo.ImagenesPerfil usando la conexión activa."""
    cursor.execute("SELECT TOP 1 id_imagen FROM dbo.ImagenesPerfil ORDER BY NEWID()")
    fila = cursor.fetchone()
    return int(fila[0]) if fila and fila[0] is not None else None


def crear_usuario(nombre_usuario, contrasena):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id_usuario FROM dbo.Usuarios WHERE nombre_usuario = ?",
            (nombre_usuario,),
        )
        if cursor.fetchone():
            return False

        id_imagen = _obtener_id_imagen_aleatoria(cursor)
        cursor.execute(
            "INSERT INTO dbo.Usuarios (nombre_usuario, contrasena, id_imagen) VALUES (?, ?, ?)",
            (nombre_usuario, contrasena, id_imagen),
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


def obtener_todos_los_usuarios() -> list[str]:
    conexion = obtener_conexion()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT nombre_usuario FROM Usuarios ORDER BY nombre_usuario ASC"
        )
        return [fila[0].strip() for fila in cursor.fetchall() if fila[0]]
    except Exception as e:
        print(f"Error al consultar usuarios registrados: {e}")
        return []
    finally:
        conexion.close()


def guardarMensajeUnoAUno(
    remitente: str, destinatario: str, contenido: str
) -> bool:
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()

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

        ids_por_nombre = {row[1].strip().lower(): row[0] for row in filas}
        id_remitente = ids_por_nombre.get(remitente.strip().lower())
        id_destinatario = ids_por_nombre.get(destinatario.strip().lower())

        if not id_remitente or not id_destinatario:
            print(
                f"No se encontraron usuarios en BD: remitente={remitente}, destinatario={destinatario}"
            )
            return False

        # 2. Insertar incluyendo id_usuario (NOT NULL en la tabla Mensajes)
        cursor.execute(
            """
            INSERT INTO Mensajes (id_usuario, id_remitente, id_destinatario, contenido, fecha_envio)
            VALUES (?, ?, ?, ?, GETDATE())
            """,
            (id_remitente, id_remitente, id_destinatario, contenido),
        )
        conexion.commit()
        return True

    except Exception as e:
        conexion.rollback()
        print(f"Error al guardar mensaje uno a uno en SQL Server: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def crear_grupo_bd(nombre_grupo: str, id_creador: int, nombres_miembros: list[str]) -> int | None:
    """Crea el grupo, agrega al creador y a los miembros seleccionados. Retorna id_grupo."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        id_imagen = _obtener_id_imagen_aleatoria(cursor)
        cursor.execute(
            "INSERT INTO dbo.Grupos (nombre_grupo, id_creador, id_imagen) OUTPUT INSERTED.id_grupo VALUES (?, ?, ?)",
            (nombre_grupo.strip(), id_creador, id_imagen),
        )
        fila_grupo = cursor.fetchone()
        if not fila_grupo:
            return None
        id_grupo = int(fila_grupo[0])

        # Resolver IDs de todos los miembros seleccionados + asegurar al creador
        ids_miembros = {int(id_creador)}
        for nombre in nombres_miembros:
            cursor.execute(
                "SELECT id_usuario FROM dbo.Usuarios WHERE LOWER(nombre_usuario) = LOWER(?)",
                (nombre.strip(),),
            )
            row = cursor.fetchone()
            if row:
                ids_miembros.add(int(row[0]))

        for uid in ids_miembros:
            cursor.execute(
                "INSERT INTO dbo.GrupoMiembros (id_grupo, id_usuario) VALUES (?, ?)",
                (id_grupo, uid),
            )

        conexion.commit()
        return id_grupo
    except Exception as e:
        conexion.rollback()
        print(f"Error al crear grupo en SQL Server: {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()



def obtener_miembros_grupo(id_grupo: int) -> list[str]:
    """Retorna los nombres de usuario que pertenecen al grupo."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT u.nombre_usuario
            FROM dbo.Usuarios u
            INNER JOIN dbo.GrupoMiembros gm ON u.id_usuario = gm.id_usuario
            WHERE gm.id_grupo = ?
            """,
            (id_grupo,),
        )
        return [row[0].strip() for row in cursor.fetchall() if row[0]]
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def guardar_mensaje_grupo(id_grupo: int, remitente: str, contenido: str) -> bool:
    """Guarda un mensaje grupal validando primero que el remitente sea miembro."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT u.id_usuario
            FROM dbo.Usuarios u
            INNER JOIN dbo.GrupoMiembros gm ON u.id_usuario = gm.id_usuario
            WHERE gm.id_grupo = ? AND LOWER(u.nombre_usuario) = LOWER(?)
            """,
            (id_grupo, remitente.strip()),
        )
        row = cursor.fetchone()
        if not row:
            return False  # No pertenece al grupo, no tiene permiso

        id_remitente = int(row[0])
        cursor.execute(
            """
            INSERT INTO dbo.MensajesGrupo (id_grupo, id_remitente, contenido, fecha_envio)
            VALUES (?, ?, ?, GETDATE())
            """,
            (id_grupo, id_remitente, contenido),
        )
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        print(f"Error al guardar mensaje de grupo: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def recuperar_historial_grupo(id_grupo: int, usuario_solicitante: str) -> list[dict]:
    """Retorna el historial del grupo solo si el solicitante es miembro."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        # Verificar membresía
        cursor.execute(
            """
            SELECT 1
            FROM dbo.GrupoMiembros gm
            INNER JOIN dbo.Usuarios u ON gm.id_usuario = u.id_usuario
            WHERE gm.id_grupo = ? AND LOWER(u.nombre_usuario) = LOWER(?)
            """,
            (id_grupo, usuario_solicitante.strip()),
        )
        if not cursor.fetchone():
            return []

        cursor.execute(
            """
            SELECT mg.id_mensaje, u.nombre_usuario AS remitente, mg.contenido, mg.fecha_envio
            FROM dbo.MensajesGrupo mg
            INNER JOIN dbo.Usuarios u ON mg.id_remitente = u.id_usuario
            WHERE mg.id_grupo = ?
            ORDER BY mg.fecha_envio ASC, mg.id_mensaje ASC
            """,
            (id_grupo,),
        )
        return [
            {
                "id_mensaje": fila.id_mensaje,
                "remitente": fila.remitente,
                "contenido": fila.contenido,
                "fecha_envio": fila.fecha_envio.isoformat() if fila.fecha_envio else None,
            }
            for fila in cursor.fetchall()
        ]
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()

def crear_canal_bd(
    nombre_canal: str, descripcion: str, id_creador: int
) -> int | None:
    """Crea un canal en dbo.Canales con su id_creador. Retorna id_canal o None."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        id_imagen = _obtener_id_imagen_aleatoria(cursor)
        nombre_limpio = nombre_canal.strip()
        desc_limpia = descripcion.strip() if descripcion else None

        # Evitar duplicados por nombre (case-insensitive)
        cursor.execute(
            "SELECT id_canal FROM dbo.Canales WHERE LOWER(nombre_canal) = LOWER(?)",
            (nombre_limpio,),
        )
        if cursor.fetchone():
            print(f"El canal '{nombre_limpio}' ya existe en la BD.")
            return None

        cursor.execute(
            """
            INSERT INTO dbo.Canales (nombre_canal, descripcion, id_creador, id_imagen)
            OUTPUT INSERTED.id_canal
            VALUES (?, ?, ?, ?)
            """,
            (nombre_limpio, desc_limpia, int(id_creador), id_imagen),
        )
        fila = cursor.fetchone()
        if not fila:
            return None

        id_canal = int(fila[0])
        conexion.commit()
        return id_canal
    except Exception as e:
        conexion.rollback()
        print(f"Error al crear canal en SQL Server: {e}")
        return None
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()




def guardar_mensaje_canal(
    id_canal: int, remitente: str, contenido: str
) -> bool:
    """Guarda un mensaje en dbo.MensajesCanal SOLO si el remitente es el creador."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT u.id_usuario, c.id_creador
            FROM dbo.Canales c
            INNER JOIN dbo.Usuarios u ON LOWER(u.nombre_usuario) = LOWER(?)
            WHERE c.id_canal = ?
            """,
            (remitente.strip(), int(id_canal)),
        )
        fila = cursor.fetchone()
        if not fila:
            return False

        id_usuario = int(fila[0])
        id_creador = int(fila[1])

        # Regla: solo el creador del canal puede publicar
        if id_usuario != id_creador:
            return False

        cursor.execute(
            """
            INSERT INTO dbo.MensajesCanal (id_canal, id_remitente, contenido, fecha_envio)
            VALUES (?, ?, ?, GETDATE())
            """,
            (int(id_canal), id_usuario, contenido),
        )
        conexion.commit()
        return True
    except Exception as e:
        conexion.rollback()
        print(f"Error al guardar mensaje de canal: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def recuperar_historial_canal(id_canal: int) -> list[dict]:
    """Retorna todos los mensajes de un canal ordenados cronológicamente."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                mc.id_mensaje_canal,
                u.nombre_usuario AS remitente,
                mc.contenido,
                mc.fecha_envio
            FROM dbo.MensajesCanal mc
            INNER JOIN dbo.Usuarios u ON mc.id_remitente = u.id_usuario
            WHERE mc.id_canal = ?
            ORDER BY mc.fecha_envio ASC, mc.id_mensaje_canal ASC
            """,
            (int(id_canal),),
        )
        return [
            {
                "id_mensaje": fila.id_mensaje_canal,
                "remitente": fila.remitente.strip(),
                "contenido": fila.contenido,
                "fecha_envio": (
                    fila.fecha_envio.isoformat() if fila.fecha_envio else None
                ),
            }
            for fila in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Error al recuperar historial del canal: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def obtener_usuarios_con_imagen() -> list[dict]:
    """Retorna todos los usuarios con su clave_imagen asignada."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                u.id_usuario,
                u.nombre_usuario,
                ip.clave_imagen
            FROM dbo.Usuarios u
            LEFT JOIN dbo.ImagenesPerfil ip ON u.id_imagen = ip.id_imagen
            ORDER BY u.nombre_usuario ASC
            """
        )
        return [
            {
                "id_usuario": int(row.id_usuario),
                "nombre_usuario": row.nombre_usuario.strip(),
                "imagen": row.clave_imagen.strip() if row.clave_imagen else None,
            }
            for row in cursor.fetchall()
            if row.nombre_usuario
        ]
    except Exception as e:
        print(f"Error al obtener usuarios con imagen: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()

def obtener_grupos_usuario(id_usuario: int) -> list[dict]:
    """Retorna únicamente los grupos donde el usuario es miembro, con su imagen."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                g.id_grupo,
                g.nombre_grupo,
                ip.clave_imagen
            FROM dbo.Grupos g
            INNER JOIN dbo.GrupoMiembros gm ON g.id_grupo = gm.id_grupo
            LEFT JOIN dbo.ImagenesPerfil ip ON g.id_imagen = ip.id_imagen
            WHERE gm.id_usuario = ?
            ORDER BY g.nombre_grupo ASC
            """,
            (id_usuario,),
        )
        return [
            {
                "id_grupo": int(row.id_grupo),
                "nombre_grupo": row.nombre_grupo.strip(),
                "imagen": row.clave_imagen.strip() if row.clave_imagen else None,
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Error al obtener grupos del usuario: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def obtener_canales() -> list[dict]:
    """Retorna todos los canales disponibles junto con su creador e imagen."""
    conexion = obtener_conexion()
    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                c.id_canal,
                c.nombre_canal,
                c.descripcion,
                c.id_creador,
                u.nombre_usuario AS creador,
                ip.clave_imagen
            FROM dbo.Canales c
            INNER JOIN dbo.Usuarios u ON c.id_creador = u.id_usuario
            LEFT JOIN dbo.ImagenesPerfil ip ON c.id_imagen = ip.id_imagen
            ORDER BY c.nombre_canal ASC
            """
        )
        canales = []
        for fila in cursor.fetchall():
            canales.append(
                {
                    "id_canal": int(fila.id_canal),
                    "nombre_canal": fila.nombre_canal.strip(),
                    "descripcion": fila.descripcion.strip() if fila.descripcion else "",
                    "id_creador": int(fila.id_creador),
                    "creador": fila.creador.strip(),
                    "imagen": fila.clave_imagen.strip() if fila.clave_imagen else None,
                }
            )
        return canales
    except Exception as e:
        print(f"Error al obtener canales: {e}")
        return []
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()