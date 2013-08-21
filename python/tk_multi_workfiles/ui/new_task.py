# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'new_task.ui'
#
# Created: Mon Jan 21 00:17:31 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_NewTask(object):
    def setupUi(self, NewTask):
        NewTask.setObjectName("NewTask")
        NewTask.resize(451, 289)
        self.verticalLayout = QtGui.QVBoxLayout(NewTask)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtGui.QLabel(NewTask)
        self.label_3.setWordWrap(True)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setHorizontalSpacing(20)
        self.gridLayout.setObjectName("gridLayout")
        self.label_4 = QtGui.QLabel(NewTask)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)
        self.entity = QtGui.QLabel(NewTask)
        self.entity.setObjectName("entity")
        self.gridLayout.addWidget(self.entity, 2, 1, 1, 1)
        self.label_6 = QtGui.QLabel(NewTask)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 3, 0, 1, 1)
        self.assigned_to = QtGui.QLabel(NewTask)
        self.assigned_to.setObjectName("assigned_to")
        self.gridLayout.addWidget(self.assigned_to, 3, 1, 1, 1)
        self.label = QtGui.QLabel(NewTask)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)
        self.pipeline_step = QtGui.QComboBox(NewTask)
        self.pipeline_step.setObjectName("pipeline_step")
        self.gridLayout.addWidget(self.pipeline_step, 4, 1, 1, 1)
        self.label_2 = QtGui.QLabel(NewTask)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 5, 0, 1, 1)
        self.task_name = QtGui.QLineEdit(NewTask)
        self.task_name.setObjectName("task_name")
        self.gridLayout.addWidget(self.task_name, 5, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        spacerItem = QtGui.QSpacerItem(20, 19, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(NewTask)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(NewTask)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), NewTask.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), NewTask.reject)
        QtCore.QMetaObject.connectSlotsByName(NewTask)

    def retranslateUi(self, NewTask):
        NewTask.setWindowTitle(QtGui.QApplication.translate("NewTask", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("NewTask", "<b><big>Create a new Task</big></b>\n"
"<br><br>\n"
"Type in a Task Name and select a Pipeline Step below.\n"
"<br><br>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("NewTask", "Entity", None, QtGui.QApplication.UnicodeUTF8))
        self.entity.setText(QtGui.QApplication.translate("NewTask", "Shot ABC 123", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("NewTask", "Assigned to", None, QtGui.QApplication.UnicodeUTF8))
        self.assigned_to.setText(QtGui.QApplication.translate("NewTask", "Mr John Smith", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("NewTask", "Pipeline Step", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("NewTask", "Task Name", None, QtGui.QApplication.UnicodeUTF8))

