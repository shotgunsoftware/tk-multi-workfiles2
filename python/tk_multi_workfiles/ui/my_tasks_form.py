# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'my_tasks_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_MyTasksForm(object):
    def setupUi(self, MyTasksForm):
        MyTasksForm.setObjectName("MyTasksForm")
        MyTasksForm.resize(359, 541)
        self.verticalLayout = QtGui.QVBoxLayout(MyTasksForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(2, 6, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(2, -1, 2, 1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.filter_btn = QtGui.QToolButton(MyTasksForm)
        self.filter_btn.setStyleSheet("")
        self.filter_btn.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.filter_btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.filter_btn.setAutoRaise(False)
        self.filter_btn.setObjectName("filter_btn")
        self.horizontalLayout.addWidget(self.filter_btn)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.new_task_btn = QtGui.QPushButton(MyTasksForm)
        self.new_task_btn.setObjectName("new_task_btn")
        self.horizontalLayout.addWidget(self.new_task_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(1, -1, 1, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.search_ctrl = SearchWidget(MyTasksForm)
        self.search_ctrl.setMinimumSize(QtCore.QSize(0, 20))
        self.search_ctrl.setStyleSheet("#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.search_ctrl.setObjectName("search_ctrl")
        self.horizontalLayout_2.addWidget(self.search_ctrl)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.task_tree = QtGui.QTreeView(MyTasksForm)
        self.task_tree.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.task_tree.setProperty("showDropIndicator", False)
        self.task_tree.setRootIsDecorated(False)
        self.task_tree.setObjectName("task_tree")
        self.task_tree.header().setVisible(False)
        self.verticalLayout.addWidget(self.task_tree)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(MyTasksForm)
        QtCore.QMetaObject.connectSlotsByName(MyTasksForm)

    def retranslateUi(self, MyTasksForm):
        MyTasksForm.setWindowTitle(QtGui.QApplication.translate("MyTasksForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.filter_btn.setText(QtGui.QApplication.translate("MyTasksForm", "Filter", None, QtGui.QApplication.UnicodeUTF8))
        self.new_task_btn.setText(QtGui.QApplication.translate("MyTasksForm", "+ New Task", None, QtGui.QApplication.UnicodeUTF8))

from ..framework_qtwidgets import SearchWidget
