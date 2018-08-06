# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crash_dbg_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_CrashDbgForm(object):
    def setupUi(self, CrashDbgForm):
        CrashDbgForm.setObjectName("CrashDbgForm")
        CrashDbgForm.resize(503, 395)
        self.verticalLayout = QtGui.QVBoxLayout(CrashDbgForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tree_view = QtGui.QTreeView(CrashDbgForm)
        self.tree_view.setObjectName("tree_view")
        self.horizontalLayout.addWidget(self.tree_view)
        self.list_view = QtGui.QListView(CrashDbgForm)
        self.list_view.setObjectName("list_view")
        self.horizontalLayout.addWidget(self.list_view)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(CrashDbgForm)
        QtCore.QMetaObject.connectSlotsByName(CrashDbgForm)

    def retranslateUi(self, CrashDbgForm):
        CrashDbgForm.setWindowTitle(QtGui.QApplication.translate("CrashDbgForm", "Form", None, QtGui.QApplication.UnicodeUTF8))

