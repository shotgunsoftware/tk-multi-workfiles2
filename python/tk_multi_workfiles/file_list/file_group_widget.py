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

views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")
GroupWidgetBase = views.GroupWidgetBase

spinner_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "spinner_widget")
SpinnerWidget = spinner_widget.SpinnerWidget

from ..file_model import FileModel
from ..ui.file_group_widget import Ui_FileGroupWidget

class FileGroupWidget(GroupWidgetBase):
    """
    """
    def __init__(self, parent=None):
        """
        Construction
        """
        GroupWidgetBase.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileGroupWidget()
        self._ui.setupUi(self)
        
        self._ui.expand_check_box.stateChanged.connect(self._on_expand_checkbox_state_changed)
        
        # replace the spinner widget with our SpinnerWidget widget:
        proxy_widget = self._ui.spinner
        proxy_size = proxy_widget.geometry()
        proxy_min_size = proxy_widget.minimumSize()
        
        spinner_widget = SpinnerWidget(self)
        spinner_widget.setMinimumSize(proxy_min_size)
        spinner_widget.setGeometry(proxy_size)        

        layout = self._ui.horizontalLayout
        idx = layout.indexOf(proxy_widget)
        layout.removeWidget(proxy_widget)
        layout.insertWidget(idx, spinner_widget)
        
        self._ui.spinner.setParent(None)
        self._ui.spinner.deleteLater()
        self._ui.spinner = spinner_widget
        
        self._show_msg = False

    def set_item(self, model_idx):
        """
        """
        label = model_idx.data()
        self._ui.expand_check_box.setText(label)
        
        # update if the spinner should be visible or not:
        search_status = model_idx.data(FileModel.SEARCH_STATUS_ROLE)
        if search_status == None:
            search_status = FileModel.SEARCH_COMPLETED
            
        # show the spinner if needed:
        self._ui.spinner.setVisible(search_status == FileModel.SEARCHING)
        
        search_msg = ""
        if search_status == FileModel.SEARCHING:
            search_msg = "Searching for files..."
        elif search_status == FileModel.SEARCH_COMPLETED:
            if not model_idx.model().hasChildren(model_idx):
                search_msg = "No files found!"
        elif search_status == FileModel.SEARCH_FAILED:
            search_msg = model_idx.data(FileModel.SEARCH_MSG_ROLE) or ""
        self._ui.msg_label.setText(search_msg)
                        
        self._show_msg = bool(search_msg)
                        
        show_msg = self._show_msg and self._ui.expand_check_box.checkState() == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)

    def set_expanded(self, expand=True):
        """
        """
        if (self._ui.expand_check_box.checkState() == QtCore.Qt.Checked) != expand:
            self._ui.expand_check_box.setCheckState(QtCore.Qt.Checked if expand else QtCore.Qt.Unchecked)

    def _on_expand_checkbox_state_changed(self, state):
        """
        """
        show_msg = self._show_msg and state == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)
        
        self.toggle_expanded.emit(state != QtCore.Qt.Unchecked)
    