# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'browser_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_BrowserForm(object):
    def setupUi(self, BrowserForm):
        BrowserForm.setObjectName("BrowserForm")
        BrowserForm.resize(982, 616)
        self.horizontalLayout = QtGui.QHBoxLayout(BrowserForm)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtGui.QSplitter(BrowserForm)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.task_browser_tabs = QtGui.QTabWidget(self.splitter)
        self.task_browser_tabs.setMinimumSize(QtCore.QSize(200, 0))
        self.task_browser_tabs.setObjectName("task_browser_tabs")
        self.file_browser_tabs = QtGui.QTabWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_browser_tabs.sizePolicy().hasHeightForWidth())
        self.file_browser_tabs.setSizePolicy(sizePolicy)
        self.file_browser_tabs.setObjectName("file_browser_tabs")
        self.horizontalLayout.addWidget(self.splitter)

        self.retranslateUi(BrowserForm)
        self.file_browser_tabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(BrowserForm)

    def retranslateUi(self, BrowserForm):
        BrowserForm.setWindowTitle(QtGui.QApplication.translate("BrowserForm", "Form", None, QtGui.QApplication.UnicodeUTF8))

