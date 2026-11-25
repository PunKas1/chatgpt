# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QMenu,
    QMenuBar,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class Ui_Messenger(object):
    def setupUi(self, Messenger):
        if not Messenger.objectName():
            Messenger.setObjectName("Messenger")
        Messenger.resize(840, 560)
        Messenger.setStyleSheet("""
            QMainWindow, #centralwidget {
                background-color: #121214;
                color: #ffffff;
                font-family: "Segoe UI";
            }
            QLabel#lblUserConectado {
                background-color: #1e1e22;
                border: 1px solid #2e2e34;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 13px;
                color: #4ade80;
            }
            QLabel#lblIndicadorChat {
                background-color: #1e1e22;
                border: 1px solid #2e2e34;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 14px;
                color: #60a5fa;
            }
            QPushButton.tabBtn {
                background-color: #1e1e22;
                color: #a1a1aa;
                border: 1px solid #2e2e34;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton.tabBtn:hover {
                background-color: #27272a;
                color: #ffffff;
            }
            QPushButton.tabBtn[active="true"] {
                background-color: #2563eb;
                color: #ffffff;
                border: 1px solid #3b82f6;
            }
            QPushButton#btnCrearGrupo, QPushButton#btnCrearCanal {
                background-color: #16a34a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#btnCrearGrupo:hover, QPushButton#btnCrearCanal:hover {
                background-color: #15803d;
            }
            QListView#listaChats, QListWidget#listaMiembrosGrupo {
                background-color: #18181b;
                border: 1px solid #2e2e34;
                border-radius: 8px;
                padding: 4px;
                color: #f4f4f5;
                font-size: 13px;
                outline: none;
            }
            QListView#listaChats::item, QListWidget#listaMiembrosGrupo::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QListView#listaChats::item:selected {
                background-color: #2563eb;
                color: #ffffff;
            }
            QListView#listaChats::item:hover:!selected,
            QListWidget#listaMiembrosGrupo::item:hover {
                background-color: #27272a;
            }
            QTextBrowser#txtMsgs {
                background-color: #18181b;
                border: 1px solid #2e2e34;
                border-radius: 8px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QFrame#cardFormGrupo, QFrame#cardFormCanal {
                background-color: #18181b;
                border: 1px solid #2e2e34;
                border-radius: 8px;
            }
            QLabel.formLabel {
                color: #d4d4d8;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
            QLineEdit#txtSend, QLineEdit#txtNombreGrupo, QLineEdit#txtNombreCanal, QLineEdit#txtDescripcionCanal {
                background-color: #1e1e22;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit#txtSend:focus, QLineEdit#txtNombreGrupo:focus, QLineEdit#txtNombreCanal:focus, QLineEdit#txtDescripcionCanal:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton#btnSend, QPushButton#btnGuardarGrupo, QPushButton#btnGuardarCanal {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#btnSend:hover, QPushButton#btnGuardarGrupo:hover, QPushButton#btnGuardarCanal:hover {
                background-color: #1d4ed8;
            }
            QPushButton#btnCancelarGrupo, QPushButton#btnCancelarCanal {
                background-color: #27272a;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#btnCancelarGrupo:hover, QPushButton#btnCancelarCanal:hover {
                background-color: #3f3f46;
            }
            QMenuBar {
                background-color: #18181b;
                color: #e4e4e7;
            }
            QMenuBar::item:selected {
                background-color: #27272a;
            }
            QMenu {
                background-color: #1e1e22;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
            }
            QMenu::item:selected {
                background-color: #2563eb;
            }

            QPushButton#btnCerrarSesion {
                background-color: #dc2626;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#btnCerrarSesion:hover {
                background-color: #b91c1c;
            }
            QPushButton#btnCerrarSesion:pressed {
                background-color: #991b1b;
            }
        """)

        self.actionSalir = QAction(Messenger)
        self.actionSalir.setObjectName("actionSalir")

        self.centralwidget = QWidget(Messenger)
        self.centralwidget.setObjectName("centralwidget")

        self.mainLayout = QHBoxLayout(self.centralwidget)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)

        # ================= PANEL IZQUIERDO =================
        self.leftPanel = QVBoxLayout()
        self.leftPanel.setSpacing(8)

        self.headerUserLayout = QHBoxLayout()
        self.headerUserLayout.setContentsMargins(0, 0, 0, 0)
        self.headerUserLayout.setSpacing(8)

        self.lblAvatarUsuario = QLabel(self.centralwidget)
        self.lblAvatarUsuario.setObjectName("lblAvatarUsuario")
        self.lblAvatarUsuario.setFixedSize(36, 36)
        self.lblAvatarUsuario.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblAvatarUsuario.setStyleSheet(
            """
            QLabel#lblAvatarUsuario {
                background-color: #1e1e22;
                border: 1px solid #2e2e34;
                border-radius: 8px;
            }
            """
        )
        self.headerUserLayout.addWidget(self.lblAvatarUsuario)

        self.lblUserConectado = QLabel(self.centralwidget)
        self.lblUserConectado.setObjectName("lblUserConectado")
        self.headerUserLayout.addWidget(self.lblUserConectado, 1)

        self.leftPanel.addLayout(self.headerUserLayout)

        self.tabsLayout = QHBoxLayout()
        self.tabsLayout.setSpacing(6)

        self.btnChats = QPushButton(self.centralwidget)
        self.btnChats.setObjectName("btnChats")
        self.btnChats.setProperty("class", "tabBtn")
        self.btnChats.setProperty("active", "true")

        self.btnGrupos = QPushButton(self.centralwidget)
        self.btnGrupos.setObjectName("btnGrupos")
        self.btnGrupos.setProperty("class", "tabBtn")
        self.btnGrupos.setProperty("active", "false")

        self.btnCanal = QPushButton(self.centralwidget)
        self.btnCanal.setObjectName("btnCanal")
        self.btnCanal.setProperty("class", "tabBtn")
        self.btnCanal.setProperty("active", "false")

        self.tabsLayout.addWidget(self.btnChats)
        self.tabsLayout.addWidget(self.btnGrupos)
        self.tabsLayout.addWidget(self.btnCanal)
        self.leftPanel.addLayout(self.tabsLayout)

        # Botón para abrir formulario de crear grupo (solo visible en pestaña Grupos)
        self.btnCrearGrupo = QPushButton(self.centralwidget)
        self.btnCrearGrupo.setObjectName("btnCrearGrupo")
        self.btnCrearGrupo.setVisible(False)
        self.leftPanel.addWidget(self.btnCrearGrupo)

        # Botón para abrir formulario de crear canal (solo visible en pestaña Canales)
        self.btnCrearCanal = QPushButton(self.centralwidget)
        self.btnCrearCanal.setObjectName("btnCrearCanal")
        self.btnCrearCanal.setVisible(False)
        self.leftPanel.addWidget(self.btnCrearCanal)

        self.listaChats = QListView(self.centralwidget)
        self.listaChats.setObjectName("listaChats")
        self.listaChats.setMinimumWidth(240)
        self.listaChats.setIconSize(QSize(30, 30))
        self.leftPanel.addWidget(self.listaChats)

        self.mainLayout.addLayout(self.leftPanel, 1)

        # ================= PANEL DERECHO =================
        self.rightPanel = QVBoxLayout()
        self.rightPanel.setSpacing(8)

        # Barra superior derecha con botón Cerrar sesión pegado a la esquina superior derecha
        self.topBarLayout = QHBoxLayout()
        self.topBarLayout.setContentsMargins(0, 0, 0, 0)
        self.topBarLayout.setSpacing(8)
        self.topBarLayout.addStretch()

        self.btnCerrarSesion = QPushButton(self.centralwidget)
        self.btnCerrarSesion.setObjectName("btnCerrarSesion")
        self.topBarLayout.addWidget(self.btnCerrarSesion)

        self.rightPanel.addLayout(self.topBarLayout)

        self.headerChatLayout = QHBoxLayout()
        self.headerChatLayout.setContentsMargins(0, 0, 0, 0)
        self.headerChatLayout.setSpacing(8)

        self.lblAvatarChat = QLabel(self.centralwidget)
        self.lblAvatarChat.setObjectName("lblAvatarChat")
        self.lblAvatarChat.setFixedSize(40, 40)
        self.lblAvatarChat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblAvatarChat.setStyleSheet(
            """
            QLabel#lblAvatarChat {
                background-color: #1e1e22;
                border: 1px solid #2e2e34;
                border-radius: 8px;
            }
            """
        )
        self.headerChatLayout.addWidget(self.lblAvatarChat)

        self.lblIndicadorChat = QLabel(self.centralwidget)
        self.lblIndicadorChat.setObjectName("lblIndicadorChat")
        self.headerChatLayout.addWidget(self.lblIndicadorChat, 1)

        self.rightPanel.addLayout(self.headerChatLayout)

        # Contenedor apilado: Página 0 = Chat | Página 1 = Formulario Crear Grupo | Página 2 = Formulario Crear Canal
        self.stackedDerecha = QStackedWidget(self.centralwidget)
        self.stackedDerecha.setObjectName("stackedDerecha")

        # --- PÁGINA 0: VISTA NORMAL DE CHAT ---
        self.pageChat = QWidget()
        self.pageChatLayout = QVBoxLayout(self.pageChat)
        self.pageChatLayout.setContentsMargins(0, 0, 0, 0)
        self.pageChatLayout.setSpacing(8)

        self.txtMsgs = QTextBrowser(self.pageChat)
        self.txtMsgs.setObjectName("txtMsgs")
        self.txtMsgs.setFrameShape(QFrame.Shape.Box)
        self.txtMsgs.setOpenExternalLinks(False)
        self.pageChatLayout.addWidget(self.txtMsgs)

        self.sendLayout = QHBoxLayout()
        self.sendLayout.setSpacing(8)

        self.txtSend = QLineEdit(self.pageChat)
        self.txtSend.setObjectName("txtSend")
        self.txtSend.setMaxLength(1023)

        self.btnSend = QPushButton(self.pageChat)
        self.btnSend.setObjectName("btnSend")

        self.lblSoloCreadorCanal = QLabel(self.pageChat)
        self.lblSoloCreadorCanal.setObjectName("lblSoloCreadorCanal")
        self.lblSoloCreadorCanal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblSoloCreadorCanal.setStyleSheet(
            """
            QLabel#lblSoloCreadorCanal {
                background-color: #1e1e22;
                border: 1px solid #2e2e34;
                border-radius: 8px;
                padding: 8px 12px;
                color: #a1a1aa;
                font-size: 13px;
                font-style: italic;
            }
            """
        )
        self.lblSoloCreadorCanal.setVisible(False)

        self.sendLayout.addWidget(self.txtSend)
        self.sendLayout.addWidget(self.btnSend)
        self.sendLayout.addWidget(self.lblSoloCreadorCanal)

        self.pageChatLayout.addLayout(self.sendLayout)

        self.stackedDerecha.addWidget(self.pageChat)

        # --- PÁGINA 1: FORMULARIO CREAR GRUPO ---
        self.pageCrearGrupo = QWidget()
        self.pageGrupoOuter = QVBoxLayout(self.pageCrearGrupo)
        self.pageGrupoOuter.setContentsMargins(0, 0, 0, 0)

        self.cardFormGrupo = QFrame(self.pageCrearGrupo)
        self.cardFormGrupo.setObjectName("cardFormGrupo")
        self.formGrupoLayout = QVBoxLayout(self.cardFormGrupo)
        self.formGrupoLayout.setContentsMargins(18, 18, 18, 18)
        self.formGrupoLayout.setSpacing(12)

        self.lblTituloFormGrupo = QLabel(self.cardFormGrupo)
        self.lblTituloFormGrupo.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #ffffff; background: transparent;"
        )
        self.formGrupoLayout.addWidget(self.lblTituloFormGrupo)

        self.lblNombreGrupo = QLabel(self.cardFormGrupo)
        self.lblNombreGrupo.setProperty("class", "formLabel")
        self.formGrupoLayout.addWidget(self.lblNombreGrupo)

        self.txtNombreGrupo = QLineEdit(self.cardFormGrupo)
        self.txtNombreGrupo.setObjectName("txtNombreGrupo")
        self.txtNombreGrupo.setMaxLength(80)
        self.formGrupoLayout.addWidget(self.txtNombreGrupo)

        self.lblMiembrosGrupo = QLabel(self.cardFormGrupo)
        self.lblMiembrosGrupo.setProperty("class", "formLabel")
        self.formGrupoLayout.addWidget(self.lblMiembrosGrupo)

        self.listaMiembrosGrupo = QListWidget(self.cardFormGrupo)
        self.listaMiembrosGrupo.setObjectName("listaMiembrosGrupo")
        self.formGrupoLayout.addWidget(self.listaMiembrosGrupo)

        self.botonesFormGrupo = QHBoxLayout()
        self.botonesFormGrupo.setSpacing(10)
        self.botonesFormGrupo.addStretch()

        self.btnCancelarGrupo = QPushButton(self.cardFormGrupo)
        self.btnCancelarGrupo.setObjectName("btnCancelarGrupo")

        self.btnGuardarGrupo = QPushButton(self.cardFormGrupo)
        self.btnGuardarGrupo.setObjectName("btnGuardarGrupo")

        self.botonesFormGrupo.addWidget(self.btnCancelarGrupo)
        self.botonesFormGrupo.addWidget(self.btnGuardarGrupo)
        self.formGrupoLayout.addLayout(self.botonesFormGrupo)

        self.pageGrupoOuter.addWidget(self.cardFormGrupo)
        self.stackedDerecha.addWidget(self.pageCrearGrupo)

        # --- PÁGINA 2: FORMULARIO CREAR CANAL ---
        self.pageCrearCanal = QWidget()
        self.pageCanalOuter = QVBoxLayout(self.pageCrearCanal)
        self.pageCanalOuter.setContentsMargins(0, 0, 0, 0)

        self.cardFormCanal = QFrame(self.pageCrearCanal)
        self.cardFormCanal.setObjectName("cardFormCanal")
        self.formCanalLayout = QVBoxLayout(self.cardFormCanal)
        self.formCanalLayout.setContentsMargins(18, 18, 18, 18)
        self.formCanalLayout.setSpacing(12)

        self.lblTituloFormCanal = QLabel(self.cardFormCanal)
        self.lblTituloFormCanal.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #ffffff; background: transparent;"
        )
        self.formCanalLayout.addWidget(self.lblTituloFormCanal)

        self.lblNombreCanal = QLabel(self.cardFormCanal)
        self.lblNombreCanal.setProperty("class", "formLabel")
        self.formCanalLayout.addWidget(self.lblNombreCanal)

        self.txtNombreCanal = QLineEdit(self.cardFormCanal)
        self.txtNombreCanal.setObjectName("txtNombreCanal")
        self.txtNombreCanal.setMaxLength(80)
        self.formCanalLayout.addWidget(self.txtNombreCanal)

        self.lblDescripcionCanal = QLabel(self.cardFormCanal)
        self.lblDescripcionCanal.setProperty("class", "formLabel")
        self.formCanalLayout.addWidget(self.lblDescripcionCanal)

        self.txtDescripcionCanal = QLineEdit(self.cardFormCanal)
        self.txtDescripcionCanal.setObjectName("txtDescripcionCanal")
        self.txtDescripcionCanal.setMaxLength(200)
        self.formCanalLayout.addWidget(self.txtDescripcionCanal)

        self.formCanalLayout.addStretch()

        self.botonesFormCanal = QHBoxLayout()
        self.botonesFormCanal.setSpacing(10)
        self.botonesFormCanal.addStretch()

        self.btnCancelarCanal = QPushButton(self.cardFormCanal)
        self.btnCancelarCanal.setObjectName("btnCancelarCanal")

        self.btnGuardarCanal = QPushButton(self.cardFormCanal)
        self.btnGuardarCanal.setObjectName("btnGuardarCanal")

        self.botonesFormCanal.addWidget(self.btnCancelarCanal)
        self.botonesFormCanal.addWidget(self.btnGuardarCanal)
        self.formCanalLayout.addLayout(self.botonesFormCanal)

        self.pageCanalOuter.addWidget(self.cardFormCanal)
        self.stackedDerecha.addWidget(self.pageCrearCanal)

        self.rightPanel.addWidget(self.stackedDerecha)
        self.mainLayout.addLayout(self.rightPanel, 2)

        Messenger.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(Messenger)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 840, 28))
        self.menuArchivo = QMenu(self.menubar)
        self.menuArchivo.setObjectName("menuArchivo")
        Messenger.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuArchivo.menuAction())
        self.menuArchivo.addAction(self.actionSalir)

        self.retranslateUi(Messenger)
        QMetaObject.connectSlotsByName(Messenger)

    def retranslateUi(self, Messenger):
        Messenger.setWindowTitle(
            QCoreApplication.translate("Messenger", "Messenger", None)
        )
        self.actionSalir.setText(
            QCoreApplication.translate("Messenger", "&Salir", None)
        )
        self.actionSalir.setShortcut(
            QCoreApplication.translate("Messenger", "Ctrl+X", None)
        )
        self.lblUserConectado.setText(
            QCoreApplication.translate("Messenger", "User: Desconectado", None)
        )
        self.btnChats.setText(
            QCoreApplication.translate("Messenger", "Chats", None)
        )
        self.btnGrupos.setText(
            QCoreApplication.translate("Messenger", "Grupos", None)
        )
        self.btnCanal.setText(
            QCoreApplication.translate("Messenger", "Canal", None)
        )
        self.btnCrearGrupo.setText(
            QCoreApplication.translate("Messenger", "+ Crear grupo", None)
        )
        self.lblIndicadorChat.setText(
            QCoreApplication.translate("Messenger", "Chat actual: Global", None)
        )
        self.txtSend.setPlaceholderText(
            QCoreApplication.translate("Messenger", "Escribe un mensaje en Global...", None)
        )
        self.btnSend.setText(
            QCoreApplication.translate("Messenger", "Enviar", None)
        )
        self.lblTituloFormGrupo.setText(
            QCoreApplication.translate("Messenger", "Crear nuevo grupo", None)
        )
        self.lblNombreGrupo.setText(
            QCoreApplication.translate("Messenger", "1. Nombre del grupo:", None)
        )
        self.txtNombreGrupo.setPlaceholderText(
            QCoreApplication.translate("Messenger", "Ej. Proyecto Telemática...", None)
        )
        self.lblMiembrosGrupo.setText(
            QCoreApplication.translate("Messenger", "2. Selecciona los miembros (tú ya estás incluido):", None)
        )
        self.btnCancelarGrupo.setText(
            QCoreApplication.translate("Messenger", "Cancelar", None)
        )
        self.btnGuardarGrupo.setText(
            QCoreApplication.translate("Messenger", "Crear grupo", None)
        )
        self.menuArchivo.setTitle(
            QCoreApplication.translate("Messenger", "&Archivo", None)
        )

        self.btnCrearCanal.setText(
            QCoreApplication.translate("Messenger", "+ Crear canal", None)
        )
        self.lblTituloFormCanal.setText(
            QCoreApplication.translate("Messenger", "Crear nuevo canal", None)
        )
        self.lblNombreCanal.setText(
            QCoreApplication.translate("Messenger", "1. Nombre del canal:", None)
        )
        self.txtNombreCanal.setPlaceholderText(
            QCoreApplication.translate("Messenger", "Ej. Avisos generales...", None)
        )
        self.lblDescripcionCanal.setText(
            QCoreApplication.translate("Messenger", "2. Descripción del canal:", None)
        )
        self.txtDescripcionCanal.setPlaceholderText(
            QCoreApplication.translate("Messenger", "De qué trata este canal...", None)
        )
        self.btnCancelarCanal.setText(
            QCoreApplication.translate("Messenger", "Cancelar", None)
        )
        self.btnGuardarCanal.setText(
            QCoreApplication.translate("Messenger", "Crear canal", None)
        )

        self.lblSoloCreadorCanal.setText(
            QCoreApplication.translate(
                "Messenger", "Solo el creador puede enviar mensajes", None
            )
        )

        self.btnCerrarSesion.setText(
            QCoreApplication.translate("Messenger", "Cerrar sesión", None)
        )