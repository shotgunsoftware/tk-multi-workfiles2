# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\qa\sg_envs\dv\tk\tk-multi-workfiles2\resources\file_list_form.ui'
#
# Created: Tue Aug 15 10:03:02 2023
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
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
        self.horizontalLayout_8 = QtGui.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(1, -1, 1, -1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.user_filter_btn = UserFilterButton(FileListForm)
        self.user_filter_btn.setStyleSheet("#user_filter_btn {\n"
"       width: 40;\n"
"       height: 24;\n"
"       border: 0px, none;\n"
"       border-image: url(:/tk-multi-workfiles2/users_none.png);\n"
"}\n"
"#user_filter_btn::hover, #user_filter_btn::pressed {\n"
"       border-image: url(:/tk-multi-workfiles2/users_none_hover.png);\n"
"}\n"
"\n"
"#user_filter_btn[user_style=\"none\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_none.png);\n"
"}\n"
"#user_filter_btn[user_style=\"current\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_current.png);\n"
"}\n"
"#user_filter_btn[user_style=\"other\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_other.png);\n"
"}\n"
"#user_filter_btn[user_style=\"all\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_all.png);\n"
"}\n"
"\n"
"#user_filter_btn::hover[user_style=\"none\"], #user_filter_btn::pressed[user_style=\"none\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_none_hover.png);\n"
"}\n"
"#user_filter_btn::hover[user_style=\"current\"], #user_filter_btn::pressed[user_style=\"current\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_current_hover.png);\n"
"}\n"
"#user_filter_btn::hover[user_style=\"other\"], #user_filter_btn::pressed[user_style=\"other\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_other_hover.png);\n"
"}\n"
"#user_filter_btn::hover[user_style=\"all\"], #user_filter_btn::pressed[user_style=\"all\"] {\n"
"       border-image: url(:/tk-multi-workfiles2/users_all_hover.png);\n"
"}\n"
"\n"
"#user_filter_btn::menu-indicator, #user_filter_btn::menu-indicator::pressed, #user_filter_btn::menu-indicator::open {\n"
"       left: -2px;\n"
"       top: -2px;\n"
"       width: 8px;\n"
"       height: 6px;\n"
"}\n"
"")
        self.user_filter_btn.setText("")
        self.user_filter_btn.setFlat(True)
        self.user_filter_btn.setObjectName("user_filter_btn")
        self.horizontalLayout_3.addWidget(self.user_filter_btn)
        self.all_versions_cb = QtGui.QCheckBox(FileListForm)
        self.all_versions_cb.setObjectName("all_versions_cb")
        self.horizontalLayout_3.addWidget(self.all_versions_cb)
        self.check_refs_cb = QtGui.QCheckBox(FileListForm)
        self.check_refs_cb.setObjectName("check_refs_cb")
        self.horizontalLayout_3.addWidget(self.check_refs_cb)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.thumbnail_mode = QtGui.QToolButton(FileListForm)
        self.thumbnail_mode.setMinimumSize(QtCore.QSize(26, 26))
        self.thumbnail_mode.setText("")
        self.thumbnail_mode.setCheckable(True)
        self.thumbnail_mode.setChecked(False)
        self.thumbnail_mode.setObjectName("thumbnail_mode")
        self.horizontalLayout_3.addWidget(self.thumbnail_mode)
        self.list_mode = QtGui.QToolButton(FileListForm)
        self.list_mode.setMinimumSize(QtCore.QSize(26, 26))
        self.list_mode.setText("")
        self.list_mode.setCheckable(True)
        self.list_mode.setChecked(True)
        self.list_mode.setObjectName("list_mode")
        self.horizontalLayout_3.addWidget(self.list_mode)
        self.search_ctrl = SearchWidget(FileListForm)
        self.search_ctrl.setMinimumSize(QtCore.QSize(100, 0))
        self.search_ctrl.setStyleSheet("#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.search_ctrl.setObjectName("search_ctrl")
        self.horizontalLayout_3.addWidget(self.search_ctrl)
        self.filter_menu_btn = FilterMenuButton(FileListForm)
        self.filter_menu_btn.setObjectName("filter_menu_btn")
        self.horizontalLayout_3.addWidget(self.filter_menu_btn)
        self.horizontalLayout_3.setStretch(3, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.view_pages = QtGui.QStackedWidget(FileListForm)
        self.view_pages.setObjectName("view_pages")
        self.list_page = QtGui.QWidget()
        self.list_page.setObjectName("list_page")
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.list_page)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.file_list_view = GroupedItemView(self.list_page)
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
        self.verticalLayout_2.addWidget(self.view_pages)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.item_size_slider = QtGui.QSlider(FileListForm)
        self.item_size_slider.setMinimumSize(QtCore.QSize(150, 0))
        self.item_size_slider.setMaximumSize(QtCore.QSize(150, 16777215))
        self.item_size_slider.setStyleSheet(" QSlider::handle:horizontal {\n"
"       border: 1px solid palette(base);\n"
"     border-radius: 3px;\n"
"     width: 4px;\n"
"     background: palette(light);\n"
" }")
        self.item_size_slider.setMinimum(20)
        self.item_size_slider.setMaximum(200)
        self.item_size_slider.setOrientation(QtCore.Qt.Horizontal)
        self.item_size_slider.setObjectName("item_size_slider")
        self.horizontalLayout.addWidget(self.item_size_slider)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_8.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.retranslateUi(FileListForm)
        self.view_pages.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(FileListForm)

    def retranslateUi(self, FileListForm):
        FileListForm.setWindowTitle(QtGui.QApplication.translate("FileListForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.user_filter_btn.setProperty("user_style", QtGui.QApplication.translate("FileListForm", "current", None, QtGui.QApplication.UnicodeUTF8))
        self.all_versions_cb.setText(QtGui.QApplication.translate("FileListForm", "All Versions", None, QtGui.QApplication.UnicodeUTF8))
        self.check_refs_cb.setText(QtGui.QApplication.translate("FileListForm", "Check References on Open", None, QtGui.QApplication.UnicodeUTF8))
        self.thumbnail_mode.setToolTip(QtGui.QApplication.translate("FileListForm", "Thumbnail Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.thumbnail_mode.setAccessibleName(QtGui.QApplication.translate("FileListForm", "thumbnail_mode", None, QtGui.QApplication.UnicodeUTF8))
        self.list_mode.setToolTip(QtGui.QApplication.translate("FileListForm", "List Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.list_mode.setAccessibleName(QtGui.QApplication.translate("FileListForm", "list_mode", None, QtGui.QApplication.UnicodeUTF8))
        self.search_ctrl.setAccessibleName(QtGui.QApplication.translate("FileListForm", "Search All Files", None, QtGui.QApplication.UnicodeUTF8))
        self.filter_menu_btn.setText(QtGui.QApplication.translate("FileListForm", "Filter", None, QtGui.QApplication.UnicodeUTF8))

from ..file_list.file_details_view import FileDetailsView
from ..file_list.user_filter_button import UserFilterButton
from ..framework_qtwidgets import FilterMenuButton, GroupedItemView, SearchWidget
from .
