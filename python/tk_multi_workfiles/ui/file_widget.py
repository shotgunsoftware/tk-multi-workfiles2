# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_FileWidget(object):
    def setupUi(self, FileWidget):
        FileWidget.setObjectName("FileWidget")
        FileWidget.resize(291, 76)
        FileWidget.setStyleSheet("")
        self.horizontalLayout = QtGui.QHBoxLayout(FileWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.background = QtGui.QFrame(FileWidget)
        self.background.setStyleSheet("#background {\n"
"border-style: solid;\n"
"border-width: 2px;\n"
"border-radius: 2px;\n"
"}\n"
"\n"
"#background[selected=false] {\n"
"    background-color: rgb(0,0,0,0);\n"
"    border-color: rgb(0,0,0,0);\n"
"}\n"
"\n"
"#background[selected=true] {\n"
"/*\n"
"    background-color: rgb(135, 166, 185, 50);\n"
"    border-color: rgb(135, 166, 185);\n"
"*/\n"
"    background-color: rgb(0, 178, 236, 30);\n"
"    border-color: rgb(0, 178, 236);\n"
"}")
        self.background.setFrameShape(QtGui.QFrame.StyledPanel)
        self.background.setFrameShadow(QtGui.QFrame.Plain)
        self.background.setLineWidth(2)
        self.background.setProperty("selected", True)
        self.background.setObjectName("background")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.thumbnail = QtGui.QLabel(self.background)
        self.thumbnail.setMinimumSize(QtCore.QSize(96, 64))
        self.thumbnail.setMaximumSize(QtCore.QSize(96, 64))
        self.thumbnail.setStyleSheet("")
        self.thumbnail.setText("")
        self.thumbnail.setTextFormat(QtCore.Qt.AutoText)
        self.thumbnail.setPixmap(QtGui.QPixmap(":/tk-multi-workfiles2/thumb_empty.png"))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.horizontalLayout_2.addWidget(self.thumbnail)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(self.background)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem1 = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(2, 1)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout.addWidget(self.background)

        self.retranslateUi(FileWidget)
        QtCore.QMetaObject.connectSlotsByName(FileWidget)

    def retranslateUi(self, FileWidget):
        FileWidget.setWindowTitle(QtGui.QApplication.translate("FileWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileWidget", "<b>Title</b>", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
