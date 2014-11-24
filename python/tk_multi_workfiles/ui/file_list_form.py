# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_list_form.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_FileListForm(object):
    def setupUi(self, FileListForm):
        FileListForm.setObjectName("FileListForm")
        FileListForm.resize(566, 479)
        self.verticalLayout = QtGui.QVBoxLayout(FileListForm)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setContentsMargins(2, 8, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.grid_radio_btn = QtGui.QRadioButton(FileListForm)
        self.grid_radio_btn.setChecked(True)
        self.grid_radio_btn.setObjectName("grid_radio_btn")
        self.horizontalLayout.addWidget(self.grid_radio_btn)
        self.details_radio_btn = QtGui.QRadioButton(FileListForm)
        self.details_radio_btn.setObjectName("details_radio_btn")
        self.horizontalLayout.addWidget(self.details_radio_btn)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.checkBox = QtGui.QCheckBox(FileListForm)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_3.addWidget(self.checkBox)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.search_ctrl = SearchWidget(FileListForm)
        self.search_ctrl.setMinimumSize(QtCore.QSize(100, 0))
        self.search_ctrl.setStyleSheet("#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.search_ctrl.setObjectName("search_ctrl")
        self.horizontalLayout_3.addWidget(self.search_ctrl)
        self.horizontalLayout_3.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.view_pages = QtGui.QStackedWidget(FileListForm)
        self.view_pages.setObjectName("view_pages")
        self.list_page = QtGui.QWidget()
        self.list_page.setObjectName("list_page")
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.list_page)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.file_list_view = QtGui.QListView(self.list_page)
        self.file_list_view.setObjectName("file_list_view")
        self.horizontalLayout_5.addWidget(self.file_list_view)
        self.view_pages.addWidget(self.list_page)
        self.details_page = QtGui.QWidget()
        self.details_page.setObjectName("details_page")
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.details_page)
        self.horizontalLayout_4.setContentsMargins(0, 5, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.file_details_view = FileDetailsView(self.details_page)
        self.file_details_view.setObjectName("file_details_view")
        self.horizontalLayout_4.addWidget(self.file_details_view)
        self.view_pages.addWidget(self.details_page)
        self.verticalLayout.addWidget(self.view_pages)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(FileListForm)
        self.view_pages.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(FileListForm)

    def retranslateUi(self, FileListForm):
        FileListForm.setWindowTitle(QtGui.QApplication.translate("FileListForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.grid_radio_btn.setText(QtGui.QApplication.translate("FileListForm", "Grid", None, QtGui.QApplication.UnicodeUTF8))
        self.details_radio_btn.setText(QtGui.QApplication.translate("FileListForm", "Details", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox.setText(QtGui.QApplication.translate("FileListForm", "All Versions", None, QtGui.QApplication.UnicodeUTF8))

from ..file_details_view import FileDetailsView
from ..search_widget import SearchWidget
