import socket
import threading


clients_lock = threading.Lock()

class Cliente:
    def __init__(self):
        self.name = ""
        self.conn = conn
        self.addr = addr

def clientthread(conn, addr):
    try:
        conn.sendall(f"Bienvenido {addr}\n".encode('utf-8'))
    except OSError:
        pass

        while True:
                message = conn.recv(BUFFER_SIZE)
                if not message:
                        break
                
                print(f"<{addr[0]}> {message}")
                msg = message.decode('utf-8')
                # Mensajes especiales (comandos)
                if msg.startswith('<name>'):
                    setName(conn, msg.removeprefix('<name>'))
                elif msg.startswith('<command>'):
                    broadcast(msg + '\n', conn)
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
    for client in list_of_clients:
        try:
            client.conn.sendall(package)
        except OSError:
            remove(client)




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
            nuevo_cliente = Cliente()
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