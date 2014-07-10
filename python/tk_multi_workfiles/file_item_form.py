# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
from tank.platform.qt import QtGui, QtCore

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

from .ui.file_item_form import Ui_FileItemForm

class FileItemForm(browser_widget.ListItem):
    """
    Custom browser widget list item that contains and additional 'locked' icon
    for non-editable/readon-only items
    """
    def __init__(self, app, worker, parent=None):
        """
        """
        browser_widget.ListItem.__init__(self, app, worker, parent)
        
    def set_is_editable(self, editable, not_editable_reason = None):
        """
        Set if the file this item represents is editable - if not editable 
        then an additional padlock icon is shown with it's tooltip indicating 
        the reason why.
        """
        self.ui.locked_label.setVisible(not editable)
        self.ui.locked_label.setToolTip(not_editable_reason or "")
        
    def _setup_ui(self):
        """
        Setup the Qt UI.  Typically, this just instantiates the UI class
        and calls its .setupUi(self) method.
        
        :returns:    The constructed QWidget
        """
        ui = Ui_FileItemForm()
        ui.setupUi(self)
        return ui