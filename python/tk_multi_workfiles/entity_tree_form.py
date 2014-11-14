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


class EntityTreeForm(QtGui.QWidget):
    """
    """
    create_new_task = QtCore.Signal()
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_EntityTreeForm()
        self._ui.setupUi(self)
        
        # connect up controls:
        self._ui.new_task_btn.clicked.connect(self._on_new_task)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = overlay_module.ShotgunModelOverlayWidget(None, self._ui.entity_tree)
        
    def set_model(self, model):
        """
        """
        self._ui.entity_tree.setModel(model)
        self._overlay_widget.set_model(model)
        
    def _on_new_task(self):
        """
        """
        self.create_new_task.emit()    
    
    
    
    
    
        