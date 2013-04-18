# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'save_as_form.ui'
#
# Created: Thu Apr 18 09:54:44 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SaveAsForm(object):
    def setupUi(self, SaveAsForm):
        SaveAsForm.setObjectName("SaveAsForm")
        SaveAsForm.resize(510, 294)
        SaveAsForm.setMinimumSize(QtCore.QSize(510, 0))
        SaveAsForm.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(SaveAsForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setSpacing(16)
        self.verticalLayout_2.setContentsMargins(12, 12, 12, 4)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.header_frame = QtGui.QFrame(SaveAsForm)
        self.header_frame.setStyleSheet("#header_frame {\n"
"border-style: solid;\n"
"border-radius: 3;\n"
"border-width: 1;\n"
"border-color: rgb(32,32,32);\n"
"}")
        self.header_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.header_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.header_frame.setObjectName("header_frame")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.header_frame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtGui.QLabel(self.header_frame)
        self.label_2.setMinimumSize(QtCore.QSize(80, 80))
        self.label_2.setMaximumSize(QtCore.QSize(80, 80))
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap(":/res/save_as_icon.png"))
        self.label_2.setScaledContents(False)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.header_label = QtGui.QLabel(self.header_frame)
        self.header_label.setWordWrap(True)
        self.header_label.setObjectName("header_label")
        self.horizontalLayout_2.addWidget(self.header_label)
        self.verticalLayout_2.addWidget(self.header_frame)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setHorizontalSpacing(16)
        self.gridLayout.setVerticalSpacing(10)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(4, -1, -1, -1)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.name_edit = QtGui.QLineEdit(SaveAsForm)
        self.name_edit.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.name_edit.setFrame(True)
        self.name_edit.setObjectName("name_edit")
        self.horizontalLayout_4.addWidget(self.name_edit)
        self.reset_version_cb = QtGui.QCheckBox(SaveAsForm)
        self.reset_version_cb.setObjectName("reset_version_cb")
        self.horizontalLayout_4.addWidget(self.reset_version_cb)
        self.gridLayout.addLayout(self.horizontalLayout_4, 0, 1, 1, 1)
        self.label_5 = QtGui.QLabel(SaveAsForm)
        self.label_5.setMinimumSize(QtCore.QSize(0, 0))
        self.label_5.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_5.setIndent(4)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.filename_preview_label = QtGui.QLabel(SaveAsForm)
        self.filename_preview_label.setIndent(4)
        self.filename_preview_label.setObjectName("filename_preview_label")
        self.gridLayout.addWidget(self.filename_preview_label, 1, 1, 1, 1)
        self.path_preview_edit = QtGui.QTextEdit(SaveAsForm)
        self.path_preview_edit.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.path_preview_edit.sizePolicy().hasHeightForWidth())
        self.path_preview_edit.setSizePolicy(sizePolicy)
        self.path_preview_edit.setMinimumSize(QtCore.QSize(0, 0))
        self.path_preview_edit.setMaximumSize(QtCore.QSize(16777215, 60))
        self.path_preview_edit.setStyleSheet("QTextEdit {\n"
"background-color: rgb(0,0,0,0);\n"
"border-style: none;\n"
"}")
        self.path_preview_edit.setFrameShape(QtGui.QFrame.NoFrame)
        self.path_preview_edit.setFrameShadow(QtGui.QFrame.Plain)
        self.path_preview_edit.setLineWidth(0)
        self.path_preview_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.path_preview_edit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.path_preview_edit.setReadOnly(True)
        self.path_preview_edit.setAcceptRichText(True)
        self.path_preview_edit.setObjectName("path_preview_edit")
        self.gridLayout.addWidget(self.path_preview_edit, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(SaveAsForm)
        self.label_4.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_4.setIndent(4)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)
        self.label_6 = QtGui.QLabel(SaveAsForm)
        self.label_6.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_6.setMargin(4)
        self.label_6.setIndent(0)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.break_line = QtGui.QFrame(SaveAsForm)
        self.break_line.setFrameShape(QtGui.QFrame.HLine)
        self.break_line.setFrameShadow(QtGui.QFrame.Sunken)
        self.break_line.setObjectName("break_line")
        self.verticalLayout.addWidget(self.break_line)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(12, 8, 12, 12)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.cancel_btn = QtGui.QPushButton(SaveAsForm)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout_3.addWidget(self.cancel_btn)
        self.continue_btn = QtGui.QPushButton(SaveAsForm)
        self.continue_btn.setObjectName("continue_btn")
        self.horizontalLayout_3.addWidget(self.continue_btn)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(SaveAsForm)
        QtCore.QMetaObject.connectSlotsByName(SaveAsForm)
        SaveAsForm.setTabOrder(self.continue_btn, self.cancel_btn)

    def retranslateUi(self, SaveAsForm):
        SaveAsForm.setWindowTitle(QtGui.QApplication.translate("SaveAsForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.header_label.setText(QtGui.QApplication.translate("SaveAsForm", "Type in a name below and Tank will save the current scene", None, QtGui.QApplication.UnicodeUTF8))
        self.reset_version_cb.setText(QtGui.QApplication.translate("SaveAsForm", "Reset Version No.?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("SaveAsForm", "<html><head/><body><p><span style=\" font-weight:600;\">Name:</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.filename_preview_label.setText(QtGui.QApplication.translate("SaveAsForm", "name.v001.ma", None, QtGui.QApplication.UnicodeUTF8))
        self.path_preview_edit.setHtml(QtGui.QApplication.translate("SaveAsForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Lucida Grande\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">/foo/bar/...</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">line 2</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">line 3</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("SaveAsForm", "<html><head/><body><p><span style=\" font-weight:600;\">Preview:</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("SaveAsForm", "<html><head/><body><p><span style=\" font-weight:600;\">Work Area:</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("SaveAsForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.continue_btn.setText(QtGui.QApplication.translate("SaveAsForm", "Save", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
from . import resources_rc
