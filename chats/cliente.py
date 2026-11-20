import json
import socket
import sys

from PySide6.QtCore import QModelIndex, Qt, QThread, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QWidget,
)

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
        server.sendall(f"<name>{user_id}|{name}\n".encode("utf-8"))

    def run(self):
        global connected, server
        buffer = ""
        try:
            while connected:
                chunk = server.recv(BUFFER_SIZE)
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
            if server:
                try:
                    server.close()
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
        self.usuario_activo = None
        self.actionConectar.triggered.connect(self.showDialog)
        self.actionSalir.triggered.connect(self.salir)
        self.coneccion = None
        self.btnSend.clicked.connect(self.mensaje_saliente)
        self.setWindowTitle("Messenger - Desconectado")
        self.txtSend.returnPressed.connect(self.mensaje_saliente)

        self.modelo_chats = QStandardItemModel()
        self.listaChats.setModel(self.modelo_chats)
        self.listaChats.clicked.connect(self.user_seleccionado)

        # Conecta automáticamente con los datos ingresados en el login
        if host and port and user_name:
            self.conectar_servidor(host, port, user_id, user_name)

    def conectar_servidor(self, host, port, user_id, user_name):
        self.coneccion = ThreadSocket(host, port, user_id, user_name)
        self.coneccion.signal_message.connect(self.procesar_mensaje)
        self.coneccion.start()
        self.setWindowTitle(f"Messenger - Conectado ({user_name})")

    def mensaje_saliente(self):
        texto = self.txtSend.text().strip()
        if texto and connected and server:
            server.sendall(f"{texto}\n".encode("utf-8"))
            self.txtSend.clear()
            self.mensage_entrante(f"<Tú> {texto}\n")

    def salir(self):
        if self.coneccion:
            self.coneccion.stop()
        sys.exit()

    def showDialog(self):
        dialog = MiDialogo(self)
        resp = dialog.exec()
        if resp == 1:
            host = dialog.txtServer.text().strip()
            user = dialog.txtUser.text().strip() or self.user_name
            port = dialog.txtPort.text().strip()
            if host and port and port.isnumeric():
                self.conectar_servidor(host, int(port), self.user_id, user)

    def procesar_mensaje(self, msg: str):
        if msg.startswith("<users>"):
            contenido = msg.removeprefix("<users>")
            if contenido.endswith("</users>"):
                contenido = contenido[:-8]
            usuarios = [u.strip() for u in contenido.split(",") if u.strip()]
            self.actualizar_usuarios(usuarios)

        elif msg.startswith("<historial_data>"):
            payload = msg.removeprefix("<historial_data>").strip()
            self.mostrar_historial(payload)

        elif msg.startswith("<historial>") and msg.endswith("</historial>"):
            payload = msg.removeprefix("<historial>")[:-12].strip()
            self.mostrar_historial(payload)

        else:
            self.mensage_entrante(msg + "\n")

    def mensage_entrante(self, mensaje):
        self.txtMsgs.setPlainText(self.txtMsgs.toPlainText() + mensaje)
        self.txtMsgs.verticalScrollBar().setValue(
            self.txtMsgs.verticalScrollBar().maximum()
        )

    def mostrar_historial(self, raw_data: str):
        try:
            data = json.loads(raw_data.strip())
        except json.JSONDecodeError:
            self.txtMsgs.appendPlainText("Error al obtener historial")
            return

        con_usuario = data.get("con_usuario")
        mensajes = data.get("mensajes", [])

        if getattr(self, "usuario_activo", None) and con_usuario != self.usuario_activo:
            return

        self.txtMsgs.clear()

        if not mensajes:
            self.txtMsgs.appendPlainText(f"No hay mensajes previos con {con_usuario}")
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
            usuario = usuario.strip()
            if usuario:
                item = QStandardItem(usuario)
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

        if connected and server:
            try:
                server.sendall(f"<historial>{usuario}\n".encode("utf-8"))
            except OSError as e:
                self.mensage_entrante(f"[Error al pedir historial: {e}]\n")


class MiDialogo(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = VentanaLogin()
    login.show()
    sys.exit(app.exec())

"""
