from PySide6.QtWidgets import QMainWindow, QDialog, QApplication
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
import json
from uis.principal_ui import *
from uis.conectar_ui import *
from PySide6.QtCore import QThread, Signal
import sys
import socket

class ThreadSocket(QThread):
    signal_message = Signal(str)

    def __init__(self, sock, host, port, name):
        global connected
        super().__init__()
        self.sock = sock
        self.sock.connect((host, port))
        connected = True
        self.sock.sendall(f"<name>{name}\n".encode("utf-8"))

    def run(self):
        global connected
        buffer = ""
        try:
            while connected:
                chunk = self.sock.recv(BUFFER_SIZE)
                if not chunk:
                    self.signal_message.emit("<!!disconected!!>")
                    break

                buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    linea = linea.strip()
                    if linea:
                        self.signal_message.emit(linea)

        except Exception:
            self.signal_message.emit("<!!error!!>")
        finally:
            try:
                self.sock.close()
            except OSError:
                pass
            connected = False
        
        
    def stop(self):
        global connected
        connected = False
        self.wait()



class MainWindow(QMainWindow, Ui_Messenger):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self)
        self.actionConectar.triggered.connect(self.showDialog)
        self.actionSalir.triggered.connect(self.salir)
        self.coneccion = None
        self.btnSend.clicked.connect(self.mensaje_saliente)
        self.setWindowTitle("Messenger - Desconectado")
        self.txtSend.returnPressed.connect(self.mensaje_saliente)
        self.modelo_chats = QStandardItemModel()
        self.listaChats.setModel(self.modelo_chats)
        self.actualizar_usuarios(["Ana", "Luis", "Sofía"])
        self.listaChats.clicked.connect(self.user_seleccionado)

        
    def mensaje_saliente(self):
        texto = self.txtSend.text().strip()
        if texto and connected and getattr(self, "sock", None):
            self.sock.sendall(f"{texto}\n".encode("utf-8"))
            self.txtSend.clear()
            self.mensage_entrante(f"<Tú> {texto}")
            
        
    def salir(self):
        exit()
        
    def showDialog(self):
        dialog = MiDialogo(self)
        resp = dialog.exec()
        if resp == 1:
            host = dialog.txtServer.text().strip()
            user = dialog.txtUser.text().strip()
            port = dialog.txtPort.text().strip()
            if host and port and port.isnumeric():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock = sock
                self.coneccion = ThreadSocket(sock, host, int(port), user)
                self.coneccion.signal_message.connect(self.mensage_entrante)
                self.coneccion.start()
                self.setWindowTitle(f"Messenger - Conectado ({user})")
            
    def mensage_entrante(self, mensaje):
        self.txtMsgs.setPlainText(self.txtMsgs.toPlainText() + mensaje)
        self.txtMsgs.verticalScrollBar().setValue(self.txtMsgs.verticalScrollBar().maximum())

    def mostrar_historial(self, raw_data:str):
        try:
            data=json.loads(raw_data.strip())
        except json.JSONDecodeError:
            self.txtMsgs.appendPlainText("Error al obtener historial")
            return

        con_usuario=data.get("con_usuario")
        mensajes=data.get("mensajes",[])

        if getattr(self, "usuario_activo", None) and con_usuario != self.usuario_activo:
            return

        self.txtMsgs.clear()

        if not mensajes:
            self.txtMsgs.appendPlainText(f"no hay mensajes previos con {con_usuario}")
            return

        for msg in mensajes:
            remitente = msg.get("remitente", "Desconocido")
            contenido = msg.get("contenido", "")
            fecha = msg.get("fecha_envio", "")

            if fecha:
                linea = f"[{fecha}] {remitente}: {contenido}"
            else:
                linea = f"{remitente}: {contenido}"

            self.txtMsgs.appendPlainText(linea)
        scrollbar = self.txtMsgs.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def actualizar_usuarios(self, usuarios: list[str]):
        self.modelo_chats.clear()
        for usuario in usuarios:
            usuario =usuario.strip()
            if usuario:
                item= QStandardItem(usuario)
                item.setEditable(False)
                item.setData(usuario, Qt.ItemDataRole.UserRole)
                self.modelo_chats.appendRow(item)

    def user_seleccionado(self, index: QModelIndex):
        usuario = index.data(Qt.ItemDataRole.UserRole) or index.data()
        if not usuario:
            return
        usuario = str(usuario).strip()
        self.usuario_activo = usuario
        self.txtSend.setPlaceholderText(f"Mensaje a {usuario}...")
        self.txtSend.setFocus()

        if connected and getattr(self, "sock", None):
            try:
                self.sock.sendall(f"<historial>{usuario}\n".encode("utf-8"))
            except OSError as e:
                self.mensage_entrante(f"[Error al pedir historial: {e}]")

class MiDialogo(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)


BUFFER_SIZE = 1024
connected = False
if __name__ == "__main__":
    # Usamos un número pequeño para tener una respuesta rápida
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())