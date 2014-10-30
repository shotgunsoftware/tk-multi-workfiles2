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

class FileOpenForm(QtGui.QWidget):
    """
    UI for opening a publish or work file
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self.__ui = Ui_FileOpenForm()
        self.__ui.setupUi(self)