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
from sgtk.platform.qt import QtGui, QtCore

from .file_action import FileAction

class ShowInShotgunAction(FileAction):
    """
    """
    def _open_url_for_published_file(self, file):
        """
        """
        # construct the url:
        published_file_entity_type = sgtk.util.get_published_file_entity_type(self._app.sgtk)
        url = "%s/detail/%s/%d" % (self._app.sgtk.shotgun.base_url, published_file_entity_type, file.published_file_id)
        
        # and open it:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


class ShowPublishInShotgunAction(ShowInShotgunAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        ShowInShotgunAction.__init__(self, "Show Publish in Shotgun", file, file_versions, environment)
        
    def execute(self, parent_ui):
        """
        """
        if not self.file or not self.file.is_published:
            return

        self._open_url_for_published_file(self.file)

class ShowLatestPublishInShotgunAction(ShowInShotgunAction):
    """
    """
    def __init__(self, file, file_versions, environment):
        ShowInShotgunAction.__init__(self, "Show Latest Publish in Shotgun", file, file_versions, environment)
        
    def execute(self, parent_ui):
        """
        """
        publish_versions = [v for v, f in self.file_versions.iteritems() if f.is_published]
        if not publish_versions:
            return
        
        max_publish_version = max(publish_versions)
        self._open_url_for_published_file(self.file_versions[max_publish_version])