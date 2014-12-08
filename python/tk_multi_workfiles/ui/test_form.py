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
        TestForm.resize(609, 436)
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
        self.listView.setObjectName("listView")
        self.horizontalLayout.addWidget(self.listView)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.tab_2)
        self.horizontalLayout_3.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.treeView = QtGui.QTreeView(self.tab_2)
        self.treeView.setObjectName("treeView")
        self.horizontalLayout_3.addWidget(self.treeView)
        self.tabWidget.addTab(self.tab_2, "")
        self.horizontalLayout_2.addWidget(self.tabWidget)

        self.retranslateUi(TestForm)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(TestForm)

    def retranslateUi(self, TestForm):
        TestForm.setWindowTitle(QtGui.QApplication.translate("TestForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("TestForm", "Tab 1", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("TestForm", "Tab 2", None, QtGui.QApplication.UnicodeUTF8))

