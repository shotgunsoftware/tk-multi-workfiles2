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

from .ui.navigation_widget import Ui_NavigationWidget

class NavigationWidget(QtGui.QWidget):
    """
    """
    navigate = QtCore.Signal(object)

    class _DestinationInfo(object):
        def __init__(self, label, destination):
            self.label = label
            self.destination = destination

    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        self._destinations = []
        self._current_idx = 0

        # set up the UI
        self._ui = Ui_NavigationWidget()
        self._ui.setupUi(self)

        self._ui.nav_home_btn.clicked.connect(self._on_nav_home_clicked)
        self._ui.nav_prev_btn.clicked.connect(self._on_nav_prev_clicked)
        self._ui.nav_next_btn.clicked.connect(self._on_nav_next_clicked)
        
        self._update_ui()

    def add_destination(self, label, destination):
        """
        """
        new_destination_info = NavigationWidget._DestinationInfo(label, destination)
        self._destinations = self._destinations[:self._current_idx+1] + [new_destination_info]
        self._current_idx = len(self._destinations)-1
        self._update_ui()
        
    def _on_nav_home_clicked(self):
        """
        """
        if not self._destinations:
            return

        self._current_idx = 0
        destination_info = self._destinations[self._current_idx]
        self.navigate.emit(destination_info.destination)
        self._update_ui()

    def _on_nav_prev_clicked(self):
        """
        """
        if not self._destinations or self._current_idx == 0:
            return

        self._current_idx = self._current_idx - 1
        destination_info = self._destinations[self._current_idx]
        self.navigate.emit(destination_info.destination)
        self._update_ui()
        
    def _on_nav_next_clicked(self):
        """
        """
        if self._current_idx >= (len(self._destinations) - 1):
            return

        self._current_idx = self._current_idx + 1
        destination_info = self._destinations[self._current_idx]
        self.navigate.emit(destination_info.destination)
        self._update_ui()
        
    def _update_ui(self):
        """
        """
        self._ui.nav_home_btn.setEnabled(len(self._destinations) > 0)
        self._ui.nav_prev_btn.setEnabled(self._current_idx > 0)
        self._ui.nav_next_btn.setEnabled(self._current_idx < (len(self._destinations) - 1))



