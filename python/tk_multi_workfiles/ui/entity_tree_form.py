# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'entity_tree_form.ui'
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


from ..framework_qtwidgets import SearchWidget

from  . import resources_rc

class Ui_EntityTreeForm(object):
    def setupUi(self, EntityTreeForm):
        if not EntityTreeForm.objectName():
            EntityTreeForm.setObjectName(u"EntityTreeForm")
        EntityTreeForm.resize(349, 367)
        self.verticalLayout = QVBoxLayout(EntityTreeForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 6, 2, 2)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, -1, 2, 1)
        self.task_status_combo = QComboBox(EntityTreeForm)
        self.task_status_combo.setObjectName(u"task_status_combo")

        self.horizontalLayout.addWidget(self.task_status_combo)

        self.my_tasks_cb = QCheckBox(EntityTreeForm)
        self.my_tasks_cb.setObjectName(u"my_tasks_cb")

        self.horizontalLayout.addWidget(self.my_tasks_cb)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.new_task_btn = QPushButton(EntityTreeForm)
        self.new_task_btn.setObjectName(u"new_task_btn")

        self.horizontalLayout.addWidget(self.new_task_btn)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(1, -1, 1, -1)
        self.search_ctrl = SearchWidget(EntityTreeForm)
        self.search_ctrl.setObjectName(u"search_ctrl")
        self.search_ctrl.setMinimumSize(QSize(0, 20))
        self.search_ctrl.setStyleSheet(u"#search_ctrl {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.horizontalLayout_2.addWidget(self.search_ctrl)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.entity_tree = QTreeView(EntityTreeForm)
        self.entity_tree.setObjectName(u"entity_tree")
        self.entity_tree.setStyleSheet(u"QTreeView::item {\n"
"padding: 2px;\n"
"}\n"
"\n"
"QTreeView::branch:has-children:!has-siblings:closed,\n"
"QTreeView::branch:closed:has-children:has-siblings  {\n"
"        border-image: none;\n"
"		image: url(:/tk-multi-workfiles2/tree_arrow_collapsed.png);\n"
"}\n"
"\n"
"QTreeView::branch:open:has-children:!has-siblings,\n"
"QTreeView::branch:open:has-children:has-siblings   {\n"
"        border-image: none;\n"
"		image: url(:/tk-multi-workfiles2/tree_arrow_expanded.png);\n"
"}")
        self.entity_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.entity_tree.setProperty("showDropIndicator", False)
        self.entity_tree.setIconSize(QSize(20, 20))
        self.entity_tree.header().setVisible(False)

        self.verticalLayout.addWidget(self.entity_tree)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(EntityTreeForm)

        QMetaObject.connectSlotsByName(EntityTreeForm)
    # setupUi

    def retranslateUi(self, EntityTreeForm):
        EntityTreeForm.setWindowTitle(QCoreApplication.translate("EntityTreeForm", u"Form", None))
        self.task_status_combo.setText(QCoreApplication.translate("EntityTreeForm", u"Task Status", None))
        self.my_tasks_cb.setText(QCoreApplication.translate("EntityTreeForm", u"My Tasks Only", None))
        self.new_task_btn.setText(QCoreApplication.translate("EntityTreeForm", u"+ New Task", None))
#if QT_CONFIG(accessibility)
        self.search_ctrl.setAccessibleName(QCoreApplication.translate("EntityTreeForm", u"Search Entity", None))
#endif // QT_CONFIG(accessibility)
    # retranslateUi
