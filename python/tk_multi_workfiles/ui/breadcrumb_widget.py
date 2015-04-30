# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'breadcrumb_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_BreadcrumbWidget(object):
    def setupUi(self, BreadcrumbWidget):
        BreadcrumbWidget.setObjectName("BreadcrumbWidget")
        BreadcrumbWidget.resize(396, 26)
        self.horizontalLayout = QtGui.QHBoxLayout(BreadcrumbWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.path_label = QtGui.QLabel(BreadcrumbWidget)
        self.path_label.setObjectName("path_label")
        self.horizontalLayout.addWidget(self.path_label)
        spacerItem = QtGui.QSpacerItem(81, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.retranslateUi(BreadcrumbWidget)
        QtCore.QMetaObject.connectSlotsByName(BreadcrumbWidget)

    def retranslateUi(self, BreadcrumbWidget):
        BreadcrumbWidget.setWindowTitle(QtGui.QApplication.translate("BreadcrumbWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.path_label.setText(QtGui.QApplication.translate("BreadcrumbWidget", "I <span style=\'color:#2C93E2\'>&#9656;</span> Am <span style=\'color:#2C93E2\'>&#9656;</span> Groot", None, QtGui.QApplication.UnicodeUTF8))

