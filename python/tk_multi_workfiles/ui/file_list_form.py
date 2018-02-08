# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_list_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_FileListForm(object):
    def setupUi(self, FileListForm):
        FileListForm.setObjectName("FileListForm")
        FileListForm.resize(675, 632)
        self.verticalLayout = QtGui.QVBoxLayout(FileListForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(2, 6, 2, 2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(1, -1, 1, -1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.user_filter_btn = UserFilterButton(FileListForm)
        self.user_filter_btn.setStyleSheet("#user_filter_btn {\n"
"    width: 40;\n"
"    height: 24;\n"
"    border: 0px, none;\n"
"    border-image: url(:/tk-multi-workfiles2/users_none.png);\n"
"}\n"
"#user_filter_btn::hover, #user_filter_btn::pressed {\n"
"    border-image: url(:/tk-multi-workfiles2/users_none_hover.png);\n"
"}\n"
"\n"
"#user_filter_btn[user_style=\"none\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_none.png);\n"
"}\n"
"#user_filter_btn[user_style=\"current\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_current.png);\n"
"}\n"
"#user_filter_btn[user_style=\"other\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_other.png);\n"
"}\n"
"#user_filter_btn[user_style=\"all\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_all.png);\n"
"}\n"
"\n"
"#user_filter_btn::hover[user_style=\"none\"], #user_filter_btn::pressed[user_style=\"none\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_none_hover.png);\n"
"}\n"
"#user_filter_btn::hover[user_style=\"current\"], #user_filter_btn::pressed[user_style=\"current\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_current_hover.png);\n"
"}\n"
"#user_filter_btn::hover[user_style=\"other\"], #user_filter_btn::pressed[user_style=\"other\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_other_hover.png);\n"
"}\n"
"#user_filter_btn::hover[user_style=\"all\"], #user_filter_btn::pressed[user_style=\"all\"] {\n"
"    border-image: url(:/tk-multi-workfiles2/users_all_hover.png);\n"
"}\n"
"\n"
"#user_filter_btn::menu-indicator, #user_filter_btn::menu-indicator::pressed, #user_filter_btn::menu-indicator::open {\n"
"    left: -2px;\n"
"    top: -2px;\n"
"    width: 8px;\n"
"    height: 6px;\n"
"}\n"
"")
        self.user_filter_btn.setText("")
        self.user_filter_btn.setFlat(True)
        self.user_filter_btn.setObjectName("user_filter_btn")
        self.horizontalLayout_3.addWidget(self.user_filter_btn)
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
        self.user_filter_btn.setProperty("user_style", QtGui.QApplication.translate("FileListForm", "current", None, QtGui.QApplication.UnicodeUTF8))
        self.all_versions_cb.setText(QtGui.QApplication.translate("FileListForm", "All Versions", None, QtGui.QApplication.UnicodeUTF8))

from ..file_list.file_details_view import FileDetailsView
from ..file_list.user_filter_button import UserFilterButton
from ..framework_qtwidgets import GroupedListView, SearchWidget
from . import resources_rc
