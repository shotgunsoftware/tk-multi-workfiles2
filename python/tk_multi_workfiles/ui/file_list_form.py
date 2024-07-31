# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'file_list_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from sgtk.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from sgtk.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


from ..framework_qtwidgets import GroupedItemView
from ..framework_qtwidgets import SearchWidget
from ..framework_qtwidgets import FilterMenuButton
from ..file_list.file_details_view import FileDetailsView
from ..file_list.user_filter_button import UserFilterButton

from  . import resources_rc

class Ui_FileListForm(object):
    def setupUi(self, FileListForm):
        if not FileListForm.objectName():
            FileListForm.setObjectName(u"FileListForm")
        FileListForm.resize(675, 632)
        self.verticalLayout = QVBoxLayout(FileListForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 6, 2, 2)
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(1, -1, 1, -1)
        self.user_filter_btn = UserFilterButton(FileListForm)
        self.user_filter_btn.setObjectName(u"user_filter_btn")
        self.user_filter_btn.setStyleSheet(u"#user_filter_btn {\n"
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
"#user_filter_btn::hover[user_style=\"current\"], "
                        "#user_filter_btn::pressed[user_style=\"current\"] {\n"
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
        self.user_filter_btn.setFlat(True)

        self.horizontalLayout_3.addWidget(self.user_filter_btn)

        self.all_versions_cb = QCheckBox(FileListForm)
        self.all_versions_cb.setObjectName(u"all_versions_cb")

        self.horizontalLayout_3.addWidget(self.all_versions_cb)

        self.check_refs_cb = QCheckBox(FileListForm)
        self.check_refs_cb.setObjectName(u"check_refs_cb")

        self.horizontalLayout_3.addWidget(self.check_refs_cb)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.thumbnail_mode = QToolButton(FileListForm)
        self.thumbnail_mode.setObjectName(u"thumbnail_mode")
        self.thumbnail_mode.setMinimumSize(QSize(26, 26))
        self.thumbnail_mode.setCheckable(True)
        self.thumbnail_mode.setChecked(False)

        self.horizontalLayout_3.addWidget(self.thumbnail_mode)

        self.list_mode = QToolButton(FileListForm)
        self.list_mode.setObjectName(u"list_mode")
        self.list_mode.setMinimumSize(QSize(26, 26))
        self.list_mode.setCheckable(True)
        self.list_mode.setChecked(True)

        self.horizontalLayout_3.addWidget(self.list_mode)

        self.search_ctrl = SearchWidget(FileListForm)
        self.search_ctrl.setObjectName(u"search_ctrl")
        self.search_ctrl.setMinimumSize(QSize(100, 0))
        self.search_ctrl.setStyleSheet(u"#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.horizontalLayout_3.addWidget(self.search_ctrl)

        self.horizontalLayout_3.setStretch(2, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.view_pages = QStackedWidget(FileListForm)
        self.view_pages.setObjectName(u"view_pages")
        self.list_page = QWidget()
        self.list_page.setObjectName(u"list_page")
        self.horizontalLayout_5 = QHBoxLayout(self.list_page)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.file_list_view = GroupedItemView(self.list_page)
        self.file_list_view.setObjectName(u"file_list_view")
        self.file_list_view.setStyleSheet(u"")

        self.horizontalLayout_5.addWidget(self.file_list_view)

        self.view_pages.addWidget(self.list_page)
        self.details_page = QWidget()
        self.details_page.setObjectName(u"details_page")
        self.horizontalLayout_4 = QHBoxLayout(self.details_page)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.file_details_view = FileDetailsView(self.details_page)
        self.file_details_view.setObjectName(u"file_details_view")

        self.horizontalLayout_4.addWidget(self.file_details_view)

        self.view_pages.addWidget(self.details_page)

        self.verticalLayout_2.addWidget(self.view_pages)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.item_size_slider = QSlider(FileListForm)
        self.item_size_slider.setObjectName(u"item_size_slider")
        self.item_size_slider.setMinimumSize(QSize(150, 0))
        self.item_size_slider.setMaximumSize(QSize(150, 16777215))
        self.item_size_slider.setStyleSheet(u" QSlider::handle:horizontal {\n"
"       border: 1px solid palette(base);\n"
"     border-radius: 3px;\n"
"     width: 4px;\n"
"     background: palette(light);\n"
" }")
        self.item_size_slider.setMinimum(20)
        self.item_size_slider.setMaximum(200)
        self.item_size_slider.setOrientation(Qt.Horizontal)

        self.horizontalLayout.addWidget(self.item_size_slider)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_8.addLayout(self.verticalLayout_2)

        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.retranslateUi(FileListForm)

        self.view_pages.setCurrentIndex(0)

        QMetaObject.connectSlotsByName(FileListForm)
    # setupUi

    def retranslateUi(self, FileListForm):
        FileListForm.setWindowTitle(QCoreApplication.translate("FileListForm", u"Form", None))
        self.user_filter_btn.setText("")
        self.user_filter_btn.setProperty("user_style", QCoreApplication.translate("FileListForm", u"current", None))
        self.all_versions_cb.setText(QCoreApplication.translate("FileListForm", u"All Versions", None))
        self.check_refs_cb.setText(QCoreApplication.translate("FileListForm", u"Check References on Open", None))
#if QT_CONFIG(tooltip)
        self.thumbnail_mode.setToolTip(QCoreApplication.translate("FileListForm", u"Thumbnail Mode", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.thumbnail_mode.setAccessibleName(QCoreApplication.translate("FileListForm", u"thumbnail_mode", None))
#endif // QT_CONFIG(accessibility)
        self.thumbnail_mode.setText("")
#if QT_CONFIG(tooltip)
        self.list_mode.setToolTip(QCoreApplication.translate("FileListForm", u"List Mode", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.list_mode.setAccessibleName(QCoreApplication.translate("FileListForm", u"list_mode", None))
#endif // QT_CONFIG(accessibility)
        self.list_mode.setText("")
#if QT_CONFIG(accessibility)
        self.search_ctrl.setAccessibleName(QCoreApplication.translate("FileListForm", u"Search All Files", None))
#endif // QT_CONFIG(accessibility)
    # retranslateUi
