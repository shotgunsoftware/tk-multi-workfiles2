# Copyright (c) 2014 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""

"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

overlay_module = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
ShotgunModelOverlayWidget = overlay_module.ShotgunModelOverlayWidget

from .my_task_item_delegate import MyTaskItemDelegate
from ..entity_proxy_model import EntityProxyModel
from ..ui.my_tasks_form import Ui_MyTasksForm
                  
class MyTasksForm(QtGui.QWidget):
    """
    """
    task_selected = QtCore.Signal(object, object, object)
    create_new_task = QtCore.Signal(object, object, object)
    
    def __init__(self, model, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._current_task_id = None
        
        # set up the UI
        self._ui = Ui_MyTasksForm()
        self._ui.setupUi(self)
        
        # tmp until we have a usable filter button!
        self._ui.filter_btn.hide()
        
        self._ui.search_ctrl.set_placeholder_text("Search My Tasks")
        
        # connect up controls:
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)
        self._ui.new_task_btn.clicked.connect(self._on_new_task)
        self._update_ui(False)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = ShotgunModelOverlayWidget(None, self._ui.task_tree)
        self._overlay_widget.set_model(model)

        # create a filter proxy model between the source model and the task tree view:
        self._filter_model = EntityProxyModel(["content", {"entity":"name"}], self)
        self._filter_model.rowsInserted.connect(self._on_model_rows_inserted)
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
        """
        print "Selecting task %s" % task_id
        
        # track the selected task - this allows the task to be selected when
        # it appears in the model if the model hasn't been fully populated yet:
        self._current_task_id = task_id
        return self._select_current_task(clear_filter=True, 
                                         clear_selection_if_not_found=True)
        
    def get_selected_task_details(self):
        """
        """
        # get the currently selected index:
        selected_indexes = self._ui.task_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) != 1:
            return (None, None, None)
        
        return self._get_task_details(selected_indexes[0])
        
    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------
        
    def _get_task_details(self, idx):
        """
        """
        # extract the selected model index from the selection:
        src_idx = self._filter_model.mapToSource(idx)
        if not src_idx.isValid():
            return (None, None, None)
        
        # get the item for the specified index from the source model:
        item = src_idx.model().itemFromIndex(src_idx)
        
        # and extract the information we need from it:
        sg_data = item.get_sg_data()

        entity = sg_data.get("entity", {})        
        step = sg_data.get("step", {})
        task = {"type":"Task", "id":sg_data["id"], "content":sg_data["content"]}

        return (entity, step, task)
        
    def _select_current_task(self, clear_filter, clear_selection_if_not_found):
        """
        """
        # we want to make sure we don't emit any signals whilst we are 
        # manipulating the selection:
        prev_signals_blocked = self.blockSignals(True)
        try:
            item = None
            if self._current_task_id:
                src_model = self._filter_model.sourceModel()
                item = src_model.item_from_entity("Task", self._current_task_id)
                
            if item:
                # try to get an index from the current filtered model:
                idx = self._filter_model.mapFromSource(item.index())
                if not idx.isValid() and clear_filter:
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
                    
                    # enable the UI:
                    self._update_ui(True)
                    
                    return True
            
            # if we got this far then we didn't find the task for some reason
            if clear_selection_if_not_found:
                self._ui.task_tree.selectionModel().clear()
                # enable the UI:
                self._update_ui(False)
                
            return False
        finally:
            self.blockSignals(prev_signals_blocked)

    def _on_search_changed(self, search_text):
        """
        """
        # clear the selection before changing anything - reset clears the selection
        # without emitting any signals:
        self._ui.task_tree.selectionModel().reset()
        self._update_ui(False)
        try:
            # update the proxy filter search text:
            self._update_filter(search_text)
        finally:
            # reselect the 'current' task if possible:
            self._select_current_task(clear_filter=False, clear_selection_if_not_found=False)
                
    def _on_selection_changed(self, selected, deselected):
        """
        """
        # get the task details for the selection:
        entity = step = task = None
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            entity, step, task = self._get_task_details(selected_indexes[0])
        
        # update the UI:
        self._update_ui(task != None)
        
        # make sure we track the current task:
        self._current_task_id = task["id"] if task else None
            
        # emit selection_changed signal:            
        self.task_selected.emit(entity, step, task)
        
    def _on_model_rows_inserted(self, parent, first, last):
        """
        """
        # try to select the current task from the new items in the model:
        self._select_current_task(clear_filter=False, clear_selection_if_not_found=False)

    def _update_ui(self, have_task):
        """
        """
        self._ui.new_task_btn.setEnabled(have_task)
    
    def _update_filter(self, search_text):
        """
        """
        # update the proxy filter search text:
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self._filter_model.setFilterRegExp(filter_reg_exp)

    def _on_new_task(self):
        """
        """
        entity, step, task = self.get_selected_task_details()
        if not task:
            return
        
        self.create_new_task.emit(entity, step, task)
        
        
        
                