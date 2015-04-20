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

overlay_module = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
ShotgunModelOverlayWidget = overlay_module.ShotgunModelOverlayWidget

from .my_task_item_delegate import MyTaskItemDelegate
from ..entity_proxy_model import EntityProxyModel
from ..ui.my_tasks_form import Ui_MyTasksForm

class MyTasksForm(QtGui.QWidget):
    """
    My Tasks widget class
    """

    # Signal emitted when a task is selected in the tree
    task_selected = QtCore.Signal(object)# task

    # Signal emitted when the 'New Task' button is clicked
    create_new_task = QtCore.Signal(object, object)# entity, step

    def __init__(self, model, parent=None):
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
        self._ui.new_task_btn.setEnabled(False)

        # connect up controls:
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)
        self._ui.new_task_btn.clicked.connect(self._on_new_task)

        # create the overlay 'busy' widget:
        self._overlay_widget = ShotgunModelOverlayWidget(None, self._ui.task_tree)
        self._overlay_widget.set_model(model)

        # create a filter proxy model between the source model and the task tree view:
        self._filter_model = EntityProxyModel(["content", {"entity":"name"}], self)
        self._filter_model.rowsInserted.connect(self._on_filter_model_rows_inserted)
        self._filter_model.setSourceModel(model)
        self._ui.task_tree.setModel(self._filter_model)

        item_delegate = MyTaskItemDelegate(self._ui.task_tree)
        self._ui.task_tree.setItemDelegate(item_delegate)

        # connect to the selection model for the tree view:
        selection_model = self._ui.task_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

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
        self._ui.task_tree.selectionModel().reset()
        self._current_item_ref = None
        self._update_ui()

        # try to update the selection:
        return self._update_selection(clear_filter_if_not_found=True)

    def get_selected_task(self):
        """
        Get the currently selected task

        :returns:   A Shotgun entity dictionary with details about the currently
                    selected task
        """
        # get the currently selected index:
        selected_indexes = self._ui.task_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) != 1:
            return None

        item = self._item_from_index(selected_indexes[0])
        return item.get_sg_data() if item else None

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------

    def _item_from_index(self, idx):
        """
        Find the corresponding model item from the specified index.  This handles
        the indirection introduced by the filter model.

        :param idx: The model index to find the item for
        :returns:   The item in the model represented by the index
        """
        src_idx = self._filter_model.mapToSource(idx)
        return self._filter_model.sourceModel().itemFromIndex(src_idx)

    def _update_selection(self, clear_filter_if_not_found):
        """
        Update the selection to either the to-be-selected task if set or the current item if known.  The 
        current item is the item that was last selected but which may no longer be visible in the view due 
        to filtering.  This allows it to be tracked so that the selection state is correctly restored when 
        it becomes visible again.

        :param clear_filter_if_not_found:       If True and the item to select isn't currently visible then
                                                the filter will be cleared before trying to select the item 
                                                again
        :returns:                               True if the item is found and selected, otherwise False
        """
        # we want to make sure we don't emit any signals whilst we are 
        # manipulating the selection:
        signals_blocked = self.blockSignals(True)
        try:
            item = None
            if self._task_id_to_select:
                # we know about a task that we should try to select:
                src_model = self._filter_model.sourceModel()
                item = src_model.item_from_entity("Task", self._task_id_to_select)
            elif self._current_item_ref:
                # an item was previously selected and we are tracking it
                item = self._current_item_ref()

            if item:
                # try to get an index from the current filtered model:
                idx = self._filter_model.mapFromSource(item.index())
                if not idx.isValid() and clear_filter_if_not_found:
                    # lets try clearing the filter and looking again:
                    self._update_filter("")
                    signals_blocked = self._ui.search_ctrl.blockSignals(True)
                    try:
                        self._ui.search_ctrl.clear()
                    finally:
                        self._ui.search_ctrl.blockSignals(signals_blocked)

                    # take another look for the index in the filtered model:
                    idx = self._filter_model.mapFromSource(item.index())

                if idx.isValid():
                    # scroll to the item in the list:
                    self._ui.task_tree.scrollTo(idx)

                    # select the item:
                    selection_flags = QtGui.QItemSelectionModel.Clear | QtGui.QItemSelectionModel.SelectCurrent
                    self._ui.task_tree.selectionModel().select(idx, selection_flags)

                    return True

            return False
        finally:
            self.blockSignals(signals_blocked)

    def _on_search_changed(self, search_text):
        """
        Slot triggered when the search text has been changed.

        :param search_text: The new search text
        """
        # clear the selection before changing anything - reset clears the selection
        # without emitting any signals:
        self._ui.task_tree.selectionModel().reset()
        self._update_ui()
        try:
            # update the proxy filter search text:
            self._update_filter(search_text)
        finally:
            # and update the selection - this will restore the original selection if possible.
            self._update_selection(clear_filter_if_not_found=False)
                
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
        self.task_selected.emit(task)
        
    def _on_filter_model_rows_inserted(self, parent, first, last):
        """
        Slot triggered when new rows are inserted into the filter model.  This allows us
        to update the selection if a new row matches the task-to-select.

        :param parent_idx:  The parent model index of the rows that were inserted
        :param first:       The first row id inserted
        :param last:        The last row id inserted
        """
        # try to select the current task from the new items in the model:
        self._update_selection(clear_filter_if_not_found=False)

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
        # update the proxy filter search text:
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self._filter_model.setFilterRegExp(filter_reg_exp)

    def _on_new_task(self):
        """
        Slot triggered when the new task button is clicked.  Extracts the necessary
        information from the widget and raises a uniform signal for containing code
        """
        # get the currently selected task:
        task = self.get_selected_task()
        if not task:
            return

        entity = task.get("entity")
        if not entity:
            return
        step = task.get("step")

        self.create_new_task.emit(entity, step)
