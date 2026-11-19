from PySide6.QtWidgets import QMainWindow, QDialog
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from uis.principal_ui import *
from uis.conectar_ui import *
from PySide6.QtCore import QThread, Signal
import sys
import socket

class ThreadSocket(QThread):
    global connected
    signal_message = Signal(str)
    def __init__(self, host, port, name):
        global connected
        super().__init__()
        server.connect((host, port))
        connected = True
        server.send(bytes(f"<name>{name}", 'utf-8'))

    def run(self):
        global connected
        try:
            while connected:
                message = server.recv(BUFFER_SIZE)
                if message:
                    self.signal_message.emit(message.decode("utf-8"))
                else:
                    self.signal_message.emit("<!!disconected!!>")
                    break
                
        except ...:
            self.signal_message.emit("<!!error!!>")
        finally:
            server.close()
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
        str = self.txtSend.text()
        if str != "" and connected:
            server.send(bytes(str, 'utf-8'))
            self.txtSend.clear()
            self.mensage_entrante("<Tú> " + str + '\n')
            
        
    def salir(self):
        exit()
        
    def showDialog(self):
        dialog = MiDialogo(self)
        resp = dialog.exec()
        if resp == 1:
            server = dialog.txtServer.text()
            user = dialog.txtUser.text()
            port = dialog.txtPort.text()
            if server and not server.isspace() and port and port.isnumeric():
                self.coneccion = ThreadSocket(server, int(port), user)
                self.coneccion.signal_message.connect(self.mensage_entrante)
                self.coneccion.start()
                self.setWindowTitle("Messenger - Conectado")
            
    def mensage_entrante(self, mensaje):
        self.txtMsgs.setPlainText(self.txtMsgs.toPlainText() + mensaje)
        self.txtMsgs.verticalScrollBar().setValue(self.txtMsgs.verticalScrollBar().maximum())

    def actualizar_usuarios(self, usuarios: list[str]):
        self.modelo_chats.clear()
        for usuario in usuarios:
            usuario =usuario.strip()
            if usuario:
                item= QStandardItem(usuario)
                item.setEditable(False)
                item.setData(usuario, Qt.ItemDataRole.UserRole)
                self.modelo_chats.appendRow(item)

    def user_seleccionado(self, index:QModelIndex):
        usuario = index.data(Qt.ItemDataRole.UserRole) or index.data()
        self.txtSend.setPlaceholderText(f"Mensaje a {usuario}...")
        self.txtSend.setFocus()
        if not  usuario:
            return
        

class MiDialogo(QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

if __name__ == "__main__":
    BUFFER_SIZE = 1024  # Usamos un número pequeño para tener una respuesta rápida
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())