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
        TaskWidget.resize(331, 88)
        self.horizontalLayout = QtGui.QHBoxLayout(TaskWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.thumbnail_label = QtGui.QLabel(TaskWidget)
        self.thumbnail_label.setMinimumSize(QtCore.QSize(64, 64))
        self.thumbnail_label.setMaximumSize(QtCore.QSize(64, 64))
        self.thumbnail_label.setObjectName("thumbnail_label")
        self.horizontalLayout.addWidget(self.thumbnail_label)
        self.description_label = QtGui.QLabel(TaskWidget)
        self.description_label.setObjectName("description_label")
        self.horizontalLayout.addWidget(self.description_label)
        self.find_btn = QtGui.QPushButton(TaskWidget)
        self.find_btn.setObjectName("find_btn")
        self.horizontalLayout.addWidget(self.find_btn)
        self.horizontalLayout.setStretch(1, 1)

        self.retranslateUi(TaskWidget)
        QtCore.QMetaObject.connectSlotsByName(TaskWidget)

    def retranslateUi(self, TaskWidget):
        TaskWidget.setWindowTitle(QtGui.QApplication.translate("TaskWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.thumbnail_label.setText(QtGui.QApplication.translate("TaskWidget", "task icon", None, QtGui.QApplication.UnicodeUTF8))
        self.description_label.setText(QtGui.QApplication.translate("TaskWidget", "task details", None, QtGui.QApplication.UnicodeUTF8))
        self.find_btn.setText(QtGui.QApplication.translate("TaskWidget", "O", None, QtGui.QApplication.UnicodeUTF8))

