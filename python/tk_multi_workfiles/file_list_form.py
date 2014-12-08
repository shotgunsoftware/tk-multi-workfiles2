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

from .file_model import FileModel, FileModelOverlayWidget

from .ui.file_list_form import Ui_FileListForm

class FileListForm(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileListForm()
        self._ui.setupUi(self)
        
        self._overlay_widget = FileModelOverlayWidget(parent = self._ui.view_pages)
        
        self._ui.details_radio_btn.toggled.connect(self._on_view_toggled)
        
                
    def _on_view_toggled(self, checked):
        """
        """
        if self._ui.details_radio_btn.isChecked():
            self._ui.view_pages.setCurrentWidget(self._ui.details_page)
        else:
            self._ui.view_pages.setCurrentWidget(self._ui.list_page)
            
    def set_model(self, model):
        """
        """
        self._ui.file_list_view.setModel(model)
        self._ui.file_details_view.setModel(model)
        self._overlay_widget.set_model(model)
        