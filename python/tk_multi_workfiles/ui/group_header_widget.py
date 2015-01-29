# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'group_header_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_GroupHeaderWidget(object):
    def setupUi(self, GroupHeaderWidget):
        GroupHeaderWidget.setObjectName("GroupHeaderWidget")
        GroupHeaderWidget.resize(391, 53)
        self.verticalLayout = QtGui.QVBoxLayout(GroupHeaderWidget)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBox = QtGui.QCheckBox(GroupHeaderWidget)
        self.checkBox.setText("")
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout.addWidget(self.checkBox)
        self.title_label = QtGui.QLabel(GroupHeaderWidget)
        self.title_label.setStyleSheet("#title_label {\n"
"font-size: 16px;\n"
"}")
        self.title_label.setObjectName("title_label")
        self.horizontalLayout.addWidget(self.title_label)
        self.horizontalLayout.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.line = QtGui.QFrame(GroupHeaderWidget)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)

        self.retranslateUi(GroupHeaderWidget)
        QtCore.QMetaObject.connectSlotsByName(GroupHeaderWidget)

    def retranslateUi(self, GroupHeaderWidget):
        GroupHeaderWidget.setWindowTitle(QtGui.QApplication.translate("GroupHeaderWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.title_label.setText(QtGui.QApplication.translate("GroupHeaderWidget", "Layout - Planning", None, QtGui.QApplication.UnicodeUTF8))

