# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'browser_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_BrowserForm(object):
    def setupUi(self, BrowserForm):
        BrowserForm.setObjectName("BrowserForm")
        BrowserForm.resize(984, 751)
        self.horizontalLayout = QtGui.QHBoxLayout(BrowserForm)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtGui.QSplitter(BrowserForm)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.vertical_splitter = QtGui.QSplitter(self.splitter)
        self.vertical_splitter.setOrientation(QtCore.Qt.Vertical)
        self.vertical_splitter.setObjectName("vertical_splitter")
        self.task_browser_tabs = QtGui.QTabWidget(self.vertical_splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.task_browser_tabs.sizePolicy().hasHeightForWidth())
        self.task_browser_tabs.setSizePolicy(sizePolicy)
        self.task_browser_tabs.setMinimumSize(QtCore.QSize(200, 0))
        self.task_browser_tabs.setObjectName("task_browser_tabs")
        self.step_filters_frame = QtGui.QFrame(self.vertical_splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.step_filters_frame.sizePolicy().hasHeightForWidth())
        self.step_filters_frame.setSizePolicy(sizePolicy)
        self.step_filters_frame.setMinimumSize(QtCore.QSize(0, 0))
        self.step_filters_frame.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.step_filters_frame.setObjectName("step_filters_frame")
        self.verticalLayout = QtGui.QVBoxLayout(self.step_filters_frame)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.step_filter_label = QtGui.QLabel(self.step_filters_frame)
        self.step_filter_label.setAlignment(QtCore.Qt.AlignCenter)
        self.step_filter_label.setObjectName("step_filter_label")
        self.verticalLayout.addWidget(self.step_filter_label)
        self.step_filter_list_widget = QtGui.QListWidget(self.step_filters_frame)
        self.step_filter_list_widget.setObjectName("step_filter_list_widget")
        self.verticalLayout.addWidget(self.step_filter_list_widget)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.select_all_step_button = QtGui.QPushButton(self.step_filters_frame)
        self.select_all_step_button.setFlat(False)
        self.select_all_step_button.setObjectName("select_all_step_button")
        self.horizontalLayout_2.addWidget(self.select_all_step_button)
        self.select_none_step_button = QtGui.QPushButton(self.step_filters_frame)
        self.select_none_step_button.setFlat(False)
        self.select_none_step_button.setObjectName("select_none_step_button")
        self.horizontalLayout_2.addWidget(self.select_none_step_button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout.setStretch(1, 1)
        self.file_browser_tabs = QtGui.QTabWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.file_browser_tabs.sizePolicy().hasHeightForWidth())
        self.file_browser_tabs.setSizePolicy(sizePolicy)
        self.file_browser_tabs.setObjectName("file_browser_tabs")
        self.horizontalLayout.addWidget(self.splitter)

        self.retranslateUi(BrowserForm)
        self.file_browser_tabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(BrowserForm)

    def retranslateUi(self, BrowserForm):
        BrowserForm.setWindowTitle(QtGui.QApplication.translate("BrowserForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.step_filter_label.setText(QtGui.QApplication.translate("BrowserForm", "Filter by Pipeline Step", None, QtGui.QApplication.UnicodeUTF8))
        self.select_all_step_button.setText(QtGui.QApplication.translate("BrowserForm", "Select All", None, QtGui.QApplication.UnicodeUTF8))
        self.select_none_step_button.setText(QtGui.QApplication.translate("BrowserForm", "Select None", None, QtGui.QApplication.UnicodeUTF8))

