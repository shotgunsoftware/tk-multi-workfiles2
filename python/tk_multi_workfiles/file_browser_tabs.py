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
Tab widget that will act as the container widget for the various
work file/publish list views
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

class FileBrowserTabs(QtGui.QTabWidget):
    """
    """
        
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QTabWidget.__init__(self, parent)
        