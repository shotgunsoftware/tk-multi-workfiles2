# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Implementation of the my tasks list widget consisting of a list view displaying the contents
of a Shotgun data model of my tasks, a text search and a filter control.
"""

from sgtk.platform.qt import QtCore, QtGui
from .my_task_item_delegate import MyTaskItemDelegate
from ..util import monitor_qobject_lifetime
from ..entity_tree.entity_tree_form import EntityTreeForm
from .my_tasks_proxy_model import MyTasksProxyModel

class SortFieldWidget( QtGui.QWidget ):

    def __init__(self, text, parent):
        super(SortFieldWidget, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.text = QtGui.QLabel(text, self)
        self.asc_check_box = QtGui.QRadioButton(self)
        self.desc_check_box = QtGui.QRadioButton(self)
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addItem(spacerItem)
        self.layout.addWidget(self.asc_check_box)
        self.layout.addWidget(self.desc_check_box)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(self.layout)

        defaultHLBackground = "#%02x%02x%02x" % self.palette().highlight().color().getRgb()[:3]
        defaultHLText = "#%02x%02x%02x" % self.palette().highlightedText().color().getRgb()[:3]

        highlight = self.palette().highlight().color().name()
        css = "QWidget:hover { background:%s; color: white;} QWidget { padding: 4px;}" % (highlight)
        self.setStyleSheet(css)

        # self.setStyleSheet("QWidget:hover { selection-background-color:%s; color: %s;};" % (defaultHLBackground, defaultHLText))

    def set_sort_dirction(self, direction):
        if direction.lower() == "ascending":
            self.asc_check_box.setChecked(True)
        elif direction.lower() == "descending":
            self.desc_check_box.setChecked(True)

class SortOptionWidget( QtGui.QWidget ):

    def __init__(self, text, parent):
        super(SortOptionWidget, self).__init__(parent)

        self.state = QtGui.QRadioButton(self)
        self.text = QtGui.QLabel(text, self)
        self.options = QtGui.QPushButton("X", self)

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.state)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.options)
        self.layout.setContentsMargins(4, 4, 4, 4)

        highlight = self.palette().highlight().color().name()
        css = "QWidget:hover { background:%s; color: white;} QWidget { padding: 4px;}" % (highlight)
        self.setStyleSheet(css)

        # defaultHLBackground = "#%02x%02x%02x" % self.palette().highlight().color().getRgb()[:3]
        # defaultHLText = "#%02x%02x%02x" % self.palette().highlightedText().color().getRgb()[:3]
        # self.setAutoFillBackground(True)
        # self.setStyleSheet(
        #     "QWidget:hover { selection-background-color:%s; color: %s;};" % (defaultHLBackground, defaultHLText))


class MyTasksForm(EntityTreeForm):
    """
    My Tasks widget class
    """

    def __init__(self, tasks_model, allow_task_creation, parent):
        """
        Construction

        :param model:   The Shotgun Model this widget should connect to
        :param parent:  The parent QWidget for this control
        """
        EntityTreeForm.__init__(
            self, tasks_model, "My Tasks", allow_task_creation, tasks_model.extra_display_fields, parent
        )

        sort_data = tasks_model.sort_data
        self.chosen_sort_option = 0

        if sort_data:

            self._highlighted_action = None
            self._sort_fields_menu = None

            self.sort_model = MyTasksProxyModel(self)
            self.sort_model.filter_by_fields = []
            self.sort_model.setDynamicSortFilter(True)
            self.sort_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
            # we set the sort order, but we may actually perform a different sort order
            # in the proxy model on a per field basis
            self.sort_model.sort(0, QtCore.Qt.AscendingOrder)

            # default to the first sort option.
            sort_option = sort_data[0]
            self._set_sort_option(sort_option)

            sort_options_menu = QtGui.QMenu(self._ui.sort_tbn)
            separator = QtGui.QWidgetAction(sort_options_menu)
            separator.setDefaultWidget(QtGui.QLabel("Presets:"))
            # separator.setSeparator(True)
            # separator.setEnabled(False)
            sort_options_menu.addAction(separator)
            sort_options_menu.triggered.connect(self._on_set_sort_option)
            # sort_options_menu.hovered.connect(self._on_sort_option_hover)

            self._ui.sort_tbn.setMenu(sort_options_menu)
            self._sort_menu_lambdas = []
            alignmentGroup = QtGui.QActionGroup(self)

            for n, sort_option in enumerate(sort_data):

                sort_callable = lambda data=sort_option : self._set_sort_option(data)
                self._sort_menu_lambdas.append(sort_callable)

                sort_option_widget = SortOptionWidget(sort_option["name"], self)

                action = QtGui.QWidgetAction( sort_options_menu)
                # action = QtGui.QAction(sort_option["name"], sort_options_menu)
                action.setCheckable(True)
                if n == 0:
                    action.setChecked(True)
                action.setData(sort_option)
                alignmentGroup.addAction(action)
                action.setDefaultWidget(sort_option_widget)
                # action.triggered.connect(sort_callable)
                sort_options_menu.addAction(action)

                # sort_fields_menu = QtGui.QMenu(self._ui.sort_tbn)
                # # sort_fields_menu.triggered.connect(self._set_sort_option_test)
                # action.setMenu(sort_fields_menu)
                #
                # # now loop over the fields and create a sub menu for them to all direction change.
                # for sort_field in sort_option["sort_fields"]:
                #     # sort_field_widget = SortFieldWidget(sort_field["field_name"], self)
                #     # sort_field_widget.set_sort_dirction(sort_field.get("direction","ascending"))
                #
                #     # field_action = QtGui.QWidgetAction(sort_fields_menu)
                #     # field_action.setDefaultWidget(sort_field_widget)
                #     field_action = QtGui.QAction(sort_field["field_name"], sort_fields_menu)
                #     sort_fields_menu.addAction(field_action)


            monitor_qobject_lifetime(self.sort_model, "My Tasks Sort model")
            self.sort_model.setSourceModel(tasks_model)
            self._ui.entity_tree.setModel(self.sort_model)

            self._ui.sort_tbn.show()

        # There is no need for the my tasks toggle.
        self._ui.my_tasks_cb.hide()

        # Sets an item delete to show a list of tiles for tasks instead of nodes in a tree.
        self._item_delegate = None
        # create the item delegate - make sure we keep a reference to the delegate otherwise
        # things may crash later on!
        self._item_delegate = MyTaskItemDelegate(tasks_model.extra_display_fields, self._ui.entity_tree)
        monitor_qobject_lifetime(self._item_delegate)
        self._ui.entity_tree.setItemDelegate(self._item_delegate)



    def shut_down(self):
        """
        Clean up as much as we can to help the gc once the widget is finished with.
        """
        signals_blocked = self.blockSignals(True)
        try:
            EntityTreeForm.shut_down(self)
            # detach and clean up the item delegate:
            self._ui.entity_tree.setItemDelegate(None)
            if self._item_delegate:
                self._item_delegate.setParent(None)
                self._item_delegate.deleteLater()
                self._item_delegate = None
        finally:
            self.blockSignals(signals_blocked)

    def _on_sort_option_hover(self, action):
        print "here"

        if self._highlighted_action == action:
            return
        else:
            if self._sort_fields_menu is not None:
                self._sort_fields_menu.close()

            self._highlighted_action = action

            sort_option = action.data()

            # self._sort_fields_menu = QtGui.QMenu(action.menu())
            # self._sort_fields_menu.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
            # self._sort_fields_menu.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
            # # self._sort_fields_menu.triggered.connect(self._set_sort_option_test)
            # # action.setMenu(self._sort_fields_menu)
            #
            # # now loop over the fields and create a sub menu for them to all direction change.
            # for sort_field in sort_option["sort_fields"]:
            #     sort_field_widget = SortFieldWidget(sort_field["field_name"], self)
            #     sort_field_widget.set_sort_dirction(sort_field.get("direction","ascending"))
            #
            #     field_action = QtGui.QWidgetAction(self._sort_fields_menu)
            #     field_action.setDefaultWidget(sort_field_widget)
            #     self._sort_fields_menu.addAction(field_action)
            #
            # self._sort_fields_menu.show()


    def _on_set_sort_option(self, action):
        self._set_sort_option(action.data())

    def _set_sort_option(self, sort_option):
        sort_fields = sort_option['sort_fields']
        self.sort_model.primary_sort_field = sort_fields[0]

        if len(sort_fields) > 1:
            self.sort_model.sort_by_fields = sort_fields[1:]
        else:
            self.sort_model.sort_by_fields = []

        self._ui.sort_tbn.setText("Sort By: %s" % (sort_option["name"]))
        self.sort_model.invalidate()