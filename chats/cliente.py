import html
import json
import socket
import sys
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from uis.conectar_ui import *
from uis.iniciarSesion_ui import *
from uis.principal_ui import *

BUFFER_SIZE = 1024

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"


class ThreadSocket(QThread):
    signal_connected = Signal()
    signal_message = Signal(str)
    signal_error = Signal(str)

    def __init__(self, host: str, port: int, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self._running = True
        self.sock = None
        self.connected = False

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, self.port))
            sock.settimeout(1.0)
            self.sock = sock
            self.connected = True
            self.signal_connected.emit()
        except OSError as e:
            self.connected = False
            self.signal_error.emit(str(e))
            return

        buffer = ""
        try:
            while self._running and self.connected:
                try:
                    chunk = sock.recv(BUFFER_SIZE)
                except socket.timeout:
                    continue
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
            if self._running:
                self.signal_message.emit("<!!error!!>")
        finally:
            self.connected = False
            try:
                sock.close()
            except OSError:
                pass

    def enviar(self, texto: str) -> bool:
        if not self.connected or not self.sock:
            return False
        try:
            if not texto.endswith("\n"):
                texto += "\n"
            self.sock.sendall(texto.encode("utf-8"))
            return True
        except OSError:
            self.connected = False
            return False

    def stop(self):
        self._running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
        self.wait(2000)


class VentanaLogin(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ventana_principal = None
        self.coneccion = None
        self._login_exitoso = False

        self.bton_login.clicked.connect(lambda: self._conectar_y_enviar("login"))
        self.bton_crear.clicked.connect(lambda: self._conectar_y_enviar("registro"))

    def _set_botones(self, estado: bool):
        self.bton_login.setEnabled(estado)
        self.bton_crear.setEnabled(estado)

    def _conectar_y_enviar(self, accion: str):
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

        self._set_botones(False)
        if self.coneccion:
            self.coneccion.stop()

        sock_thread = ThreadSocket(host, int(port), parent=self)
        self.coneccion = sock_thread
        payload = json.dumps(
            {"usuario": usuario, "contrasena": contrasena}, ensure_ascii=False
        )

        sock_thread.signal_connected.connect(
            lambda: sock_thread.enviar(f"<{accion}>{payload}")
        )
        sock_thread.signal_message.connect(self._procesar_respuesta_auth)
        sock_thread.signal_error.connect(self._on_error_red)
        sock_thread.start()

    def _procesar_respuesta_auth(self, linea: str):
        if linea.startswith("<registro_ok>"):
            self._set_botones(True)
            if self.coneccion:
                self.coneccion.stop()
                self.coneccion = None
            QMessageBox.information(
                self,
                "Cuenta creada",
                "El usuario se registró correctamente. Ahora puedes iniciar sesión.",
            )

        elif linea.startswith("<registro_err>"):
            self._set_botones(True)
            if self.coneccion:
                self.coneccion.stop()
                self.coneccion = None
            motivo = (
                linea.removeprefix("<registro_err>").strip()
                or "Ese nombre de usuario ya está registrado."
            )
            QMessageBox.warning(self, "Error de registro", motivo)

        elif linea.startswith("<login_ok>"):
            try:
                datos = json.loads(linea.removeprefix("<login_ok>").strip())
            except json.JSONDecodeError:
                self._set_botones(True)
                QMessageBox.critical(
                    self, "Error de protocolo", "Respuesta inválida del servidor."
                )
                return

            self.coneccion.signal_message.disconnect(self._procesar_respuesta_auth)
            self.coneccion.signal_error.disconnect(self._on_error_red)

            self._login_exitoso = True
            self.ventana_principal = MainWindow(
                user_id=datos["user_id"],
                user_name=datos["user_name"],
                coneccion=self.coneccion,
            )
            self.coneccion.setParent(self.ventana_principal)
            self.ventana_principal.show()
            self.close()

        elif linea.startswith("<login_err>"):
            self._set_botones(True)
            if self.coneccion:
                self.coneccion.stop()
                self.coneccion = None
            motivo = (
                linea.removeprefix("<login_err>").strip()
                or "Usuario o contraseña incorrectos."
            )
            QMessageBox.warning(self, "Acceso denegado", motivo)

        elif linea in ("<!!disconected!!>", "<!!error!!>"):
            self._set_botones(True)
            if self.coneccion:
                self.coneccion.stop()
                self.coneccion = None
            QMessageBox.critical(
                self, "Desconectado", "Se perdió la conexión con el servidor."
            )

    def _on_error_red(self, err: str):
        self._set_botones(True)
        if self.coneccion:
            self.coneccion.stop()
            self.coneccion = None
        QMessageBox.critical(
            self, "Error de conexión", f"No se pudo conectar al servidor:\n{err}"
        )

    def closeEvent(self, event):
        if not self._login_exitoso and self.coneccion:
            self.coneccion.stop()
        super().closeEvent(event)


class MainWindow(QMainWindow, Ui_Messenger):

    def __init__(
        self,
        user_id=None,
        user_name: str = "",
        coneccion: ThreadSocket | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.user_id = user_id
        self.user_name = user_name
        self.coneccion = coneccion

        self.usuario_activo = "Global"
        self.grupo_activo_id = None
        self.canal_activo_id = None
        self.canal_creador_id = None
        self.categoria_actual = "chats"

        self.usuarios_conectados = []
        self.todos_usuarios_bd = []
        self.historial_global = []
        self.grupos_disponibles = []
        self.canales_disponibles = []
        self.imagenes_usuarios = {}
        self._cache_imagenes = {}

        self.actionSalir.triggered.connect(self.salir)
        self.btnSend.clicked.connect(self.mensaje_saliente)
        self.txtSend.returnPressed.connect(self.mensaje_saliente)

        if hasattr(self, "listaChats"):
            self.listaChats.setIconSize(QSize(30, 30))

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

        # Botones del formulario de crear canal
        if hasattr(self, "btnCrearCanal"):
            self.btnCrearCanal.clicked.connect(self.abrir_formulario_canal)
        if hasattr(self, "btnCancelarCanal"):
            self.btnCancelarCanal.clicked.connect(self.cerrar_formulario_canal)
        if hasattr(self, "btnGuardarCanal"):
            self.btnGuardarCanal.clicked.connect(self.confirmar_crear_canal)

        self.modelo_chats = QStandardItemModel()
        self.listaChats.setModel(self.modelo_chats)
        self.listaChats.clicked.connect(self.user_seleccionado)

        if hasattr(self, "btnCerrarSesion"):
            self.btnCerrarSesion.clicked.connect(self.cerrar_sesion)

        if hasattr(self, "lblUserConectado"):
            etiqueta_user = (
                f"Usuario: {user_name}" if user_name else "Usuario: Desconectado"
            )
            self.lblUserConectado.setText(etiqueta_user)
        if hasattr(self, "lblIndicadorChat"):
            self.lblIndicadorChat.setText("Chat actual: Global")
        self.txtSend.setPlaceholderText("Mensaje en Global...")

        if self.esta_conectado:
            self.coneccion.signal_message.connect(self.procesar_mensaje)
            self.coneccion.signal_error.connect(
                lambda err: self.agregar_aviso_sistema(f"[Error de socket: {err}]")
            )
            self.setWindowTitle(f"Messenger - Conectado ({user_name})")
            self.coneccion.enviar("<init_data>")
        else:
            self.setWindowTitle("Messenger - Desconectado")

        self.refrescar_lista_actual()

    @property
    def esta_conectado(self) -> bool:
        return bool(self.coneccion and self.coneccion.connected)

    # ==================== IMÁGENES Y AVATARES ====================
    def _obtener_pixmap_imagen(self, clave_imagen: str | None) -> QPixmap | None:
        if not clave_imagen:
            return None

        clave = str(clave_imagen).strip()
        if clave in self._cache_imagenes:
            return self._cache_imagenes[clave]

        ruta = IMAGES_DIR / clave
        if not ruta.exists():
            return None

        pixmap = QPixmap(str(ruta))
        if pixmap.isNull():
            return None

        self._cache_imagenes[clave] = pixmap
        return pixmap

    def _obtener_icono_imagen(self, clave_imagen: str | None) -> QIcon:
        pixmap = self._obtener_pixmap_imagen(clave_imagen)
        if not pixmap:
            return QIcon()
        return QIcon(pixmap)

    def _actualizar_avatar_chat(self, clave_imagen: str | None = None):
        if not hasattr(self, "lblAvatarChat"):
            return

        pixmap = self._obtener_pixmap_imagen(clave_imagen)
        if pixmap:
            escalado = pixmap.scaled(
                36,
                36,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lblAvatarChat.setPixmap(escalado)
        else:
            self.lblAvatarChat.clear()

    def _actualizar_avatar_usuario_actual(self):
        if not hasattr(self, "lblAvatarUsuario"):
            return

        clave_img = None
        if self.user_name:
            clave_img = self.imagenes_usuarios.get(self.user_name.strip().lower())

        pixmap = self._obtener_pixmap_imagen(clave_img)
        if pixmap:
            escalado = pixmap.scaled(
                32,
                32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lblAvatarUsuario.setPixmap(escalado)
        else:
            self.lblAvatarUsuario.clear()

    # ==================== NAVEGACIÓN DE PESTAÑAS ====================
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

        if hasattr(self, "btnCrearCanal"):
            self.btnCrearCanal.setVisible(pestana == "canal")

        if hasattr(self, "stackedDerecha"):
            self.stackedDerecha.setCurrentIndex(0)

        self._actualizar_avatar_chat(None)

        if pestana != "grupos":
            self.grupo_activo_id = None

        if pestana != "canal":
            self.canal_activo_id = None
            self.canal_creador_id = None
            self._actualizar_permiso_envio_canal(True)

        if pestana == "grupos" and not self.grupo_activo_id:
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(
                "Selecciona un grupo de la lista o haz clic en '+ Crear grupo'"
            )
            if hasattr(self, "lblIndicadorChat"):
                self.lblIndicadorChat.setText("Grupos")
        elif pestana == "canal" and not self.canal_activo_id:
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(
                "Selecciona un canal de la lista o haz clic en '+ Crear canal'"
            )
            if hasattr(self, "lblIndicadorChat"):
                self.lblIndicadorChat.setText("Canales")
        elif pestana == "chats":
            self.usuario_activo = "Global"
            self.actualizar_indicador_chat()
            self.txtSend.setPlaceholderText("Mensaje en Global...")
            self.mostrar_global()

        self.refrescar_lista_actual()

    def _actualizar_permiso_envio_canal(self, permitido: bool):
        self.txtSend.setEnabled(permitido)
        self.btnSend.setEnabled(permitido)
        if not permitido:
            self.txtSend.setPlaceholderText(
                "Solo el creador puede enviar mensajes en este canal."
            )

    # ==================== FORMULARIO CREAR GRUPO ====================
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

        if hasattr(self, "lblIndicadorChat"):
            self.lblIndicadorChat.setText("Nuevo grupo")
        if hasattr(self, "stackedDerecha"):
            self.stackedDerecha.setCurrentIndex(1)
        self.txtNombreGrupo.setFocus()

    def cerrar_formulario_grupo(self):
        if hasattr(self, "stackedDerecha"):
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

        if not self.esta_conectado:
            QMessageBox.warning(
                self, "Sin conexión", "No estás conectado al servidor."
            )
            return

        payload = json.dumps(
            {"nombre": nombre_grupo, "miembros": miembros}, ensure_ascii=False
        )
        if self.coneccion.enviar(f"<crear_grupo>{payload}"):
            self.btnGuardarGrupo.setEnabled(False)

    # ==================== FORMULARIO CREAR CANAL ====================
    def abrir_formulario_canal(self):
        if hasattr(self, "txtNombreCanal"):
            self.txtNombreCanal.clear()
        if hasattr(self, "txtDescripcionCanal"):
            self.txtDescripcionCanal.clear()
        if hasattr(self, "lblIndicadorChat"):
            self.lblIndicadorChat.setText("Nuevo canal")
        if hasattr(self, "stackedDerecha"):
            indice_canal = 2 if self.stackedDerecha.count() > 2 else 1
            self.stackedDerecha.setCurrentIndex(indice_canal)
        if hasattr(self, "txtNombreCanal"):
            self.txtNombreCanal.setFocus()

    def cerrar_formulario_canal(self):
        if hasattr(self, "stackedDerecha"):
            self.stackedDerecha.setCurrentIndex(0)
        self.actualizar_indicador_chat()

    def confirmar_crear_canal(self):
        nombre_canal = (
            self.txtNombreCanal.text().strip()
            if hasattr(self, "txtNombreCanal")
            else ""
        )
        if not nombre_canal:
            QMessageBox.warning(
                self, "Falta nombre", "Escribe un nombre para el canal."
            )
            return

        if not self.esta_conectado:
            QMessageBox.warning(
                self, "Sin conexión", "No estás conectado al servidor."
            )
            return

        datos_canal = {"nombre": nombre_canal}
        if hasattr(self, "txtDescripcionCanal"):
            datos_canal["descripcion"] = self.txtDescripcionCanal.text().strip()

        payload = json.dumps(datos_canal, ensure_ascii=False)
        if self.coneccion.enviar(f"<crear_canal>{payload}"):
            if hasattr(self, "btnGuardarCanal"):
                self.btnGuardarCanal.setEnabled(False)

    # ==================== LISTAS Y RENDERIZADO ====================
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
            if isinstance(usuario, dict):
                if es_grupo and "nombre_grupo" in usuario:
                    nombre_g = str(usuario["nombre_grupo"]).strip()
                    if not nombre_g:
                        continue
                    item = QStandardItem(f"👥 {nombre_g}")
                    item.setIcon(self._obtener_icono_imagen(usuario.get("imagen")))
                    item.setEditable(False)
                    item.setData(usuario, Qt.ItemDataRole.UserRole)
                    self.modelo_chats.appendRow(item)
                elif "nombre_canal" in usuario:
                    nombre_c = str(usuario["nombre_canal"]).strip()
                    if not nombre_c:
                        continue
                    item = QStandardItem(f"📢 {nombre_c}")
                    item.setIcon(self._obtener_icono_imagen(usuario.get("imagen")))
                    item.setEditable(False)
                    item.setData(usuario, Qt.ItemDataRole.UserRole)
                    self.modelo_chats.appendRow(item)
                continue

            usuario_str = str(usuario).strip()
            if not usuario_str:
                continue

            if es_chat:
                if usuario_str == "Global":
                    texto_visible = "🌐 Global"
                elif usuario_str.lower() == mi_usuario_lower:
                    icono = (
                        "🟢"
                        if (
                            self.esta_conectado
                            or usuario_str.lower() in conectados_lower
                        )
                        else "🔴"
                    )
                    texto_visible = f"{icono} {usuario_str} (tú)"
                elif usuario_str.lower() in conectados_lower:
                    texto_visible = f"🟢 {usuario_str}"
                else:
                    texto_visible = f"🔴 {usuario_str}"
            else:
                texto_visible = usuario_str

            item = QStandardItem(texto_visible)
            item.setEditable(False)
            item.setData(usuario_str, Qt.ItemDataRole.UserRole)

            if es_chat and usuario_str != "Global":
                clave_img = self.imagenes_usuarios.get(usuario_str.lower())
                if clave_img:
                    item.setIcon(self._obtener_icono_imagen(clave_img))

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
                if (es_yo and self.esta_conectado)
                or (usuario.lower() in conectados_lower)
                else "🔴 Desconectado"
            )
            self.lblIndicadorChat.setText(f"Chat actual: {etiqueta} · {estado}")
        elif self.categoria_actual == "canal":
            if getattr(self, "canal_activo_id", None):
                self.lblIndicadorChat.setText(f"Canal: {usuario}")
            else:
                self.lblIndicadorChat.setText("Canales")

    # ==================== BURBUJAS Y MENSAJES EN PANTALLA ====================
    def agregar_aviso_sistema(self, texto: str):
        seguro = html.escape(texto)
        bloque = (
            '<div style="text-align:center; color:#888888; font-size:12px; '
            f'margin:6px 0;"><i>{seguro}</i></div>'
        )
        self.txtMsgs.moveCursor(QTextCursor.MoveOperation.End)
        self.txtMsgs.insertHtml(bloque + "<br>")
        self.txtMsgs.moveCursor(QTextCursor.MoveOperation.End)

    def agregar_burbuja(self, remitente: str, texto: str, es_mio: bool = False):
        rem_seguro = html.escape(remitente)
        txt_seguro = html.escape(texto).replace("\n", "<br>")
        if es_mio:
            bloque = (
                '<div style="text-align:right; margin:6px 10px;">'
                '<span style="display:inline-block; background-color:#2b5278; '
                "color:#ffffff; padding:8px 12px; border-radius:10px; "
                f'max-width:70%; text-align:left;">'
                f'<b style="font-size:11px; color:#a8d1ff;">{rem_seguro}</b><br>'
                f"{txt_seguro}</span></div>"
            )
        else:
            bloque = (
                '<div style="text-align:left; margin:6px 10px;">'
                '<span style="display:inline-block; background-color:#26292e; '
                "color:#f1f1f1; padding:8px 12px; border-radius:10px; "
                f'max-width:70%; text-align:left;">'
                f'<b style="font-size:11px; color:#6ab2f2;">{rem_seguro}</b><br>'
                f"{txt_seguro}</span></div>"
            )
        self.txtMsgs.moveCursor(QTextCursor.MoveOperation.End)
        self.txtMsgs.insertHtml(bloque + "<br>")
        self.txtMsgs.moveCursor(QTextCursor.MoveOperation.End)

    def mostrar_global(self):
        self.txtMsgs.clear()
        for entrada in self.historial_global:
            if entrada[0] == "burbuja":
                _, remitente, texto, es_mio = entrada
                self.agregar_burbuja(remitente, texto, es_mio=es_mio)
            elif entrada[0] == "aviso":
                self.agregar_aviso_sistema(entrada[1])

    # ==================== SELECCIÓN, ENVÍO Y RECEPCIÓN ====================
    def user_seleccionado(self, index: QModelIndex):
        data = index.data(Qt.ItemDataRole.UserRole) or index.data()
        if not data:
            return

        if hasattr(self, "stackedDerecha"):
            self.stackedDerecha.setCurrentIndex(0)

        if self.categoria_actual == "grupos" and isinstance(data, dict):
            self.grupo_activo_id = data["id_grupo"]
            self.canal_activo_id = None
            self.canal_creador_id = None
            self.usuario_activo = data["nombre_grupo"]

            self._actualizar_permiso_envio_canal(True)
            self._actualizar_avatar_chat(data.get("imagen"))
            self.actualizar_indicador_chat()

            self.txtSend.setPlaceholderText(f"Mensaje en {self.usuario_activo}...")
            self.txtSend.setFocus()
            self.txtMsgs.clear()

            if self.esta_conectado:
                if not self.coneccion.enviar(
                    f"<historial_grupo>{self.grupo_activo_id}"
                ):
                    self.agregar_aviso_sistema(
                        "[Error al pedir historial del grupo]"
                    )
            return

        if self.categoria_actual == "canal" and isinstance(data, dict):
            self.grupo_activo_id = None
            self.canal_activo_id = data["id_canal"]
            self.canal_creador_id = data.get("id_creador")
            self.usuario_activo = data["nombre_canal"]

            es_creador = (
                self.canal_creador_id is not None
                and str(self.canal_creador_id) == str(self.user_id)
            )
            self._actualizar_permiso_envio_canal(es_creador)
            self._actualizar_avatar_chat(data.get("imagen"))
            self.actualizar_indicador_chat()

            if es_creador:
                self.txtSend.setPlaceholderText(f"Mensaje en #{self.usuario_activo}...")
                self.txtSend.setFocus()
            self.txtMsgs.clear()

            if self.esta_conectado:
                if not self.coneccion.enviar(
                    f"<historial_canal>{self.canal_activo_id}"
                ):
                    self.agregar_aviso_sistema(
                        "[Error al pedir historial del canal]"
                    )
            return

        self.grupo_activo_id = None
        self.canal_activo_id = None
        self.canal_creador_id = None
        usuario = str(data).strip()
        self.usuario_activo = usuario

        self._actualizar_permiso_envio_canal(True)
        if usuario == "Global":
            self._actualizar_avatar_chat(None)
        else:
            self._actualizar_avatar_chat(self.imagenes_usuarios.get(usuario.lower()))

        self.actualizar_indicador_chat()
        self.txtSend.setPlaceholderText(f"Mensaje en {usuario}...")
        self.txtSend.setFocus()

        if usuario == "Global":
            self.mostrar_global()
        elif self.categoria_actual == "chats" and self.esta_conectado:
            self.txtMsgs.clear()
            if not self.coneccion.enviar(f"<historial>{usuario}"):
                self.agregar_aviso_sistema("[Error al pedir historial]")
        else:
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(f"Estás en {usuario}")

    def mensaje_saliente(self):
        texto = self.txtSend.text().strip()
        destino = getattr(self, "usuario_activo", None) or "Global"
        if not texto or not self.esta_conectado:
            return

        if self.categoria_actual == "grupos":
            if not getattr(self, "grupo_activo_id", None):
                self.agregar_aviso_sistema(
                    "Selecciona o crea un grupo antes de enviar un mensaje."
                )
                return
            if self.coneccion.enviar(f"<grupo_msg>{self.grupo_activo_id}|{texto}"):
                self.txtSend.clear()
                self.agregar_burbuja("Tú", texto, es_mio=True)
            return

        if self.categoria_actual == "canal":
            if not getattr(self, "canal_activo_id", None):
                self.agregar_aviso_sistema(
                    "Selecciona o crea un canal antes de enviar un mensaje."
                )
                return
            if (
                self.canal_creador_id is not None
                and str(self.canal_creador_id) != str(self.user_id)
            ):
                self.agregar_aviso_sistema(
                    "Solo el creador puede enviar mensajes en este canal."
                )
                return
            if self.coneccion.enviar(f"<canal_msg>{self.canal_activo_id}|{texto}"):
                self.txtSend.clear()
                self.agregar_burbuja("Tú", texto, es_mio=True)
            return

        if destino == "Global":
            if self.coneccion.enviar(texto):
                self.historial_global.append(("burbuja", "Tú", texto, True))
                self.txtSend.clear()
                self.agregar_burbuja("Tú", texto, es_mio=True)
        else:
            if self.coneccion.enviar(f"<msg>{destino}|{texto}"):
                self.txtSend.clear()
                self.agregar_burbuja("Tú", texto, es_mio=True)

    def _aplicar_usuarios_bd(self, usuarios_info: list):
        if usuarios_info:
            self.imagenes_usuarios = {
                u["nombre_usuario"].strip().lower(): u.get("imagen")
                for u in usuarios_info
                if u.get("nombre_usuario")
            }
            bd_lower = {u.lower() for u in self.todos_usuarios_bd}
            for u in usuarios_info:
                nombre_bd = u.get("nombre_usuario", "").strip()
                if nombre_bd and nombre_bd.lower() not in bd_lower:
                    self.todos_usuarios_bd.append(nombre_bd)
                    bd_lower.add(nombre_bd.lower())

        bd_lower = {u.lower() for u in self.todos_usuarios_bd}
        for u in self.usuarios_conectados:
            if u.lower() not in bd_lower:
                self.todos_usuarios_bd.append(u)
                bd_lower.add(u.lower())

        self._actualizar_avatar_usuario_actual()

    def _renderizar_historial(self, mensajes: list):
        self.txtMsgs.clear()
        if not mensajes:
            self.agregar_aviso_sistema("No hay mensajes anteriores.")
            return

        mi_nombre = self.user_name.strip().lower()
        for m in mensajes:
            remitente = str(m.get("remitente", "Desconocido"))
            texto = str(m.get("contenido") or m.get("mensaje") or "")
            es_mio = remitente.strip().lower() == mi_nombre
            etiqueta = "Tú" if es_mio else remitente
            self.agregar_burbuja(etiqueta, texto, es_mio=es_mio)

    def procesar_mensaje(self, linea: str):
        if linea == "<!!disconected!!>":
            self.setWindowTitle("Messenger - Desconectado")
            self.agregar_aviso_sistema("[Desconectado del servidor]")
            self.refrescar_lista_actual()
            self.actualizar_indicador_chat()
            return

        if linea == "<!!error!!>":
            self.setWindowTitle("Messenger - Error de conexión")
            self.agregar_aviso_sistema("[Error de comunicación con el servidor]")
            return

        # Carga inicial desde el servidor
        if linea.startswith("<init_data_ok>"):
            try:
                datos = json.loads(linea.removeprefix("<init_data_ok>"))
                self._aplicar_usuarios_bd(datos.get("usuarios", []))
                self.canales_disponibles = datos.get("canales", [])
                self.grupos_disponibles = datos.get("grupos", [])
                self.refrescar_lista_actual()
                self.actualizar_indicador_chat()
            except json.JSONDecodeError as e:
                print(f"Error decodificando init_data_ok: {e}")
            return

        # Respuesta al crear grupo
        if linea.startswith("<grupo_creado_ok>"):
            self.btnGuardarGrupo.setEnabled(True)
            try:
                grupo = json.loads(linea.removeprefix("<grupo_creado_ok>"))
            except json.JSONDecodeError:
                return

            id_grupo = grupo["id_grupo"]
            nombre_grupo = grupo["nombre_grupo"]
            if not any(
                int(g["id_grupo"]) == int(id_grupo) for g in self.grupos_disponibles
            ):
                self.grupos_disponibles.append(grupo)

            self.grupo_activo_id = id_grupo
            self.canal_activo_id = None
            self.canal_creador_id = None
            self.usuario_activo = nombre_grupo

            self._actualizar_permiso_envio_canal(True)
            self._actualizar_avatar_chat(grupo.get("imagen"))
            self.cerrar_formulario_grupo()
            self.refrescar_lista_actual()
            self.txtSend.setPlaceholderText(f"Mensaje en {nombre_grupo}...")
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(f"Grupo '{nombre_grupo}' creado.")
            return

        if linea.startswith("<grupo_creado_err>"):
            self.btnGuardarGrupo.setEnabled(True)
            motivo = (
                linea.removeprefix("<grupo_creado_err>").strip()
                or "No se pudo crear el grupo."
            )
            QMessageBox.warning(self, "Error", motivo)
            return

        # Notificación cuando otro usuario te agrega a un grupo
        if linea.startswith("<nuevo_grupo>"):
            cuerpo = linea.removeprefix("<nuevo_grupo>").strip()
            try:
                grupo = json.loads(cuerpo)
                if not any(
                    int(g["id_grupo"]) == int(grupo["id_grupo"])
                    for g in self.grupos_disponibles
                ):
                    self.grupos_disponibles.append(grupo)
                    self.refrescar_lista_actual()
            except json.JSONDecodeError:
                pass
            return

        # Respuesta al crear canal
        if linea.startswith("<canal_creado_ok>"):
            if hasattr(self, "btnGuardarCanal"):
                self.btnGuardarCanal.setEnabled(True)
            try:
                canal = json.loads(linea.removeprefix("<canal_creado_ok>"))
            except json.JSONDecodeError:
                return

            id_canal = canal["id_canal"]
            nombre_canal = canal["nombre_canal"]
            if not any(
                int(c["id_canal"]) == int(id_canal) for c in self.canales_disponibles
            ):
                self.canales_disponibles.append(canal)

            self.grupo_activo_id = None
            self.canal_activo_id = id_canal
            self.canal_creador_id = canal.get("id_creador", self.user_id)
            self.usuario_activo = nombre_canal

            self._actualizar_permiso_envio_canal(True)
            self._actualizar_avatar_chat(canal.get("imagen"))
            self.cerrar_formulario_canal()
            self.refrescar_lista_actual()
            self.txtSend.setPlaceholderText(f"Mensaje en #{nombre_canal}...")
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(f"Canal '#{nombre_canal}' creado.")
            return

        if linea.startswith("<canal_creado_err>"):
            if hasattr(self, "btnGuardarCanal"):
                self.btnGuardarCanal.setEnabled(True)
            motivo = (
                linea.removeprefix("<canal_creado_err>").strip()
                or "No se pudo crear el canal."
            )
            QMessageBox.warning(self, "Error", motivo)
            return

        # Notificación de nuevo canal público
        if linea.startswith("<nuevo_canal>"):
            cuerpo = linea.removeprefix("<nuevo_canal>").strip()
            try:
                canal = json.loads(cuerpo)
                if not any(
                    int(c["id_canal"]) == int(canal["id_canal"])
                    for c in self.canales_disponibles
                ):
                    self.canales_disponibles.append(canal)
                    self.refrescar_lista_actual()
            except json.JSONDecodeError:
                pass
            return

        # Lista de usuarios conectados
        if linea.startswith("<users>"):
            cuerpo = linea.removeprefix("<users>").strip()
            try:
                lista = json.loads(cuerpo)
                if isinstance(lista, list):
                    self.usuarios_conectados = [str(u).strip() for u in lista if u]
            except json.JSONDecodeError:
                self.usuarios_conectados = [
                    u.strip() for u in cuerpo.split(",") if u.strip()
                ]
            self._aplicar_usuarios_bd([])
            self.refrescar_lista_actual()
            self.actualizar_indicador_chat()
            return

        # Historiales (privado, grupo, canal)
        if linea.startswith(("<historial>", "<historial_grupo>", "<historial_canal>")):
            for prefijo in ("<historial>", "<historial_grupo>", "<historial_canal>"):
                if linea.startswith(prefijo):
                    cuerpo = linea.removeprefix(prefijo).strip()
                    try:
                        mensajes = json.loads(cuerpo)
                        if isinstance(mensajes, list):
                            self._renderizar_historial(mensajes)
                    except json.JSONDecodeError as e:
                        print(f"Error al leer historial: {e}")
                    return

        # Mensaje privado entrante: <msg>remitente|texto
        if linea.startswith("<msg>"):
            cuerpo = linea.removeprefix("<msg>")
            if "|" in cuerpo:
                remitente, texto = cuerpo.split("|", 1)
                if (
                    self.categoria_actual == "chats"
                    and self.usuario_activo.strip().lower() == remitente.strip().lower()
                ):
                    self.agregar_burbuja(remitente, texto, es_mio=False)
                else:
                    self.agregar_aviso_sistema(f"Nuevo mensaje privado de {remitente}")
            return

        # Mensaje de grupo entrante: <grupo_msg>id_grupo|remitente|texto
        if linea.startswith("<grupo_msg>"):
            partes = linea.removeprefix("<grupo_msg>").split("|", 2)
            if len(partes) == 3:
                id_grupo, remitente, texto = partes
                if (
                    self.categoria_actual == "grupos"
                    and str(self.grupo_activo_id) == str(id_grupo)
                ):
                    self.agregar_burbuja(remitente, texto, es_mio=False)
            return

        # Mensaje de canal entrante: <canal_msg>id_canal|remitente|texto
        if linea.startswith("<canal_msg>"):
            partes = linea.removeprefix("<canal_msg>").split("|", 2)
            if len(partes) == 3:
                id_canal, remitente, texto = partes
                if (
                    self.categoria_actual == "canal"
                    and str(self.canal_activo_id) == str(id_canal)
                ):
                    self.agregar_burbuja(remitente, texto, es_mio=False)
            return

        # Mensaje global entrante
        if ":" in linea:
            remitente, texto = linea.split(":", 1)
            remitente = remitente.strip()
            texto = texto.strip()
            self.historial_global.append(("burbuja", remitente, texto, False))
            if self.categoria_actual == "chats" and self.usuario_activo == "Global":
                self.agregar_burbuja(remitente, texto, es_mio=False)
        else:
            self.historial_global.append(("aviso", linea))
            if self.categoria_actual == "chats" and self.usuario_activo == "Global":
                self.agregar_aviso_sistema(linea)

    # ==================== CIERRE DE SESIÓN Y VENTANA ====================
    def cerrar_sesion(self):
        if self.coneccion:
            self.coneccion.stop()
            self.coneccion = None
        self.login = VentanaLogin()
        self.login.show()
        self.close()

    def salir(self):
        self.close()

    def closeEvent(self, event):
        if self.coneccion:
            self.coneccion.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaLogin()
    ventana.show()
    sys.exit(app.exec())