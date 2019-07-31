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
        self.direction_checkbox = QtGui.QCheckBox(self, text)
        self.direction_checkbox.setObjectName("direction_checkbox")
        self.direction_checkbox.setText(text)
        self.direction_checkbox.setLayoutDirection(QtCore.Qt.RightToLeft)

        ss = """
#direction_checkbox {
    padding-left: 7;
    padding-right: 7;
    padding-top: 4;
    padding-bottom: 4;
}

#direction_checkbox::indicator:checked
{image: url(:/tk-multi-workfiles2/sort_order_ascending.png);}

#direction_checkbox::indicator:checked:hover
{image: url(:/tk-multi-workfiles2/sort_order_ascending_hover.png);}

#direction_checkbox::indicator:checked:pressed
{image: url(:/tk-multi-workfiles2/sort_order_ascending_pressed.png);}


#direction_checkbox::indicator:unchecked
{image: url(:/tk-multi-workfiles2/sort_order_descending.png);}

#direction_checkbox::indicator:unchecked:hover
{image: url(:/tk-multi-workfiles2/sort_order_descending_hover.png);}

#direction_checkbox::indicator:unchecked:pressed
{image: url(:/tk-multi-workfiles2/sort_order_descending_pressed.png);}

"""

        self.direction_checkbox.setStyleSheet(ss)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.direction_checkbox)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self._triggerAction = lambda: self.action.activate(QtGui.QAction.ActionEvent.Trigger)
        self.direction_checkbox.toggled.connect(self._triggerAction)

    @property
    def sort_direction(self):
        """
        returns the state of the widget's sorting direction.
        A value of either "ascending" or "descending" will be given.
        :return: str
        """
        if self.direction_checkbox.isChecked():
            return "ascending"
        else:
            return "descending"

    @sort_direction.setter
    def sort_direction(self, direction):
        """
        Sets the sorting direction on the widget for the field.
        :param direction: str of either "ascending" or "descending"
        :return:
        """
        if direction.lower() == "ascending":
            self.direction_checkbox.setChecked(True)
        elif direction.lower() == "descending":
            self.direction_checkbox.setChecked(False)
        else:
            raise ValueError("Unrecognised direction: \"%s\", please provide either ascending or descending" % direction)

class SortOptionWidget( QtGui.QWidget ):

    def __init__(self, text, action, parent):
        super(SortOptionWidget, self).__init__(parent)
        self.action = action

        self.state = QtGui.QRadioButton(text, self)
        self.options = QtGui.QToolButton( self )
        self.options.setIcon(QtGui.QIcon(":/tk-multi-workfiles2/cog.png"))
        self.options.setArrowType(QtCore.Qt.NoArrow)
        self.options.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.options.setCheckable(True)

        self.state.setSizePolicy( QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding ,QtGui.QSizePolicy.Minimum,))
        self._triggerAction = lambda : self.action.activate(QtGui.QAction.ActionEvent.Trigger)
        self.state.toggled.connect(self._triggerAction)
        # we are monkey patching the mousePressEvent so that we can capture when the button is pressed without waiting
        # for the menu to close. The pressed signal only gets called once the menu is closed.
        self.options.mousePressEvent = self._sort_options_mouse_event

        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.state)
        self.layout.addWidget(self.options)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        highlight = self.palette().highlight().color().name()
        css = "QWidget { padding-left: 7; padding-right: 15; padding-top: 4; padding-bottom: 4;}"
        self.state.setStyleSheet(css)
        self.setStyleSheet("QWidget:hover { background: %s; color: white; }" % (highlight))

    def _sort_options_mouse_event(self, event):
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
            self._current_sort_option = None

            self.sort_model = MyTasksProxyModel(self)
            self.sort_model.filter_by_fields = []
            self.sort_model.setDynamicSortFilter(True)
            self.sort_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
            # we set the sort order, but we may actually perform a different sort order
            # in the proxy model on a per field basis
            self.sort_model.sort(0, QtCore.Qt.AscendingOrder)

            self._sort_options_menu = QtGui.QMenu(self._ui.sort_tbn)

            self._ui.sort_tbn.setMenu(self._sort_options_menu)
            self._sort_menu_lambdas = []

            # Create button group for all our action radio buttons to belong to
            self._optionRadioButtonGroup = QtGui.QButtonGroup(self)
            self._fieldsSortDirRadioButtonGroup = QtGui.QButtonGroup(self)

            highlight = self.palette().highlight().color().name()
            css = "QWidget { padding-left: 7; padding-right: 15; padding-top: 4; padding-bottom: 4;} " \
                  "QWidget:hover { background: %s; color: white; }" % (highlight)

            # used to record the progress through the menu building, it will be set to the following in order
            # start, fields, presets
            build_menu_progress = "start"

            # The list of sort data is pre sorted by type, ie fields at the top presets bellow
            # This allows us to build the menu in order
            for n, sort_option in enumerate(sort_data):

                if sort_option["type"] == "field":

                    if build_menu_progress == "start":
                        field_heading = QtGui.QWidgetAction(self._sort_options_menu)
                        field_heading.setDefaultWidget(QtGui.QLabel("Fields:"))
                        field_heading.setEnabled(False)
                        self._sort_options_menu.addAction(field_heading)

                        build_menu_progress = "fields"

                    sort_callable = lambda option=sort_option: self._sort_by_sort_option(option)

                    field_action = QtGui.QWidgetAction(self._sort_options_menu)
                    rbtn = QtGui.QRadioButton(sort_option["display_name"])
                    rbtn.clicked.connect(sort_callable)

                    rbtn.setStyleSheet(css)
                    self._optionRadioButtonGroup.addButton(rbtn)
                    field_action.setDefaultWidget(rbtn)
                    data = {
                        "field_name": sort_option["field_name"],
                        "sort_option_name": sort_option["display_name"],
                    }

                    field_action.setData(data)
                    self._sort_options_menu.addAction(field_action)

                elif sort_option["type"] == "preset":
                    if build_menu_progress == "fields":

                        sep = QtGui.QAction(self._sort_options_menu)
                        sep.setSeparator(True)
                        self._sort_options_menu.addAction(sep)

                        ascending_action = QtGui.QWidgetAction(self._sort_options_menu)
                        self.asc_rbtn = QtGui.QRadioButton("Ascending")
                        self.asc_rbtn.setStyleSheet(css)
                        self.asc_rbtn.setChecked(True)
                        # We only need to connect to the signal of the ascending radio button and not the descending
                        # as their are only two radio buttons in this group, and the toggle of one will cover both.
                        sort_callable = lambda: self._sort_by_sort_option(self._current_sort_option)
                        self.asc_rbtn.toggled.connect(sort_callable)
                        self._fieldsSortDirRadioButtonGroup.addButton(self.asc_rbtn)
                        ascending_action.setDefaultWidget(self.asc_rbtn)
                        self._sort_options_menu.addAction(ascending_action)

                        descending_action = QtGui.QWidgetAction(self._sort_options_menu)
                        self.desc_rbtn = QtGui.QRadioButton("Descending")
                        self.desc_rbtn.setStyleSheet(css)
                        self._fieldsSortDirRadioButtonGroup.addButton(self.desc_rbtn)
                        descending_action.setDefaultWidget(self.desc_rbtn)
                        self._sort_options_menu.addAction(descending_action)

                        presets_heading = QtGui.QWidgetAction(self._sort_options_menu)
                        presets_heading.setDefaultWidget(QtGui.QLabel("Presets:"))
                        presets_heading.setEnabled(False)
                        self._sort_options_menu.addAction(presets_heading)

                        build_menu_progress = "presets"

                    self.build_preset_action(sort_option)

            monitor_qobject_lifetime(self.sort_model, "My Tasks Sort model")
            self.sort_model.setSourceModel(tasks_model)
            self._ui.entity_tree.setModel(self.sort_model)
            # connect to the selection model for the tree view:
            selection_model = self._ui.entity_tree.selectionModel()
            if selection_model:
                selection_model.selectionChanged.connect(self._on_selection_changed)

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

    def build_preset_action(self, data ):
        menu = self._sort_options_menu
        sort_callable = lambda option=data: self._sort_by_sort_option(option)
        self._sort_menu_lambdas.append(sort_callable)

        # Create a QWidgetAction so that
        sort_option_action = QtGui.QWidgetAction(menu)

        # Now create the custom widget
        sort_option_widget = SortOptionWidget(data["display_name"], sort_option_action, menu)

        # the radio buttons are all in different widgets so here we group them under the same QButtonGroup
        self._optionRadioButtonGroup.addButton(sort_option_widget.state)
        if data.get("default", False):
            sort_option_widget.state.setChecked(True)
            self._sort_by_sort_option(data)

        sort_option_action.setCheckable(True)

        sort_option_action.setData({"sort_option_name":data["display_name"],
                                   "sort_option_type":data["type"]})
        sort_option_action.setDefaultWidget(sort_option_widget)
        sort_option_action.triggered.connect(sort_callable)
        menu.addAction(sort_option_action)

        # fields
        sort_fields_menu = QtGui.QMenu(sort_option_widget.options)
        sort_option_widget.options.setMenu(sort_fields_menu)
        sort_fields_menu.triggered.connect(self._on_change_sort_direction)

        # now loop over the fields and create a sub menu for them to all direction change.
        for sort_field in data["sort_fields"]:
            self.build_field_action(sort_fields_menu, sort_field, data)

    def build_field_action(self, menu, data, sort_option ):
        field_action = QtGui.QWidgetAction(menu)

        sort_field_widget = SortFieldWidget(data["display_name"], field_action, menu)
        sort_field_widget.sort_direction = data.get("direction", "ascending")

        field_action.setDefaultWidget(sort_field_widget)

        action_data = {
            "field_name": data["field_name"],
            "sort_option_name": sort_option["display_name"],
            "sort_option_type": sort_option["type"]
        }

        field_action.setData(action_data)

        # field_action = QtGui.QAction(sort_field["field_name"], sort_fields_menu)
        menu.addAction(field_action)

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

    def _get_sort_option(self, sort_option_name, sort_option_type):
        """
        This method returns the sort option data from the task model for the given sort option name (preset name.)

        :param sort_option_name: The name of the sort option preset to retrieve the data for
        :return: dict - containing the sort_option data
        """
        return next( (sort_option for sort_option in self.tasks_model.sort_data
                      if sort_option["display_name"] == sort_option_name and
                      sort_option["type"] == sort_option_type), None)

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
        sort_option = self._get_sort_option(data["sort_option_name"], data["sort_option_type"])
        field_name = data["field_name"]

        for num, field_data in enumerate(sort_option["sort_fields"]):
            if field_data["field_name"] != field_name:
                continue

            # update the sort model field's directionn
            sort_option["sort_fields"][num]["direction"] = action.defaultWidget().sort_direction
            break

        # trigger a resort
        self._sort_by_sort_option(sort_option)

    def _sort_by_sort_option(self, sort_option):
        """
        When passed a sort option it updates the sort model to sort by the new parameters
        :param sort_option: dict - The sort option data for a specific preset from the task model
        :return: None
        """
        if sort_option["type"] == "field":
            # set the sort direction on the field based on the direction action menu items widgets status
            sort_option['direction'] = "ascending" if self.asc_rbtn.isChecked() else "descending"
            sort_fields = [sort_option]
        elif sort_option["type"] == "preset":
            sort_fields = sort_option["sort_fields"]

        self.sort_model.primary_sort_field = sort_fields[0]
        self.sort_model.sort_by_fields = sort_fields[1:] if len(sort_fields) > 1 else []

        self._ui.sort_tbn.setText("Sort By: %s" % (sort_option["display_name"]))
        # now trigger a resort in the UI
        self.sort_model.invalidate()
        self._current_sort_option = sort_option