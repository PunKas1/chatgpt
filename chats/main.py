import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from chats.cliente import MainWindow
from dbs import mssql
from uis.iniciarSesion_ui import Ui_Form
from uis.principal_ui import Ui_Messenger  # Si principal es QWidget, cambia QMainWindow por QWidget


class VentanaLogin(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ventana_principal = None

        # Revisa los nombres de botones según tu iniciarSesion_ui.py
        # (en tu versión anterior eran bton_login / bton_crear)
        self.bton_login.clicked.connect(self.iniciar_sesion)
        self.bton_crear.clicked.connect(self.crear_cuenta)

    def crear_cuenta(self):
        usuario = self.lineEdit.text().strip()
        contrasena = self.lineEdit_2.text().strip()

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

    def iniciar_sesion(self):
        usuario = self.lineEdit.text().strip()
        contrasena = self.lineEdit_2.text().strip()
        ip = self.lineEdit_3.text().strip()
        puerto = self.lineEdit_4.text().strip()

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
            datos_usuario = mssql.autenticar_usuario(usuario, contrasena)
            if not datos_usuario:
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "Usuario o contraseña incorrectos.",
                )
                return

            id_usuario, nombre_usuario = datos_usuario

            # Abre MainWindow (de chats/cliente.py) y conecta el socket
            self.ventana_principal = MainWindow(
                user_id=id_usuario,
                user_name=nombre_usuario,
                host=ip,
                port=int(puerto),
            )
            self.ventana_principal.show()
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

    