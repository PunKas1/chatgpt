import json
import socket
import threading

from dbs.mssql import (
    autenticar_usuario,
    crear_canal_bd,
    crear_grupo_bd,
    crear_usuario,
    guardar_mensaje_canal,
    guardar_mensaje_grupo,
    guardarMensajeUnoAUno,
    obtener_canales,
    obtener_grupos_usuario,
    obtener_miembros_grupo,
    obtener_usuarios_con_imagen,
    recuperar_historial_canal,
    recuperar_historial_grupo,
    recuperarHistorialUnoAUno,
)

BUFFER_SIZE = 1024
clients_lock = threading.Lock()
list_of_clients = []


class Cliente:
    def __init__(self, conn, addr):
        self.user_id = ""
        self.name = ""
        self.conn = conn
        self.addr = addr


def enviar_linea(conn, texto: str) -> bool:
    try:
        if not texto.endswith("\n"):
            texto += "\n"
        conn.sendall(texto.encode("utf-8"))
        return True
    except OSError:
        return False


def isUserConnected(user_id: str, name: str) -> bool:
    with clients_lock:
        for client in list_of_clients:
            if not client.name:
                continue
            if (user_id and str(client.user_id) == str(user_id)) or (
                client.name.lower() == name.lower()
            ):
                return True
    return False


def connected_users() -> list[str]:
    with clients_lock:
        return [c.name for c in list_of_clients if c.name]


def broadcast_connected_users():
    payload = json.dumps(connected_users(), ensure_ascii=False)
    package = f"<users>{payload}\n".encode("utf-8")

    with clients_lock:
        targets = [c for c in list_of_clients if c.name]

    for client in targets:
        try:
            client.conn.sendall(package)
        except OSError:
            remove(client)


def getCliente(connection):
    with clients_lock:
        for client in list_of_clients:
            if client.conn == connection:
                return client
        return None


def remove(target):
    removed_authenticated = False

    with clients_lock:
        for client in list(list_of_clients):
            if client is target or client.conn == target:
                list_of_clients.remove(client)
                if client.name:
                    removed_authenticated = True
                try:
                    client.conn.close()
                except OSError:
                    pass
                break

    if removed_authenticated:
        broadcast_connected_users()


# ==================== AUTENTICACIÓN Y REGISTRO ====================
def procesar_registro(conn, raw_json: str):
    try:
        datos = json.loads(raw_json)
        usuario = str(datos.get("usuario", "")).strip()
        contrasena = str(datos.get("contrasena", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        enviar_linea(conn, "<registro_err>Formato de solicitud inválido.")
        return

    if not usuario or not contrasena:
        enviar_linea(conn, "<registro_err>Completa usuario y contraseña.")
        return

    try:
        creado = crear_usuario(usuario, contrasena)
    except Exception as e:
        enviar_linea(conn, f"<registro_err>Error en base de datos: {e}")
        return

    if creado:
        enviar_linea(conn, "<registro_ok>")
    else:
        enviar_linea(conn, "<registro_err>Ese nombre de usuario ya está registrado.")


def procesar_login(cliente: Cliente, raw_json: str):
    try:
        datos = json.loads(raw_json)
        usuario = str(datos.get("usuario", "")).strip()
        contrasena = str(datos.get("contrasena", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        enviar_linea(cliente.conn, "<login_err>Formato de solicitud inválido.")
        return

    if not usuario or not contrasena:
        enviar_linea(cliente.conn, "<login_err>Completa usuario y contraseña.")
        return

    try:
        datos_usuario = autenticar_usuario(usuario, contrasena)
    except Exception as e:
        enviar_linea(cliente.conn, f"<login_err>Error en base de datos: {e}")
        return

    if not datos_usuario:
        enviar_linea(cliente.conn, "<login_err>Usuario o contraseña incorrectos.")
        return

    id_usuario, nombre_usuario = datos_usuario

    if isUserConnected(str(id_usuario), nombre_usuario):
        enviar_linea(
            cliente.conn,
            "<login_err>Este usuario ya tiene una sesión activa.",
        )
        return

    with clients_lock:
        cliente.user_id = str(id_usuario)
        cliente.name = nombre_usuario

    respuesta = json.dumps(
        {"user_id": id_usuario, "user_name": nombre_usuario},
        ensure_ascii=False,
    )
    if enviar_linea(cliente.conn, f"<login_ok>{respuesta}"):
        broadcast_connected_users()


# ==================== DATOS INICIALES, GRUPOS Y CANALES ====================
def enviar_datos_iniciales(cliente: Cliente):
    try:
        usuarios = obtener_usuarios_con_imagen()
        canales = obtener_canales()
        uid = int(cliente.user_id) if str(cliente.user_id).isdigit() else cliente.user_id
        grupos = obtener_grupos_usuario(uid)
    except Exception as e:
        print(f"Error consultando datos iniciales para {cliente.name}: {e}")
        usuarios, canales, grupos = [], [], []

    payload = json.dumps(
        {
            "usuarios": usuarios,
            "canales": canales,
            "grupos": grupos,
        },
        ensure_ascii=False,
        default=str,
    )
    if not enviar_linea(cliente.conn, f"<init_data_ok>{payload}"):
        remove(cliente)


def procesar_crear_grupo(cliente: Cliente, raw_json: str):
    try:
        datos = json.loads(raw_json)
        nombre_grupo = str(datos.get("nombre", "")).strip()
        miembros = [
            str(m).strip() for m in datos.get("miembros", []) if str(m).strip()
        ]
    except (json.JSONDecodeError, AttributeError):
        enviar_linea(cliente.conn, "<grupo_creado_err>Datos de grupo inválidos.")
        return

    if not nombre_grupo or not miembros:
        enviar_linea(
            cliente.conn,
            "<grupo_creado_err>Indica el nombre del grupo y al menos un miembro.",
        )
        return

    uid = int(cliente.user_id) if str(cliente.user_id).isdigit() else cliente.user_id
    try:
        id_grupo = crear_grupo_bd(nombre_grupo, uid, miembros)
    except Exception as e:
        enviar_linea(cliente.conn, f"<grupo_creado_err>Error de BD: {e}")
        return

    if not id_grupo:
        enviar_linea(
            cliente.conn,
            "<grupo_creado_err>No se pudo guardar el grupo en la base de datos.",
        )
        return

    grupos_usuario = obtener_grupos_usuario(uid)
    grupo_obj = next(
        (g for g in grupos_usuario if str(g.get("id_grupo")) == str(id_grupo)),
        {"id_grupo": id_grupo, "nombre_grupo": nombre_grupo, "imagen": None},
    )

    payload = json.dumps(grupo_obj, ensure_ascii=False, default=str)
    enviar_linea(cliente.conn, f"<grupo_creado_ok>{payload}")

    miembros_set = {m.lower() for m in miembros}
    miembros_set.discard(cliente.name.strip().lower())

    with clients_lock:
        targets = [
            c
            for c in list_of_clients
            if c.name and c.name.strip().lower() in miembros_set
        ]

    for target in targets:
        if not enviar_linea(target.conn, f"<nuevo_grupo>{payload}"):
            remove(target)


def procesar_crear_canal(cliente: Cliente, raw_json: str):
    try:
        datos = json.loads(raw_json)
        nombre_canal = str(datos.get("nombre", "")).strip()
        descripcion = str(datos.get("descripcion", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        enviar_linea(cliente.conn, "<canal_creado_err>Datos de canal inválidos.")
        return

    if not nombre_canal:
        enviar_linea(cliente.conn, "<canal_creado_err>Escribe un nombre para el canal.")
        return

    uid = int(cliente.user_id) if str(cliente.user_id).isdigit() else cliente.user_id
    try:
        id_canal = crear_canal_bd(nombre_canal, descripcion, uid)
    except Exception as e:
        enviar_linea(cliente.conn, f"<canal_creado_err>Error de BD: {e}")
        return

    if not id_canal:
        enviar_linea(
            cliente.conn,
            "<canal_creado_err>No se pudo crear el canal o ya existe uno con ese nombre.",
        )
        return

    canales = obtener_canales()
    canal_obj = next(
        (c for c in canales if str(c.get("id_canal")) == str(id_canal)),
        {
            "id_canal": id_canal,
            "nombre_canal": nombre_canal,
            "descripcion": descripcion,
            "id_creador": uid,
            "imagen": None,
        },
    )

    payload = json.dumps(canal_obj, ensure_ascii=False, default=str)
    enviar_linea(cliente.conn, f"<canal_creado_ok>{payload}")

    with clients_lock:
        targets = [
            c for c in list_of_clients if c.name and c.conn != cliente.conn
        ]

    for target in targets:
        if not enviar_linea(target.conn, f"<nuevo_canal>{payload}"):
            remove(target)


# ==================== HISTORIALES Y MENSAJERÍA ====================
def recuperarHistorial(client: Cliente, usuario_objetivo: str):
    if not client or not client.name or not usuario_objetivo:
        return

    mensajes = recuperarHistorialUnoAUno(
        usuario_actual=client.name,
        usuario_objetivo=usuario_objetivo,
    )
    payload = json.dumps(mensajes, ensure_ascii=False, default=str)
    if not enviar_linea(client.conn, f"<historial>{payload}"):
        remove(client)


def recuperarHistorialGrupo(client: Cliente, id_grupo: int):
    if not client or not client.name:
        return

    mensajes = recuperar_historial_grupo(
        id_grupo=id_grupo,
        usuario_solicitante=client.name,
    )
    payload = json.dumps(mensajes, ensure_ascii=False, default=str)
    if not enviar_linea(client.conn, f"<historial_grupo>{payload}"):
        remove(client)


def recuperarHistorialCanal(client: Cliente, id_canal: int):
    if not client or not client.name:
        return

    mensajes = recuperar_historial_canal(id_canal=id_canal)
    payload = json.dumps(mensajes, ensure_ascii=False, default=str)
    if not enviar_linea(client.conn, f"<historial_canal>{payload}"):
        remove(client)


def enviarMensajeGrupo(remitente_client: Cliente, id_grupo: int, contenido: str):
    if not remitente_client or not remitente_client.name or not contenido:
        return

    if not guardar_mensaje_grupo(id_grupo, remitente_client.name, contenido):
        return

    miembros_lower = {
        m.strip().lower() for m in obtener_miembros_grupo(id_grupo) if m.strip()
    }
    remitente_lower = remitente_client.name.strip().lower()
    paquete = f"<grupo_msg>{id_grupo}|{remitente_client.name}|{contenido}"

    with clients_lock:
        targets = [
            c
            for c in list_of_clients
            if c.name
            and c.name.lower() in miembros_lower
            and c.name.lower() != remitente_lower
        ]

    for client in targets:
        if not enviar_linea(client.conn, paquete):
            remove(client)


def enviarMensajeCanal(remitente_client: Cliente, id_canal: int, contenido: str):
    if not remitente_client or not remitente_client.name or not contenido:
        return

    if not guardar_mensaje_canal(id_canal, remitente_client.name, contenido):
        if not enviar_linea(
            remitente_client.conn,
            "Solo el creador del canal puede enviar mensajes.",
        ):
            remove(remitente_client)
        return

    paquete = f"<canal_msg>{id_canal}|{remitente_client.name}|{contenido}"

    with clients_lock:
        targets = [
            c
            for c in list_of_clients
            if c.name and c.conn != remitente_client.conn
        ]

    for client in targets:
        if not enviar_linea(client.conn, paquete):
            remove(client)


def broadcast(message: str, connection):
    with clients_lock:
        targets = [
            c for c in list_of_clients if c.name and c.conn != connection
        ]

    for client in targets:
        if not enviar_linea(client.conn, message):
            remove(client)


# ==================== HILO PRINCIPAL POR CLIENTE ====================
def clientthread(conn, addr):
    buffer = ""
    try:
        while True:
            chunk = conn.recv(BUFFER_SIZE)
            if not chunk:
                break

            buffer += chunk.decode("utf-8", errors="replace")
            while "\n" in buffer:
                linea, buffer = buffer.split("\n", 1)
                msg = linea.strip()
                if not msg:
                    continue

                print(f"<{addr[0]}> {msg}")
                cliente_actual = getCliente(conn)
                if not cliente_actual:
                    return

                # 1. Comandos permitidos antes de iniciar sesión
                if msg.startswith("<registro>"):
                    procesar_registro(conn, msg.removeprefix("<registro>").strip())
                    continue

                if msg.startswith("<login>"):
                    procesar_login(cliente_actual, msg.removeprefix("<login>").strip())
                    continue

                # 2. Bloquear operaciones si el cliente no ha iniciado sesión
                if not cliente_actual.name:
                    enviar_linea(conn, "<login_err>Debes iniciar sesión primero.")
                    continue

                # 3. Comandos de sesión autenticada
                if msg == "<init_data>":
                    enviar_datos_iniciales(cliente_actual)

                elif msg.startswith("<crear_grupo>"):
                    procesar_crear_grupo(
                        cliente_actual, msg.removeprefix("<crear_grupo>").strip()
                    )

                elif msg.startswith("<crear_canal>"):
                    procesar_crear_canal(
                        cliente_actual, msg.removeprefix("<crear_canal>").strip()
                    )

                elif msg.startswith("<historial>"):
                    usuario_objetivo = msg.removeprefix("<historial>").strip()
                    recuperarHistorial(cliente_actual, usuario_objetivo)

                elif msg.startswith("<grupo_msg>"):
                    payload = msg.removeprefix("<grupo_msg>")
                    if "|" not in payload:
                        continue
                    id_g_str, contenido = payload.split("|", 1)
                    id_g_str = id_g_str.strip()
                    contenido = contenido.strip()
                    if id_g_str.isdigit() and contenido:
                        enviarMensajeGrupo(
                            cliente_actual, int(id_g_str), contenido
                        )

                elif msg.startswith("<historial_grupo>"):
                    id_g_str = msg.removeprefix("<historial_grupo>").strip()
                    if id_g_str.isdigit():
                        recuperarHistorialGrupo(cliente_actual, int(id_g_str))

                elif msg.startswith("<canal_msg>"):
                    payload = msg.removeprefix("<canal_msg>")
                    if "|" not in payload:
                        continue
                    id_c_str, contenido = payload.split("|", 1)
                    id_c_str = id_c_str.strip()
                    contenido = contenido.strip()
                    if id_c_str.isdigit() and contenido:
                        enviarMensajeCanal(
                            cliente_actual, int(id_c_str), contenido
                        )

                elif msg.startswith("<historial_canal>"):
                    id_c_str = msg.removeprefix("<historial_canal>").strip()
                    if id_c_str.isdigit():
                        recuperarHistorialCanal(cliente_actual, int(id_c_str))

                elif msg.startswith("<msg>"):
                    payload = msg.removeprefix("<msg>")
                    if "|" not in payload:
                        continue
                    destinatario, contenido = payload.split("|", 1)
                    destinatario = destinatario.strip()
                    contenido = contenido.strip()
                    if not contenido:
                        continue

                    guardarMensajeUnoAUno(
                        remitente=cliente_actual.name,
                        destinatario=destinatario,
                        contenido=contenido,
                    )

                    with clients_lock:
                        objetivo_client = next(
                            (
                                c
                                for c in list_of_clients
                                if c.name
                                and c.name.lower() == destinatario.lower()
                            ),
                            None,
                        )

                    if objetivo_client:
                        paquete = f"<msg>{cliente_actual.name}|{contenido}"
                        if not enviar_linea(objetivo_client.conn, paquete):
                            remove(objetivo_client)

                else:
                    message_to_send = f"{cliente_actual.name}: {msg}"
                    broadcast(message_to_send, conn)

    except (ConnectionResetError, ConnectionAbortedError, OSError):
        pass
    finally:
        remove(conn)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 3061

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)
    server.settimeout(1.0)

    print(f"Escuchando conexiones en: {(host, port)}")
    try:
        while True:
            try:
                conn, addr = server.accept()
                conn.settimeout(None)
            except socket.timeout:
                continue

            nuevo_cliente = Cliente(conn, addr)
            with clients_lock:
                list_of_clients.append(nuevo_cliente)

            print(f"Cliente conectado: {addr}")
            threading.Thread(
                target=clientthread, args=(conn, addr), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nCaught keyboard interrupt, exiting")
    finally:
        with clients_lock:
            clients_snapshot = list(list_of_clients)
            list_of_clients.clear()

        for client in clients_snapshot:
            try:
                client.conn.close()
            except OSError:
                pass
        try:
            server.close()
        except OSError:
            pass
    print("Conexión terminada.")