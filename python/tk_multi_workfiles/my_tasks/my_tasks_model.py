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
Implementation of the 'My Tasks' data model
"""

import sgtk
from sgtk.platform.qt import QtGui

from ..util import resolve_filters
from ..entity_models import ShotgunExtendedEntityModel

class MyTasksModel(ShotgunExtendedEntityModel):
    """
    Specialisation of the Shotgun entity model that represents a single users tasks.  Note that we derive
    from the Shotgun entity model so that we have access to the entity icons it provides.  These are used 
    later by the MyTaskItemDelegate when rending a widget for a task in the My Tasks view.
    """
    def __init__(self, project, user, extra_display_fields, my_tasks_filters, parent, bg_task_manager=None):
        """
        Construction

        :param project:                 A Shotgun entity dictionary representing the project that my tasks should
                                        be loaded for.
        :param user:                    A Shotgun entity dictionary representing the user whom tasks should be loaded 
                                        for
        :param extra_display_fields:    List of additional fields that should be loaded for each task
        :param parent:                  The parent QObject for this model
        :param bg_task_manager:         A BackgroundTaskManager instance that will be used to perform all
                                        background threaded work.
        """
        self.extra_display_fields = extra_display_fields or []

        filters = [["project", "is", project]]
        filters.extend(resolve_filters(my_tasks_filters))

        fields = ["image", "entity", "content"]
        fields.extend(self.extra_display_fields)

        ShotgunExtendedEntityModel.__init__(
            self,
            "Task",
            filters,
            ["content"],
            fields,
            parent=parent,
            download_thumbs=True,
            bg_load_thumbs = True,
            bg_task_manager=bg_task_manager
        )

    def _populate_default_thumbnail(self, item):
        """
        Override base class method as we don't need the default thumbnail that it
        provides.

        :param item:    The QStandardItem to populate the default thumbnail for.
        """
        # do nothing.
        pass

    def _populate_thumbnail_image(self, item, field, image, path):
        """
        Overriden base class method that populates the thumbnail for a task model item.

        :param item:    The QStandardItem representing the task
        :param field:   The Shotgun field that the thumbnail was loaded for
        :param image:   The thumbnail QImage
        :param path:    The path on disk to the thumbnail file
        """
        if field != "image":
            # there may be other thumbnails being loaded in as part of the data flow
            # (in particular, created_by.HumanUser.image) - these ones we just want to 
            # ignore and not display.
            return

        thumb = QtGui.QPixmap.fromImage(image)
        item.setIcon(QtGui.QIcon(thumb))


