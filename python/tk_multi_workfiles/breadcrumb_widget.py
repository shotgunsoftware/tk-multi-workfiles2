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
from sgtk.platform.qt import QtCore, QtGui

from .ui.breadcrumb_widget import Ui_BreadcrumbWidget

class Breadcrumb(object):
    def __init__(self, label):
        self._label = label

    @property
    def label(self):
        return self._label

class BreadcrumbWidget(QtGui.QWidget):
    """
    """
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_BreadcrumbWidget()
        self._ui.setupUi(self)
        
        self._ui.path_label.setText("")
        
    def set(self, breadcrumbs):
        """
        """
        # build a single path from the list of crumbs:
        path = "<span style='color:#2C93E2'> &#9656; </span>".join([crumb.label for crumb in breadcrumbs])
        
        # and update the label:
        self._ui.path_label.setText(path)
