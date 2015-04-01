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
import weakref

import sgtk
from sgtk.platform.qt import QtCore, QtGui

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

overlay_module = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
ShotgunModelOverlayWidget = overlay_module.ShotgunModelOverlayWidget

from ..ui.entity_tree_form import Ui_EntityTreeForm
from .entity_tree_proxy_model import EntityTreeProxyModel


class EntityTreeForm(QtGui.QWidget):
    """
    """
    
    entity_selected = QtCore.Signal(object)# selection details
    create_new_task = QtCore.Signal(object, object)# entity, step
    
    def __init__(self, entity_model, search_label, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._collapse_steps_with_tasks = True
        self._current_entity = None
        self._current_item = None
        
        self._expanded_items = set()
        self._processed_root_items = set()
        
        # set up the UI
        self._ui = Ui_EntityTreeForm()
        self._ui.setupUi(self)
        
        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        
        # connect up controls:
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)
        
        if entity_model and entity_model.get_entity_type() == "Task":
            self._ui.new_task_btn.clicked.connect(self._on_new_task)
            self._ui.new_task_btn.setEnabled(False)
            self._ui.my_tasks_cb.toggled.connect(self._on_my_tasks_only_toggled)
        else:
            self._ui.new_task_btn.hide()
            self._ui.my_tasks_cb.hide()
            
        self._ui.entity_tree.expanded.connect(self._on_item_expanded)
        self._ui.entity_tree.collapsed.connect(self._on_item_collapsed)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = overlay_module.ShotgunModelOverlayWidget(None, self._ui.entity_tree)
        self._overlay_widget.set_model(entity_model)

        # create a filter proxy model between the source model and the task tree view:
        self._filter_model = EntityTreeProxyModel(["content", {"entity":"name"}], self)
        self._filter_model.rowsInserted.connect(self._on_model_rows_inserted)
        self._filter_model.setSourceModel(entity_model)
        self._ui.entity_tree.setModel(self._filter_model)
        self._expand_root_rows()

        # connect to the selection model for the tree view:
        selection_model = self._ui.entity_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    def select_entity(self, entity_type, entity_id):
        """
        """
        # track the selected entity - this allows the entity to be selected when
        # it appears in the model even if the model hasn't been fully populated yet:
        self._current_entity = {"type":entity_type, "id":entity_id}
        self._current_item = None
        return self._select_current_entity(clear_filter=True, 
                                           clear_selection_if_not_found=True)

    def get_selection_details(self):
        """
        :returns:   {"label":label, "entity":entity, "children":[children]}
        """
        # get the currently selected index:
        selected_indexes = self._ui.entity_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) != 1:
            return {}
        
        return self._get_entity_details(selected_indexes[0])

    # ------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------

    def _get_entity_details(self, idx):
        """
        :returns: {"label":label, "entity":entity, "children":[children]}
        """
        if not idx.isValid():
            return {}

        item = self._item_from_index(idx)
        if not item:
            return {}
        
        # get details for this item:
        label = item.text()
        src_model = self._filter_model.sourceModel()
        entity = src_model.get_entity(item)
        
        # get details for children:
        children = []
        collapsed_children = []
        
        for row in range(self._filter_model.rowCount(idx)):
            child_idx = self._filter_model.index(row, 0, idx)
            child_item = self._item_from_index(child_idx)
            if not child_item:
                continue
            
            child_label = child_item.text()
            child_entity = src_model.get_entity(child_item)
            children.append({"label":child_label, "entity":child_entity})
            
            if self._collapse_steps_with_tasks and child_entity and child_entity["type"] == "Step":
                # see if grand-child is actually a task:
                for child_row in range(self._filter_model.rowCount(child_idx)):
                    grandchild_idx = self._filter_model.index(child_row, 0, child_idx)
                    grandchild_item = self._item_from_index(grandchild_idx)
                    if not grandchild_item:
                        continue
                    
                    grandchild_label = grandchild_item.text()
                    grandchild_entity = src_model.get_entity(grandchild_item)
                    if grandchild_entity and grandchild_entity["type"] == "Task":
                        # found a task under a step so we can safely collapse tasks to steps!
                        collapsed_child_label = "%s - %s" % (child_label, grandchild_label)
                        collapsed_children.append({"label":collapsed_child_label, "entity":grandchild_entity})

        if collapsed_children:
            # prefer collapsed children instead of children if we have them
            children = collapsed_children
        elif self._collapse_steps_with_tasks and entity and entity["type"] == "Step":
            # it's possible that entity is actually a Step and the Children are all tasks - if this is
            # the case then update the child entities to be 'collapsed' and clear the entity on the Step
            # item:
            for child in children:
                child_label = child["label"]
                child_entity = child["entity"]
                if child_entity and child_entity["type"] == "Task":
                    collapsed_child_label = "%s - %s" % (label, child_label)
                    collapsed_children.append({"label":collapsed_child_label, "entity":child_entity})
                    
            if collapsed_children:
                entity = None
                children = collapsed_children
        
        return {"label":label, "entity":entity, "children":children}

    def _on_search_changed(self, search_text):
        """
        """
        self._ui.entity_tree.selectionModel().reset()
        self._update_ui()
        try:        
            # update the proxy filter search text:
            self._update_filter(search_text)
        finally:
            self._select_current_entity(clear_filter=False, clear_selection_if_not_found=False)
        
    def _on_my_tasks_only_toggled(self, checked):
        """
        """
        self._ui.entity_tree.selectionModel().reset()
        self._update_ui()
        try:        
            self._filter_model.only_show_my_tasks = checked
        finally:
            self._select_current_entity(clear_filter=False, clear_selection_if_not_found=False)
        
    def _update_filter(self, search_text):
        """
        """
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self._filter_model.setFilterRegExp(filter_reg_exp)
        
    def _select_current_entity(self, clear_filter, clear_selection_if_not_found):
        """
        """
        # we want to make sure we don't emit any signals whilst we are 
        # manipulating the selection:
        prev_signals_blocked = self.blockSignals(True)
        try:
            item = None
            if self._current_item:
                item = self._current_item()
                
            if not item and self._current_entity:
                src_model = self._filter_model.sourceModel()
                if src_model.get_entity_type() == self._current_entity["type"]:
                    item = src_model.item_from_entity(self._current_entity["type"], self._current_entity["id"])
                
            if item:
                self._current_item = weakref.ref(item)
                                
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
                    # make sure the item is expanded and visible in the tree:
                    self._ui.entity_tree.scrollTo(idx)

                    # select the item:
                    selection_flags = QtGui.QItemSelectionModel.Clear | QtGui.QItemSelectionModel.SelectCurrent 
                    self._ui.entity_tree.selectionModel().select(idx, selection_flags)
                    
                    # update the UI:
                    self._update_ui()
                    
                    return True
            
            # if we got this far then we didn't find the task for some reason
            if clear_selection_if_not_found:
                self._ui.entity_tree.selectionModel().clear()
                # update the UI:
                self._update_ui()

            return False
        finally:
            self.blockSignals(prev_signals_blocked)
        
    def _update_ui(self):
        """
        """
        enable_new_tasks = False

        selected_indexes = self._ui.entity_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) == 1:
            item = self._item_from_index(selected_indexes[0])
            entity = self._filter_model.sourceModel().get_entity(item)
            #if entity and entity.get("type") in ("Step", "Task"):
            if entity and entity["type"] != "Step":
                if entity["type"] == "Task":
                    if entity.get("entity"):
                        enable_new_tasks = True
                else:
                    enable_new_tasks = True

        self._ui.new_task_btn.setEnabled(enable_new_tasks)
        
    def _on_selection_changed(self, selected, deselected):
        """
        """
        selection_details = {}
        item = None
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            selection_details = self._get_entity_details(selected_indexes[0])
            item = self._item_from_index(selected_indexes[0])

        # update the UI
        self._update_ui()

        # keep track of the current item:
        self._current_item = weakref.ref(item) if item else None
        self._current_entity = None
        
        # emit selection_changed signal:
        self.entity_selected.emit(selection_details)
        
    def _on_model_rows_inserted(self, parent_idx, first, last):
        """
        """
        self._ui.entity_tree.setUpdatesEnabled(False)
        try:
            if parent_idx and parent_idx.isValid():
                # update the expanded state of the parent item:
                item = self._item_from_index(parent_idx)
                if item and weakref.ref(item) in self._expanded_items:
                    self._ui.entity_tree.expand(parent_idx)
                    
            # step through all new rows updating expanded state:
            for row in range(first, last+1):
                idx = self._filter_model.index(row, 0, parent_idx)
                # recursively step through all children of the new row:
                self._fix_expanded_state_r(idx)
        finally:
            self._ui.entity_tree.setUpdatesEnabled(True)

    def _fix_expanded_state_r(self, idx):
        """
        """
        # update the expanded state of this item:
        item = self._item_from_index(idx)
        if item:
            ref = weakref.ref(item)
            if not idx.parent().isValid():
                # this is a root item
                if ref not in self._processed_root_items:
                    self._processed_root_items.add(ref)
                    self._expanded_items.add(ref)

            if ref in self._expanded_items:
                self._ui.entity_tree.expand(idx)

        # iterate through all children:
        for row in range(0, self._filter_model.rowCount(idx)):
            child_idx = idx.child(row, 0)
            self._fix_expanded_state_r(child_idx)

    def _expand_root_rows(self):
        """
        """
        self._ui.entity_tree.setUpdatesEnabled(False)
        try:
            for row in range(self._filter_model.rowCount()):
                idx = self._filter_model.index(row, 0)
                item = self._item_from_index(idx)
                if not item:
                    continue
    
                ref = weakref.ref(item)
                if ref in self._processed_root_items:
                    continue
                    
                self._processed_root_items.add(ref)
                self._ui.entity_tree.expand(idx)
        finally:
            self._ui.entity_tree.setUpdatesEnabled(True)

    def _item_from_index(self, idx):
        """
        """
        src_idx = self._filter_model.mapToSource(idx)
        return self._filter_model.sourceModel().itemFromIndex(src_idx)
            
    def _on_item_expanded(self, idx):
        """
        """
        item = self._item_from_index(idx)
        if not item:
            return
        self._expanded_items.add(weakref.ref(item))
    
    def _on_item_collapsed(self, idx):
        """
        """
        item = self._item_from_index(idx)
        if not item:
            return
        self._expanded_items.discard(weakref.ref(item))
            
        
    def _on_new_task(self):
        """
        """
        if not self._filter_model:
            return
        
        selected_index = None
        selected_indexes = self._ui.entity_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) != 1:
            return
        
        # extract the selected model index from the selection:
        selected_index = self._filter_model.mapToSource(selected_indexes[0])

        # determine the currently selected entity:
        entity_model = selected_index.model()
        entity_item = entity_model.itemFromIndex(selected_index)
        entity = entity_model.get_entity(entity_item)
        if not entity:
            return

        if entity["type"] == "Step":
            # can't create tasks on steps!
            return

        step = None
        if entity["type"] == "Task":
            step = entity.get("step")
            entity = entity.get("entity")
            if not entity:
                return

        # and emit the signal for this entity:
        self.create_new_task.emit(entity, step)

