# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_TestForm(object):
    def setupUi(self, TestForm):
        TestForm.setObjectName("TestForm")
        TestForm.resize(726, 497)
        self.horizontalLayout_2 = QtGui.QHBoxLayout(TestForm)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tabWidget = QtGui.QTabWidget(TestForm)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.horizontalLayout = QtGui.QHBoxLayout(self.tab)
        self.horizontalLayout.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listView = QtGui.QListView(self.tab)
        self.listView.setFlow(QtGui.QListView.LeftToRight)
        self.listView.setResizeMode(QtGui.QListView.Adjust)
        self.listView.setViewMode(QtGui.QListView.IconMode)
        self.listView.setUniformItemSizes(False)
        self.listView.setObjectName("listView")
        self.horizontalLayout.addWidget(self.listView)
        self.tabWidget.addTab(self.tab, "")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.tab_3)
        self.horizontalLayout_4.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.treeView = QtGui.QTreeView(self.tab_3)
        self.treeView.setObjectName("treeView")
        self.horizontalLayout_4.addWidget(self.treeView)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.tab_2)
        self.horizontalLayout_3.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.customView = GroupedListView(self.tab_2)
        self.customView.setStyleSheet("")
        self.customView.setObjectName("customView")
        self.horizontalLayout_3.addWidget(self.customView)
        self.tabWidget.addTab(self.tab_2, "")
        self.horizontalLayout_2.addWidget(self.tabWidget)

        self.retranslateUi(TestForm)
        self.tabWidget.setCurrentIndex(2)
        QtCore.QMetaObject.connectSlotsByName(TestForm)

    def retranslateUi(self, TestForm):
        TestForm.setWindowTitle(QtGui.QApplication.translate("TestForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("TestForm", "List", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("TestForm", "Tree", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("TestForm", "Custom", None, QtGui.QApplication.UnicodeUTF8))

from ..grouped_list_view import GroupedListView
