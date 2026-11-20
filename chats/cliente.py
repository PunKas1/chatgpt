from PySide6.QtWidgets import QMainWindow, QDialog, QApplication
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
import json
from uis.principal_ui import *
from uis.conectar_ui import *
from PySide6.QtCore import QThread, Signal
import sys
import socket
import sys

# Permite importar 'uis' y 'dbs' al ejecutar cliente.py directamente desde VS Code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QWidget
from dbs import mssql
from uis.conectar_ui import *
from uis.iniciarSesion_ui import *
from uis.principal_ui import *

BUFFER_SIZE = 1024
server = None
connected = False


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


class VentanaLogin(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ventana_principal = None

        # Conectar botones de iniciarSesion.ui
        self.bton_login.clicked.connect(self.iniciar_sesion)
        self.bton_crear.clicked.connect(self.crear_cuenta)

    def crear_cuenta(self):
        usuario = self.lineEdit.text().strip()
        contrasena = self.lineEdit_2.text().strip()

        if not usuario or not contrasena:
            QMessageBox.warning(
                self, "Campos vacíos", "Ingresa un usuario y una contraseña."
            )
            return

        try:
            if mssql.crear_usuario(usuario, contrasena):
                QMessageBox.information(
                    self,
                    "Cuenta creada",
                    f"El usuario '{usuario}' se registró correctamente.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Usuario existente",
                    "Ese nombre de usuario ya está registrado.",
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de base de datos",
                f"No se pudo crear la cuenta:\n{e}",
            )

    def iniciar_sesion(self):
        usuario = self.lineEdit.text().strip()
        contrasena = self.lineEdit_2.text().strip()
        host = self.lineEdit_3.text().strip()
        port = self.lineEdit_4.text().strip()

        if not all([usuario, contrasena, host, port]):
            QMessageBox.warning(
                self,
                "Campos vacíos",
                "Completa usuario, contraseña, IP y puerto.",
            )
            return

        if not port.isdigit():
            QMessageBox.warning(
                self, "Puerto inválido", "El puerto debe ser un número."
            )
            return

        try:
            # 1. Validar credenciales en SQL Server y recuperar (id_usuario, nombre_usuario)
            datos_usuario = mssql.autenticar_usuario(usuario, contrasena)
            if not datos_usuario:
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "Usuario o contraseña incorrectos.",
                )
                return

            id_usuario, nombre_usuario = datos_usuario

            # 2. Abrir ventana principal y conectar el socket enviando ID y nombre
            self.ventana_principal = MainWindow(
                user_id=id_usuario,
                user_name=nombre_usuario,
                host=host,
                port=int(port),
            )
            self.ventana_principal.show()
            self.close()

        except ConnectionRefusedError:
            QMessageBox.critical(
                self,
                "Error de conexión",
                f"No se pudo conectar al servidor {host}:{port}.",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Ocurrió un error al iniciar sesión:\n{e}"
            )


class MainWindow(QMainWindow, Ui_Messenger):

    def __init__(
        self,
        user_id=None,
        user_name="",
        host=None,
        port=None,
        *args,
        **kwargs,
    ):
        QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self)
        self.user_id = user_id
        self.user_name = user_name
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
        if self.coneccion:
            self.coneccion.stop()
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
    login = VentanaLogin()
    login.show()
    sys.exit(app.exec())