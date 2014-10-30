# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'breadcrumb_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_BreadcrumbWidget(object):
    def setupUi(self, BreadcrumbWidget):
        BreadcrumbWidget.setObjectName("BreadcrumbWidget")
        BreadcrumbWidget.resize(200, 23)
        self.horizontalLayout = QtGui.QHBoxLayout(BreadcrumbWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(BreadcrumbWidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.label_4 = QtGui.QLabel(BreadcrumbWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.label_2 = QtGui.QLabel(BreadcrumbWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.label_5 = QtGui.QLabel(BreadcrumbWidget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout.addWidget(self.label_5)
        self.label_3 = QtGui.QLabel(BreadcrumbWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        spacerItem = QtGui.QSpacerItem(81, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.retranslateUi(BreadcrumbWidget)
        QtCore.QMetaObject.connectSlotsByName(BreadcrumbWidget)

    def retranslateUi(self, BreadcrumbWidget):
        BreadcrumbWidget.setWindowTitle(QtGui.QApplication.translate("BreadcrumbWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("BreadcrumbWidget", "I", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("BreadcrumbWidget", "<span style=\'color:#2C93E2\'>&#9656;</span>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("BreadcrumbWidget", "Am", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("BreadcrumbWidget", "<span style=\'color:#2C93E2\'>&#9656;</span>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("BreadcrumbWidget", "Groot", None, QtGui.QApplication.UnicodeUTF8))

