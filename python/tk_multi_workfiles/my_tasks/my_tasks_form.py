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
    
    task_selected = QtCore.Signal(object)
    create_new_task = QtCore.Signal(object)
    
    def __init__(self, model, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_MyTasksForm()
        self._ui.setupUi(self)
        
        self._ui.search_ctrl.set_placeholder_text("Search My Tasks")
        
        # connect up controls:
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)
        self._ui.new_task_btn.clicked.connect(self._on_new_task)
        self._ui.new_task_btn.setEnabled(False)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = ShotgunModelOverlayWidget(None, self._ui.task_tree)
        self._overlay_widget.set_model(model)

        # create a filter proxy model between the source model and the task tree view:
        self._filter_model = EntityProxyModel(["content", {"entity":"name"}], self)
        self._filter_model.setSourceModel(model)
        self._ui.task_tree.setModel(self._filter_model)

        item_delegate = MyTaskItemDelegate(self._ui.task_tree)
        self._ui.task_tree.setItemDelegate(item_delegate)

        # connect to the selection model for the tree view:
        selection_model = self._ui.task_tree.selectionModel()
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
            selected_index = self._filter_model.mapToSource(selected_indexes[0])
            
        self._ui.new_task_btn.setEnabled(selected_index != None)
            
        # emit selection_changed signal:            
        self.task_selected.emit(selected_index)
        
    def _on_new_task(self):
        """
        """
        if not self._filter_model:
            return
        
        selected_index = None
        selected_indexes = self._ui.task_tree.selectionModel().selectedIndexes()
        if len(selected_indexes) != 1:
            return
        
        # extract the selected model index from the selection:
        selected_index = self._filter_model.mapToSource(selected_indexes[0])
        
        self.create_new_task.emit(selected_index)
        
        
        
                