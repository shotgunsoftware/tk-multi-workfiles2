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

from ..file_model import FileModel
from ..ui.file_group_widget import Ui_FileGroupWidget
from ..util import get_model_data, get_model_str
from ..framework_qtwidgets import SpinnerWidget, GroupWidgetBase
from ..user_cache import g_user_cache
from ..errors import MissingTemplatesError
from ..actions.new_file_action import NewFileAction

class FileGroupWidget(GroupWidgetBase):
    """
    """

    def __init__(self, parent):
        """
        Construction
        """
        GroupWidgetBase.__init__(self, parent)

        # set up the UI
        self._ui = Ui_FileGroupWidget()
        self._ui.setupUi(self)
        
        self.setFocusProxy(self._ui.expand_check_box)
        
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

        proxy_widget.setParent(None)
        proxy_widget.deleteLater()

        self._ui.spinner = spinner_widget

        self._show_msg = False

    def set_item(self, model_idx):
        """
        """
        group_name = get_model_str(model_idx)
        work_area = get_model_data(model_idx, FileModel.WORK_AREA_ROLE)
        search_status = get_model_data(model_idx, FileModel.SEARCH_STATUS_ROLE)

        # update group and user names:
        self._ui.title_label.setText(group_name)
        display_user = (work_area and work_area.contains_user_sandboxes)
        if display_user:
            user_name = "Unknown's"
            if work_area.context and work_area.context.user:
                if g_user_cache.current_user and g_user_cache.current_user["id"] == work_area.context.user["id"]:
                    user_name = "My"
                else: 
                    user_name = "%s's" % work_area.context.user.get("name", "Unknown")
            self._ui.user_label.setText("(%s Files)" % user_name)
            self._ui.user_label.show()
        else:
            self._ui.user_label.hide()

        # update if the spinner should be visible or not:
        if search_status == None:
            search_status = FileModel.SEARCH_COMPLETED

        # Show the spinner if needed:
        self._ui.spinner.setVisible(search_status == FileModel.SEARCHING)

        # update the status message:
        idx_has_children = model_idx.model().hasChildren(model_idx)
        search_msg = ""
        if search_status == FileModel.SEARCHING and not idx_has_children:
            search_msg = "Searching for files..."
        elif work_area and search_status == FileModel.SEARCH_COMPLETED and not idx_has_children:
            templates = work_area.get_missing_templates()
            if not work_area.are_settings_loaded():
                search_msg = "Shotgun Workfiles hasn't been setup."
            elif templates:
                search_msg = MissingTemplatesError.generate_missing_templates_message(templates)
            else:
                search_msg = "No files found."
        elif search_status == FileModel.SEARCH_FAILED:
            search_msg = get_model_str(model_idx, FileModel.SEARCH_MSG_ROLE)
        self._ui.msg_label.setText(search_msg)

        self._show_msg = bool(search_msg)

        show_msg = self._show_msg and self._ui.expand_check_box.checkState() == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)

    def set_expanded(self, expand=True):
        """
        """
        if (self._ui.expand_check_box.checkState() == QtCore.Qt.Checked) != expand:
            self._ui.expand_check_box.setCheckState(QtCore.Qt.Checked if expand else QtCore.Qt.Unchecked)

    def mouseReleaseEvent(self, event):
        """
        """
        self._ui.expand_check_box.toggle()

    def _on_expand_checkbox_state_changed(self, state):
        """
        """
        show_msg = self._show_msg and state == QtCore.Qt.Checked
        self._ui.msg_label.setVisible(show_msg)
        
        self.toggle_expanded.emit(state != QtCore.Qt.Unchecked)
