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

import sgtk


class WorkfilesManagement(sgtk.get_hook_baseclass()):

    WORKFILE_ENTITY = "CustomEntity45"

    def is_implemented(self):
        return True

    def register_workfile(self, name, version, context, work_template, path, description, image):

        # FIXME: Big giant smelly hack. Do not do this!!!
        # We need to refactor in core the logic that allows to turn a templated path into a
        # file reference. Here we'll use the code from create publish and run it in dry-run mode.
        # The method returns the new published data
        sg_path = sgtk.util.shotgun.publish_creation._create_published_file(
            context.sgtk,
            context,
            path,
            name,
            version,
            None,
            comment="",
            published_file_type=None,
            created_by_user=None,
            created_at=None,
            version_entity=None,
            dry_run=True
        )["path"]

        self.parent.shotgun.create(
            self.WORKFILE_ENTITY,
            {
                "code": name,
                "sg_version": version,
                "sg_task": context.task,
                "sg_step": context.step,
                "sg_link": context.entity or context.project,
                "sg_template": work_template.name,
                "sg_path": sg_path,
                "project": context.project
            }
        )

    def find_work_files(self, context, work_template, version_compare_ignore_fields, valid_file_extensions):

        if context.task:
            filters = [["sg_task", "is", context.task]]
        elif context.step:
            filters = [
                ["sg_link", "is", context.entity or context.project],
                ["sg_step", "is", context.step]
            ]
        elif context.entity:
            filters = [["sg_link", "is", context.entity]]
        else:
            filters = [["entity", "is", context.project]]

        filters.append(["sg_template", "is", work_template.name])

        print filters

        work_files = self.parent.shotgun.find(
            self.WORKFILE_ENTITY,
            filters,
            fields=[
                "code", "description", "image",
                "updated_at", "updated_by",
                "sg_version", "sg_link", "sg_step", "sg_task",
                "sg_path"
            ]
        )

        print work_files

        work_file_item_details = []
        for wf in work_files:

            # FIXME: Big smelly hack. We'll reuse the logic for resolving paths from publishes.
            fake_sg_publish_data = {
                "id": wf["id"],
                "path": wf["sg_path"]
            }

            path = self.get_publish_path(fake_sg_publish_data)

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
