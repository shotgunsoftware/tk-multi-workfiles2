# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_open_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_FileOpenForm(object):
    def setupUi(self, FileOpenForm):
        FileOpenForm.setObjectName("FileOpenForm")
        FileOpenForm.resize(956, 718)
        self.verticalLayout = QtGui.QVBoxLayout(FileOpenForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.nav = NavigationWidget(FileOpenForm)
        self.nav.setMinimumSize(QtCore.QSize(80, 30))
        self.nav.setStyleSheet("#history_btns {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.nav.setObjectName("nav")
        self.horizontalLayout_3.addWidget(self.nav)
        self.breadcrumbs = BreadcrumbWidget(FileOpenForm)
        self.breadcrumbs.setStyleSheet("#breadcrumbs {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.breadcrumbs.setObjectName("breadcrumbs")
        self.horizontalLayout_3.addWidget(self.breadcrumbs)
        self.horizontalLayout_3.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.browser = BrowserForm(FileOpenForm)
        self.browser.setStyleSheet("#browser {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.browser.setObjectName("browser")
        self.verticalLayout.addWidget(self.browser)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.new_file_btn = QtGui.QPushButton(FileOpenForm)
        self.new_file_btn.setObjectName("new_file_btn")
        self.horizontalLayout.addWidget(self.new_file_btn)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cancel_btn = QtGui.QPushButton(FileOpenForm)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout.addWidget(self.cancel_btn)
        self.open_btn = QtGui.QPushButton(FileOpenForm)
        self.open_btn.setStyleSheet("#open_btn {\n"
"}")
        self.open_btn.setObjectName("open_btn")
        self.horizontalLayout.addWidget(self.open_btn)
        self.open_options_btn = QtGui.QPushButton(FileOpenForm)
        self.open_options_btn.setFlat(False)
        self.open_options_btn.setObjectName("open_options_btn")
        self.horizontalLayout.addWidget(self.open_options_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(FileOpenForm)
        QtCore.QMetaObject.connectSlotsByName(FileOpenForm)

    def retranslateUi(self, FileOpenForm):
        FileOpenForm.setWindowTitle(QtGui.QApplication.translate("FileOpenForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.new_file_btn.setText(QtGui.QApplication.translate("FileOpenForm", "+ New File", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("FileOpenForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.open_btn.setText(QtGui.QApplication.translate("FileOpenForm", "Open", None, QtGui.QApplication.UnicodeUTF8))
        self.open_options_btn.setText(QtGui.QApplication.translate("FileOpenForm", "...", None, QtGui.QApplication.UnicodeUTF8))

from ..framework_qtwidgets import NavigationWidget, BreadcrumbWidget
from ..browser_form import BrowserForm
from . import resources_rc
