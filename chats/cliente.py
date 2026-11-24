import html
import json
import re
import socket
import sys
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSize, Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel, QTextCursor
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

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"


class WorkerBD(QThread):
    finished_ok = Signal(object)
    finished_err = Signal(str)

    def __init__(self, fn, *args, parent=None, **kwargs):
        super().__init__(parent)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            resultado = self.fn(*self.args, **self.kwargs)
            self.finished_ok.emit(resultado)
        except Exception as exc:
            self.finished_err.emit(str(exc))


class ThreadSocket(QThread):
    signal_message = Signal(str)
    signal_error = Signal(str)

    def __init__(self, host, port, user_id, name, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.user_id = user_id
        self.name = name
        self._running = True
        self.sock = None

    def run(self):
        global connected, server
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, self.port))
            sock.settimeout(1.0)
            self.sock = sock
            server = sock
            connected = True
            sock.sendall(f"<name>{self.user_id}|{self.name}\n".encode("utf-8"))
        except OSError as e:
            connected = False
            self.signal_error.emit(str(e))
            return

        buffer = ""
        try:
            while self._running and connected:
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
            connected = False
            try:
                sock.close()
            except OSError:
                pass
            if server is sock:
                server = None

    def stop(self):
        global connected
        self._running = False
        connected = False
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
        self._workers = []

        self.bton_login.clicked.connect(self.iniciar_sesion)
        self.bton_crear.clicked.connect(self.crear_cuenta)

    def _run_worker(self, fn, on_ok, on_err, *args, **kwargs):
        worker = WorkerBD(fn, *args, parent=self, **kwargs)
        self._workers.append(worker)

        def _cleanup():
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.finished.connect(_cleanup)
        worker.start()

    def crear_cuenta(self):
        usuario = self.lineEdit.text().strip()
        contrasena = self.lineEdit_2.text().strip()

        if not usuario or not contrasena:
            QMessageBox.warning(
                self, "Campos vacíos", "Ingresa un usuario y una contraseña."
            )
            return

        self.bton_crear.setEnabled(False)
        self.bton_login.setEnabled(False)

        def _on_ok(creado):
            self.bton_crear.setEnabled(True)
            self.bton_login.setEnabled(True)
            if creado:
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

        def _on_err(err):
            self.bton_crear.setEnabled(True)
            self.bton_login.setEnabled(True)
            QMessageBox.critical(
                self,
                "Error de base de datos",
                f"No se pudo crear la cuenta:\n{err}",
            )

        self._run_worker(mssql.crear_usuario, _on_ok, _on_err, usuario, contrasena)

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

        self.bton_login.setEnabled(False)
        self.bton_crear.setEnabled(False)

        def _on_ok(datos_usuario):
            self.bton_login.setEnabled(True)
            self.bton_crear.setEnabled(True)
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

        def _on_err(err):
            self.bton_login.setEnabled(True)
            self.bton_crear.setEnabled(True)
            QMessageBox.critical(
                self, "Error", f"Ocurrió un error al iniciar sesión:\n{err}"
            )

        self._run_worker(
            mssql.autenticar_usuario, _on_ok, _on_err, usuario, contrasena
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
        self.canal_activo_id = None
        self.canal_creador_id = None
        self.categoria_actual = "chats"
        self.usuarios_conectados = []
        self.todos_usuarios_bd = []
        self.historial_global = []
        self.grupos_disponibles = []
        self.canales_disponibles = []
        self._workers = []
        self._cache_imagenes = {}

        self.actionSalir.triggered.connect(self.salir)
        self.coneccion = None
        self.btnSend.clicked.connect(self.mensaje_saliente)
        self.setWindowTitle("Messenger - Desconectado")
        self.txtSend.returnPressed.connect(self.mensaje_saliente)
        self.imagenes_usuarios = {}

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
        self.refrescar_lista_actual()

        if host and port and user_name:
            self.conectar_servidor(host, port, user_id, user_name)

    def _run_worker(self, fn, on_ok, on_err=None, *args, **kwargs):
        worker = WorkerBD(fn, *args, parent=self, **kwargs)
        self._workers.append(worker)

        def _cleanup():
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()

        worker.finished_ok.connect(on_ok)
        if on_err:
            worker.finished_err.connect(on_err)
        else:
            worker.finished_err.connect(lambda err: print(f"Error en hilo BD: {err}"))
        worker.finished.connect(_cleanup)
        worker.start()

    def _consultar_datos_iniciales(self, uid):
        usuarios_info = mssql.obtener_usuarios_con_imagen()
        canales = mssql.obtener_canales()
        grupos = mssql.obtener_grupos_usuario(uid) if uid is not None else []
        return usuarios_info, canales, grupos

    def conectar_servidor(self, host, port, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name
        self.cargar_usuarios_bd()

        if self.coneccion:
            self.coneccion.stop()

        self.coneccion = ThreadSocket(host, port, user_id, user_name, parent=self)
        self.coneccion.signal_message.connect(self.procesar_mensaje)
        self.coneccion.signal_error.connect(
            lambda err: self.agregar_aviso_sistema(f"[Error de socket: {err}]")
        )
        self.coneccion.start()
        self.setWindowTitle(f"Messenger - Conectado ({user_name})")
        if hasattr(self, "lblUserConectado"):
            self.lblUserConectado.setText(f"Usuario: {user_name}")
        self.refrescar_lista_actual()

    def cargar_usuarios_bd(self):
        def _aplicar(resultado):
            usuarios_info, canales, grupos = resultado
            self.todos_usuarios_bd = [u["nombre_usuario"] for u in usuarios_info]
            self.imagenes_usuarios = {
                u["nombre_usuario"].strip().lower(): u["imagen"]
                for u in usuarios_info
                if u.get("nombre_usuario")
            }
            self.canales_disponibles = canales
            self.grupos_disponibles = grupos
            self._actualizar_avatar_usuario_actual()
            self.refrescar_lista_actual()

        self._run_worker(
            self._consultar_datos_iniciales,
            _aplicar,
            lambda err: print(f"Error al cargar datos de BD: {err}"),
            self.user_id,
        )

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

        self.refrescar_lista_actual()

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

        self.lblIndicadorChat.setText("Nuevo grupo")
        self.stackedDerecha.setCurrentIndex(1)
        self.txtNombreGrupo.setFocus()

    def cerrar_formulario_grupo(self):
        self.stackedDerecha.setCurrentIndex(0)
        self.actualizar_indicador_chat()

    def _crear_grupo_y_consultar(self, nombre_grupo, uid, miembros):
        id_grupo = mssql.crear_grupo_bd(nombre_grupo, uid, miembros)
        if not id_grupo:
            return None, []
        grupos = mssql.obtener_grupos_usuario(uid) if uid is not None else []
        return id_grupo, grupos

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

        self.btnGuardarGrupo.setEnabled(False)

        def _on_ok(resultado):
            self.btnGuardarGrupo.setEnabled(True)
            id_grupo, grupos = resultado
            if not id_grupo:
                QMessageBox.critical(
                    self, "Error", "No se pudo guardar el grupo en la base de datos."
                )
                return

            self.grupos_disponibles = grupos
            grupo_creado = next(
                (g for g in self.grupos_disponibles if int(g["id_grupo"]) == int(id_grupo)),
                None,
            )
            clave_img_grupo = grupo_creado.get("imagen") if grupo_creado else None

            if connected and server:
                try:
                    lista_csv = ",".join(miembros)
                    paquete = (
                        f"<nuevo_grupo>{id_grupo}|{nombre_grupo}|"
                        f"{lista_csv}|{clave_img_grupo or ''}\n"
                    )
                    server.sendall(paquete.encode("utf-8"))
                except OSError as e:
                    print(f"Error al notificar nuevo grupo por socket: {e}")

            self.refrescar_lista_actual()
            self.grupo_activo_id = id_grupo
            self.canal_activo_id = None
            self.canal_creador_id = None
            self.usuario_activo = nombre_grupo

            self._actualizar_permiso_envio_canal(True)
            self._actualizar_avatar_chat(clave_img_grupo)
            self.actualizar_indicador_chat()

            self.cerrar_formulario_grupo()
            self.txtSend.setPlaceholderText(f"Mensaje en {nombre_grupo}...")
            self.txtMsgs.clear()
            self.agregar_aviso_sistema(
                f"Grupo '{nombre_grupo}' creado. Miembros: {', '.join(miembros)}"
            )

        def _on_err(err):
            self.btnGuardarGrupo.setEnabled(True)
            QMessageBox.critical(self, "Error", f"No se pudo crear el grupo:\n{err}")

        self._run_worker(
            self._crear_grupo_y_consultar,
            _on_ok,
            _on_err,
            nombre_grupo,
            self.user_id,
            miembros,
        )

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
                        if (connected or usuario_str.lower() in conectados_lower)
                        else "⚪"
                    )
                    texto_visible = f"{icono} {usuario_str} (tú)"
                elif usuario_str.lower() in conectados_lower:
                    texto_visible = f"🟢 {usuario_str}"
                else:
                    texto_visible = f"⚪ {usuario_str}"
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
                if (es_yo and connected) or (usuario.lower() in conectados_lower)
                else "⚪ Desconectado"
            )
            self.lblIndicadorChat.setText(f"Chat actual: {etiqueta} · {estado}")
        elif self.categoria_actual == "canal":
            self.lblIndicadorChat.setText(f"Canal: {usuario}")

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

            self.txtSend.setPlaceholderText(f"Mensaje en #{self.usuario_activo}...")
            if es_creador:
                self.txtSend.setFocus()
            self.txtMsgs.clear()

            if connected and server:
                try:
                    server.sendall(
                        f"<historial_canal>{self.canal_activo_id}\n".encode("utf-8")
                    )
                except OSError as e:
                    self.agregar_aviso_sistema(
                        f"[Error al pedir historial del canal: {e}]"
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
        destino = getattr(self, "usuario_activo", None) or "Global"
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

        elif self.categoria_actual == "canal":
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
            server.sendall(
                f"<canal_msg>{self.canal_activo_id}|{texto}\n".encode("utf-8")
            )
            self.txtSend.clear()
            self.agregar_burbuja("Tú", texto, es_mio=True)
            return

        elif destino == "Global":
            server.sendall(f"{texto}\n".encode("utf-8"))
            self.historial_global.append(("burbuja", "Tú", texto, True))

        else:
            paquete = f"<msg>{destino}|{texto}\n"
            server.sendall(paquete.encode("utf-8"))

        self.txtSend.clear()
        self.agregar_burbuja("Tú", texto, es_mio=True)

    def _aplicar_usuarios_bd(self, usuarios_info):
        if usuarios_info:
            self.imagenes_usuarios = {
                u["nombre_usuario"].strip().lower(): u["imagen"]
                for u in usuarios_info
                if u.get("nombre_usuario")
            }
            bd_lower = {u.lower() for u in self.todos_usuarios_bd}
            for u in usuarios_info:
                nombre_bd = u["nombre_usuario"]
                if nombre_bd.lower() not in bd_lower:
                    self.todos_usuarios_bd.append(nombre_bd)
                    bd_lower.add(nombre_bd.lower())

        bd_lower = {u.lower() for u in self.todos_usuarios_bd}
        for u in self.usuarios_conectados:
            if u.lower() not in bd_lower:
                self.todos_usuarios_bd.append(u)
                bd_lower.add(u.lower())

        self._actualizar_avatar_usuario_actual()
        self.refrescar_lista_actual()
        self.actualizar_indicador_chat()

    def procesar_mensaje(self, msg: str):
        if msg.startswith("<users>"):
            contenido = msg.removeprefix("<users>")
            if contenido.endswith("</users>"):
                contenido = contenido[:-8]
            self.usuarios_conectados = [
                u.strip() for u in contenido.split(",") if u.strip()
            ]
            self.refrescar_lista_actual()
            self.actualizar_indicador_chat()
            self._run_worker(mssql.obtener_usuarios_con_imagen, self._aplicar_usuarios_bd)

        elif msg.startswith("<nuevo_grupo>"):
            payload = msg.removeprefix("<nuevo_grupo>")
            partes = payload.split("|", 2)
            clave_img = (
                partes[2].strip() if len(partes) >= 3 and partes[2].strip() else None
            )

            if self.user_id is not None:
                def _on_grupos(grupos):
                    self.grupos_disponibles = grupos
                    if self.categoria_actual == "grupos":
                        self.refrescar_lista_actual()

                self._run_worker(mssql.obtener_grupos_usuario, _on_grupos, None, self.user_id)
            elif len(partes) >= 2:
                id_g_str = partes[0].strip()
                nom_g = partes[1].strip()
                if id_g_str.isdigit() and nom_g and hasattr(self, "_agregar_grupo_local"):
                    self._agregar_grupo_local(
                        {
                            "id_grupo": int(id_g_str),
                            "nombre_grupo": nom_g,
                            "imagen": clave_img,
                        }
                    )
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

        elif msg.startswith("<nuevo_canal>"):
            payload = msg.removeprefix("<nuevo_canal>")
            partes = payload.split("|", 4)
            if len(partes) >= 2:
                id_str = partes[0].strip()
                nombre_c = partes[1].strip()
                desc_c = partes[2].strip() if len(partes) >= 3 else ""
                creador_id_str = partes[3].strip() if len(partes) >= 4 else ""
                clave_img = (
                    partes[4].strip() if len(partes) >= 5 and partes[4].strip() else None
                )

                canal_dict = {
                    "id_canal": int(id_str) if id_str.isdigit() else id_str,
                    "nombre_canal": nombre_c,
                    "descripcion": desc_c,
                    "id_creador": int(creador_id_str)
                    if creador_id_str.isdigit()
                    else None,
                    "creador": "",
                    "imagen": clave_img,
                }
                if (
                    self._agregar_canal_local(canal_dict)
                    and self.categoria_actual == "canal"
                ):
                    self.refrescar_lista_actual()

        elif msg.startswith("<canal_msg>"):
            payload = msg.removeprefix("<canal_msg>")
            partes = payload.split("|", 2)
            if len(partes) == 3:
                id_c_str, remitente, contenido = partes
                remitente = remitente.strip()
                if remitente.lower() == self.user_name.strip().lower():
                    return
                if (
                    self.categoria_actual == "canal"
                    and str(getattr(self, "canal_activo_id", "")) == id_c_str.strip()
                ):
                    self.agregar_burbuja(remitente, contenido, es_mio=False)
                else:
                    self.agregar_aviso_sistema(
                        f"Nuevo mensaje en canal de {remitente}"
                    )

        elif msg.startswith("<historial_canal_data>"):
            payload = msg.removeprefix("<historial_canal_data>").strip()
            self.mostrar_historial_canal(payload)

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

    def mostrar_historial_canal(self, raw_data: str):
        try:
            data = json.loads(raw_data.strip())
        except json.JSONDecodeError:
            self.agregar_aviso_sistema("Error al obtener historial del canal")
            return

        id_canal = data.get("id_canal")
        mensajes = data.get("mensajes", [])

        if getattr(self, "canal_activo_id", None) != id_canal:
            return

        self.txtMsgs.clear()

        if not mensajes:
            self.agregar_aviso_sistema("No hay mensajes previos en este canal")
            return

        for msg in mensajes:
            remitente = msg.get("remitente", "Desconocido")
            contenido = msg.get("contenido", "")
            fecha = msg.get("fecha_envio", "")
            es_mio = remitente.strip().lower() == self.user_name.strip().lower()
            self.agregar_burbuja(remitente, contenido, es_mio=es_mio, fecha=fecha)

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

    def _detener_hilos(self):
        if self.coneccion:
            self.coneccion.stop()
            self.coneccion = None
        for worker in list(self._workers):
            worker.wait(2000)

    def closeEvent(self, event):
        self._detener_hilos()
        super().closeEvent(event)

    def salir(self):
        self._detener_hilos()
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

    def abrir_formulario_canal(self):
        self.txtNombreCanal.clear()
        self.txtDescripcionCanal.clear()
        self.lblIndicadorChat.setText("Nuevo canal")
        self.stackedDerecha.setCurrentWidget(self.pageCrearCanal)
        self.txtNombreCanal.setFocus()

    def cerrar_formulario_canal(self):
        self.txtNombreCanal.clear()
        self.txtDescripcionCanal.clear()
        self.stackedDerecha.setCurrentWidget(self.pageChat)
        self.actualizar_indicador_chat()

    def _agregar_canal_local(self, canal: dict) -> bool:
        nombre = str(canal.get("nombre_canal", "")).strip()
        id_canal = canal.get("id_canal")
        if not nombre:
            return False

        for c in self.canales_disponibles:
            if isinstance(c, dict):
                if (id_canal is not None and c.get("id_canal") == id_canal) or (
                    c.get("nombre_canal", "").strip().lower() == nombre.lower()
                ):
                    return False
            elif str(c).strip().lower() == nombre.lower():
                return False

        self.canales_disponibles.append(
            {
                "id_canal": id_canal,
                "nombre_canal": nombre,
                "descripcion": str(canal.get("descripcion", "")).strip(),
                "id_creador": canal.get("id_creador"),
                "creador": str(canal.get("creador", "")).strip(),
                "imagen": canal.get("imagen"),
            }
        )
        self.canales_disponibles.sort(
            key=lambda x: (
                x["nombre_canal"].lower() if isinstance(x, dict) else str(x).lower()
            )
        )
        return True

    def _crear_canal_y_consultar(self, nombre_canal, descripcion_canal, uid):
        id_canal = mssql.crear_canal_bd(
            nombre_canal=nombre_canal,
            descripcion=descripcion_canal,
            id_creador=uid,
        )
        if not id_canal:
            return None, None
        canales_bd = mssql.obtener_canales()
        canal_bd = next(
            (c for c in canales_bd if int(c["id_canal"]) == int(id_canal)), None
        )
        clave_img = canal_bd.get("imagen") if canal_bd else None
        return id_canal, clave_img

    def confirmar_crear_canal(self):
        nombre_canal = self.txtNombreCanal.text().strip()
        descripcion_canal = self.txtDescripcionCanal.text().strip()

        if not nombre_canal:
            QMessageBox.warning(
                self, "Falta nombre", "Escribe un nombre para el canal."
            )
            return

        if self.user_id is None:
            QMessageBox.warning(
                self, "Sesión no válida", "No se detectó tu usuario para crear el canal."
            )
            return

        self.btnGuardarCanal.setEnabled(False)

        def _on_ok(resultado):
            self.btnGuardarCanal.setEnabled(True)
            id_canal, clave_img = resultado
            if not id_canal:
                QMessageBox.critical(
                    self,
                    "Error al crear canal",
                    "No se pudo guardar el canal (puede que ya exista o haya error en BD).",
                )
                return

            nuevo_canal = {
                "id_canal": id_canal,
                "nombre_canal": nombre_canal,
                "descripcion": descripcion_canal,
                "id_creador": self.user_id,
                "creador": self.user_name,
                "imagen": clave_img,
            }

            self._agregar_canal_local(nuevo_canal)
            if self.categoria_actual == "canal":
                self.refrescar_lista_actual()

            if connected and server:
                try:
                    paquete = (
                        f"<nuevo_canal>{id_canal}|{nombre_canal}|"
                        f"{descripcion_canal}|{self.user_id}|{clave_img}\n"
                    )
                    server.sendall(paquete.encode("utf-8"))
                except OSError as e:
                    print(f"Error al notificar nuevo canal por socket: {e}")

            self.grupo_activo_id = None
            self.canal_activo_id = id_canal
            self.canal_creador_id = self.user_id
            self.usuario_activo = nombre_canal

            self._actualizar_permiso_envio_canal(True)
            self._actualizar_avatar_chat(clave_img)
            self.actualizar_indicador_chat()

            self.cerrar_formulario_canal()
            self.txtSend.setPlaceholderText(f"Mensaje en #{nombre_canal}...")
            self.txtMsgs.clear()

            aviso = f"Canal '{nombre_canal}' creado."
            if descripcion_canal:
                aviso += f" Descripción: {descripcion_canal}"
            self.agregar_aviso_sistema(aviso)

        def _on_err(err):
            self.btnGuardarCanal.setEnabled(True)
            QMessageBox.critical(
                self, "Error al crear canal", f"Ocurrió un error en BD:\n{err}"
            )

        self._run_worker(
            self._crear_canal_y_consultar,
            _on_ok,
            _on_err,
            nombre_canal,
            descripcion_canal,
            self.user_id,
        )

    def _actualizar_permiso_envio_canal(self, puede_escribir: bool = True):
        if hasattr(self, "lblSoloCreadorCanal"):
            self.lblSoloCreadorCanal.setVisible(not puede_escribir)
        if hasattr(self, "txtSend"):
            self.txtSend.setVisible(puede_escribir)
            self.txtSend.setEnabled(puede_escribir)
            if not puede_escribir:
                self.txtSend.clear()
        if hasattr(self, "btnSend"):
            self.btnSend.setVisible(puede_escribir)
            self.btnSend.setEnabled(puede_escribir)

    def cerrar_sesion(self):
        respuesta = QMessageBox.question(
            self,
            "Cerrar sesión",
            "¿Seguro que quieres cerrar tu sesión actual?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        self._detener_hilos()
        self.ventana_login = VentanaLogin()
        self.ventana_login.show()
        self.close()


class MiDialogo(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)