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

class EntityTreeProxyModel(EntityProxyModel):
    """
    """
    def __init__(self, compare_sg_fields=None, parent=None):
        """
        """
        EntityProxyModel.__init__(self, compare_sg_fields, parent)
        self._only_show_my_tasks = False

    @property
    def only_show_my_tasks(self):
        return self._only_show_my_tasks
    
    @only_show_my_tasks.setter
    def only_show_my_tasks(self, show):
        if self._only_show_my_tasks != show:
            self._only_show_my_tasks = show
            self.invalidateFilter()

    def _is_item_accepted(self, item, parent_accepted):
        """
        """
        if self._only_show_my_tasks:
            
            sg_entity = item.model().get_entity(item)
            if sg_entity and sg_entity["type"] == "Task":
                
                assignees = sg_entity.get("task_assignees", [])
                assignee_ids = [a["id"] for a in assignees if "id" in a]
                
                # make sure that the current user is in this lise of assignees:
                app = sgtk.platform.current_bundle()
                current_user = sgtk.util.get_current_user(app.sgtk)
                
                if not current_user or current_user["id"] not in assignee_ids:
                    # task isn't assigned to the current user so this item
                    # is definitely not accepted!
                    return False

        # fall back to the base implementation:        
        return EntityProxyModel._is_item_accepted(self, item, parent_accepted)