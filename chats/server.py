import json
import socket
import threading

from dbs.mssql import (
    guardar_mensaje_canal,
    guardar_mensaje_grupo,
    guardarMensajeUnoAUno,
    obtener_canales,
    obtener_miembros_grupo,
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


def isUserConnected(user_id: str, name: str) -> bool:
    with clients_lock:
        for client in list_of_clients:
            if not client.name:
                continue
            if (user_id and client.user_id == user_id) or (
                client.name.lower() == name.lower()
            ):
                return True
    return False


def broadcast_connected_users():
    users = ",".join(connected_users())
    package = f"<users>{users}</users>\n".encode("utf-8")

    with clients_lock:
        targets = list(list_of_clients)

    for client in targets:
        try:
            client.conn.sendall(package)
        except OSError:
            remove(client)


def setName(connection, raw_payload: str) -> bool:
    datos = raw_payload.strip()
    user_id, nombre = datos.split("|", 1) if "|" in datos else ("", datos)
    user_id = user_id.strip()
    nombre = nombre.strip()

    if not nombre:
        return False

    if isUserConnected(user_id, nombre):
        try:
            connection.sendall("<!!duplicate!!>\n".encode("utf-8"))
        except OSError:
            pass
        return False

    with clients_lock:
        for client in list_of_clients:
            if client.conn == connection:
                client.user_id = user_id
                client.name = nombre
                break

    broadcast_connected_users()
    return True


def getName(connection) -> str:
    with clients_lock:
        for client in list_of_clients:
            if client.conn == connection:
                return client.name
        return ""


def getCliente(connection):
    with clients_lock:
        for client in list_of_clients:
            if client.conn == connection:
                return client
        return None


def recuperarHistorial(client, usuario_objetivo: str):
    if not client or not client.name or not usuario_objetivo:
        return

    mensajes = recuperarHistorialUnoAUno(
        usuario_actual=client.name,
        usuario_objetivo=usuario_objetivo,
    )
    payload = json.dumps(
        {
            "con_usuario": usuario_objetivo,
            "mensajes": mensajes,
        },
        ensure_ascii=False,
    )

    try:
        client.conn.sendall(f"<historial_data>{payload}\n".encode("utf-8"))
    except OSError:
        remove(client)


def recuperarHistorialGrupo(client, id_grupo: int):
    if not client or not client.name:
        return

    mensajes = recuperar_historial_grupo(
        id_grupo=id_grupo,
        usuario_solicitante=client.name,
    )
    payload = json.dumps(
        {
            "id_grupo": id_grupo,
            "mensajes": mensajes,
        },
        ensure_ascii=False,
    )

    try:
        client.conn.sendall(f"<historial_grupo_data>{payload}\n".encode("utf-8"))
    except OSError:
        remove(client)

def recuperarHistorialCanal(client, id_canal: int):
    if not client or not client.name:
        return

    mensajes = recuperar_historial_canal(id_canal=id_canal)
    payload = json.dumps(
        {
            "id_canal": id_canal,
            "mensajes": mensajes,
        },
        ensure_ascii=False,
    )

    try:
        client.conn.sendall(f"<historial_canal_data>{payload}\n".encode("utf-8"))
    except OSError:
        remove(client)


def notificarNuevoGrupo(id_grupo: str, nombre_grupo: str, miembros_csv: str, clave_imagen:str):
    miembros_set = {
        m.strip().lower() for m in miembros_csv.split(",") if m.strip()
    }
    if not miembros_set:
        return

    paquete = f"<nuevo_grupo>{id_grupo}|{nombre_grupo}|{clave_imagen}\n".encode("utf-8")

    with clients_lock:
        targets = [
            c for c in list_of_clients if c.name and c.name.lower() in miembros_set
        ]

    for client in targets:
        try:
            client.conn.sendall(paquete)
        except OSError:
            remove(client)

def notificarNuevoCanal(
    id_canal: str, nombre_canal: str, descripcion: str, id_creador: str, clave_imagen:str):
    if not nombre_canal:
        return

    paquete = (
        f"<nuevo_canal>{id_canal}|{nombre_canal}|{descripcion}|{id_creador}|{clave_imagen}\n"
    ).encode("utf-8")

    with clients_lock:
        targets = [c for c in list_of_clients if c.name]

    for client in targets:
        try:
            client.conn.sendall(paquete)
        except OSError:
            remove(client)


def enviarMensajeGrupo(remitente_client, id_grupo: int, contenido: str):
    if not remitente_client or not remitente_client.name or not contenido:
        return

    # Valida en SQL Server que el remitente sea miembro del grupo antes de guardar y reenviar
    if not guardar_mensaje_grupo(id_grupo, remitente_client.name, contenido):
        return

    miembros_lower = {
        m.strip().lower() for m in obtener_miembros_grupo(id_grupo) if m.strip()
    }
    remitente_lower = remitente_client.name.strip().lower()
    paquete = f"<grupo_msg>{id_grupo}|{remitente_client.name}|{contenido}\n".encode(
        "utf-8"
    )

    with clients_lock:
        targets = [
            c
            for c in list_of_clients
            if c.name
            and c.name.lower() in miembros_lower
            and c.name.lower() != remitente_lower
        ]

    for client in targets:
        try:
            client.conn.sendall(paquete)
        except OSError:
            remove(client)

def enviarMensajeCanal(remitente_client, id_canal: int, contenido: str):
    if not remitente_client or not remitente_client.name or not contenido:
        return

    # Valida en SQL Server que remitente_client.name sea el creador del canal y guarda en MensajesCanal
    if not guardar_mensaje_canal(id_canal, remitente_client.name, contenido):
        try:
            aviso = "Solo el creador del canal puede enviar mensajes.\n".encode(
                "utf-8"
            )
            remitente_client.conn.sendall(aviso)
        except OSError:
            remove(remitente_client)
        return

    paquete = (
        f"<canal_msg>{id_canal}|{remitente_client.name}|{contenido}\n"
    ).encode("utf-8")

    with clients_lock:
        targets = [
            c
            for c in list_of_clients
            if c.name and c.conn != remitente_client.conn
        ]

    for client in targets:
        try:
            client.conn.sendall(paquete)
        except OSError:
            remove(client)


def broadcast(message: str, connection):
    with clients_lock:
        targets = [c for c in list_of_clients if c.conn != connection]

    for client in targets:
        try:
            client.conn.sendall(message.encode("utf-8"))
        except OSError:
            remove(client)


def remove(target):
    removed = False

    with clients_lock:
        for client in list(list_of_clients):
            if client is target or client.conn == target:
                list_of_clients.remove(client)
                try:
                    client.conn.close()
                except OSError:
                    pass
                removed = True
                break

    if removed:
        broadcast_connected_users()


def connected_users() -> list[str]:
    with clients_lock:
        return [c.name for c in list_of_clients if c.name]


def clientthread(conn, addr):
    try:
        conn.sendall(f"Bienvenido {addr}\n".encode("utf-8"))
    except OSError:
        pass

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

                if msg.startswith("<name>"):
                    ok = setName(conn, msg.removeprefix("<name>"))
                    if not ok:
                        return
                elif msg.startswith("<command>"):
                    broadcast(msg + "\n", conn)
                elif msg.startswith("<historial>"):
                    usuario_objetivo = msg.removeprefix("<historial>").strip()
                    cliente_actual = getCliente(conn)
                    if cliente_actual:
                        recuperarHistorial(cliente_actual, usuario_objetivo)
                elif msg.startswith("<nuevo_grupo>"):
                    partes = msg.removeprefix("<nuevo_grupo>").split("|", 3)
                    if len(partes) >= 3:
                        id_g = partes[0].strip()
                        nom_g = partes[1].strip()
                        miembros_csv = partes[2]
                        img_g = partes[3].strip() if len(partes) >= 4 else ""
                        notificarNuevoGrupo(id_g, nom_g, miembros_csv, img_g)
                elif msg.startswith("<grupo_msg>"):
                    payload = msg.removeprefix("<grupo_msg>")
                    if "|" not in payload:
                        continue
                    id_g_str, contenido = payload.split("|", 1)
                    id_g_str = id_g_str.strip()
                    contenido = contenido.strip()
                    cliente_actual = getCliente(conn)
                    if id_g_str.isdigit() and cliente_actual and contenido:
                        enviarMensajeGrupo(
                            cliente_actual, int(id_g_str), contenido
                        )
                elif msg.startswith("<historial_grupo>"):
                    id_g_str = msg.removeprefix("<historial_grupo>").strip()
                    cliente_actual = getCliente(conn)
                    if id_g_str.isdigit() and cliente_actual:
                        recuperarHistorialGrupo(cliente_actual, int(id_g_str))
                elif msg.startswith("<nuevo_canal>"):
                    partes = msg.removeprefix("<nuevo_canal>").split("|", 4)
                    if len(partes) >= 2:
                        id_c = partes[0].strip()
                        nom_c = partes[1].strip()
                        desc_c = partes[2].strip() if len(partes) >= 3 else ""
                        creador_c = partes[3].strip() if len(partes) >= 4 else ""
                        img_c = partes[4].strip() if len(partes) >= 5 else ""
                        notificarNuevoCanal(id_c, nom_c, desc_c, creador_c, img_c)
                        notificarNuevoCanal(id_c, nom_c, desc_c, creador_c)
                elif msg.startswith("<canal_msg>"):
                    payload = msg.removeprefix("<canal_msg>")
                    if "|" not in payload:
                        continue
                    id_c_str, contenido = payload.split("|", 1)
                    id_c_str = id_c_str.strip()
                    contenido = contenido.strip()
                    cliente_actual = getCliente(conn)
                    if id_c_str.isdigit() and cliente_actual and contenido:
                        enviarMensajeCanal(
                            cliente_actual, int(id_c_str), contenido
                        )
                elif msg.startswith("<historial_canal>"):
                    id_c_str = msg.removeprefix("<historial_canal>").strip()
                    cliente_actual = getCliente(conn)
                    if id_c_str.isdigit() and cliente_actual:
                        recuperarHistorialCanal(cliente_actual, int(id_c_str))
                elif msg.startswith("<msg>"):
                    payload = msg.removeprefix("<msg>")
                    if "|" not in payload:
                        continue
                    destinatario, contenido = payload.split("|", 1)
                    destinatario = destinatario.strip()
                    contenido = contenido.strip()
                    cliente_actual = getCliente(conn)
                    if not cliente_actual or not cliente_actual.name or not contenido:
                        continue
                    guardarMensajeUnoAUno(
                        remitente=cliente_actual.name,
                        destinatario=destinatario,
                        contenido=contenido,
                    )

                    with clients_lock:
                        objetivo_conn = None
                        for c in list_of_clients:
                            if c.name.lower() == destinatario.lower():
                                objetivo_conn = c.conn
                                break

                    if objetivo_conn:
                        try:
                            paquete = f"<msg>{cliente_actual.name}|{contenido}\n".encode(
                                "utf-8"
                            )
                            objetivo_conn.sendall(paquete)
                        except OSError:
                            remove(objetivo_conn)
                else:
                    remitente = getName(conn) or addr[0]
                    message_to_send = f"<{remitente}> {msg}\n"
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