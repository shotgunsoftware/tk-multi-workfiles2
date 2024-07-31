# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'browser_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from tank.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


class Ui_BrowserForm(object):
    def setupUi(self, BrowserForm):
        if not BrowserForm.objectName():
            BrowserForm.setObjectName(u"BrowserForm")
        BrowserForm.resize(984, 751)
        self.horizontalLayout = QHBoxLayout(BrowserForm)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(BrowserForm)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.vertical_splitter = QSplitter(self.splitter)
        self.vertical_splitter.setObjectName(u"vertical_splitter")
        self.vertical_splitter.setOrientation(Qt.Vertical)
        self.task_browser_tabs = QTabWidget(self.vertical_splitter)
        self.task_browser_tabs.setObjectName(u"task_browser_tabs")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.task_browser_tabs.sizePolicy().hasHeightForWidth())
        self.task_browser_tabs.setSizePolicy(sizePolicy)
        self.task_browser_tabs.setMinimumSize(QSize(200, 0))
        self.vertical_splitter.addWidget(self.task_browser_tabs)
        self.step_filters_frame = QFrame(self.vertical_splitter)
        self.step_filters_frame.setObjectName(u"step_filters_frame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.step_filters_frame.sizePolicy().hasHeightForWidth())
        self.step_filters_frame.setSizePolicy(sizePolicy1)
        self.step_filters_frame.setMinimumSize(QSize(0, 0))
        self.step_filters_frame.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.step_filters_frame)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.step_filter_label = QLabel(self.step_filters_frame)
        self.step_filter_label.setObjectName(u"step_filter_label")
        self.step_filter_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.step_filter_label)

        self.step_filter_list_widget = QListWidget(self.step_filters_frame)
        self.step_filter_list_widget.setObjectName(u"step_filter_list_widget")

        self.verticalLayout.addWidget(self.step_filter_list_widget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.select_all_step_button = QPushButton(self.step_filters_frame)
        self.select_all_step_button.setObjectName(u"select_all_step_button")
        self.select_all_step_button.setFlat(False)

        self.horizontalLayout_2.addWidget(self.select_all_step_button)

        self.select_none_step_button = QPushButton(self.step_filters_frame)
        self.select_none_step_button.setObjectName(u"select_none_step_button")
        self.select_none_step_button.setFlat(False)

        self.horizontalLayout_2.addWidget(self.select_none_step_button)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalLayout.setStretch(1, 1)
        self.vertical_splitter.addWidget(self.step_filters_frame)
        self.splitter.addWidget(self.vertical_splitter)
        self.file_browser_tabs = QTabWidget(self.splitter)
        self.file_browser_tabs.setObjectName(u"file_browser_tabs")
        sizePolicy2 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.file_browser_tabs.sizePolicy().hasHeightForWidth())
        self.file_browser_tabs.setSizePolicy(sizePolicy2)
        self.splitter.addWidget(self.file_browser_tabs)

        self.horizontalLayout.addWidget(self.splitter)

        self.retranslateUi(BrowserForm)

        self.file_browser_tabs.setCurrentIndex(-1)

        QMetaObject.connectSlotsByName(BrowserForm)
    # setupUi

    def retranslateUi(self, BrowserForm):
        BrowserForm.setWindowTitle(QCoreApplication.translate("BrowserForm", u"Form", None))
        self.step_filter_label.setText(QCoreApplication.translate("BrowserForm", u"Filter by Pipeline Step", None))
        self.select_all_step_button.setText(QCoreApplication.translate("BrowserForm", u"Select All", None))
        self.select_none_step_button.setText(QCoreApplication.translate("BrowserForm", u"Select None", None))
    # retranslateUi
