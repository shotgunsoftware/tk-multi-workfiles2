# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'file_save_form.ui'
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


from ..framework_qtwidgets import ElidedLabel
from ..framework_qtwidgets import NavigationWidget
from ..framework_qtwidgets import BreadcrumbWidget
from ..browser_form import BrowserForm

from  . import resources_rc

class Ui_FileSaveForm(object):
    def setupUi(self, FileSaveForm):
        if not FileSaveForm.objectName():
            FileSaveForm.setObjectName(u"FileSaveForm")
        FileSaveForm.resize(850, 539)
        self.verticalLayout = QVBoxLayout(FileSaveForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(12, 12, 12, 4)
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.expand_checkbox = QCheckBox(FileSaveForm)
        self.expand_checkbox.setObjectName(u"expand_checkbox")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.expand_checkbox.sizePolicy().hasHeightForWidth())
        self.expand_checkbox.setSizePolicy(sizePolicy)
        self.expand_checkbox.setMaximumSize(QSize(16777215, 24))
        self.expand_checkbox.setStyleSheet(u"#expand_checkbox::indicator {\n"
"width: 24;\n"
"height: 24;\n"
"}\n"
"\n"
"#expand_checkbox::indicator::unchecked {\n"
"	image: url(:/tk-multi-workfiles2/save_expand.png);\n"
"\n"
"}\n"
"\n"
"#expand_checkbox::indicator::unchecked::hover {\n"
"	image: url(:/tk-multi-workfiles2/save_expand_hover.png);\n"
"}\n"
"\n"
"#expand_checkbox::indicator::unchecked::pressed {\n"
"	image: url(:/tk-multi-workfiles2/save_expand_pressed.png);\n"
"}\n"
"\n"
"#expand_checkbox::indicator::checked {\n"
"    image: url(:/tk-multi-workfiles2/save_collapse.png);\n"
"}\n"
"\n"
"#expand_checkbox::indicator::checked:hover {\n"
"    image: url(:/tk-multi-workfiles2/save_collapse_hover.png);\n"
"}\n"
"\n"
"#expand_checkbox::indicator::checked:pressed {\n"
"    image: url(:/tk-multi-workfiles2/save_collapse_pressed.png);\n"
"}")

        self.horizontalLayout_3.addWidget(self.expand_checkbox)

        self.gridLayout_2.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)

        self.nav = NavigationWidget(FileSaveForm)
        self.nav.setObjectName(u"nav")
        self.nav.setMinimumSize(QSize(80, 30))
        self.nav.setStyleSheet(u"#nav {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.gridLayout_2.addWidget(self.nav, 0, 1, 1, 1)

        self.breadcrumbs = BreadcrumbWidget(FileSaveForm)
        self.breadcrumbs.setObjectName(u"breadcrumbs")
        self.breadcrumbs.setMinimumSize(QSize(0, 30))
        self.breadcrumbs.setStyleSheet(u"#breadcrumbs {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.gridLayout_2.addWidget(self.breadcrumbs, 0, 2, 1, 1)

        self.gridLayout_2.setColumnStretch(2, 1)

        self.verticalLayout_3.addLayout(self.gridLayout_2)

        self.browser = BrowserForm(FileSaveForm)
        self.browser.setObjectName(u"browser")
        self.browser.setStyleSheet(u"#browser {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.verticalLayout_3.addWidget(self.browser)

        self.verticalLayout_3.setStretch(1, 1)

        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.line = QFrame(FileSaveForm)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(20)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(12, 4, 12, 4)
        self.file_controls_grid = QGridLayout()
        self.file_controls_grid.setObjectName(u"file_controls_grid")
        self.file_controls_grid.setHorizontalSpacing(14)
        self.file_controls_grid.setVerticalSpacing(6)
        self.version_label = QLabel(FileSaveForm)
        self.version_label.setObjectName(u"version_label")
        self.version_label.setMinimumSize(QSize(0, 0))
        self.version_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.version_label.setIndent(-1)

        self.file_controls_grid.addWidget(self.version_label, 1, 0, 1, 1)

        self.name_label = QLabel(FileSaveForm)
        self.name_label.setObjectName(u"name_label")
        self.name_label.setMinimumSize(QSize(0, 0))
        self.name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.name_label.setIndent(-1)

        self.file_controls_grid.addWidget(self.name_label, 0, 0, 1, 1)

        self.file_type_label = QLabel(FileSaveForm)
        self.file_type_label.setObjectName(u"file_type_label")
        self.file_type_label.setMinimumSize(QSize(0, 0))
        self.file_type_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.file_type_label.setIndent(-1)

        self.file_controls_grid.addWidget(self.file_type_label, 2, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
#ifndef Q_OS_MAC
        self.horizontalLayout_2.setSpacing(-1)
#endif
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.version_spinner = QSpinBox(FileSaveForm)
        self.version_spinner.setObjectName(u"version_spinner")
        self.version_spinner.setMaximum(9999999)

        self.horizontalLayout_2.addWidget(self.version_spinner)

        self.use_next_available_cb = QCheckBox(FileSaveForm)
        self.use_next_available_cb.setObjectName(u"use_next_available_cb")

        self.horizontalLayout_2.addWidget(self.use_next_available_cb)

        self.horizontalSpacer_2 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.file_controls_grid.addLayout(self.horizontalLayout_2, 1, 1, 1, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.file_type_menu = QComboBox(FileSaveForm)
        self.file_type_menu.setObjectName(u"file_type_menu")
        self.file_type_menu.setMinimumSize(QSize(200, 0))

        self.horizontalLayout_6.addWidget(self.file_type_menu)

        self.horizontalSpacer_3 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)

        self.file_controls_grid.addLayout(self.horizontalLayout_6, 2, 1, 1, 1)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.name_edit = QLineEdit(FileSaveForm)
        self.name_edit.setObjectName(u"name_edit")
        self.name_edit.setMaximumSize(QSize(200, 16777215))
        self.name_edit.setFrame(True)

        self.horizontalLayout_8.addWidget(self.name_edit)

        self.horizontalSpacer_4 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_4)

        self.horizontalLayout_8.setStretch(0, 1)

        self.file_controls_grid.addLayout(self.horizontalLayout_8, 0, 1, 1, 1)

        self.file_controls_grid.setColumnStretch(1, 1)
        self.file_controls_grid.setColumnMinimumWidth(0, 80)

        self.verticalLayout_2.addLayout(self.file_controls_grid)

        self.feedback_stacked_widget = QStackedWidget(FileSaveForm)
        self.feedback_stacked_widget.setObjectName(u"feedback_stacked_widget")
        self.preview_page = QWidget()
        self.preview_page.setObjectName(u"preview_page")
        self.verticalLayout_4 = QVBoxLayout(self.preview_page)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.preview_grid = QGridLayout()
        self.preview_grid.setObjectName(u"preview_grid")
        self.preview_grid.setHorizontalSpacing(14)
        self.preview_grid.setVerticalSpacing(1)
        self.preview_label = QLabel(self.preview_page)
        self.preview_label.setObjectName(u"preview_label")
        self.preview_label.setAlignment(Qt.AlignRight|Qt.AlignTop|Qt.AlignTrailing)
        self.preview_label.setIndent(-1)

        self.preview_grid.addWidget(self.preview_label, 0, 0, 1, 1)

        self.file_name_preview = QLabel(self.preview_page)
        self.file_name_preview.setObjectName(u"file_name_preview")
        self.file_name_preview.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.file_name_preview.setWordWrap(True)
        self.file_name_preview.setIndent(-1)

        self.preview_grid.addWidget(self.file_name_preview, 0, 1, 1, 1)

        self.work_area_preview = ElidedLabel(self.preview_page)
        self.work_area_preview.setObjectName(u"work_area_preview")
        sizePolicy1 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.work_area_preview.sizePolicy().hasHeightForWidth())
        self.work_area_preview.setSizePolicy(sizePolicy1)
        self.work_area_preview.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.work_area_preview.setWordWrap(True)
        self.work_area_preview.setIndent(-1)
        self.work_area_preview.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.preview_grid.addWidget(self.work_area_preview, 1, 1, 1, 1)

        self.work_area_label = QLabel(self.preview_page)
        self.work_area_label.setObjectName(u"work_area_label")
        self.work_area_label.setAlignment(Qt.AlignRight|Qt.AlignTop|Qt.AlignTrailing)
        self.work_area_label.setIndent(-1)

        self.preview_grid.addWidget(self.work_area_label, 1, 0, 1, 1)

        self.preview_grid.setColumnStretch(1, 1)
        self.preview_grid.setColumnMinimumWidth(0, 80)

        self.verticalLayout_4.addLayout(self.preview_grid)

        self.feedback_stacked_widget.addWidget(self.preview_page)
        self.warning_page = QWidget()
        self.warning_page.setObjectName(u"warning_page")
        self.horizontalLayout_7 = QHBoxLayout(self.warning_page)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.warning_grid = QGridLayout()
        self.warning_grid.setObjectName(u"warning_grid")
        self.warning_grid.setHorizontalSpacing(14)
        self.warning_grid.setVerticalSpacing(6)
        self.warning_grid.setContentsMargins(0, -1, -1, -1)
        self.warning = QLabel(self.warning_page)
        self.warning.setObjectName(u"warning")
        self.warning.setMinimumSize(QSize(0, 45))
        self.warning.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.warning.setWordWrap(True)
        self.warning.setMargin(0)
        self.warning.setIndent(-1)
        self.warning.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.warning_grid.addWidget(self.warning, 0, 1, 1, 1)

        self.warning_label = QLabel(self.warning_page)
        self.warning_label.setObjectName(u"warning_label")
        self.warning_label.setAlignment(Qt.AlignRight|Qt.AlignTop|Qt.AlignTrailing)
        self.warning_label.setIndent(-1)

        self.warning_grid.addWidget(self.warning_label, 0, 0, 1, 1)

        self.warning_grid.setColumnStretch(1, 1)
        self.warning_grid.setColumnMinimumWidth(0, 80)

        self.horizontalLayout_7.addLayout(self.warning_grid)

        self.feedback_stacked_widget.addWidget(self.warning_page)

        self.verticalLayout_2.addWidget(self.feedback_stacked_widget)

        self.verticalLayout_2.setStretch(1, 1)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.break_line = QFrame(FileSaveForm)
        self.break_line.setObjectName(u"break_line")
        self.break_line.setFrameShape(QFrame.HLine)
        self.break_line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.break_line)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(12, 8, 12, 12)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.cancel_btn = QPushButton(FileSaveForm)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.horizontalLayout_4.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(FileSaveForm)
        self.save_btn.setObjectName(u"save_btn")

        self.horizontalLayout_4.addWidget(self.save_btn)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.verticalLayout.setStretch(0, 1)
        QWidget.setTabOrder(self.name_edit, self.version_spinner)
        QWidget.setTabOrder(self.version_spinner, self.use_next_available_cb)
        QWidget.setTabOrder(self.use_next_available_cb, self.file_type_menu)
        QWidget.setTabOrder(self.file_type_menu, self.cancel_btn)
        QWidget.setTabOrder(self.cancel_btn, self.save_btn)
        QWidget.setTabOrder(self.save_btn, self.expand_checkbox)

        self.retranslateUi(FileSaveForm)

        self.feedback_stacked_widget.setCurrentIndex(0)
        self.save_btn.setDefault(True)

        QMetaObject.connectSlotsByName(FileSaveForm)
    # setupUi

    def retranslateUi(self, FileSaveForm):
        FileSaveForm.setWindowTitle(QCoreApplication.translate("FileSaveForm", u"Form", None))
#if QT_CONFIG(tooltip)
        self.expand_checkbox.setToolTip(QCoreApplication.translate("FileSaveForm", u"Toggle Browser", None))
#endif // QT_CONFIG(tooltip)
        self.expand_checkbox.setText("")
        self.version_label.setText(QCoreApplication.translate("FileSaveForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Version:</span></p></body></html>", None))
        self.name_label.setText(QCoreApplication.translate("FileSaveForm", u"<html><head/><body><p><span style=\" font-weight:600;\">Name:</span></p></body></html>", None))
        self.file_type_label.setText(QCoreApplication.translate("FileSaveForm", u"<html><head/><body><p><span style=\" font-weight:600;\">File Type:</span></p></body></html>", None))
#if QT_CONFIG(accessibility)
        self.version_spinner.setAccessibleName(QCoreApplication.translate("FileSaveForm", u"Version Number", None))
#endif // QT_CONFIG(accessibility)
        self.use_next_available_cb.setText(QCoreApplication.translate("FileSaveForm", u"Use Next Available Version Number", None))
#if QT_CONFIG(accessibility)
        self.file_type_menu.setAccessibleName(QCoreApplication.translate("FileSaveForm", u"File Type", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.name_edit.setAccessibleName(QCoreApplication.translate("FileSaveForm", u"Name Edit", None))
#endif // QT_CONFIG(accessibility)
        self.preview_label.setText(QCoreApplication.translate("FileSaveForm", u"<html><head/><body><p><span style=\" font-weight:600; color:rgb(120, 120, 120)\">Preview:</span></p></body></html>", None))
        self.file_name_preview.setText(QCoreApplication.translate("FileSaveForm", u"preview", None))
        self.work_area_preview.setText(QCoreApplication.translate("FileSaveForm", u".../work/area", None))
        self.work_area_label.setText(QCoreApplication.translate("FileSaveForm", u"<html><head/><body><p><span style=\" font-weight:600; color:rgb(120, 120, 120)\">Work Area:</span></p></body></html>", None))
        self.warning.setText(QCoreApplication.translate("FileSaveForm", u"warning", None))
        self.warning_label.setText(QCoreApplication.translate("FileSaveForm", u"<html><head/><body><p><span style=\" font-weight:600; color:rgb(226, 146, 0)\">Warning:</span></p></body></html>", None))
        self.cancel_btn.setText(QCoreApplication.translate("FileSaveForm", u"Cancel", None))
        self.save_btn.setText(QCoreApplication.translate("FileSaveForm", u"Save", None))
    # retranslateUi
