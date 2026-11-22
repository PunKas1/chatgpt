# -*- coding: utf-8 -*-

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(500, 580)
        Form.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        Form.setStyleSheet("""
            /* Fondo general de la ventana (mismo tono que principal_ui) */
            QWidget#Form {
                background-color: #121214;
                color: #ffffff;
                font-family: "Segoe UI";
            }

            /* Tarjeta central */
            QFrame#card_login {
                background-color: #18181b;
                border: 1px solid #2e2e34;
                border-radius: 14px;
            }

            /* Estilo base para etiquetas */
            QLabel {
                color: #e4e4e7;
                font-family: "Segoe UI";
                font-size: 13px;
                background: transparent;
            }

            /* Título principal */
            QLabel#label_4 {
                color: #ffffff;
                font-family: "Segoe UI";
                font-size: 28px;
                font-weight: bold;
            }

            /* Subtítulo */
            QLabel#label_7 {
                color: #60a5fa;
                font-family: "Segoe UI";
                font-size: 16px;
                font-weight: bold;
            }

            /* Etiquetas de los campos */
            QLabel#label_2, QLabel#label_3, QLabel#label_5, QLabel#label_6 {
                color: #a1a1aa;
                font-family: "Segoe UI";
                font-size: 12px;
                font-weight: bold;
            }

            /* Cajas de texto */
            QLineEdit {
                background-color: #1e1e22;
                color: #ffffff;
                font-family: "Segoe UI";
                font-size: 13px;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 6px 12px;
            }

            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #222227;
            }

            /* Botón principal (Iniciar sesión) */
            QPushButton#bton_login {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton#bton_login:hover {
                background-color: #1d4ed8;
            }

            QPushButton#bton_login:pressed {
                background-color: #1e40af;
            }

            /* Botón secundario (Crear cuenta) */
            QPushButton#bton_crear {
                background-color: #1e1e22;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 10px 16px;
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton#bton_crear:hover {
                background-color: #27272a;
                color: #ffffff;
            }

            QPushButton#bton_crear:pressed {
                background-color: #3f3f46;
            }
        """)

        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(16, 16, 16, 16)

        self.card_login = QFrame(Form)
        self.card_login.setObjectName("card_login")
        self.card_login.setMinimumSize(QSize(440, 520))
        self.card_login.setMaximumSize(QSize(440, 520))
        self.card_login.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_login.setFrameShadow(QFrame.Shadow.Raised)

        # Título y subtítulo
        self.label_4 = QLabel(self.card_login)
        self.label_4.setObjectName("label_4")
        self.label_4.setGeometry(QRect(30, 24, 380, 42))
        font = QFont()
        font.setFamilies(["Segoe UI"])
        font.setBold(True)
        self.label_4.setFont(font)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_7 = QLabel(self.card_login)
        self.label_7.setObjectName("label_7")
        self.label_7.setGeometry(QRect(30, 68, 380, 28))
        self.label_7.setFont(font)
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Usuario
        self.label_2 = QLabel(self.card_login)
        self.label_2.setObjectName("label_2")
        self.label_2.setGeometry(QRect(80, 118, 280, 18))

        self.lineEdit = QLineEdit(self.card_login)
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setGeometry(QRect(80, 140, 280, 38))

        # Contraseña
        self.label_3 = QLabel(self.card_login)
        self.label_3.setObjectName("label_3")
        self.label_3.setGeometry(QRect(80, 190, 280, 18))

        self.lineEdit_2 = QLineEdit(self.card_login)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.lineEdit_2.setGeometry(QRect(80, 212, 280, 38))
        self.lineEdit_2.setEchoMode(QLineEdit.EchoMode.Password)

        # IP del Servidor
        self.label_5 = QLabel(self.card_login)
        self.label_5.setObjectName("label_5")
        self.label_5.setGeometry(QRect(80, 262, 280, 18))

        self.lineEdit_3 = QLineEdit(self.card_login)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.lineEdit_3.setGeometry(QRect(80, 284, 280, 38))

        # Puerto
        self.label_6 = QLabel(self.card_login)
        self.label_6.setObjectName("label_6")
        self.label_6.setGeometry(QRect(80, 334, 280, 18))

        self.lineEdit_4 = QLineEdit(self.card_login)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.lineEdit_4.setGeometry(QRect(80, 356, 280, 38))

        # Botones alineados al ancho de los campos (280 px en total)
        self.bton_login = QPushButton(self.card_login)
        self.bton_login.setObjectName("bton_login")
        self.bton_login.setGeometry(QRect(80, 424, 134, 42))

        self.bton_crear = QPushButton(self.card_login)
        self.bton_crear.setObjectName("bton_crear")
        self.bton_crear.setGeometry(QRect(226, 424, 134, 42))

        self.gridLayout.addWidget(self.card_login, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(
            QCoreApplication.translate("Form", "Messenger - Inicio de Sesión", None)
        )
        self.lineEdit.setPlaceholderText(
            QCoreApplication.translate("Form", "Nombre de usuario", None)
        )
        self.lineEdit_2.setPlaceholderText(
            QCoreApplication.translate("Form", "Contraseña", None)
        )
        self.bton_login.setText(
            QCoreApplication.translate("Form", "Iniciar sesión", None)
        )
        self.bton_crear.setText(
            QCoreApplication.translate("Form", "Crear cuenta", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("Form", "Usuario", None)
        )
        self.label_3.setText(
            QCoreApplication.translate("Form", "Contraseña", None)
        )
        self.label_4.setText(
            QCoreApplication.translate("Form", "Messenger", None)
        )
        self.label_5.setText(
            QCoreApplication.translate("Form", "IP del Servidor", None)
        )
        self.lineEdit_3.setPlaceholderText(
            QCoreApplication.translate("Form", "Ej. 127.0.0.1", None)
        )
        self.label_6.setText(
            QCoreApplication.translate("Form", "Puerto", None)
        )
        self.lineEdit_4.setPlaceholderText(
            QCoreApplication.translate("Form", "Ej. 3061", None)
        )
        self.label_7.setText(
            QCoreApplication.translate("Form", "Inicio de Sesión", None)
        )


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    Form = QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())