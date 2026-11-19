# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'iniciarSesion.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(478, 578)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.card_login = QFrame(Form)
        self.card_login.setObjectName(u"card_login")
        self.card_login.setMinimumSize(QSize(460, 560))
        self.card_login.setMaximumSize(QSize(460, 560))
        self.card_login.setStyleSheet(u"/* Fondo general de la ventana */\n"
"#Form {\n"
"    background-color: rgb(2, 34, 5);\n"
"}\n"
"\n"
"/* Tarjeta central con bordes redondos y borde sutil */\n"
"#card_login {\n"
"    background-color: rgb(39, 39, 39);\n"
"    border: 1px solid #27272a;\n"
"    border-radius: 16px;\n"
"    padding: 24px;\n"
"}\n"
"\n"
"/* Estilo base para cualquier QLabel nuevo (evita texto negro invisible) */\n"
"QLabel {\n"
"    color: #ffffff;\n"
"    font-family: \"Segoe UI\";\n"
"    font-size: 14px;\n"
"}\n"
"\n"
"/* T\u00edtulo principal */\n"
"#label_4 {\n"
"    color: #ffffff;\n"
"    font-family: \"Comic Sans MS\";\n"
"    font-size: 35px; \n"
"    font-weight: bold;\n"
"}\n"
"\n"
"#label_7{\n"
"	color: rgb(13, 104, 223);\n"
"    font-family: \"Comic Sans MS\";\n"
"    font-size: 25px; \n"
"    font-weight: bold;\n"
"}\n"
"\n"
"/* Etiquetas de campos (con el guion bajo que asigna Qt Designer) */\n"
"#label_2, #label_3, #label_5, #label_6{\n"
"    color: #ffffff;\n"
"    font-family: \"Comic Sans MS\";\n"
"    font-si"
                        "ze: 16px;\n"
"    font-weight: normal;\n"
"}\n"
"QLineEdit {\n"
"    background-color: rgb(29, 29, 29);\n"
"    color: rgb(255, 255, 255);\n"
"    font-family: \"Comic Sans MS\";\n"
"    font-size: 10px;\n"
"    border: 1px solid rgb(60, 60, 60);\n"
"    border-radius: 6px;\n"
"    padding: 4px 8px;\n"
"}\n"
"\n"
"\n"
"#bton_login {\n"
"    background-color: #ffffff;\n"
"    color: #09090b;\n"
"    border: none;\n"
"    border-radius: 8px;\n"
"    padding: 10px 18px;\n"
"    font-family: \"Segoe UI\";\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"#bton_login:hover {\n"
"    background-color: #e4e4e7;\n"
"}\n"
"\n"
"/* Bot\u00f3n secundario oscuro con borde */\n"
"#bton_crear {\n"
"    background-color: #1e1e22;\n"
"    color: #ffffff;\n"
"    border: 1px solid #3f3f46;\n"
"    border-radius: 8px;\n"
"    padding: 10px 18px;\n"
"    font-family: \"Segoe UI\";\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"#bton_crear:hover {\n"
"    background-color: #27272a;\n"
"}")
        self.card_login.setFrameShape(QFrame.Shape.StyledPanel)
        self.card_login.setFrameShadow(QFrame.Shadow.Raised)
        self.lineEdit = QLineEdit(self.card_login)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(130, 170, 201, 41))
        self.lineEdit_2 = QLineEdit(self.card_login)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setGeometry(QRect(130, 240, 201, 41))
        self.bton_login = QPushButton(self.card_login)
        self.bton_login.setObjectName(u"bton_login")
        self.bton_login.setGeometry(QRect(100, 460, 121, 41))
        self.bton_crear = QPushButton(self.card_login)
        self.bton_crear.setObjectName(u"bton_crear")
        self.bton_crear.setGeometry(QRect(240, 460, 121, 41))
        self.label_2 = QLabel(self.card_login)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(130, 150, 101, 16))
        self.label_3 = QLabel(self.card_login)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(130, 220, 111, 16))
        self.label_4 = QLabel(self.card_login)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(60, 20, 341, 61))
        font = QFont()
        font.setFamilies([u"Comic Sans MS"])
        font.setBold(True)
        self.label_4.setFont(font)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_5 = QLabel(self.card_login)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(130, 290, 121, 16))
        self.lineEdit_3 = QLineEdit(self.card_login)
        self.lineEdit_3.setObjectName(u"lineEdit_3")
        self.lineEdit_3.setGeometry(QRect(130, 310, 201, 41))
        self.label_6 = QLabel(self.card_login)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(130, 360, 111, 16))
        self.lineEdit_4 = QLineEdit(self.card_login)
        self.lineEdit_4.setObjectName(u"lineEdit_4")
        self.lineEdit_4.setGeometry(QRect(130, 380, 201, 41))
        self.label_7 = QLabel(self.card_login)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(60, 70, 341, 61))
        self.label_7.setFont(font)
        self.label_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.card_login, 0, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.lineEdit.setText("")
        self.lineEdit.setPlaceholderText(QCoreApplication.translate("Form", u"EjemUser", None))
        self.lineEdit_2.setText("")
        self.lineEdit_2.setPlaceholderText(QCoreApplication.translate("Form", u"Password", None))
        self.bton_login.setText(QCoreApplication.translate("Form", u"Iniciar sesi\u00f3n", None))
        self.bton_crear.setText(QCoreApplication.translate("Form", u"Crear cuenta", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Usuario:", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Contrase\u00f1a:", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Chat de Gpt", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"IP del Servidor:", None))
        self.lineEdit_3.setText("")
        self.lineEdit_3.setPlaceholderText(QCoreApplication.translate("Form", u"0.000.000.0", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"Puerto:", None))
        self.lineEdit_4.setText("")
        self.lineEdit_4.setPlaceholderText(QCoreApplication.translate("Form", u"####", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"Inicio de Sesi\u00f3n", None))
    # retranslateUi

