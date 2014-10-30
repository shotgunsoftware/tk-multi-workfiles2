# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'entity_tree_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_EntityTreeForm(object):
    def setupUi(self, EntityTreeForm):
        EntityTreeForm.setObjectName("EntityTreeForm")
        EntityTreeForm.resize(353, 334)
        self.verticalLayout = QtGui.QVBoxLayout(EntityTreeForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.my_tasks_cb = QtGui.QCheckBox(EntityTreeForm)
        self.my_tasks_cb.setObjectName("my_tasks_cb")
        self.horizontalLayout.addWidget(self.my_tasks_cb)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.new_task_btn = QtGui.QPushButton(EntityTreeForm)
        self.new_task_btn.setObjectName("new_task_btn")
        self.horizontalLayout.addWidget(self.new_task_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.search_ctrl = SearchWidget(EntityTreeForm)
        self.search_ctrl.setMinimumSize(QtCore.QSize(0, 20))
        self.search_ctrl.setStyleSheet("#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.search_ctrl.setObjectName("search_ctrl")
        self.verticalLayout.addWidget(self.search_ctrl)
        self.entity_tree = QtGui.QTreeView(EntityTreeForm)
        self.entity_tree.setObjectName("entity_tree")
        self.verticalLayout.addWidget(self.entity_tree)
        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(EntityTreeForm)
        QtCore.QMetaObject.connectSlotsByName(EntityTreeForm)

    def retranslateUi(self, EntityTreeForm):
        EntityTreeForm.setWindowTitle(QtGui.QApplication.translate("EntityTreeForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.my_tasks_cb.setText(QtGui.QApplication.translate("EntityTreeForm", "My Tasks Only", None, QtGui.QApplication.UnicodeUTF8))
        self.new_task_btn.setText(QtGui.QApplication.translate("EntityTreeForm", "+ New Task", None, QtGui.QApplication.UnicodeUTF8))

from ..search_widget import SearchWidget
