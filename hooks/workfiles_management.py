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
    # The custom entity has the following custom fields:
    # sg_version (number): version number of the scene
    # sg_task (task entity): task associated with the work file
    # sg_step (step entity): step associated with the work file
    # sg_link (asset, project or shot entity): entity associated with the work file
    # sg_template (text): Name of the Toolkit template used to generate the file name.
    # sg_path (file/link): Path to the file on disk.
    # sg_path_cache (str): Relative path to the file inside the local storage.
    # sg_path_cache_storage (local storage entity): LocalStorage the file is part of. This can't
    #   be created through the GUI, but can be programmatically:
    #   shotgun.schema_field_create("CustomEntity45", "entity", "Path Cache Storage", {"valid_types": ["LocalStorage"]})

    def is_implemented(self):
        """
        When this methods true, the workfiles application will use this hook for file discovery.
        """
        return True

    def register_workfile(self, name, version, context, work_template, path, description, image):
        """
        Registers a work file with Shotgun.

        :param name str: Name of the work file.
        :param int version: Version of the work file.
        :param context: Context we're saving into.
        :type context: :class:`sgtk.Context`
        :param work_template: Template associated with this work file.
        :type work_template: :class:`sgtk.Template`
        :param str path: Path to the file on disk.
        :param str image: Path to the image associated with the work file.
        """

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

        new_workfile = {
            "code": name,
            "sg_version": version,
            "sg_task": context.task,
            "sg_step": context.step,
            "sg_link": context.entity or context.project,
            "sg_template": work_template.name,
            "sg_path": sg_path,
            "project": context.project
        }

        if "local_storage" in sg_path and "relative_path" in sg_path:
            new_workfile["sg_path_cache_storage"] = sg_path["local_storage"]
            new_workfile["sg_path_cache"] = sg_path["relative_path"]

        self.parent.shotgun.create(
            self.WORKFILE_ENTITY,
            new_workfile
        )

    def find_work_files(self, context, work_template, version_compare_ignore_fields, valid_file_extensions):
        """
        Finds all the work files for a given context.

        :param context: Context for the files.
        :type context: :class:`sgtk.Context`
        :param work_template: Template used to search for files.
        :type work_template: :class:`sgtk.Template`
        :param list(str) version_compare_ignore_fields: A list of fields that should be ignored when
            comparing files to determine if they are different versions of the same file. If
            this is left empty then only the version field will be ignored. Care should be taken
            when specifying fields to ignore as Toolkit will expect the version to be unique across
            files that have different values for those fields and will error if this isn't the case.
        :param list(str) valid_file_extensions: List of valid file extension types.

        :returns: A list work file item. Each item has the following format::
            {
                "name": "something",
                "version": 42,
                "task": {"type": "Task", "id": 38},
                "path": "/path/to/the/file.dcc",
                "description": "something descriptive",
                "thumbnail": {"type": "url", "path": "https://site.com/b/c/.png"}
                "modified_at": datetime.datetime(2018, 9, 26),
                "modified_by": {"type": "HumanUser", "id": 343}
            }
        """

        # Build out a filter to return the requested files.
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
                "version": wf["sg_version"],
                "name": wf["code"],
                "task": wf["sg_task"],
                "path": path,
                "description": wf["description"],
                "thumbnail": wf["image"],
                "modified_at": wf["updated_at"],
                "modified_by": wf["updated_by"],
            })

        return work_file_item_details
