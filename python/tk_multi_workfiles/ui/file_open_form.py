# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_open_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_FileOpenForm(object):
    def setupUi(self, FileOpenForm):
        FileOpenForm.setObjectName("FileOpenForm")
        FileOpenForm.resize(639, 519)
        self.verticalLayout = QtGui.QVBoxLayout(FileOpenForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.history_btns = NavigationWidget(FileOpenForm)
        self.history_btns.setMinimumSize(QtCore.QSize(100, 50))
        self.history_btns.setStyleSheet("#history_btns {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.history_btns.setObjectName("history_btns")
        self.horizontalLayout_3.addWidget(self.history_btns)
        self.breadcrumbs = BreadcrumbWidget(FileOpenForm)
        self.breadcrumbs.setStyleSheet("#breadcrumbs {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.breadcrumbs.setObjectName("breadcrumbs")
        self.horizontalLayout_3.addWidget(self.breadcrumbs)
        self.horizontalLayout_3.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.task_browser_tabs = TaskBrowserTabs(FileOpenForm)
        self.task_browser_tabs.setMinimumSize(QtCore.QSize(200, 0))
        self.task_browser_tabs.setObjectName("task_browser_tabs")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.task_browser_tabs.addTab(self.tab, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.task_browser_tabs.addTab(self.tab_2, "")
        self.horizontalLayout_2.addWidget(self.task_browser_tabs)
        self.file_browser_tabs = FileBrowserTabs(FileOpenForm)
        self.file_browser_tabs.setObjectName("file_browser_tabs")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.file_browser_tabs.addTab(self.tab_3, "")
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.file_browser_tabs.addTab(self.tab_4, "")
        self.horizontalLayout_2.addWidget(self.file_browser_tabs)
        self.horizontalLayout_2.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton = QtGui.QPushButton(FileOpenForm)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_2 = QtGui.QPushButton(FileOpenForm)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.pushButton_3 = QtGui.QPushButton(FileOpenForm)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout.addWidget(self.pushButton_3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(FileOpenForm)
        QtCore.QMetaObject.connectSlotsByName(FileOpenForm)

    def retranslateUi(self, FileOpenForm):
        FileOpenForm.setWindowTitle(QtGui.QApplication.translate("FileOpenForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.task_browser_tabs.setTabText(self.task_browser_tabs.indexOf(self.tab), QtGui.QApplication.translate("FileOpenForm", "Tab 1", None, QtGui.QApplication.UnicodeUTF8))
        self.task_browser_tabs.setTabText(self.task_browser_tabs.indexOf(self.tab_2), QtGui.QApplication.translate("FileOpenForm", "Tab 2", None, QtGui.QApplication.UnicodeUTF8))
        self.file_browser_tabs.setTabText(self.file_browser_tabs.indexOf(self.tab_3), QtGui.QApplication.translate("FileOpenForm", "Tab 1", None, QtGui.QApplication.UnicodeUTF8))
        self.file_browser_tabs.setTabText(self.file_browser_tabs.indexOf(self.tab_4), QtGui.QApplication.translate("FileOpenForm", "Tab 2", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("FileOpenForm", "+ New File", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_2.setText(QtGui.QApplication.translate("FileOpenForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_3.setText(QtGui.QApplication.translate("FileOpenForm", "Open", None, QtGui.QApplication.UnicodeUTF8))

from ..navigation_widget import NavigationWidget
from ..breadcrumb_widget import BreadcrumbWidget
from ..task_browser_tabs import TaskBrowserTabs
from ..file_browser_tabs import FileBrowserTabs
