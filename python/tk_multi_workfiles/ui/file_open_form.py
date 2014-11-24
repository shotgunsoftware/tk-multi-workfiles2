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
        FileOpenForm.resize(912, 719)
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
        self.splitter = QtGui.QSplitter(FileOpenForm)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName("splitter")
        self.task_browser_tabs = TaskBrowserTabs(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.task_browser_tabs.sizePolicy().hasHeightForWidth())
        self.task_browser_tabs.setSizePolicy(sizePolicy)
        self.task_browser_tabs.setMinimumSize(QtCore.QSize(300, 0))
        self.task_browser_tabs.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.task_browser_tabs.setObjectName("task_browser_tabs")
        self.my_tasks_form = MyTasksForm()
        self.my_tasks_form.setObjectName("my_tasks_form")
        self.task_browser_tabs.addTab(self.my_tasks_form, "")
        self.file_browser_tabs = FileBrowserTabs(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_browser_tabs.sizePolicy().hasHeightForWidth())
        self.file_browser_tabs.setSizePolicy(sizePolicy)
        self.file_browser_tabs.setObjectName("file_browser_tabs")
        self.verticalLayout.addWidget(self.splitter)
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
        self.open_btn.setObjectName("open_btn")
        self.horizontalLayout.addWidget(self.open_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(FileOpenForm)
        self.file_browser_tabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(FileOpenForm)

    def retranslateUi(self, FileOpenForm):
        FileOpenForm.setWindowTitle(QtGui.QApplication.translate("FileOpenForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.task_browser_tabs.setTabText(self.task_browser_tabs.indexOf(self.my_tasks_form), QtGui.QApplication.translate("FileOpenForm", "My Tasks", None, QtGui.QApplication.UnicodeUTF8))
        self.new_file_btn.setText(QtGui.QApplication.translate("FileOpenForm", "+ New File", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("FileOpenForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.open_btn.setText(QtGui.QApplication.translate("FileOpenForm", "Open", None, QtGui.QApplication.UnicodeUTF8))

from ..my_tasks_form import MyTasksForm
from ..navigation_widget import NavigationWidget
from ..breadcrumb_widget import BreadcrumbWidget
from ..task_browser_tabs import TaskBrowserTabs
from ..file_browser_tabs import FileBrowserTabs
