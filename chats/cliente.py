import json
import os
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

    def __init__(self, host, port, user_id, name):
        global connected, server
        super().__init__()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((host, port))
        connected = True
        # Envía el ID y el nombre al servidor para notificar la conexión
        server.send(bytes(f"<name>{user_id}|{name}", "utf-8"))

    def run(self):
        global connected, server
        try:
            while connected:
                message = server.recv(BUFFER_SIZE)
                if message:
                    self.signal_message.emit(message.decode("utf-8"))
                else:
                    self.signal_message.emit("<!!disconected!!>")
                    break
        except Exception:
            self.signal_message.emit("<!!error!!>")
        finally:
            if server:
                server.close()
            connected = False

    def stop(self):
        global connected, server
        connected = False
        if server:
            try:
                server.close()
            except Exception:
                pass
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

        # Conecta automáticamente con los datos ingresados en el login
        if host and port and user_name:
            self.conectar_servidor(host, port, user_id, user_name)

    def conectar_servidor(self, host, port, user_id, user_name):
        self.coneccion = ThreadSocket(host, port, user_id, user_name)
        self.coneccion.signal_message.connect(self.mensage_entrante)
        self.coneccion.start()
        self.setWindowTitle(f"Messenger - Conectado ({user_name})")

    def mensaje_saliente(self):
        texto = self.txtSend.text()
        if texto != "" and connected:
            server.send(bytes(texto, "utf-8"))
            self.txtSend.clear()
            self.mensage_entrante("<Tú> " + texto + "\n")

    def salir(self):
        if self.coneccion:
            self.coneccion.stop()
        exit()

    def showDialog(self):
        if self.coneccion:
            self.coneccion.stop()
        dialog = MiDialogo(self)
        resp = dialog.exec()
        if resp == 1:
            host = dialog.txtServer.text()
            user = dialog.txtUser.text()
            port = dialog.txtPort.text()
            if host and not host.isspace() and port and port.isnumeric():
                self.conectar_servidor(host, int(port), self.user_id, user)

    def mensage_entrante(self, mensaje):
        if "<!!duplicate!!>" in mensaje:
            if self.coneccion:
                self.coneccion.stop()
            QMessageBox.warning(
                self,
                "Sesión ya activa",
                f"El perfil '{self.user_name}' ya está conectado en otra ventana.",
            )
            self.login = VentanaLogin()
            self.login.show()
            self.close()
            return

        self.txtMsgs.setPlainText(self.txtMsgs.toPlainText() + mensaje)
        self.txtMsgs.verticalScrollBar().setValue(
            self.txtMsgs.verticalScrollBar().maximum()
        )


class MiDialogo(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = VentanaLogin()
    login.show()
    sys.exit(app.exec())