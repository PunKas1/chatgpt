import json
import socket
import threading

from dbs.mssql import recuperarHistorialUnoAUno, guardarMensajeUnoAUno

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
                            paquete = f"<msg>{cliente_actual.name}|{contenido}\n".encode("utf-8")
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