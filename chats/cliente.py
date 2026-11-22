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
    QListWidgetItem,
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
        global connected, server
        connected = False
        if server:
            try:
                server.shutdown(socket.SHUT_RDWR)
                server.close()
            except OSError:
                pass
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
            datos_usuario = mssql.autenticar_usuario(usuario, contrasena)
            if not datos_usuario:
                QMessageBox.warning(
                    self,
                    "Acceso denegado",
                    "Usuario o contraseña incorrectos.",
                )
                return

            id_usuario, nombre_usuario = datos_usuario

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
        self.usuario_activo = "Global"
        self.grupo_activo_id = None
        self.categoria_actual = "chats"
        self.usuarios_conectados = []
        self.todos_usuarios_bd = []
        self.historial_global = []
        self.grupos_disponibles = []
        self.canales_disponibles = ["Canal Anuncios", "Canal Dudas"]

        self.actionSalir.triggered.connect(self.salir)
        self.coneccion = None
        self.btnSend.clicked.connect(self.mensaje_saliente)
        self.setWindowTitle("Messenger - Desconectado")
        self.txtSend.returnPressed.connect(self.mensaje_saliente)

        # Pestañas superiores
        if hasattr(self, "btnChats"):
            self.btnChats.clicked.connect(lambda: self.cambiar_pestana("chats"))
        if hasattr(self, "btnGrupos"):
            self.btnGrupos.clicked.connect(lambda: self.cambiar_pestana("grupos"))
        if hasattr(self, "btnCanal"):
            self.btnCanal.clicked.connect(lambda: self.cambiar_pestana("canal"))

        # Botones del formulario de crear grupo
        if hasattr(self, "btnCrearGrupo"):
            self.btnCrearGrupo.clicked.connect(self.abrir_formulario_grupo)
        if hasattr(self, "btnCancelarGrupo"):
            self.btnCancelarGrupo.clicked.connect(self.cerrar_formulario_grupo)
        if hasattr(self, "btnGuardarGrupo"):
            self.btnGuardarGrupo.clicked.connect(self.confirmar_crear_grupo)

        self.modelo_chats = QStandardItemModel()
        self.listaChats.setModel(self.modelo_chats)
        self.listaChats.clicked.connect(self.user_seleccionado)

        if hasattr(self, "lblUserConectado"):
            etiqueta_user = (
                f"Usuario: {user_name}" if user_name else "Usuario: Desconectado"
            )
            self.lblUserConectado.setText(etiqueta_user)
        if hasattr(self, "lblIndicadorChat"):
            self.lblIndicadorChat.setText("Chat actual: Global")
        self.txtSend.setPlaceholderText("Mensaje en Global...")
        self.refrescar_lista_actual()

        if host and port and user_name:
            self.conectar_servidor(host, port, user_id, user_name)

    def conectar_servidor(self, host, port, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name
        self.cargar_usuarios_bd()
        self.coneccion = ThreadSocket(host, port, user_id, user_name)
        self.coneccion.signal_message.connect(self.procesar_mensaje)
        self.coneccion.start()
        self.setWindowTitle(f"Messenger - Conectado ({user_name})")
        if hasattr(self, "lblUserConectado"):
            self.lblUserConectado.setText(f"Usuario: {user_name}")
        self.refrescar_lista_actual()

    def cargar_usuarios_bd(self):
        try:
            self.todos_usuarios_bd = mssql.obtener_todos_los_usuarios()
            if self.user_id is not None:
                self.grupos_disponibles = mssql.obtener_grupos_usuario(self.user_id)
        except Exception:
            self.todos_usuarios_bd = []
            self.grupos_disponibles = []

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

        if hasattr(self, "btnCrearGrupo"):
            self.btnCrearGrupo.setVisible(pestana == "grupos")

        if hasattr(self, "stackedDerecha"):
            self.stackedDerecha.setCurrentIndex(0)

        if pestana != "grupos":
            self.grupo_activo_id = None
        elif not self.grupo_activo_id:
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(
                "Selecciona un grupo de la lista o haz clic en '+ Crear grupo'"
            )
            if hasattr(self, "lblIndicadorChat"):
                self.lblIndicadorChat.setText("Grupos")

        self.refrescar_lista_actual()

    # ==================== PASO 4: FORMULARIO CREAR GRUPO ====================
    def abrir_formulario_grupo(self):
        self.txtNombreGrupo.clear()
        self.listaMiembrosGrupo.clear()

        unicos = {}
        for u in self.todos_usuarios_bd + self.usuarios_conectados:
            limpio = u.strip()
            if limpio and limpio.lower() != self.user_name.strip().lower():
                unicos[limpio.lower()] = limpio

        for nombre in sorted(unicos.values(), key=str.lower):
            item = QListWidgetItem(nombre)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.listaMiembrosGrupo.addItem(item)

        self.lblIndicadorChat.setText("Nuevo grupo")
        self.stackedDerecha.setCurrentIndex(1)
        self.txtNombreGrupo.setFocus()

    def cerrar_formulario_grupo(self):
        self.stackedDerecha.setCurrentIndex(0)
        self.actualizar_indicador_chat()

    def confirmar_crear_grupo(self):
        nombre_grupo = self.txtNombreGrupo.text().strip()
        if not nombre_grupo:
            QMessageBox.warning(
                self, "Falta nombre", "Escribe un nombre para el grupo."
            )
            return

        miembros = []
        for i in range(self.listaMiembrosGrupo.count()):
            item = self.listaMiembrosGrupo.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                miembros.append(item.text().strip())

        if not miembros:
            QMessageBox.warning(
                self, "Sin miembros", "Selecciona al menos un miembro para el grupo."
            )
            return

        id_grupo = mssql.crear_grupo_bd(nombre_grupo, self.user_id, miembros)
        if not id_grupo:
            QMessageBox.critical(
                self, "Error", "No se pudo guardar el grupo en la base de datos."
            )
            return

        if connected and server:
            lista_csv = ",".join(miembros)
            server.sendall(
                f"<nuevo_grupo>{id_grupo}|{nombre_grupo}|{lista_csv}\n".encode("utf-8")
            )

        self.grupos_disponibles = mssql.obtener_grupos_usuario(self.user_id)
        self.refrescar_lista_actual()

        self.grupo_activo_id = id_grupo
        self.usuario_activo = nombre_grupo
        self.cerrar_formulario_grupo()
        self.txtSend.setPlaceholderText(f"Mensaje en {nombre_grupo}...")
        self.txtMsgs.clear()
        self.agregar_aviso_sistema(
            f"Grupo '{nombre_grupo}' creado. Miembros: {', '.join(miembros)}"
        )

    # ==================== PASO 5: LISTAS Y RENDERIZADO ====================
    def refrescar_lista_actual(self):
        if self.categoria_actual == "chats":
            unicos = {}
            for u in self.todos_usuarios_bd + self.usuarios_conectados:
                limpio = u.strip()
                if limpio:
                    unicos[limpio.lower()] = limpio

            mi_usuario = self.user_name.strip()
            if mi_usuario:
                unicos[mi_usuario.lower()] = mi_usuario

            lista_usuarios = list(unicos.values())
            conectados_lower = {u.lower() for u in self.usuarios_conectados}
            mi_usuario_lower = mi_usuario.lower()

            lista_usuarios.sort(
                key=lambda u: (
                    u.lower() != mi_usuario_lower,
                    u.lower() not in conectados_lower,
                    u.lower(),
                )
            )
            self.actualizar_usuarios(["Global"] + lista_usuarios, es_chat=True)
        elif self.categoria_actual == "grupos":
            self.actualizar_usuarios(
                self.grupos_disponibles, es_chat=False, es_grupo=True
            )
        elif self.categoria_actual == "canal":
            self.actualizar_usuarios(self.canales_disponibles, es_chat=False)

    def actualizar_usuarios(
        self, usuarios: list, es_chat: bool = False, es_grupo: bool = False
    ):
        self.modelo_chats.clear()
        conectados_lower = {u.lower() for u in self.usuarios_conectados}
        mi_usuario_lower = self.user_name.strip().lower()

        for usuario in usuarios:
            if es_grupo and isinstance(usuario, dict):
                nombre_g = usuario["nombre_grupo"]
                item = QStandardItem(f"👥 {nombre_g}")
                item.setEditable(False)
                item.setData(usuario, Qt.ItemDataRole.UserRole)
                self.modelo_chats.appendRow(item)
                continue

            usuario = str(usuario).strip()
            if not usuario:
                continue

            if es_chat:
                if usuario == "Global":
                    texto_visible = "🌐 Global"
                elif usuario.lower() == mi_usuario_lower:
                    icono = (
                        "🟢"
                        if (connected or usuario.lower() in conectados_lower)
                        else "⚪"
                    )
                    texto_visible = f"{icono} {usuario} (tú)"
                elif usuario.lower() in conectados_lower:
                    texto_visible = f"🟢 {usuario}"
                else:
                    texto_visible = f"⚪ {usuario}"
            else:
                texto_visible = usuario

            item = QStandardItem(texto_visible)
            item.setEditable(False)
            item.setData(usuario, Qt.ItemDataRole.UserRole)
            self.modelo_chats.appendRow(item)

    def actualizar_indicador_chat(self):
        if not hasattr(self, "lblIndicadorChat"):
            return
        usuario = getattr(self, "usuario_activo", "Global")
        if self.categoria_actual == "grupos":
            if getattr(self, "grupo_activo_id", None):
                self.lblIndicadorChat.setText(f"Grupo: {usuario}")
            else:
                self.lblIndicadorChat.setText("Grupos")
        elif usuario == "Global":
            self.lblIndicadorChat.setText("Chat actual: Global")
        elif self.categoria_actual == "chats":
            conectados_lower = {u.lower() for u in self.usuarios_conectados}
            es_yo = usuario.lower() == self.user_name.strip().lower()
            etiqueta = f"{usuario} (tú)" if es_yo else usuario
            estado = (
                "🟢 En línea"
                if (es_yo and connected) or (usuario.lower() in conectados_lower)
                else "⚪ Desconectado"
            )
            self.lblIndicadorChat.setText(f"Chat actual: {etiqueta} · {estado}")
        elif self.categoria_actual == "canal":
            self.lblIndicadorChat.setText(f"Canal: {usuario}")

    # ==================== PASO 6: SELECCIÓN, ENVÍO Y RECEPCIÓN ====================
    def user_seleccionado(self, index: QModelIndex):
        data = index.data(Qt.ItemDataRole.UserRole) or index.data()
        if not data:
            return

        if hasattr(self, "stackedDerecha"):
            self.stackedDerecha.setCurrentIndex(0)

        # Selección de un grupo
        if self.categoria_actual == "grupos" and isinstance(data, dict):
            self.grupo_activo_id = data["id_grupo"]
            self.usuario_activo = data["nombre_grupo"]
            self.actualizar_indicador_chat()
            self.txtSend.setPlaceholderText(f"Mensaje en {self.usuario_activo}...")
            self.txtSend.setFocus()
            self.txtMsgs.clear()

            if connected and server:
                try:
                    server.sendall(
                        f"<historial_grupo>{self.grupo_activo_id}\n".encode("utf-8")
                    )
                except OSError as e:
                    self.agregar_aviso_sistema(
                        f"[Error al pedir historial del grupo: {e}]"
                    )
            return

        # Selección de Global, privado o canal
        self.grupo_activo_id = None
        usuario = str(data).strip()
        self.usuario_activo = usuario
        self.actualizar_indicador_chat()
        self.txtSend.setPlaceholderText(f"Mensaje en {usuario}...")
        self.txtSend.setFocus()

        if usuario == "Global":
            self.mostrar_global()
        elif self.categoria_actual == "chats" and connected and server:
            self.txtMsgs.clear()
            try:
                server.sendall(f"<historial>{usuario}\n".encode("utf-8"))
            except OSError as e:
                self.agregar_aviso_sistema(f"[Error al pedir historial: {e}]")
        else:
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(f"Estás en {usuario}")

    def mensaje_saliente(self):
        texto = self.txtSend.text().strip()
        if not texto or not connected or not server:
            return

        if self.categoria_actual == "grupos":
            if not getattr(self, "grupo_activo_id", None):
                self.agregar_aviso_sistema(
                    "Selecciona o crea un grupo antes de enviar un mensaje."
                )
                return
            server.sendall(
                f"<grupo_msg>{self.grupo_activo_id}|{texto}\n".encode("utf-8")
            )
            self.txtSend.clear()
            self.agregar_burbuja("Tú", texto, es_mio=True)
            return

        destino = getattr(self, "usuario_activo", None) or "Global"

        if destino == "Global":
            server.sendall(f"{texto}\n".encode("utf-8"))
            self.historial_global.append(("burbuja", "Tú", texto, True))
        else:
            paquete = f"<msg>{destino}|{texto}\n"
            server.sendall(paquete.encode("utf-8"))

        self.txtSend.clear()
        self.agregar_burbuja("Tú", texto, es_mio=True)

    def procesar_mensaje(self, msg: str):
        if msg.startswith("<users>"):
            contenido = msg.removeprefix("<users>")
            if contenido.endswith("</users>"):
                contenido = contenido[:-8]
            self.usuarios_conectados = [
                u.strip() for u in contenido.split(",") if u.strip()
            ]
            bd_lower = {u.lower() for u in self.todos_usuarios_bd}
            for u in self.usuarios_conectados:
                if u.lower() not in bd_lower:
                    self.todos_usuarios_bd.append(u)
                    bd_lower.add(u.lower())

            self.refrescar_lista_actual()
            self.actualizar_indicador_chat()

        elif msg.startswith("<nuevo_grupo>"):
            if self.user_id is not None:
                self.grupos_disponibles = mssql.obtener_grupos_usuario(self.user_id)
                if self.categoria_actual == "grupos":
                    self.refrescar_lista_actual()

        elif msg == "<!!duplicate!!>":
            if self.coneccion:
                self.coneccion.stop()
            QMessageBox.warning(
                self,
                "Sesión duplicada",
                f"El usuario '{self.user_name}' ya tiene una sesión activa.",
            )
            self.ventana_login = VentanaLogin()
            self.ventana_login.show()
            self.close()
            return

        elif msg.startswith("<grupo_msg>"):
            payload = msg.removeprefix("<grupo_msg>")
            partes = payload.split("|", 2)
            if len(partes) == 3:
                id_g_str, remitente, contenido = partes
                remitente = remitente.strip()
                if remitente.lower() == self.user_name.strip().lower():
                    return
                if (
                    self.categoria_actual == "grupos"
                    and str(getattr(self, "grupo_activo_id", "")) == id_g_str.strip()
                ):
                    self.agregar_burbuja(remitente, contenido, es_mio=False)
                else:
                    self.agregar_aviso_sistema(
                        f"Nuevo mensaje de grupo de {remitente}"
                    )

        elif msg.startswith("<historial_grupo_data>"):
            payload = msg.removeprefix("<historial_grupo_data>").strip()
            self.mostrar_historial_grupo(payload)

        elif msg.startswith("<msg>"):
            payload = msg.removeprefix("<msg>")
            if "|" in payload:
                remitente, contenido = payload.split("|", 1)
                remitente = remitente.strip()
                if remitente.lower() == self.user_name.strip().lower():
                    return
                if (
                    getattr(self, "usuario_activo", None) or ""
                ).lower() == remitente.lower():
                    self.agregar_burbuja(remitente, contenido, es_mio=False)
                else:
                    self.agregar_aviso_sistema(
                        f"Nuevo mensaje privado de {remitente}"
                    )

        elif msg.startswith("<historial_data>"):
            payload = msg.removeprefix("<historial_data>").strip()
            self.mostrar_historial(payload)

        elif msg.startswith("<historial>") and msg.endswith("</historial>"):
            payload = msg.removeprefix("<historial>")[:-12].strip()
            self.mostrar_historial(payload)

        else:
            match_brackets = re.match(r"^<([^>]+)>\s*(.+)$", msg, re.DOTALL)
            match_colon = re.match(r"^([^:]{1,30}):\s*(.+)$", msg, re.DOTALL)

            if match_brackets and not msg.startswith("<!!"):
                remitente, contenido = match_brackets.group(1), match_brackets.group(2)
                self.historial_global.append(("burbuja", remitente, contenido, False))
                if getattr(self, "usuario_activo", None) == "Global":
                    self.agregar_burbuja(remitente, contenido, es_mio=False)
            elif match_colon and not msg.startswith("***"):
                remitente, contenido = match_colon.group(1), match_colon.group(2)
                self.historial_global.append(("burbuja", remitente, contenido, False))
                if getattr(self, "usuario_activo", None) == "Global":
                    self.agregar_burbuja(remitente, contenido, es_mio=False)
            else:
                self.historial_global.append(("sistema", msg))
                if getattr(self, "usuario_activo", None) == "Global":
                    self.agregar_aviso_sistema(msg)

    def mostrar_historial_grupo(self, raw_data: str):
        try:
            data = json.loads(raw_data.strip())
        except json.JSONDecodeError:
            self.agregar_aviso_sistema("Error al obtener historial del grupo")
            return

        id_grupo = data.get("id_grupo")
        mensajes = data.get("mensajes", [])

        if getattr(self, "grupo_activo_id", None) != id_grupo:
            return

        self.txtMsgs.clear()

        if not mensajes:
            self.agregar_aviso_sistema("No hay mensajes previos en este grupo")
            return

        for msg in mensajes:
            remitente = msg.get("remitente", "Desconocido")
            contenido = msg.get("contenido", "")
            fecha = msg.get("fecha_envio", "")
            es_mio = remitente.strip().lower() == self.user_name.strip().lower()
            self.agregar_burbuja(remitente, contenido, es_mio=es_mio, fecha=fecha)

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

    def mostrar_global(self):
        self.txtMsgs.clear()
        if not self.historial_global:
            self.agregar_aviso_sistema("Estás en el chat Global")
            return

        for item in self.historial_global:
            if item[0] == "burbuja":
                _, remitente, contenido, es_mio = item
                self.agregar_burbuja(remitente, contenido, es_mio=es_mio)
            elif item[0] == "sistema":
                _, texto = item
                self.agregar_aviso_sistema(texto)

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

    def mensage_entrante(self, mensaje):
        if hasattr(self.txtMsgs, "setPlainText"):
            self.txtMsgs.setPlainText(self.txtMsgs.toPlainText() + mensaje)
        else:
            self.txtMsgs.append(mensaje)
        self.txtMsgs.verticalScrollBar().setValue(
            self.txtMsgs.verticalScrollBar().maximum()
        )

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