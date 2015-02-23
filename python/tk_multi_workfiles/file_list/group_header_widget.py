# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from ..ui.group_header_widget import Ui_GroupHeaderWidget

class GroupHeaderWidget(QtGui.QWidget):
    """
    """
    
    expand = QtCore.Signal()
    collapse = QtCore.Signal()
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_GroupHeaderWidget()
        self._ui.setupUi(self)
        
    @property
    def label(self):
        return self._ui.title_label.text()
    
    @label.setter
    def label(self, value):
        self._ui.title_label.setText(value)
        
        