import socket
import threading

HOST = '0.0.0.0'
PORT = 65432

def recibir_mensajes(conn):
    while True:
        try:
            datos = conn.recv(1024)
            if not datos:
                print("\n[El cliente cerró la conexión]")
                break
            
            mensaje = datos.decode('utf-8')
            if mensaje.lower() == 'salir':
                print("\n[El cliente abandonó el chat]")
                break
                
            # \r limpia la línea actual de input para que no se mezcle el texto en consola
            print(f"\rCliente: {mensaje}\nTú (Servidor): ", end="")
        except:
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Servidor escuchando en {PORT}...")
    
    conn, addr = s.accept()
    with conn:
        print(f"Conectado con {addr}. Ya pueden escribir libremente (escribe 'salir' para terminar).\n")
        
        # Crear e iniciar el hilo de recepción (daemon=True hace que muera al cerrar el programa principal)
        hilo_receptor = threading.Thread(target=recibir_mensajes, args=(conn,), daemon=True)
        hilo_receptor.start()
        
        # El hilo principal se encarga de enviar
        while True:
            mensaje = input("Tú (Servidor): ")
            try:
                conn.sendall(mensaje.encode('utf-8'))
            except:
                print("Error al enviar. Conexión perdida.")
                break
                
            if mensaje.lower() == 'salir':
                print("Cerrando chat...")
                break