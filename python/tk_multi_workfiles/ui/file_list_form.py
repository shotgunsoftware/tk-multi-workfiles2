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
        FileListForm.resize(667, 631)
        self.verticalLayout = QtGui.QVBoxLayout(FileListForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(2, 6, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(1, -1, 1, -1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.grid_radio_btn = QtGui.QRadioButton(FileListForm)
        self.grid_radio_btn.setMinimumSize(QtCore.QSize(0, 0))
        self.grid_radio_btn.setMaximumSize(QtCore.QSize(26, 16777215))
        self.grid_radio_btn.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.grid_radio_btn.setStyleSheet("#grid_radio_btn::indicator {\n"
"width: 26;\n"
"height: 24;\n"
"}\n"
"\n"
"#grid_radio_btn::indicator::unchecked {\n"
"    image: url(:/tk-multi-workfiles/grid_view_unchecked.png);\n"
"}\n"
"\n"
"#grid_radio_btn::indicator::unchecked::hover {\n"
"    image: url(:/tk-multi-workfiles/grid_view_unchecked_hover.png);\n"
"}\n"
"\n"
"#grid_radio_btn::indicator::checked {\n"
"    image: url(:/tk-multi-workfiles/grid_view_checked.png);\n"
"}\n"
"\n"
"/*#grid_radio_btn::indicator::checked::hover {\n"
"    image: url(:/tk-multi-workfiles/grid_view_checked_hover.png);\n"
"}*/")
        self.grid_radio_btn.setText("")
        self.grid_radio_btn.setIconSize(QtCore.QSize(20, 20))
        self.grid_radio_btn.setChecked(True)
        self.grid_radio_btn.setObjectName("grid_radio_btn")
        self.horizontalLayout.addWidget(self.grid_radio_btn)
        self.details_radio_btn = QtGui.QRadioButton(FileListForm)
        self.details_radio_btn.setEnabled(True)
        self.details_radio_btn.setMaximumSize(QtCore.QSize(26, 16777215))
        self.details_radio_btn.setStyleSheet("#details_radio_btn::indicator {\n"
"width: 26;\n"
"height: 24;\n"
"}\n"
"\n"
"#details_radio_btn::indicator::unchecked {\n"
"    image: url(:/tk-multi-workfiles/details_view_unchecked.png);\n"
"}\n"
"\n"
"#details_radio_btn::indicator::unchecked::hover {\n"
"    image: url(:/tk-multi-workfiles/details_view_unchecked_hover.png);\n"
"}\n"
"\n"
"#details_radio_btn::indicator::checked {\n"
"    image: url(:/tk-multi-workfiles/details_view_checked.png);\n"
"}\n"
"\n"
"/*#details_radio_btn::indicator::checked::hover {\n"
"    image: url(:/tk-multi-workfiles/details_view_checked_hover.png);\n"
"}*/")
        self.details_radio_btn.setText("")
        self.details_radio_btn.setIconSize(QtCore.QSize(20, 20))
        self.details_radio_btn.setObjectName("details_radio_btn")
        self.horizontalLayout.addWidget(self.details_radio_btn)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.all_versions_cb = QtGui.QCheckBox(FileListForm)
        self.all_versions_cb.setObjectName("all_versions_cb")
        self.horizontalLayout_3.addWidget(self.all_versions_cb)
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
        self.file_list_view = GroupedListView(self.list_page)
        self.file_list_view.setStyleSheet("")
        self.file_list_view.setObjectName("file_list_view")
        self.horizontalLayout_5.addWidget(self.file_list_view)
        self.view_pages.addWidget(self.list_page)
        self.details_page = QtGui.QWidget()
        self.details_page.setObjectName("details_page")
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.details_page)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
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
        self.grid_radio_btn.setToolTip(QtGui.QApplication.translate("FileListForm", "List view", None, QtGui.QApplication.UnicodeUTF8))
        self.details_radio_btn.setToolTip(QtGui.QApplication.translate("FileListForm", "Details view", None, QtGui.QApplication.UnicodeUTF8))
        self.all_versions_cb.setText(QtGui.QApplication.translate("FileListForm", "All Versions", None, QtGui.QApplication.UnicodeUTF8))

from ..search_widget import SearchWidget
from ..file_list.file_details_view import FileDetailsView
from ..file_list.file_list_form import GroupedListView
from . import resources_rc
