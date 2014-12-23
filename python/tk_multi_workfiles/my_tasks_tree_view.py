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

class MyTasksTreeView(QtGui.QTreeView):
    """
    """
    
    def __init__(self, model, parent=None):
        """
        Construction
        """
        QtGui.QTreeView.__init__(self, parent)
        
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        
        