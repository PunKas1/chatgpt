import socket
import threading
import json
from dbs.mssql import recuperarHistorialUnoAUno


clients_lock = threading.Lock()

class Cliente:
    def __init__(self,conn, addr):
        self.name = ""
        self.conn = conn
        self.addr = addr

def clientthread(conn, addr):
    try:
        conn.sendall(f"Bienvenido {addr}\n".encode('utf-8'))
    except OSError:
        pass

    try:
        while True:
            message = conn.recv(BUFFER_SIZE)
            if not message:
                break

            print(f"<{addr[0]}> {message}")
            msg = message.decode('utf-8', errors='replace').strip()
            if not msg:
                continue

            # Mensajes especiales (comandos)
            if msg.startswith('<name>'):
                setName(conn, msg.removeprefix('<name>').strip())
            elif msg.startswith('<command>'):
                broadcast(msg + '\n', conn)
            elif msg.startswith('<historial>'):
                usuario_objetivo = msg.removeprefix('<historial>').strip()
                cliente_actual = getCliente(conn)
                if cliente_actual:
                    recuperarHistorial(cliente_actual, usuario_objetivo)
            else:
                # Reenviamos el mensaje recibido a todos los demás clientes.
                message_to_send = f"<{getName(conn)}> {msg}\n"
                broadcast(message_to_send, conn)
    except OSError:
        pass
    finally:
        remove(conn)

def setName(connection, name:str):
    with clients_lock:
        for client in list_of_clients:
            if client.conn == connection:
                client.name = name.strip()
                break
        broadcast_connected_users()

def getName(connection) -> str:
    with clients_lock:
        for client in list_of_clients:
            if client.conn == connection:
                return client.name
        return ""

def recuperarHistorial(client, usuario_objetivo:str):
    with clients_lock:
        if  not client.name or not usuario_objetivo:
            return

        mensajes = recuperarHistorialUnoAUno(usuario_actual=client.name, 
                                             usuario_objetivo = usuario_objetivo)
        payload = json.dumps({
            "con_usuario":usuario_objetivo,
            "mensajes":mensajes
        }, ensure_ascii=False)
        client.conn.sendall(f"<historial_data>{payload}\n".encode('utf-8'))

def broadcast(message, connection):
    with clients_lock:

        for client in list_of_clients:
            if client.conn != connection:
                try:
                    client.conn.send(bytes(message, 'utf-8'))
                except:
                    client.conn.close()
                    remove(client)

def remove(target):
    removed =False
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

def broadcast_connected_users():
    users = ",".join(connected_users())
    package =f"<users>{users}</users>\n".encode('utf-8')
    for client in list(list_of_clients):
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




if __name__ == "__main__":
    #host = socket.gethostname()  # Esta función nos da el nombre de la máquina
    host = "0.0.0.0"
    port = 80
    BUFFER_SIZE = 1024  # Usamos un número pequeño para tener una respuesta rápida
    # Creamos un socket TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(100)  # Escuchamos hasta 100 clientes
    list_of_clients = []  # Lista de clientes conectados
    print(f"Escuchando conexiones en: {(host, port)}")
    try:
        while True:
            conn, addr = server.accept()
            nuevo_cliente = Cliente(conn, addr)
            nuevo_cliente.conn = conn
            nuevo_cliente.addr = addr
            #list_of_clients.append(conn)  # Agregamos a la lista de clientes
            list_of_clients.append(nuevo_cliente)  # Agregamos a la lista de clientes
            print(f"Cliente conectado: {addr}")
            # Creamos y ejecutamos el hilo para atender al cliente
            threading.Thread(target=clientthread, args=(conn, addr)).start()
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        conn.close()
        server.close()   
    print("Conexión terminada.")