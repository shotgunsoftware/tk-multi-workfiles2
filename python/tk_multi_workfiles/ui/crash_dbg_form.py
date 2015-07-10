# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crash_dbg_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_CrashDbgForm(object):
    def setupUi(self, CrashDbgForm):
        CrashDbgForm.setObjectName("CrashDbgForm")
        CrashDbgForm.resize(503, 395)
        self.verticalLayout = QtGui.QVBoxLayout(CrashDbgForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tree_view = QtGui.QTreeView(CrashDbgForm)
        self.tree_view.setObjectName("tree_view")
        self.verticalLayout.addWidget(self.tree_view)

        self.retranslateUi(CrashDbgForm)
        QtCore.QMetaObject.connectSlotsByName(CrashDbgForm)

    def retranslateUi(self, CrashDbgForm):
        CrashDbgForm.setWindowTitle(QtGui.QApplication.translate("CrashDbgForm", "Form", None, QtGui.QApplication.UnicodeUTF8))

