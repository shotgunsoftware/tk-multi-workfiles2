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
import weakref

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .my_task_item_delegate import MyTaskItemDelegate
from ..entity_proxy_model import EntityProxyModel
from ..ui.my_tasks_form import Ui_MyTasksForm
from ..framework_qtwidgets import Breadcrumb
from ..util import map_to_source, get_source_model, monitor_qobject_lifetime

class MyTasksForm(QtGui.QWidget):
    """
    My Tasks widget class
    """

    class _TaskBreadcrumb(Breadcrumb):
        """
        """
        def __init__(self, label, task_id):
            Breadcrumb.__init__(self, label)
            self.task_id = task_id

    # Signal emitted when a task is selected in the tree
    task_selected = QtCore.Signal(object, list)# task, breadcrumb trail

    # Signal emitted when the 'New Task' button is clicked
    create_new_task = QtCore.Signal(object, object)# entity, step

    def __init__(self, tasks_model, allow_task_creation, parent):
        """
        Construction

        :param model:   The Shotgun Model this widget should connect to
        :param parent:  The parent QWidget for this control
        """
        QtGui.QWidget.__init__(self, parent)

        # keep track of the task to select when/if it appears in the model
        self._task_id_to_select = None
        # keep track of the currently selected item
        self._current_item_ref = None

        # set up the UI
        self._ui = Ui_MyTasksForm()
        self._ui.setupUi(self)

        # tmp until we have a usable filter button!
        self._ui.filter_btn.hide()

        self._ui.search_ctrl.set_placeholder_text("Search My Tasks")

        # enable/hide the new task button depending if task creation is allowed:
        if allow_task_creation:
            self._ui.new_task_btn.clicked.connect(self._on_new_task)
            self._ui.new_task_btn.setEnabled(False)
        else:
            self._ui.new_task_btn.hide()

        self._item_delegate = None
        if tasks_model:

            if True:
                # create a filter proxy model between the source model and the task tree view:
                filter_fields = ["content", {"entity":"name"}]
                filter_fields.extend(tasks_model.extra_display_fields)
                filter_model = EntityProxyModel(self, filter_fields)
                monitor_qobject_lifetime(filter_model, "My Tasks filter model")
                filter_model.rowsInserted.connect(self._on_filter_model_rows_inserted)
                filter_model.setSourceModel(tasks_model)
                self._ui.task_tree.setModel(filter_model)

                # create the item delegate - make sure we keep a reference to the delegate otherwise 
                # things may crash later on!
                self._item_delegate = MyTaskItemDelegate(tasks_model.extra_display_fields, self._ui.task_tree)
                monitor_qobject_lifetime(self._item_delegate)
                self._ui.task_tree.setItemDelegate(self._item_delegate)

                self._ui.search_ctrl.search_edited.connect(self._on_search_changed)
            else:
                self._ui.task_tree.setModel(tasks_model)

        # connect to the selection model for the tree view:
        selection_model = self._ui.task_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    def shut_down(self):
        """
        Clean up as much as we can to help the gc once the widget is finished with.
        """
        signals_blocked = self.blockSignals(True)
        try:
            # clear any references:
            self._current_item_ref = None

            # clear the selection:
            if self._ui.task_tree.selectionModel():
                self._ui.task_tree.selectionModel().clear()

            # detach the filter model from the view:
            view_model = self._ui.task_tree.model()
            if view_model:
                self._ui.task_tree.setModel(None)
                if isinstance(view_model, EntityProxyModel):
                    view_model.setSourceModel(None)

            # detach and clean up the item delegate:
            self._ui.task_tree.setItemDelegate(None)
            if self._item_delegate:
                self._item_delegate.setParent(None)
                self._item_delegate.deleteLater()
                self._item_delegate = None

        finally:
            self.blockSignals(signals_blocked)

    def select_task(self, task_id):
        """
        Select the specified task in the list.  If the list is still being populated then the
        selection will happen when an item representing the entity appears in the model.

        Note that this doesn't emit a task_selected signal

        :param task_id: The id of the Shotgun Task to select
        :returns:       True if an item is selected, otherwise False
        """
        # track the selected task - this allows the task to be selected when
        # it appears in the model if the model hasn't been fully populated yet:
        self._task_id_to_select = task_id

        # reset the current selection without emitting a signal:
        prev_selected_item = self._reset_selection()
        self._current_item_ref = None

        # try to update the selection:
        self._update_selection(prev_selected_item)

    def get_selection(self):
        """
        Get the currently selected task as well as the breadcrumb trail that represents 
        the path for the selection.

        :returns:   A Tuple containing the task and breadcrumb trail of the current selection:
                        (task, breadcrumb_trail)

                    - task is a Shotgun entity dictionary
                    - breadcrumb_trail is a list of Breadcrumb instances
        """
        item = self._get_selected_item()
        task = item.get_sg_data() if item else None
        breadcrumb_trail = self._build_breadcrumb_trail()
        return (task, breadcrumb_trail)

    def navigate_to(self, breadcrumb_trail):
        """
        Update the selection to match the specified breadcrumb trail

        :param breadcrumb_trail:    A list of Breadcrumb instances that represent
                                    an item in the task list.
        """
        task_id_to_select = None
        if breadcrumb_trail and isinstance(breadcrumb_trail[-1], MyTasksForm._TaskBreadcrumb):
            task_id_to_select = breadcrumb_trail[-1].task_id

        self.select_task(task_id_to_select)

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------

    def _get_selected_item(self):
        """
        Get the currently selected item.

        :returns:   The currently selected model item if any
        """
        item = None
        indexes = self._ui.task_tree.selectionModel().selectedIndexes()
        if len(indexes) == 1:
            item = self._item_from_index(indexes[0])
        return item

    def _reset_selection(self):
        """
        Reset the current selection, returning the currently selected item if any.  This
        doesn't result in any signals being emitted by the current selection model.

        :returns:   The selected item before the selection was reset if any
        """
        prev_selected_item = self._get_selected_item()
        # reset the current selection without emitting any signals:
        self._ui.task_tree.selectionModel().reset()
        self._update_ui()
        return prev_selected_item

    def _item_from_index(self, idx):
        """
        Find the corresponding model item from the specified index.  This handles
        the indirection introduced by the filter model.

        :param idx: The model index to find the item for
        :returns:   The item in the model represented by the index
        """
        src_idx = map_to_source(idx)
        return src_idx.model().itemFromIndex(src_idx)

    def _update_selection(self, prev_selected_item=None):
        """
        Update the selection to either the to-be-selected task if set or the current item if known.  The 
        current item is the item that was last selected but which may no longer be visible in the view due 
        to filtering.  This allows it to be tracked so that the selection state is correctly restored when 
        it becomes visible again.
        """
        tasks_model = get_source_model(self._ui.task_tree.model())
        if not tasks_model:
            return

        # we want to make sure we don't emit any signals whilst we are 
        # manipulating the selection:
        signals_blocked = self.blockSignals(True)
        try:
            item = None
            if tasks_model and self._task_id_to_select:
                # we know about a task that we should try to select:
                item = tasks_model.item_from_entity("Task", self._task_id_to_select)
            elif self._current_item_ref:
                # an item was previously selected and we are tracking it
                item = self._current_item_ref()

            if item:
                view_model = self._ui.task_tree.model()
                idx = item.index()
                if isinstance(view_model, QtGui.QAbstractProxyModel):
                    idx = view_model.mapFromSource(idx)
                if idx.isValid():
                    # scroll to the item in the list:
                    self._ui.task_tree.scrollTo(idx)

                    # select the item as the current item:
                    self._ui.task_tree.selectionModel().setCurrentIndex(idx, QtGui.QItemSelectionModel.SelectCurrent)

        finally:
            self.blockSignals(signals_blocked)

            # if the selection is different to the previously selected item then we
            # will emit a task_selected signal:
            selected_item = self._get_selected_item()
            if id(selected_item) != id(prev_selected_item):
                # emit a selection changed signal:
                task = None
                if selected_item:
                    task = selected_item.get_sg_data()

                # emit the signal
                self._emit_task_selected(task)
                self.repaint()

    def _on_search_changed(self, search_text):
        """
        Slot triggered when the search text has been changed.

        :param search_text: The new search text
        """
        # clear the selection before changing anything - reset clears the selection
        # without emitting any signals:
        prev_selected_item = self._reset_selection()
        try:
            # update the proxy filter search text:
            self._update_filter(search_text)
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(prev_selected_item)
                
    def _on_selection_changed(self, selected, deselected):
        """
        Slot triggered when the selection changes

        :param selected:    QItemSelection containing any newly selected indexes
        :param deselected:  QItemSelection containing any newly deselected indexes
        """
        # get the task for the current selection:
        task = None
        item = None
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            item = self._item_from_index(selected_indexes[0])
            task = item.get_sg_data() if item else None

        # update the UI:
        self._update_ui()

        # make sure we track the current task:
        self._current_item_ref = weakref.ref(item) if item else None

        if self._current_item_ref:
            # clear the task-to-select as the current item now takes precedence
            self._task_id_to_select = None

        # emit selection_changed signal:
        self._emit_task_selected(task)

    def _on_filter_model_rows_inserted(self, parent, first, last):
        """
        Slot triggered when new rows are inserted into the filter model.  This allows us
        to update the selection if a new row matches the task-to-select.

        :param parent_idx:  The parent model index of the rows that were inserted
        :param first:       The first row id inserted
        :param last:        The last row id inserted
        """
        # try to select the current task from the new items in the model:
        prev_selected_item = self._get_selected_item()
        self._update_selection(prev_selected_item)

    def _update_ui(self):
        """
        Update the UI to reflect the current selection, etc.
        """
        enable_new_tasks = False
        if len(self._ui.task_tree.selectionModel().selectedIndexes()) == 1:
            # something is selected so we can add a new task
            enable_new_tasks = True

        self._ui.new_task_btn.setEnabled(enable_new_tasks)

    def _update_filter(self, search_text):
        """
        Update the search text in the filter model.

        :param search_text: The new search text to update the filter model with
        """
        view_model = self._ui.task_tree.model()
        if not isinstance(view_model, EntityProxyModel):
            return

        # update the proxy filter search text:
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        view_model.setFilterRegExp(filter_reg_exp)

    def _on_new_task(self):
        """
        Slot triggered when the new task button is clicked.  Extracts the necessary
        information from the widget and raises a uniform signal for containing code
        """
        # get the currently selected task:
        item = self._get_selected_item()
        task = item.get_sg_data() if item else None
        if not task:
            return

        entity = task.get("entity")
        if not entity:
            return
        step = task.get("step")

        self.create_new_task.emit(entity, step)

    def _build_breadcrumb_trail(self):
        """
        """
        breadcrumbs = []
        item = self._get_selected_item()
        task = item.get_sg_data() if item else None
        if task:
            entity = task.get("entity")
            if entity:
                breadcrumbs.append(Breadcrumb("<b>%s</b> %s" % (entity["type"], entity["name"])))
            step = task.get("step")
            if step:
                breadcrumbs.append(Breadcrumb("<b>Step</b> %s" % step["name"]))

            # finally, add task breadcrumb:
            breadcrumbs.append(MyTasksForm._TaskBreadcrumb("<b>Task</b> %s" % task["content"], task["id"]))

        return breadcrumbs

    def _emit_task_selected(self, task):
        """
        """
        breadcrumbs = self._build_breadcrumb_trail()
        self.task_selected.emit(task, breadcrumbs)
