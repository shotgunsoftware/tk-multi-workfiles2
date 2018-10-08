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

    def __init__(self, text, action, parent):
        super(SortFieldWidget, self).__init__(parent)

        self.action = action

        self.setAutoFillBackground(True)
        self.text = QtGui.QPushButton(text, self)
        self.text.setFlat(True)
        self.text.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum, ))
        # self.text.setMinimumHeight(32)
        css = "padding-left: 7; padding-right: 15; padding-top: 4; padding-bottom: 4; Text-align: left; border: 0px;"
        self.text.setStyleSheet(css)
        self.asc_check_box = QtGui.QRadioButton(self)
        self.desc_check_box = QtGui.QRadioButton(self)
        self.asc_check_box.setStyleSheet("padding-left: 4; padding-right: 4; padding-top: 4; padding-bottom: 4;")
        self.desc_check_box.setStyleSheet("padding-left: 4; padding-right: 4; padding-top: 4; padding-bottom: 4;")
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.asc_check_box)
        self.layout.addWidget(self.desc_check_box)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self._triggerAction = lambda: self.action.activate(QtGui.QAction.ActionEvent.Trigger)
        self.asc_check_box.toggled.connect(self._triggerAction)
        self.desc_check_box.toggled.connect(self._triggerAction)
        self.text.pressed.connect(self._swap_direction)

        # defaultHLBackground = "#%02x%02x%02x" % self.palette().highlight().color().getRgb()[:3]
        # defaultHLText = "#%02x%02x%02x" % self.palette().highlightedText().color().getRgb()[:3]

        # highlight = self.palette().highlight().color().name()
        # css = "QWidget:hover { background:%s; color: white;} QWidget { padding: 4px;}" % (highlight)
        # self.setStyleSheet(css)

        # self.setStyleSheet("QWidget:hover { selection-background-color:%s; color: %s;};" % (defaultHLBackground, defaultHLText))

    def _swap_direction(self):
        if self.asc_check_box.isChecked():
            self.desc_check_box.setChecked(True)
        else:
            self.asc_check_box.setChecked(True)

    def set_sort_direction(self, direction):
        if direction.lower() == "ascending":
            self.asc_check_box.setChecked(True)
        elif direction.lower() == "descending":
            self.desc_check_box.setChecked(True)

class SortOptionWidget( QtGui.QWidget ):

    def __init__(self, text, action, parent):
        super(SortOptionWidget, self).__init__(parent)
        self.action = action

        self.state = QtGui.QRadioButton(text, self)
        self.options = QtGui.QToolButton( self) #QtGui.QIcon(":/tk-multi-workfiles2/sorting_menu.png"),
        self.options.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.options.setCheckable(True)

        self.state.setSizePolicy( QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding ,QtGui.QSizePolicy.Minimum,))
        self._triggerAction = lambda : self.action.activate(QtGui.QAction.ActionEvent.Trigger)
        self.state.toggled.connect(self._triggerAction)
        # we are monkey patching the mousePressEvent so that we can capture when the button is pressed without waiting
        # for the menu to close. The pressed signal only gets called once the menu is closed.
        self.options.mousePressEvent = self.sort_options_mouse_event

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.state)
        self.layout.addWidget(self.options)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        highlight = self.palette().highlight().color().name()
        css = "QWidget { padding-left: 7; padding-right: 15; padding-top: 4; padding-bottom: 4;}"
        self.state.setStyleSheet(css)
        self.setStyleSheet("QWidget:hover { background: %s; color: white; }" % (highlight))

    def sort_options_mouse_event(self, event):
        self.state.setChecked(True)
        # Call the base class's implementation of the mousePressEvent
        QtGui.QToolButton.mousePressEvent(self.options, event)


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
        self.tasks_model = tasks_model
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

            sort_options_menu.addAction(separator)
            sort_options_menu.triggered.connect(self._on_set_sort_option)

            self._ui.sort_tbn.setMenu(sort_options_menu)
            self._sort_menu_lambdas = []

            # Create button group for all our action radio buttons to belong to
            radioButtonGroup = QtGui.QButtonGroup(self)

            for n, sort_option in enumerate(sort_data):

                sort_callable = lambda data=sort_option : self._set_sort_option(data)
                self._sort_menu_lambdas.append(sort_callable)

                # Create a QWidgetAction so that
                sort_option_action = QtGui.QWidgetAction( sort_options_menu )

                # Now create the custom widget
                sort_option_widget = SortOptionWidget(sort_option["name"], sort_option_action, sort_options_menu)

                # the radio buttons are all in different widgets so here we group them under the same QButtonGroup
                radioButtonGroup.addButton(sort_option_widget.state)

                sort_option_action.setCheckable(True)
                if n == 0:
                    sort_option_widget.state.setChecked(True)

                sort_option_action.setData(sort_option['name'])
                sort_option_action.setDefaultWidget(sort_option_widget)
                sort_option_action.triggered.connect(sort_callable)
                sort_options_menu.addAction(sort_option_action)

                # fields
                sort_fields_menu = QtGui.QMenu(sort_option_widget.options)
                sort_option_widget.options.setMenu(sort_fields_menu)
                sort_fields_menu.triggered.connect(self._on_change_sort_direction)

                # now loop over the fields and create a sub menu for them to all direction change.
                for sort_field in sort_option["sort_fields"]:
                    field_action = QtGui.QWidgetAction(sort_fields_menu)

                    sort_field_widget = SortFieldWidget(sort_field["display_name"], field_action, sort_option_widget)
                    sort_field_widget.set_sort_direction(sort_field.get("direction", "ascending"))

                    field_action.setDefaultWidget(sort_field_widget)

                    data = {
                        "field_name": sort_field["field_name"],
                        "sort_option_name": sort_option["name"],
                    }

                    field_action.setData(data)

                    # field_action = QtGui.QAction(sort_field["field_name"], sort_fields_menu)
                    sort_fields_menu.addAction(field_action)

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

    def _get_sort_option(self, sort_option_name):
        """
        This method returns the sort option data from the task model for the given sort option name (preset name.)

        :param sort_option_name: The name of the sort option preset to retrieve the data for
        :return: dict - containing the sort_option data
        """
        return next( (sort_option for sort_option in self.tasks_model.sort_data
                      if sort_option['name'] == sort_option_name), None)

    def _on_change_sort_direction(self, action):
        """
        This will be called when the sort option field has its sort direction changed. It update the sort_data on the
        task_model with the new direction for the field and then trigger the sorting to be reevaluated.

        :param action: QWidgetAction - for the field action
        :return: None
        """
        # The action should have the sort option name and field name stored in a dictionary on the action data.
        # as defined when the menu gets built
        data = action.data()

        # get the specific sort option data from the task model
        sort_option = self._get_sort_option(data["sort_option_name"])
        field_name = data["field_name"]

        for num, field_data in enumerate(sort_option['sort_fields']):
            if field_data['field_name'] != field_name:
                continue

            # update the sort model field's direction
            if action.defaultWidget().asc_check_box.isChecked():
                sort_option["sort_fields"][num]["direction"] = "Ascending"
            else:
                sort_option["sort_fields"][num]["direction"] = "Descending"
            break

        # trigger a resort
        self._set_sort_option(sort_option)

    def _on_set_sort_option(self, action):
        """
        This method is called by the current sort option preset being changed. This will then trigger a resorting
        of the menu based on the action representing the preset that triggered it.
        :param action: QActionWidget - for the sort option preset
        :return: None
        """
        # gather the sort data from the action and then call the _set_sort_option method to apply to the model
        sort_option = self._get_sort_option(action.data())
        self._set_sort_option(sort_option)

    def _set_sort_option(self, sort_option):
        """
        When passed a sort option it updates the sort model to sort by the new parameters
        :param sort_option: dict - The sort option data for a specific preset from the task model
        :return: None
        """

        sort_fields = sort_option['sort_fields']
        self.sort_model.primary_sort_field = sort_fields[0]

        if len(sort_fields) > 1:
            self.sort_model.sort_by_fields = sort_fields[1:]
        else:
            self.sort_model.sort_by_fields = []

        self._ui.sort_tbn.setText("Sort By: %s" % (sort_option["name"]))
        # now trigger a resort in the UI
        self.sort_model.invalidate()