# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'entity_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_entity_frame(object):
    def setupUi(self, entity_frame):
        entity_frame.setObjectName("entity_frame")
        entity_frame.resize(184, 39)
        entity_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        entity_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.horizontalLayout = QtGui.QHBoxLayout(entity_frame)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.icon_label = QtGui.QLabel(entity_frame)
        self.icon_label.setMaximumSize(QtCore.QSize(20, 20))
        self.icon_label.setText("")
        self.icon_label.setObjectName("icon_label")
        self.horizontalLayout.addWidget(self.icon_label)
        self.title_label = QtGui.QLabel(entity_frame)
        self.title_label.setText("")
        self.title_label.setObjectName("title_label")
        self.horizontalLayout.addWidget(self.title_label)
        self.detail_label = QtGui.QLabel(entity_frame)
        self.detail_label.setText("")
        self.detail_label.setObjectName("detail_label")
        self.horizontalLayout.addWidget(self.detail_label)

        self.retranslateUi(entity_frame)
        QtCore.QMetaObject.connectSlotsByName(entity_frame)

    def retranslateUi(self, entity_frame):
        entity_frame.setWindowTitle(QtGui.QApplication.translate("entity_frame", "Frame", None, QtGui.QApplication.UnicodeUTF8))

