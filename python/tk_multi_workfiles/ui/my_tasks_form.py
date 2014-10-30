# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'my_tasks_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_MyTasksForm(object):
    def setupUi(self, MyTasksForm):
        MyTasksForm.setObjectName("MyTasksForm")
        MyTasksForm.resize(341, 335)
        self.verticalLayout = QtGui.QVBoxLayout(MyTasksForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.toolButton = QtGui.QToolButton(MyTasksForm)
        self.toolButton.setStyleSheet("")
        self.toolButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.toolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toolButton.setAutoRaise(False)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout.addWidget(self.toolButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.new_task_btn = QtGui.QPushButton(MyTasksForm)
        self.new_task_btn.setObjectName("new_task_btn")
        self.horizontalLayout.addWidget(self.new_task_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.search_ctrl = SearchWidget(MyTasksForm)
        self.search_ctrl.setMinimumSize(QtCore.QSize(0, 20))
        self.search_ctrl.setStyleSheet("#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.search_ctrl.setObjectName("search_ctrl")
        self.verticalLayout.addWidget(self.search_ctrl)
        self.task_tree = QtGui.QTreeView(MyTasksForm)
        self.task_tree.setObjectName("task_tree")
        self.verticalLayout.addWidget(self.task_tree)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(MyTasksForm)
        QtCore.QMetaObject.connectSlotsByName(MyTasksForm)

    def retranslateUi(self, MyTasksForm):
        MyTasksForm.setWindowTitle(QtGui.QApplication.translate("MyTasksForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.toolButton.setText(QtGui.QApplication.translate("MyTasksForm", "Filter", None, QtGui.QApplication.UnicodeUTF8))
        self.new_task_btn.setText(QtGui.QApplication.translate("MyTasksForm", "+ New Task", None, QtGui.QApplication.UnicodeUTF8))

from ..search_widget import SearchWidget
