# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class Ui_Messenger(object):
    def setupUi(self, Messenger):
        if not Messenger.objectName():
            Messenger.setObjectName("Messenger")
        Messenger.resize(820, 540)
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
            QListView#listaChats {
                background-color: #18181b;
                border: 1px solid #2e2e34;
                border-radius: 8px;
                padding: 4px;
                color: #f4f4f5;
                font-size: 13px;
                outline: none;
            }
            QListView#listaChats::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QListView#listaChats::item:selected {
                background-color: #2563eb;
                color: #ffffff;
            }
            QListView#listaChats::item:hover:!selected {
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
            QLineEdit#txtSend {
                background-color: #1e1e22;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit#txtSend:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton#btnSend {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#btnSend:hover {
                background-color: #1d4ed8;
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

        self.actionConectar = QAction(Messenger)
        self.actionConectar.setObjectName("actionConectar")
        self.actionSalir = QAction(Messenger)
        self.actionSalir.setObjectName("actionSalir")
        self.actionMis_Comunidades = QAction(Messenger)
        self.actionMis_Comunidades.setObjectName("actionMis_Comunidades")
        self.actionMas_Comunidades = QAction(Messenger)
        self.actionMas_Comunidades.setObjectName("actionMas_Comunidades")

        self.centralwidget = QWidget(Messenger)
        self.centralwidget.setObjectName("centralwidget")

        # Layout principal horizontal (Panel Izquierdo | Panel Derecho)
        self.mainLayout = QHBoxLayout(self.centralwidget)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)

        # ================= PANEL IZQUIERDO =================
        self.leftPanel = QVBoxLayout()
        self.leftPanel.setSpacing(8)

        # 1. User conectado
        self.lblUserConectado = QLabel(self.centralwidget)
        self.lblUserConectado.setObjectName("lblUserConectado")
        self.leftPanel.addWidget(self.lblUserConectado)

        # 2. Botones: Chats | Grupos | Canal
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

        # 3. Despliegue de cosas (listaChats)
        self.listaChats = QListView(self.centralwidget)
        self.listaChats.setObjectName("listaChats")
        self.listaChats.setMinimumWidth(240)
        self.leftPanel.addWidget(self.listaChats)

        self.mainLayout.addLayout(self.leftPanel, 1)

        # ================= PANEL DERECHO =================
        self.rightPanel = QVBoxLayout()
        self.rightPanel.setSpacing(8)

        # 1. Indicador de chat
        self.lblIndicadorChat = QLabel(self.centralwidget)
        self.lblIndicadorChat.setObjectName("lblIndicadorChat")
        self.rightPanel.addWidget(self.lblIndicadorChat)

        # 2. Área de mensajes con burbujas HTML
        self.txtMsgs = QTextBrowser(self.centralwidget)
        self.txtMsgs.setObjectName("txtMsgs")
        self.txtMsgs.setFrameShape(QFrame.Shape.Box)
        self.txtMsgs.setOpenExternalLinks(False)
        self.rightPanel.addWidget(self.txtMsgs)

        # 3. Fila inferior: escribir + enviar
        self.sendLayout = QHBoxLayout()
        self.sendLayout.setSpacing(8)

        self.txtSend = QLineEdit(self.centralwidget)
        self.txtSend.setObjectName("txtSend")
        self.txtSend.setMaxLength(1023)

        self.btnSend = QPushButton(self.centralwidget)
        self.btnSend.setObjectName("btnSend")

        self.sendLayout.addWidget(self.txtSend)
        self.sendLayout.addWidget(self.btnSend)
        self.rightPanel.addLayout(self.sendLayout)

        self.mainLayout.addLayout(self.rightPanel, 2)

        Messenger.setCentralWidget(self.centralwidget)

        # Menú superior
        self.menubar = QMenuBar(Messenger)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 820, 28))
        self.menuArchivo = QMenu(self.menubar)
        self.menuArchivo.setObjectName("menuArchivo")
        self.menuComunidades = QMenu(self.menubar)
        self.menuComunidades.setObjectName("menuComunidades")
        Messenger.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuArchivo.menuAction())
        self.menubar.addAction(self.menuComunidades.menuAction())
        self.menuArchivo.addAction(self.actionConectar)
        self.menuArchivo.addSeparator()
        self.menuArchivo.addAction(self.actionSalir)
        self.menuComunidades.addAction(self.actionMis_Comunidades)
        self.menuComunidades.addAction(self.actionMas_Comunidades)

        self.retranslateUi(Messenger)
        QMetaObject.connectSlotsByName(Messenger)

    def retranslateUi(self, Messenger):
        Messenger.setWindowTitle(
            QCoreApplication.translate("Messenger", "Messenger", None)
        )
        self.actionConectar.setText(
            QCoreApplication.translate("Messenger", "Co&nectar", None)
        )
        self.actionConectar.setShortcut(
            QCoreApplication.translate("Messenger", "Ctrl+C", None)
        )
        self.actionSalir.setText(
            QCoreApplication.translate("Messenger", "&Salir", None)
        )
        self.actionSalir.setShortcut(
            QCoreApplication.translate("Messenger", "Ctrl+X", None)
        )
        self.actionMis_Comunidades.setText(
            QCoreApplication.translate("Messenger", "Mis Comunidades", None)
        )
        self.actionMas_Comunidades.setText(
            QCoreApplication.translate("Messenger", "Mas Comunidades", None)
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
        self.lblIndicadorChat.setText(
            QCoreApplication.translate("Messenger", "Chat actual: Global", None)
        )
        self.txtSend.setPlaceholderText(
            QCoreApplication.translate("Messenger", "Escribe un mensaje en Global...", None)
        )
        self.btnSend.setText(
            QCoreApplication.translate("Messenger", "Enviar", None)
        )
        self.menuArchivo.setTitle(
            QCoreApplication.translate("Messenger", "&Archivo", None)
        )
        self.menuComunidades.setTitle(
            QCoreApplication.translate("Messenger", "Comunidades", None)
        )