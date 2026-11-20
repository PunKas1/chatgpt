import html
import json
import re
import socket
import sys

from PySide6.QtCore import QModelIndex, Qt, QThread, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel, QTextCursor
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
        self.usuario_activo = "Global"  # Por defecto inicia en Global
        self.categoria_actual = "chats"
        self.usuarios_conectados = []
        self.grupos_disponibles = ["Grupo General", "Equipo Proyecto"]
        self.canales_disponibles = ["Canal Anuncios", "Canal Dudas"]

        self.actionConectar.triggered.connect(self.showDialog)
        self.actionSalir.triggered.connect(self.salir)
        self.coneccion = None
        self.btnSend.clicked.connect(self.mensaje_saliente)
        self.setWindowTitle("Messenger - Desconectado")
        self.txtSend.returnPressed.connect(self.mensaje_saliente)

        # Conectar botones de pestañas (Chats | Grupos | Canal) si existen en el UI
        if hasattr(self, "btnChats"):
            self.btnChats.clicked.connect(lambda: self.cambiar_pestana("chats"))
        if hasattr(self, "btnGrupos"):
            self.btnGrupos.clicked.connect(lambda: self.cambiar_pestana("grupos"))
        if hasattr(self, "btnCanal"):
            self.btnCanal.clicked.connect(lambda: self.cambiar_pestana("canal"))

        self.modelo_chats = QStandardItemModel()
        self.listaChats.setModel(self.modelo_chats)
        self.listaChats.clicked.connect(self.user_seleccionado)

        # Inicializar etiquetas superiores y lista por defecto en Global
        if hasattr(self, "lblUserConectado"):
            etiqueta_user = f"Usuario: {user_name}" if user_name else "Usuario: Desconectado"
            self.lblUserConectado.setText(etiqueta_user)
        if hasattr(self, "lblIndicadorChat"):
            self.lblIndicadorChat.setText("Chat actual: Global")
        self.txtSend.setPlaceholderText("Mensaje en Global...")
        self.refrescar_lista_actual()

        # Conecta automáticamente con los datos ingresados en el login
        if host and port and user_name:
            self.conectar_servidor(host, port, user_id, user_name)

    def conectar_servidor(self, host, port, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name
        self.coneccion = ThreadSocket(host, port, user_id, user_name)
        self.coneccion.signal_message.connect(self.procesar_mensaje)
        self.coneccion.start()
        self.setWindowTitle(f"Messenger - Conectado ({user_name})")
        if hasattr(self, "lblUserConectado"):
            self.lblUserConectado.setText(f"Usuario: {user_name}")

    def cambiar_pestana(self, pestana: str):
        self.categoria_actual = pestana
        botones = {
            "chats": getattr(self, "btnChats", None),
            "grupos": getattr(self, "btnGrupos", None),
            "canal": getattr(self, "btnCanal", None),
        }
        for clave, boton in botones.items():
            if boton is not None:
                boton.setProperty("active", "true" if clave == pestana else "false")
                boton.style().unpolish(boton)
                boton.style().polish(boton)
        self.refrescar_lista_actual()

    def refrescar_lista_actual(self):
        if self.categoria_actual == "chats":
            otros = [
                u for u in self.usuarios_conectados
                if u.lower() != self.user_name.strip().lower()
            ]
            self.actualizar_usuarios(["Global"] + otros)
        elif self.categoria_actual == "grupos":
            self.actualizar_usuarios(self.grupos_disponibles)
        elif self.categoria_actual == "canal":
            self.actualizar_usuarios(self.canales_disponibles)

    def agregar_burbuja(self, remitente: str, texto: str, es_mio: bool, fecha: str = ""):
        if not hasattr(self.txtMsgs, "insertHtml"):
            prefijo = "Tú" if es_mio else remitente
            self.mensage_entrante(f"<{prefijo}> {texto}\n")
            return

        texto_seguro = html.escape(texto).replace("\n", "<br>")
        remitente_seguro = html.escape("Tú" if es_mio else remitente)
        fecha_html = (
            f" <span style='color:#71717a; font-size:10px;'>({html.escape(fecha)})</span>"
            if fecha
            else ""
        )

        if es_mio:
            bloque_html = f"""
            <table width="100%" border="0" cellspacing="0" cellpadding="2">
                <tr>
                    <td width="25%"></td>
                    <td width="75%" align="right">
                        <div style="color: #93c5fd; font-size: 11px; font-weight: bold; margin-bottom: 2px;">
                            {remitente_seguro}{fecha_html}
                        </div>
                        <table border="0" cellspacing="0" cellpadding="8" style="background-color: #2563eb; border-radius: 10px;">
                            <tr>
                                <td style="color: #ffffff; font-size: 13px; text-align: left;">
                                    {texto_seguro}
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            """
        else:
            bloque_html = f"""
            <table width="100%" border="0" cellspacing="0" cellpadding="2">
                <tr>
                    <td width="75%" align="left">
                        <div style="color: #a1a1aa; font-size: 11px; font-weight: bold; margin-bottom: 2px;">
                            {remitente_seguro}{fecha_html}
                        </div>
                        <table border="0" cellspacing="0" cellpadding="8" style="background-color: #27272a; border-radius: 10px;">
                            <tr>
                                <td style="color: #f4f4f5; font-size: 13px; text-align: left;">
                                    {texto_seguro}
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td width="25%"></td>
                </tr>
            </table>
            """

        cursor = self.txtMsgs.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(bloque_html)
        self.txtMsgs.setTextCursor(cursor)
        self.txtMsgs.verticalScrollBar().setValue(
            self.txtMsgs.verticalScrollBar().maximum()
        )

    def agregar_aviso_sistema(self, texto: str):
        if not hasattr(self.txtMsgs, "insertHtml"):
            self.mensage_entrante(texto + "\n")
            return

        texto_seguro = html.escape(texto)
        bloque_html = f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="4">
            <tr>
                <td align="center" style="color: #71717a; font-size: 11px; font-style: italic;">
                    {texto_seguro}
                </td>
            </tr>
        </table>
        """
        cursor = self.txtMsgs.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(bloque_html)
        self.txtMsgs.setTextCursor(cursor)
        self.txtMsgs.verticalScrollBar().setValue(
            self.txtMsgs.verticalScrollBar().maximum()
        )

    def mensaje_saliente(self):
        texto = self.txtSend.text().strip()
        if not texto or not connected or not server:
            return

        destino = getattr(self, "usuario_activo", None) or "Global"

        if destino == "Global":
            # En Global todos hablan con todos como hasta ahora
            server.sendall(f"{texto}\n".encode("utf-8"))
        else:
            paquete = f"<msg>{destino}|{texto}\n"
            server.sendall(paquete.encode("utf-8"))

        self.txtSend.clear()
        self.agregar_burbuja("Tú", texto, es_mio=True)

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
            self.usuarios_conectados = [
                u.strip() for u in contenido.split(",") if u.strip()
            ]
            self.refrescar_lista_actual()

        elif msg.startswith("<msg>"):
            payload = msg.removeprefix("<msg>")
            if "|" in payload:
                remitente, contenido = payload.split("|", 1)
                remitente = remitente.strip()
                if getattr(self, "usuario_activo", None) == remitente:
                    self.agregar_burbuja(remitente, contenido, es_mio=False)
                else:
                    self.agregar_burbuja(
                        f"{remitente} (Privado)", contenido, es_mio=False
                    )

        elif msg.startswith("<historial_data>"):
            payload = msg.removeprefix("<historial_data>").strip()
            self.mostrar_historial(payload)

        elif msg.startswith("<historial>") and msg.endswith("</historial>"):
            payload = msg.removeprefix("<historial>")[:-12].strip()
            self.mostrar_historial(payload)

        else:
            # Mensajes generales (Global) o avisos del servidor
            match_brackets = re.match(r"^<([^>]+)>\s*(.+)$", msg, re.DOTALL)
            match_colon = re.match(r"^([^:]{1,30}):\s*(.+)$", msg, re.DOTALL)

            if match_brackets and not msg.startswith("<!!"):
                remitente, contenido = match_brackets.group(1), match_brackets.group(2)
                self.agregar_burbuja(remitente, contenido, es_mio=False)
            elif match_colon and not msg.startswith("***"):
                remitente, contenido = match_colon.group(1), match_colon.group(2)
                self.agregar_burbuja(remitente, contenido, es_mio=False)
            else:
                self.agregar_aviso_sistema(msg)

    def mensage_entrante(self, mensaje):
        if hasattr(self.txtMsgs, "setPlainText"):
            self.txtMsgs.setPlainText(self.txtMsgs.toPlainText() + mensaje)
        else:
            self.txtMsgs.append(mensaje)
        self.txtMsgs.verticalScrollBar().setValue(
            self.txtMsgs.verticalScrollBar().maximum()
        )

    def mostrar_historial(self, raw_data: str):
        try:
            data = json.loads(raw_data.strip())
        except json.JSONDecodeError:
            self.agregar_aviso_sistema("Error al obtener historial")
            return

        con_usuario = data.get("con_usuario")
        mensajes = data.get("mensajes", [])

        if getattr(self, "usuario_activo", None) and con_usuario != self.usuario_activo:
            return

        self.txtMsgs.clear()

        if not mensajes:
            self.agregar_aviso_sistema(f"No hay mensajes previos con {con_usuario}")
            return

        for msg in mensajes:
            remitente = msg.get("remitente", "Desconocido")
            contenido = msg.get("contenido", "")
            fecha = msg.get("fecha_envio", "")
            es_mio = remitente.strip().lower() == self.user_name.strip().lower()
            self.agregar_burbuja(remitente, contenido, es_mio=es_mio, fecha=fecha)

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

        if hasattr(self, "lblIndicadorChat"):
            if usuario == "Global":
                self.lblIndicadorChat.setText("Chat actual: Global")
            elif self.categoria_actual == "chats":
                self.lblIndicadorChat.setText(f"Chat actual: {usuario}")
            elif self.categoria_actual == "grupos":
                self.lblIndicadorChat.setText(f"Grupo: {usuario}")
            elif self.categoria_actual == "canal":
                self.lblIndicadorChat.setText(f"Canal: {usuario}")

        self.txtSend.setPlaceholderText(f"Mensaje en {usuario}...")
        self.txtSend.setFocus()

        if usuario != "Global" and self.categoria_actual == "chats" and connected and server:
            try:
                server.sendall(f"<historial>{usuario}\n".encode("utf-8"))
            except OSError as e:
                self.agregar_aviso_sistema(f"[Error al pedir historial: {e}]")


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