# Copyright (c) 2015 Shotgun Software Inc.
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
from sgtk import TankError
from sgtk.platform.qt import QtGui, QtCore

class Action(object):
    """
    """
    def __init__(self, label):
        """
        """
        self._app = sgtk.platform.current_bundle()
        self._label = label
        
    @property
    def label(self):
        return self._label
    
    def execute(self, parent_ui):
        """
        """
        raise NotImplementedError("Implementation of _execute() method missing for action '%s'" % self.label)

class SeparatorAction(Action):
    """
    """
    def __init__(self):
        Action.__init__(self, "---")

    def execute(self, parent_ui):
        # do nothing!
        pass