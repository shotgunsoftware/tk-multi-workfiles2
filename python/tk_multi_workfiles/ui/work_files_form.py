# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'work_files_form.ui'
#
# Created: Tue Apr 16 18:25:15 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_WorkFilesForm(object):
    def setupUi(self, WorkFilesForm):
        WorkFilesForm.setObjectName("WorkFilesForm")
        WorkFilesForm.resize(968, 579)
        WorkFilesForm.setStyleSheet("")
        self.gridLayout = QtGui.QGridLayout(WorkFilesForm)
        self.gridLayout.setContentsMargins(6, 6, 6, 6)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_6 = QtGui.QVBoxLayout()
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setContentsMargins(0, 0, -1, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.items_title_label_2 = QtGui.QLabel(WorkFilesForm)
        self.items_title_label_2.setMinimumSize(QtCore.QSize(0, 44))
        self.items_title_label_2.setStyleSheet("#items_title_label {\n"
"font-size: 14pt\n"
"}")
        self.items_title_label_2.setMargin(4)
        self.items_title_label_2.setObjectName("items_title_label_2")
        self.verticalLayout_6.addWidget(self.items_title_label_2)
        self.work_area_frame = QtGui.QFrame(WorkFilesForm)
        self.work_area_frame.setStyleSheet("#work_area_frame {\n"
"border-style: solid;\n"
"border-radius: 2px;\n"
"border-width: 1px;\n"
"border-color: rgb(32,32,32);\n"
"}")
        self.work_area_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.work_area_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.work_area_frame.setObjectName("work_area_frame")
        self.verticalLayout_7 = QtGui.QVBoxLayout(self.work_area_frame)
        self.verticalLayout_7.setContentsMargins(6, 12, 6, 6)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_2.setSpacing(12)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.task_thumbnail = QtGui.QLabel(self.work_area_frame)
        self.task_thumbnail.setMinimumSize(QtCore.QSize(160, 100))
        self.task_thumbnail.setMaximumSize(QtCore.QSize(160, 100))
        self.task_thumbnail.setFrameShape(QtGui.QFrame.NoFrame)
        self.task_thumbnail.setText("")
        self.task_thumbnail.setPixmap(QtGui.QPixmap(":/res/thumb_empty.png"))
        self.task_thumbnail.setScaledContents(False)
        self.task_thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.task_thumbnail.setMargin(0)
        self.task_thumbnail.setIndent(0)
        self.task_thumbnail.setObjectName("task_thumbnail")
        self.gridLayout_2.addWidget(self.task_thumbnail, 0, 1, 1, 1)
        self.entity_thumbnail = QtGui.QLabel(self.work_area_frame)
        self.entity_thumbnail.setMinimumSize(QtCore.QSize(160, 100))
        self.entity_thumbnail.setMaximumSize(QtCore.QSize(160, 100))
        self.entity_thumbnail.setText("")
        self.entity_thumbnail.setPixmap(QtGui.QPixmap(":/res/thumb_empty.png"))
        self.entity_thumbnail.setScaledContents(False)
        self.entity_thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.entity_thumbnail.setObjectName("entity_thumbnail")
        self.gridLayout_2.addWidget(self.entity_thumbnail, 0, 0, 1, 1)
        self.entity_details = QtGui.QLabel(self.work_area_frame)
        self.entity_details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.entity_details.setWordWrap(True)
        self.entity_details.setObjectName("entity_details")
        self.gridLayout_2.addWidget(self.entity_details, 1, 0, 1, 1)
        self.task_details = QtGui.QLabel(self.work_area_frame)
        self.task_details.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.task_details.setWordWrap(True)
        self.task_details.setObjectName("task_details")
        self.gridLayout_2.addWidget(self.task_details, 1, 1, 1, 1)
        self.verticalLayout_7.addLayout(self.gridLayout_2)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.change_work_area_btn = QtGui.QPushButton(self.work_area_frame)
        self.change_work_area_btn.setMinimumSize(QtCore.QSize(100, 0))
        self.change_work_area_btn.setObjectName("change_work_area_btn")
        self.horizontalLayout_6.addWidget(self.change_work_area_btn)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem)
        self.verticalLayout_7.addLayout(self.horizontalLayout_6)
        spacerItem1 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem1)
        self.work_area_details = QtGui.QTextEdit(self.work_area_frame)
        self.work_area_details.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.work_area_details.sizePolicy().hasHeightForWidth())
        self.work_area_details.setSizePolicy(sizePolicy)
        self.work_area_details.setMinimumSize(QtCore.QSize(0, 0))
        self.work_area_details.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.work_area_details.setStyleSheet("QTextEdit {\n"
"background-color: rgb(0,0,0,0)\n"
"}")
        self.work_area_details.setFrameShape(QtGui.QFrame.NoFrame)
        self.work_area_details.setFrameShadow(QtGui.QFrame.Plain)
        self.work_area_details.setLineWidth(0)
        self.work_area_details.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.work_area_details.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.work_area_details.setReadOnly(True)
        self.work_area_details.setAcceptRichText(True)
        self.work_area_details.setObjectName("work_area_details")
        self.verticalLayout_7.addWidget(self.work_area_details)
        self.verticalLayout_7.setStretch(3, 1)
        self.verticalLayout_6.addWidget(self.work_area_frame)
        self.gridLayout.addLayout(self.verticalLayout_6, 0, 0, 1, 1)
        self.file_list = FileListView(WorkFilesForm)
        self.file_list.setStyleSheet("#file_list {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.file_list.setObjectName("file_list")
        self.gridLayout.addWidget(self.file_list, 0, 1, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.filter_combo = QtGui.QComboBox(WorkFilesForm)
        self.filter_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.filter_combo.setObjectName("filter_combo")
        self.horizontalLayout_2.addWidget(self.filter_combo)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.new_file_btn = QtGui.QPushButton(WorkFilesForm)
        self.new_file_btn.setMinimumSize(QtCore.QSize(80, 0))
        self.new_file_btn.setObjectName("new_file_btn")
        self.horizontalLayout_2.addWidget(self.new_file_btn)
        self.open_file_btn = QtGui.QPushButton(WorkFilesForm)
        self.open_file_btn.setMinimumSize(QtCore.QSize(80, 0))
        self.open_file_btn.setObjectName("open_file_btn")
        self.horizontalLayout_2.addWidget(self.open_file_btn)
        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 1, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cancel_btn = QtGui.QPushButton(WorkFilesForm)
        self.cancel_btn.setMinimumSize(QtCore.QSize(80, 0))
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout.addWidget(self.cancel_btn)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setRowStretch(0, 1)

        self.retranslateUi(WorkFilesForm)
        QtCore.QMetaObject.connectSlotsByName(WorkFilesForm)

    def retranslateUi(self, WorkFilesForm):
        WorkFilesForm.setWindowTitle(QtGui.QApplication.translate("WorkFilesForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.items_title_label_2.setText(QtGui.QApplication.translate("WorkFilesForm", "<big>Please Choose a Work Area:</big>", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_details.setText(QtGui.QApplication.translate("WorkFilesForm", "<big>Shot blah</big><br>Description...", None, QtGui.QApplication.UnicodeUTF8))
        self.task_details.setText(QtGui.QApplication.translate("WorkFilesForm", "<big>Task Lighting</big><br>Description...", None, QtGui.QApplication.UnicodeUTF8))
        self.change_work_area_btn.setText(QtGui.QApplication.translate("WorkFilesForm", "Change...", None, QtGui.QApplication.UnicodeUTF8))
        self.work_area_details.setHtml(QtGui.QApplication.translate("WorkFilesForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Lucida Grande\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.new_file_btn.setText(QtGui.QApplication.translate("WorkFilesForm", "New File", None, QtGui.QApplication.UnicodeUTF8))
        self.open_file_btn.setText(QtGui.QApplication.translate("WorkFilesForm", "Open File", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("WorkFilesForm", "Close", None, QtGui.QApplication.UnicodeUTF8))

from ..file_list_view import FileListView
from . import resources_rc
from . import resources_rc
