# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
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
            QPushButton#btnCrearGrupo {
                background-color: #16a34a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#btnCrearGrupo:hover {
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
            QFrame#cardFormGrupo {
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
            QLineEdit#txtSend, QLineEdit#txtNombreGrupo {
                background-color: #1e1e22;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit#txtSend:focus, QLineEdit#txtNombreGrupo:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton#btnSend, QPushButton#btnGuardarGrupo {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#btnSend:hover, QPushButton#btnGuardarGrupo:hover {
                background-color: #1d4ed8;
            }
            QPushButton#btnCancelarGrupo {
                background-color: #27272a;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#btnCancelarGrupo:hover {
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

        self.lblUserConectado = QLabel(self.centralwidget)
        self.lblUserConectado.setObjectName("lblUserConectado")
        self.leftPanel.addWidget(self.lblUserConectado)

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

        self.listaChats = QListView(self.centralwidget)
        self.listaChats.setObjectName("listaChats")
        self.listaChats.setMinimumWidth(240)
        self.leftPanel.addWidget(self.listaChats)

        self.mainLayout.addLayout(self.leftPanel, 1)

        # ================= PANEL DERECHO =================
        self.rightPanel = QVBoxLayout()
        self.rightPanel.setSpacing(8)

        self.lblIndicadorChat = QLabel(self.centralwidget)
        self.lblIndicadorChat.setObjectName("lblIndicadorChat")
        self.rightPanel.addWidget(self.lblIndicadorChat)

        # Contenedor apilado: Página 0 = Chat | Página 1 = Formulario Crear Grupo
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

        self.sendLayout.addWidget(self.txtSend)
        self.sendLayout.addWidget(self.btnSend)
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