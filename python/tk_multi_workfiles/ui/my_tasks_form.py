# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'my_tasks_form.ui'
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


from ..framework_qtwidgets import SearchWidget

class Ui_MyTasksForm(object):
    def setupUi(self, MyTasksForm):
        if not MyTasksForm.objectName():
            MyTasksForm.setObjectName(u"MyTasksForm")
        MyTasksForm.resize(359, 541)
        self.verticalLayout = QVBoxLayout(MyTasksForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 6, 2, 2)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, -1, 2, 1)
        self.filter_btn = QToolButton(MyTasksForm)
        self.filter_btn.setObjectName(u"filter_btn")
        self.filter_btn.setStyleSheet(u"")
        self.filter_btn.setPopupMode(QToolButton.MenuButtonPopup)
        self.filter_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.filter_btn.setAutoRaise(False)

        self.horizontalLayout.addWidget(self.filter_btn)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.new_task_btn = QPushButton(MyTasksForm)
        self.new_task_btn.setObjectName(u"new_task_btn")

        self.horizontalLayout.addWidget(self.new_task_btn)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(1, -1, 1, -1)
        self.search_ctrl = SearchWidget(MyTasksForm)
        self.search_ctrl.setObjectName(u"search_ctrl")
        self.search_ctrl.setMinimumSize(QSize(0, 20))
        self.search_ctrl.setStyleSheet(u"#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.horizontalLayout_2.addWidget(self.search_ctrl)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.task_tree = QTreeView(MyTasksForm)
        self.task_tree.setObjectName(u"task_tree")
        self.task_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_tree.setProperty("showDropIndicator", False)
        self.task_tree.setRootIsDecorated(False)
        self.task_tree.header().setVisible(False)

        self.verticalLayout.addWidget(self.task_tree)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(MyTasksForm)

        QMetaObject.connectSlotsByName(MyTasksForm)
    # setupUi

    def retranslateUi(self, MyTasksForm):
        MyTasksForm.setWindowTitle(QCoreApplication.translate("MyTasksForm", u"Form", None))
        self.filter_btn.setText(QCoreApplication.translate("MyTasksForm", u"Filter", None))
        self.new_task_btn.setText(QCoreApplication.translate("MyTasksForm", u"+ New Task", None))
    # retranslateUi
