# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_item_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_FileItemForm(object):
    def setupUi(self, FileItemForm):
        FileItemForm.setObjectName("FileItemForm")
        FileItemForm.resize(324, 69)
        FileItemForm.setMaximumSize(QtCore.QSize(16777215, 69))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(FileItemForm)
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.background = QtGui.QFrame(FileItemForm)
        self.background.setStyleSheet("#background {\n"
"border-radius: 3px;\n"
"border-style: solid;\n"
"border-width: 1px;\n"
"border-color: rgb(32,32,32);\n"
"}")
        self.background.setFrameShape(QtGui.QFrame.StyledPanel)
        self.background.setFrameShadow(QtGui.QFrame.Raised)
        self.background.setObjectName("background")
        self.horizontalLayout = QtGui.QHBoxLayout(self.background)
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.thumbnail = ThumbnailLabel(self.background)
        self.thumbnail.setMinimumSize(QtCore.QSize(80, 55))
        self.thumbnail.setMaximumSize(QtCore.QSize(80, 55))
        self.thumbnail.setStyleSheet("")
        self.thumbnail.setText("")
        self.thumbnail.setPixmap(QtGui.QPixmap(":/res/thumb_empty.png"))
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.horizontalLayout.addWidget(self.thumbnail)
        self.details = QtGui.QLabel(self.background)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy)
        self.details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.details.setWordWrap(True)
        self.details.setObjectName("details")
        self.horizontalLayout.addWidget(self.details)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.locked_label = QtGui.QLabel(self.background)
        self.locked_label.setMinimumSize(QtCore.QSize(12, 14))
        self.locked_label.setMaximumSize(QtCore.QSize(12, 14))
        self.locked_label.setText("")
        self.locked_label.setPixmap(QtGui.QPixmap(":/res/padlock.png"))
        self.locked_label.setScaledContents(False)
        self.locked_label.setObjectName("locked_label")
        self.verticalLayout.addWidget(self.locked_label)
        self.verticalLayout.setStretch(0, 1)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout_2.addWidget(self.background)

        self.retranslateUi(FileItemForm)
        QtCore.QMetaObject.connectSlotsByName(FileItemForm)

    def retranslateUi(self, FileItemForm):
        FileItemForm.setWindowTitle(QtGui.QApplication.translate("FileItemForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.details.setText(QtGui.QApplication.translate("FileItemForm", "content", None, QtGui.QApplication.UnicodeUTF8))

from .thumbnail_label import ThumbnailLabel
from . import resources_rc
