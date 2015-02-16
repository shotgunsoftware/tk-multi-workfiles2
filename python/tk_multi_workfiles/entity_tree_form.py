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

from .ui.entity_tree_form import Ui_EntityTreeForm

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

overlay_module = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
from .entity_proxy_model import EntityProxyModel

class EntityTreeProxyModel(EntityProxyModel):
    """
    """
    def __init__(self, compare_sg_fields=None, parent=None):
        """
        """
        EntityProxyModel.__init__(self, compare_sg_fields, parent)
        self._only_show_my_tasks = False

    @property
    def only_show_my_tasks(self):
        return self._only_show_my_tasks
    
    @only_show_my_tasks.setter
    def only_show_my_tasks(self, show):
        if self._only_show_my_tasks != show:
            self._only_show_my_tasks = show
            self.invalidateFilter()

    def _is_item_accepted(self, item, parent_accepted):
        """
        """
        if self._only_show_my_tasks:
            
            sg_entity = item.model().get_entity(item)
            if sg_entity and sg_entity["type"] == "Task":
                
                assignees = sg_entity.get("task_assignees", [])
                assignee_ids = [a["id"] for a in assignees if "id" in a]
                
                # make sure that the current user is in this lise of assignees:
                app = sgtk.platform.current_bundle()
                current_user = sgtk.util.get_current_user(app.sgtk)
                
                if not current_user or current_user["id"] not in assignee_ids:
                    # task isn't assigned to the current user so this item
                    # is definitely not accepted!
                    return False

        # fall back to the base implementation:        
        return EntityProxyModel._is_item_accepted(self, item, parent_accepted)


class EntityTreeForm(QtGui.QWidget):
    """
    """
    
    entity_selected = QtCore.Signal(object)
    create_new_task = QtCore.Signal(object)
    
    def __init__(self, entity_model, search_label, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
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
        
        # create the overlay 'busy' widget:
        self._overlay_widget = overlay_module.ShotgunModelOverlayWidget(None, self._ui.entity_tree)
        self._overlay_widget.set_model(entity_model)

        # create a filter proxy model between the source model and the task tree view:
        self._filter_model = EntityTreeProxyModel(["content", {"entity":"name"}], self)
        self._filter_model.setSourceModel(entity_model)
        self._ui.entity_tree.setModel(self._filter_model)

        # connect to the selection model for the tree view:
        selection_model = self._ui.entity_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    def _on_search_changed(self, search_text):
        """
        """
        # update the proxy filter search text:
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self._filter_model.setFilterRegExp(filter_reg_exp)
        
    def _on_selection_changed(self, selected, deselected):
        """
        """
        selected_index = None
        
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            # extract the selected model index from the selection:
            proxy_index = selected_indexes[0]
            selected_index = self._filter_model.mapToSource(proxy_index)
        
        # determine if the new tasks button should be enabled:
        enable_new_tasks = selected_index != None
        if enable_new_tasks:
            
            src_model = self._filter_model
            while src_model and not isinstance(src_model, ShotgunEntityModel):
                if isinstance(src_model, QtGui.QSortFilterProxyModel):
                    src_model = src_model.sourceModel()
                else:
                    src_model = None
                    
            if src_model:
                item = src_model.itemFromIndex(selected_index)
                entity = src_model.get_entity(item)
                if not entity or entity.get("type") == "Step":
                    enable_new_tasks = False
        
        # TODO - button should only be enabled if an entity is selected that has tasks as
        # children in the tree...
        
        self._ui.new_task_btn.setEnabled(enable_new_tasks)
            
        # emit selection_changed signal:            
        self.entity_selected.emit(selected_index)
        
    def _on_my_tasks_only_toggled(self, checked):
        """
        """
        self._filter_model.only_show_my_tasks = checked
        
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
        
        self.create_new_task.emit(selected_index)        
    
    
    
    
    
        