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
Qt widget that presents the user with a list of work files and publishes
so that they can choose one to open
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.file_open_form import Ui_FileOpenForm
from .entity_tree_form import EntityTreeForm

class FileOpenForm(QtGui.QWidget):
    """
    UI for opening a publish or work file
    """
    
    @property
    def exit_code(self):
        return self._exit_code    
    
    def __init__(self, init_callback, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileOpenForm()
        self._ui.setupUi(self)
        
        # hook up controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        
        # add my-tasks
                
        # allow callback to initialize UI:
        init_callback(self)
        
    def add_entity_model(self, title, model):
        """
        """
        
        # create a new entity tab for the model:
        entity_form = EntityTreeForm(self)
        entity_form.set_model(model)
        
        self._ui.task_browser_tabs.addTab(entity_form, title)
        

        
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected        
        self.close()
        
        