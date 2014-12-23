# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'task_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_TaskWidget(object):
    def setupUi(self, TaskWidget):
        TaskWidget.setObjectName("TaskWidget")
        TaskWidget.resize(232, 70)
        self.horizontalLayout = QtGui.QHBoxLayout(TaskWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.background = QtGui.QFrame(TaskWidget)
        self.background.setStyleSheet("#background {\n"
"background-color: rgb(0, 174, 237);\n"
"border-bottom-style: solid;\n"
"border-bottom-width: 1px;\n"
"border-bottom-color: rgb(64,64,64);\n"
"}")
        self.background.setFrameShape(QtGui.QFrame.NoFrame)
        self.background.setFrameShadow(QtGui.QFrame.Plain)
        self.background.setLineWidth(0)
        self.background.setObjectName("background")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.thumbnail = QtGui.QLabel(self.background)
        self.thumbnail.setMinimumSize(QtCore.QSize(90, 50))
        self.thumbnail.setMaximumSize(QtCore.QSize(90, 50))
        self.thumbnail.setStyleSheet("#thumbnail {\n"
"background-color: rgb(32,32, 32);\n"
"}")
        self.thumbnail.setText("")
        self.thumbnail.setObjectName("thumbnail")
        self.horizontalLayout_2.addWidget(self.thumbnail)
        self.description_label = QtGui.QLabel(self.background)
        self.description_label.setStyleSheet("#description_label {\n"
"color: white;\n"
"}")
        self.description_label.setObjectName("description_label")
        self.horizontalLayout_2.addWidget(self.description_label)
        self.jump_btn = QtGui.QPushButton(self.background)
        self.jump_btn.setMaximumSize(QtCore.QSize(24, 24))
        self.jump_btn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/tk-multi-workfiles/search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.jump_btn.setIcon(icon)
        self.jump_btn.setFlat(True)
        self.jump_btn.setObjectName("jump_btn")
        self.horizontalLayout_2.addWidget(self.jump_btn)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout.addWidget(self.background)

        self.retranslateUi(TaskWidget)
        QtCore.QMetaObject.connectSlotsByName(TaskWidget)

    def retranslateUi(self, TaskWidget):
        TaskWidget.setWindowTitle(QtGui.QApplication.translate("TaskWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.description_label.setText(QtGui.QApplication.translate("TaskWidget", "task details", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
