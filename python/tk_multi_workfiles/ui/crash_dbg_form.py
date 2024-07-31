# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'crash_dbg_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from sgtk.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from sgtk.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


class Ui_CrashDbgForm(object):
    def setupUi(self, CrashDbgForm):
        if not CrashDbgForm.objectName():
            CrashDbgForm.setObjectName(u"CrashDbgForm")
        CrashDbgForm.resize(503, 395)
        self.verticalLayout = QVBoxLayout(CrashDbgForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tree_view = QTreeView(CrashDbgForm)
        self.tree_view.setObjectName(u"tree_view")

        self.horizontalLayout.addWidget(self.tree_view)

        self.list_view = QListView(CrashDbgForm)
        self.list_view.setObjectName(u"list_view")

        self.horizontalLayout.addWidget(self.list_view)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(CrashDbgForm)

        QMetaObject.connectSlotsByName(CrashDbgForm)
    # setupUi

    def retranslateUi(self, CrashDbgForm):
        CrashDbgForm.setWindowTitle(QCoreApplication.translate("CrashDbgForm", u"Form", None))
    # retranslateUi
