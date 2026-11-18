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
Hook that creates folders if needed
"""

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FileAction(HookBaseClass):
    """
    Implementation of the FileAction class
    """

    def create_folders(self, context):
        """Create folders on the disk.

        :param context: The context for which we need to create folders
        :type context: sgtk.Context
        """

        ctx_entity = context.task or context.entity or context.project

        self.logger.info("Creating filesystem structure...")
        self.parent.sgtk.create_filesystem_structure(
            ctx_entity.get("type"),
            ctx_entity.get("id"),
            engine=self.parent.engine.instance_name,
        )
        self.logger.info("Filesystem structure created.")
