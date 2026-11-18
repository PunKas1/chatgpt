import socket
import threading



HOST = '127.0.0.1'
PORT = 65432

def recibir_mensajes(sock):
    while True:
        try:
            datos = sock.recv(1024)
            if not datos:
                print("\n[El servidor cerró la conexión]")
                break
                
            mensaje = datos.decode('utf-8')
            if mensaje.lower() == 'salir':
                print("\n[El servidor abandonó el chat]")
                break
                
            print(f"\rServidor: {mensaje}\nTú (Cliente): ", end="")
        except:
            break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"Conectado a {HOST}:{PORT}. Ya pueden escribir libremente (escribe 'salir' para terminar).\n")
    
    # Iniciar hilo secundario para escuchar al servidor
    hilo_receptor = threading.Thread(target=recibir_mensajes, args=(s,), daemon=True)
    hilo_receptor.start()
    
    # Hilo principal para leer teclado y enviar
    while True:
        mensaje = input("Tú (Cliente): ")
        try:
            s.sendall(mensaje.encode('utf-8'))
        except:
            print("Error al enviar. Conexión perdida.")
            break
            
        if mensaje.lower() == 'salir':
            print("Cerrando chat...")
            break

