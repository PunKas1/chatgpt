import socket
import threading

class Cliente:
    user_id= ""
    name = ""
    conn = None
    addr = None

def isUserConnected(user_id: str, name: str) -> bool:
    for client in list_of_clients:
        if (user_id and client.user_id == user_id) or (
            client.name.lower() == name.lower()
        ):
            return True
    return False

def setName(connection, name: str, user_id: str = ""):
    for client in list_of_clients:
        if client.conn == connection:
            client.name = name
            client.user_id = user_id
            break

def clientthread(conn, addr):
    while True:
        try:
            message = conn.recv(BUFFER_SIZE)
            if message:
                print(f"<{addr[0]}> {message}")
                msg = message.decode("utf-8")

                if msg.startswith("<name>"):
                    datos = msg.removeprefix("<name>")
                    user_id, nombre = (
                        datos.split("|", 1) if "|" in datos else ("", datos)
                    )

                    if isUserConnected(user_id, nombre):
                        conn.send(bytes("<!!duplicate!!>", "utf-8"))
                        remove(conn)
                        conn.close()
                        break

                    setName(conn, nombre, user_id)
                    conn.send(bytes(f"Bienvenido {nombre}\n", "utf-8"))
                elif msg.startswith("<command>"):
                    broadcast(msg + "\n", conn)
                else:
                    remitente = getName(conn) or addr[0]
                    message_to_send = f"<{remitente}> {msg}\n"
                    broadcast(message_to_send, conn)
            else:
                remove(conn)
                break
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            remove(conn)
            break

def getName(connection) -> str:
    for client in list_of_clients:
        if client.conn == connection:
            return client.name
    return ""

def broadcast(message, connection):
    for client in list_of_clients:
        if client.conn != connection:
            try:
                client.conn.send(bytes(message, 'utf-8'))
            except:
                client.conn.close()
                remove(client)

def remove(connection):
    for client in list_of_clients:
        if client == connection or client.conn == connection:
            list_of_clients.remove(client)
            break

if __name__ == "__main__":
    # host = socket.gethostname()  # Esta función nos da el nombre de la máquina
    host = "0.0.0.0"
    port = 80
    BUFFER_SIZE = 1024  # Usamos un número pequeño para tener una respuesta rápida
    # Creamos un socket TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)  # Escuchamos hasta 100 clientes
    server.settimeout(
        1.0
    )  # Permite detectar Ctrl + C cada segundo en Windows
    list_of_clients = []  # Lista de clientes conectados
    print(f"Escuchando conexiones en: {(host, port)}")
    try:
        while True:
            try:
                conn, addr = server.accept()
                conn.settimeout(
                    None
                )  # Mantiene la conexión del cliente sin límite de tiempo
            except socket.timeout:
                continue

            nuevo_cliente = Cliente()
            nuevo_cliente.conn = conn
            nuevo_cliente.addr = addr
            list_of_clients.append(
                nuevo_cliente
            )  # Agregamos a la lista de clientes
            print(f"Cliente conectado: {addr}")
            # Creamos y ejecutamos el hilo para atender al cliente
            threading.Thread(
                target=clientthread, args=(conn, addr), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nCaught keyboard interrupt, exiting")
    finally:
        for client in list_of_clients:
            try:
                client.conn.close()
            except Exception:
                pass
        server.close()
    print("Conexión terminada.")