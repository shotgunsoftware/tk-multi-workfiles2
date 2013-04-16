# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'change_version_form.ui'
#
# Created: Tue Apr 16 18:25:15 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ChangeVersionForm(object):
    def setupUi(self, ChangeVersionForm):
        ChangeVersionForm.setObjectName("ChangeVersionForm")
        ChangeVersionForm.resize(320, 220)
        ChangeVersionForm.setMinimumSize(QtCore.QSize(320, 220))
        ChangeVersionForm.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout = QtGui.QVBoxLayout(ChangeVersionForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(ChangeVersionForm)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(20, -1, -1, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.new_version_edit = QtGui.QLineEdit(ChangeVersionForm)
        self.new_version_edit.setMaximumSize(QtCore.QSize(60, 16777215))
        self.new_version_edit.setInputMask("")
        self.new_version_edit.setMaxLength(32767)
        self.new_version_edit.setFrame(True)
        self.new_version_edit.setObjectName("new_version_edit")
        self.gridLayout.addWidget(self.new_version_edit, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(ChangeVersionForm)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.label_2 = QtGui.QLabel(ChangeVersionForm)
        self.label_2.setMinimumSize(QtCore.QSize(140, 0))
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.current_version_label = QtGui.QLabel(ChangeVersionForm)
        self.current_version_label.setObjectName("current_version_label")
        self.gridLayout.addWidget(self.current_version_label, 0, 1, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.horizontalLayout_2.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.warning_label = QtGui.QLabel(ChangeVersionForm)
        self.warning_label.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.warning_label.setWordWrap(True)
        self.warning_label.setObjectName("warning_label")
        self.verticalLayout.addWidget(self.warning_label)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.cancel_btn = QtGui.QPushButton(ChangeVersionForm)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout.addWidget(self.cancel_btn)
        self.change_version_btn = QtGui.QPushButton(ChangeVersionForm)
        self.change_version_btn.setObjectName("change_version_btn")
        self.horizontalLayout.addWidget(self.change_version_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(3, 1)
        self.verticalLayout.setStretch(4, 1)

        self.retranslateUi(ChangeVersionForm)
        QtCore.QMetaObject.connectSlotsByName(ChangeVersionForm)

    def retranslateUi(self, ChangeVersionForm):
        ChangeVersionForm.setWindowTitle(QtGui.QApplication.translate("ChangeVersionForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ChangeVersionForm", "Here you can change the version number of your current file without doing a publish", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ChangeVersionForm", "<html><head/><body><p><span style=\" font-weight:600;\">New Version:</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ChangeVersionForm", "<html><head/><body><p><span style=\" font-weight:600;\">Current Version:</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.current_version_label.setText(QtGui.QApplication.translate("ChangeVersionForm", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.warning_label.setText(QtGui.QApplication.translate("ChangeVersionForm", "Warning: Work file already exists!", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("ChangeVersionForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.change_version_btn.setText(QtGui.QApplication.translate("ChangeVersionForm", "Change Version", None, QtGui.QApplication.UnicodeUTF8))

