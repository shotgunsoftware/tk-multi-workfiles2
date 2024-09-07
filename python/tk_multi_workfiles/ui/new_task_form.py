# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_task_form.ui'
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


class Ui_NewTaskForm(object):
    def setupUi(self, NewTaskForm):
        if not NewTaskForm.objectName():
            NewTaskForm.setObjectName(u"NewTaskForm")
        NewTaskForm.resize(380, 270)
        NewTaskForm.setMinimumSize(QSize(380, 270))
        self.verticalLayout = QVBoxLayout(NewTaskForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(20)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(12, 12, 12, 4)
        self.label_3 = QLabel(NewTaskForm)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.label_3)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(20)
        self.gridLayout.setVerticalSpacing(6)
        self.assigned_to = QLabel(NewTaskForm)
        self.assigned_to.setObjectName(u"assigned_to")

        self.gridLayout.addWidget(self.assigned_to, 7, 2, 1, 1)

        self.label_6 = QLabel(NewTaskForm)
        self.label_6.setObjectName(u"label_6")
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_6.setFont(font)

        self.gridLayout.addWidget(self.label_6, 7, 0, 1, 1)

        self.label_4 = QLabel(NewTaskForm)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.gridLayout.addWidget(self.label_4, 8, 0, 1, 1)

        self.pipeline_step = QComboBox(NewTaskForm)
        self.pipeline_step.setObjectName(u"pipeline_step")

        self.gridLayout.addWidget(self.pipeline_step, 1, 2, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.gridLayout.addItem(self.verticalSpacer_3, 6, 0, 1, 1)

        self.entity = QLabel(NewTaskForm)
        self.entity.setObjectName(u"entity")

        self.gridLayout.addWidget(self.entity, 8, 2, 1, 1)

        self.label = QLabel(NewTaskForm)
        self.label.setObjectName(u"label")
        self.label.setFont(font)

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.label_2 = QLabel(NewTaskForm)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.task_name = QLineEdit(NewTaskForm)
        self.task_name.setObjectName(u"task_name")

        self.gridLayout.addWidget(self.task_name, 0, 2, 1, 1)

        self.gridLayout.setColumnStretch(2, 1)

        self.verticalLayout_2.addLayout(self.gridLayout)

        self.warning = QLabel(NewTaskForm)
        self.warning.setObjectName(u"warning")
        self.warning.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.warning)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 11, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.break_line = QFrame(NewTaskForm)
        self.break_line.setObjectName(u"break_line")
        self.break_line.setFrameShape(QFrame.HLine)
        self.break_line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.break_line)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(12, 8, 12, 12)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cancel_btn = QPushButton(NewTaskForm)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.horizontalLayout.addWidget(self.cancel_btn)

        self.create_btn = QPushButton(NewTaskForm)
        self.create_btn.setObjectName(u"create_btn")

        self.horizontalLayout.addWidget(self.create_btn)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(2, 1)
        QWidget.setTabOrder(self.task_name, self.pipeline_step)
        QWidget.setTabOrder(self.pipeline_step, self.create_btn)
        QWidget.setTabOrder(self.create_btn, self.cancel_btn)

        self.retranslateUi(NewTaskForm)
        self.cancel_btn.clicked.connect(NewTaskForm.close)

        self.create_btn.setDefault(True)

        QMetaObject.connectSlotsByName(NewTaskForm)
    # setupUi

    def retranslateUi(self, NewTaskForm):
        NewTaskForm.setWindowTitle(QCoreApplication.translate("NewTaskForm", u"Form", None))
        self.label_3.setText(QCoreApplication.translate("NewTaskForm", u"Create a new Task using the Name and Pipeline Step entered below.", None))
        self.assigned_to.setText(QCoreApplication.translate("NewTaskForm", u"Mr John Smith", None))
        self.label_6.setText(QCoreApplication.translate("NewTaskForm", u"Assigned to:", None))
        self.label_4.setText(QCoreApplication.translate("NewTaskForm", u"Entity:", None))
#if QT_CONFIG(accessibility)
        self.pipeline_step.setAccessibleName(QCoreApplication.translate("NewTaskForm", u"Pipeline Step", None))
#endif // QT_CONFIG(accessibility)
        self.entity.setText(QCoreApplication.translate("NewTaskForm", u"Shot ABC 123", None))
        self.label.setText(QCoreApplication.translate("NewTaskForm", u"Pipeline Step:", None))
        self.label_2.setText(QCoreApplication.translate("NewTaskForm", u"Task Name:", None))
#if QT_CONFIG(accessibility)
        self.task_name.setAccessibleName(QCoreApplication.translate("NewTaskForm", u"Task Name", None))
#endif // QT_CONFIG(accessibility)
        self.warning.setText("")
        self.cancel_btn.setText(QCoreApplication.translate("NewTaskForm", u"Cancel", None))
        self.create_btn.setText(QCoreApplication.translate("NewTaskForm", u"Create", None))
    # retranslateUi
