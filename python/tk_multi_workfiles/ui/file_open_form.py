# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'file_open_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from tank.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


from ..framework_qtwidgets import NavigationWidget
from ..framework_qtwidgets import BreadcrumbWidget
from ..browser_form import BrowserForm

from  . import resources_rc

class Ui_FileOpenForm(object):
    def setupUi(self, FileOpenForm):
        if not FileOpenForm.objectName():
            FileOpenForm.setObjectName(u"FileOpenForm")
        FileOpenForm.resize(956, 718)
        self.verticalLayout = QVBoxLayout(FileOpenForm)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(12)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.nav = NavigationWidget(FileOpenForm)
        self.nav.setObjectName(u"nav")
        self.nav.setMinimumSize(QSize(80, 30))
        self.nav.setStyleSheet(u"#history_btns {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.horizontalLayout_3.addWidget(self.nav)

        self.breadcrumbs = BreadcrumbWidget(FileOpenForm)
        self.breadcrumbs.setObjectName(u"breadcrumbs")
        self.breadcrumbs.setStyleSheet(u"#breadcrumbs {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.horizontalLayout_3.addWidget(self.breadcrumbs)

        self.horizontalLayout_3.setStretch(1, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.browser = BrowserForm(FileOpenForm)
        self.browser.setObjectName(u"browser")
        self.browser.setStyleSheet(u"#browser {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.verticalLayout.addWidget(self.browser)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.new_file_btn = QPushButton(FileOpenForm)
        self.new_file_btn.setObjectName(u"new_file_btn")

        self.horizontalLayout.addWidget(self.new_file_btn)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cancel_btn = QPushButton(FileOpenForm)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.horizontalLayout.addWidget(self.cancel_btn)

        self.open_btn = QPushButton(FileOpenForm)
        self.open_btn.setObjectName(u"open_btn")
        self.open_btn.setStyleSheet(u"#open_btn {\n"
"}")

        self.horizontalLayout.addWidget(self.open_btn)

        self.change_ctx_btn = QPushButton(FileOpenForm)
        self.change_ctx_btn.setObjectName(u"change_ctx_btn")

        self.horizontalLayout.addWidget(self.change_ctx_btn)

        self.open_options_btn = QPushButton(FileOpenForm)
        self.open_options_btn.setObjectName(u"open_options_btn")
        self.open_options_btn.setFlat(False)

        self.horizontalLayout.addWidget(self.open_options_btn)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(FileOpenForm)

        QMetaObject.connectSlotsByName(FileOpenForm)
    # setupUi

    def retranslateUi(self, FileOpenForm):
        FileOpenForm.setWindowTitle(QCoreApplication.translate("FileOpenForm", u"Form", None))
        self.new_file_btn.setText(QCoreApplication.translate("FileOpenForm", u"+ New File", None))
        self.cancel_btn.setText(QCoreApplication.translate("FileOpenForm", u"Cancel", None))
        self.open_btn.setText(QCoreApplication.translate("FileOpenForm", u"Open", None))
        self.change_ctx_btn.setText(QCoreApplication.translate("FileOpenForm", u"Change Context", None))
        self.open_options_btn.setText(QCoreApplication.translate("FileOpenForm", u"...", None))
    # retranslateUi
