# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'select_work_area_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_SelectWorkAreaForm(object):
    def setupUi(self, SelectWorkAreaForm):
        SelectWorkAreaForm.setObjectName("SelectWorkAreaForm")
        SelectWorkAreaForm.resize(1012, 837)
        self.verticalLayout = QtGui.QVBoxLayout(SelectWorkAreaForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mine_only_cb = QtGui.QCheckBox(SelectWorkAreaForm)
        self.mine_only_cb.setChecked(True)
        self.mine_only_cb.setObjectName("mine_only_cb")
        self.horizontalLayout_2.addWidget(self.mine_only_cb)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.entity_browser = EntityBrowserWidget(SelectWorkAreaForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entity_browser.sizePolicy().hasHeightForWidth())
        self.entity_browser.setSizePolicy(sizePolicy)
        self.entity_browser.setObjectName("entity_browser")
        self.gridLayout.addWidget(self.entity_browser, 0, 0, 1, 1)
        self.task_browser = TaskBrowserWidget(SelectWorkAreaForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.task_browser.sizePolicy().hasHeightForWidth())
        self.task_browser.setSizePolicy(sizePolicy)
        self.task_browser.setObjectName("task_browser")
        self.gridLayout.addWidget(self.task_browser, 0, 1, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.new_task_btn = QtGui.QPushButton(SelectWorkAreaForm)
        self.new_task_btn.setObjectName("new_task_btn")
        self.horizontalLayout.addWidget(self.new_task_btn)
        spacerItem1 = QtGui.QSpacerItem(0, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.cancel_btn = QtGui.QPushButton(SelectWorkAreaForm)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout.addWidget(self.cancel_btn)
        self.select_new_btn = QtGui.QPushButton(SelectWorkAreaForm)
        self.select_new_btn.setObjectName("select_new_btn")
        self.horizontalLayout.addWidget(self.select_new_btn)
        self.select_btn = QtGui.QPushButton(SelectWorkAreaForm)
        self.select_btn.setAutoDefault(False)
        self.select_btn.setDefault(True)
        self.select_btn.setObjectName("select_btn")
        self.horizontalLayout.addWidget(self.select_btn)
        self.horizontalLayout.setStretch(1, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(SelectWorkAreaForm)
        QtCore.QMetaObject.connectSlotsByName(SelectWorkAreaForm)

    def retranslateUi(self, SelectWorkAreaForm):
        SelectWorkAreaForm.setWindowTitle(QtGui.QApplication.translate("SelectWorkAreaForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.mine_only_cb.setText(QtGui.QApplication.translate("SelectWorkAreaForm", "Only Show My Tasks", None, QtGui.QApplication.UnicodeUTF8))
        self.new_task_btn.setText(QtGui.QApplication.translate("SelectWorkAreaForm", "New Task...", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("SelectWorkAreaForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.select_new_btn.setText(QtGui.QApplication.translate("SelectWorkAreaForm", "Start New Scene", None, QtGui.QApplication.UnicodeUTF8))
        self.select_btn.setText(QtGui.QApplication.translate("SelectWorkAreaForm", "Change Work Area", None, QtGui.QApplication.UnicodeUTF8))

from ..entity_browser import EntityBrowserWidget
from ..task_browser import TaskBrowserWidget
