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
        self.details_frame = QtGui.QFrame(self.background)
        self.details_frame.setObjectName("details_frame")
        self.verticalLayout = QtGui.QVBoxLayout(self.details_frame)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = ElidedLabel(self.details_frame)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.subtitle = QtGui.QLabel(self.details_frame)
        self.subtitle.setObjectName("subtitle")
        self.verticalLayout.addWidget(self.subtitle)
        spacerItem1 = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout_2.addWidget(self.details_frame)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout.addWidget(self.background)

        self.retranslateUi(FileWidget)
        QtCore.QMetaObject.connectSlotsByName(FileWidget)

    def retranslateUi(self, FileWidget):
        FileWidget.setWindowTitle(QtGui.QApplication.translate("FileWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileWidget", "<b>Title</b>", None, QtGui.QApplication.UnicodeUTF8))
        self.subtitle.setText(QtGui.QApplication.translate("FileWidget", "Subtitle", None, QtGui.QApplication.UnicodeUTF8))

from ..framework_qtwidgets import ElidedLabel
from . import resources_rc
