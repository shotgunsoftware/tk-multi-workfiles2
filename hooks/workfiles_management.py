# Copyright (c) 2018 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Abstract outs the discovery of files on disk.
"""

import os

from sgtk import get_hook_baseclass


class WorkfilesManagement(get_hook_baseclass()):

    WORKFILE_ENTITY = "CustomEntity45"

    def is_implemented(self):
        return False

    def _get_filter_from_context(self, context):

        # Create a filter for the context. Do not bother creating a super complex filter.
        # If task is set then every other field is implied.
        if context.task:
            filters = [["sg_step", "is", context.task]]
        elif context.step:
            filters = [
                ["sg_link", "is", context.entity or context.project],
                ["sg_step", "is", context.step]
            ]
        elif context.entity:
            filters = [["sg_link", "is", context.entity]]
        else:
            filters = [["entity", "is", context.project]]

        return filters

    def register_workfiles(self, name, version, context, work_template, path, description, image):
        self.parent.shotgun.create(
            self.WORKFILE_ENTITY,
            {
                "code": name,
                "sg_version": version,
                "sg_task": context.task,
                "sg_step": context.step,
                "sg_link": context.entity or context.project,
                "sg_work_template": work_template.name,
                "sg_path": path,
                "project": context.project
            }
        )

    def find_work_files(self, context, work_template, version_compare_ignore_fields, valid_file_extensions):
        work_files = self.parent.shotgun.find(
            self.WORKFILE_ENTITY,
            self._get_filter_from_context(context).extend(
                ["sg_work_template", "is", work_template.name]
            ),
            [
                "code", "description", "image",
                "updated_at", "updated_by",
                "sg_version", "sg_link", "sg_step", "sg_task",
                "sg_path"
            ]
        )

        work_file_item_details = []
        for wf in work_files:
            print(wf)
            path = self.get_publish_path(wf["sg_path"])

            # skip file if it doesn't contain a valid file extension:
            if valid_file_extensions and os.path.splitext(path)[1] not in valid_file_extensions:
                continue

            work_file_item_details.append({
                "path": path,
                "version": wf["sg_version"],
                "name": wf["code"],
                "task": wf["sg_task"],
                "description": wf["description"],
                "thumbnail": wf["image"],
                "modified_at": wf["updated_at"],
                "modified_by": wf["updated_by"],
            })

        return work_file_item_details
