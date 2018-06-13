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
from ..entity_proxy_model import EntityProxyModel
from sgtk.platform.qt import QtCore

from ..user_cache import g_user_cache

class EntityTreeProxyModel(EntityProxyModel):
    """
    Proxy model that handles searching and sorting of the
    left hand side entity hierarchies.
    """

    def __init__(self, parent, compare_sg_fields):
        """
        """
        EntityProxyModel.__init__(self, parent, compare_sg_fields)
        self._only_show_my_tasks = False

        # set proxy to auto sort alphabetically
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.sort(0, QtCore.Qt.AscendingOrder)

    #@property
    def _get_only_show_my_tasks(self):
        return self._only_show_my_tasks
    #@only_show_my_tasks.setter
    def _set_only_show_my_tasks(self, show):
        if self._only_show_my_tasks != show:
            # We're forcing a load of the model's data here to ensure we have
            # everything in memory that's required to properly filter the tree.
            # Since this my tasks checkbox feature is only available when we're
            # NOT using a deferred-query model, everything we need from Shotgun
            # is already here and we just need to populate the model with the
            # full tree of items prior to filtering.
            self.sourceModel().ensure_data_is_loaded()
            self._only_show_my_tasks = show
            self.invalidateFilter()
    only_show_my_tasks=property(_get_only_show_my_tasks, _set_only_show_my_tasks)

    def _is_row_accepted(self, src_row, src_parent_idx, parent_accepted):
        """
        """
        if self._only_show_my_tasks:
            # filter out any tasks that aren't assigned to the current user:
            current_user = g_user_cache.current_user
            if not current_user:
                return False

            src_idx = self.sourceModel().index(src_row, 0, src_parent_idx)
            if not src_idx.isValid():
                return False

            item = src_idx.model().itemFromIndex(src_idx)
            sg_entity = src_idx.model().get_entity(item)

            if not sg_entity or sg_entity["type"] != "Task":
                return False

            assignees = sg_entity.get("task_assignees", [])
            assignee_ids = [a["id"] for a in assignees if "id" in a]
            if current_user["id"] not in assignee_ids:
                return False

        # we accept this row so lets check with the base implementation:        
        return EntityProxyModel._is_row_accepted(self, src_row, src_parent_idx, parent_accepted)




