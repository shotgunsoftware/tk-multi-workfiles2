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

overlay_module = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
from .entity_proxy_model import EntityProxyModel

class EntityTreeForm(QtGui.QWidget):
    """
    """
    
    entity_selected = QtCore.Signal(object)
    create_new_task = QtCore.Signal()
    
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
        self._ui.new_task_btn.clicked.connect(self._on_new_task)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = overlay_module.ShotgunModelOverlayWidget(None, self._ui.entity_tree)
        self._overlay_widget.set_model(entity_model)

        self._proxy_model = EntityProxyModel(self)
        self._proxy_model.setSourceModel(entity_model)
        self._ui.entity_tree.setModel(self._proxy_model)

        # connect to the selection model for the tree view:
        selection_model = self._ui.entity_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
        
    def _on_selection_changed(self, selected, deselected):
        """
        """
        selected_index = None
        
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            # extract the selected model index from the selection:
            proxy_index = selected_indexes[0]
            selected_index = self._proxy_model.mapToSource(proxy_index)
            
        # emit selection_changed signal:            
        self.entity_selected.emit(selected_index)
        
        
    def _on_new_task(self):
        """
        """
        self.create_new_task.emit()    
    
    
    
    
    
        