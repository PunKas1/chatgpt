import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget

from chats.cliente import ClienteChat
from dbs import mssql
from uis.iniciarSesion_ui import Ui_Form
from uis.principal_ui import Ui_MainWindow  # Si principal es QWidget, cambia QMainWindow por QWidget


class VentanaPrincipal(QMainWindow):

    def __init__(self, id_usuario, nombre_usuario, cliente_socket):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.id_usuario = id_usuario
        self.nombre_usuario = nombre_usuario
        self.cliente = cliente_socket


class VentanaLogin(QWidget):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.cliente = ClienteChat()

        # Conectar botones
        self.ui.btn_crear.clicked.connect(self.manejar_crear_cuenta)
        self.ui.btn_login.clicked.connect(self.manejar_login)

    def manejar_crear_cuenta(self):
        usuario = self.ui.lineEdit.text().strip()
        contrasena = self.ui.lineEdit_2.text().strip()

        if not usuario or not contrasena:
            QMessageBox.warning(
                self, "Datos incompletos", "Ingresa un usuario y contraseña."
            )
            return

        try:
            if mssql.crear_usuario(usuario, contrasena):
                QMessageBox.information(
                    self, "Registro exitoso", f"Usuario '{usuario}' creado."
                )
            else:
                QMessageBox.warning(
                    self, "Duplicado", "Ese nombre de usuario ya existe."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Error de BD", f"No se pudo crear la cuenta:\n{e}"
            )

    def manejar_login(self):
        usuario = self.ui.lineEdit.text().strip()
        contrasena = self.ui.lineEdit_2.text().strip()
        ip = self.ui.lineEdit_3.text().strip()
        puerto = self.ui.lineEdit_4.text().strip()

        if not all([usuario, contrasena, ip, puerto]):
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Llena usuario, contraseña, IP y puerto.",
            )
            return

        if not puerto.isdigit():
            QMessageBox.warning(
                self, "Puerto inválido", "El puerto debe ser un número."
            )
            return

        try:
            # 1. Verificar usuario y recuperar (id_usuario, nombre_usuario)
            datos_usuario = mssql.autenticar_usuario(usuario, contrasena)
            if not datos_usuario:
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "Usuario o contraseña incorrectos.",
                )
                return

            id_usuario, nombre_usuario = datos_usuario

            # 2. Conectar al server y notificar la conexión
            self.cliente.conectar_y_notificar(
                ip, puerto, id_usuario, nombre_usuario
            )

            # 3. Abrir ventana principal del chat y cerrar el login
            self.ventana_chat = VentanaPrincipal(
                id_usuario, nombre_usuario, self.cliente
            )
            self.ventana_chat.show()
            self.close()

        except ConnectionRefusedError:
            QMessageBox.critical(
                self,
                "Servidor apagado",
                f"No se pudo conectar a {ip}:{puerto}.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un problema:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = VentanaLogin()
    login.show()
    sys.exit(app.exec())