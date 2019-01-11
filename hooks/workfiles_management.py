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
    """
    This hooks allows to drive file discovery and file persistence with the workfiles application.

    You need to implement at minimum the following hooks to get the basic functionality working:
        - register_workfiles
        - find_work_files

    If you intend on using user sandboxes for your workfiles, you can also implement
    `resolve_sandbox_users` to speed up sandbox discovery for a given context.
    """

    WORKFILE_ENTITY = "CustomEntity45"
    # The custom entity has the following custom fields:
    # sg_version (number): version number of the scene
    # sg_task (task entity): task associated with the work file
    # sg_step (step entity): step associated with the work file
    # sg_link (asset, project or shot entity): entity associated with the work file
    # sg_sandbox (person): user sandbox for the workfile (to be filled only if sandboxing is used)
    # sg_template (text): Name of the Toolkit template used to generate the file name.
    # sg_path (file/link): Path to the file on disk.
    # sg_path_cache (str): Relative path to the file inside the local storage.
    # sg_path_cache_storage (local storage entity): LocalStorage the file is part of. This can't
    #   be created through the GUI, but can be programmatically:
    #   shotgun.schema_field_create("CustomEntity45", "entity", "Path Cache Storage", {"valid_types": ["LocalStorage"]})

    def register_workfile(self, name, version, context, work_template, path, description, image):
        """
        Register a work file with Shotgun.

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

        if self._is_using_sandboxes(work_template):
            new_workfile["sg_sandbox"] = context.user

        if "local_storage" in sg_path and "relative_path" in sg_path:
            new_workfile["sg_path_cache_storage"] = sg_path["local_storage"]
            new_workfile["sg_path_cache"] = sg_path["relative_path"]

        self.parent.shotgun.create(
            self.WORKFILE_ENTITY,
            new_workfile
        )

    def find_work_files(self, context, work_template, version_compare_ignore_fields, valid_file_extensions):
        """
        Find all the work files for a given context.

        This is used to populate the file view and figure out the next available version number when saving
        a scene.

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
        fields = [
            "code", "description", "image",
            "updated_at", "updated_by",
            "sg_version", "sg_link", "sg_step", "sg_task",
            "sg_path"
        ]
        work_files = self._find_workfile_entities(
            context, work_template, fields, filter_by_user=self._is_using_sandboxes(work_template)
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

    def resolve_user_sandboxes(self, context, template, is_work_template):
        """
        Find all the user sandboxes in use for the given context and template.

        This will be used to populate the user button in the UI.

        :param context: Context of the files for which we want the sandboxes.
        :type context: :class:`sgtk.Context`
        :param work_template: Template of the files for which we want the sandboxes.
        :type work_template: :class:`sgtk.Template`
        :param bool is_work_template: If ``True``, the template is for a workfile.

        :returns: A list of HumanUser entity links. Each item has the following format:
            {
                "type": "HumanUser",
                "id": 42
            }
        """
        if is_work_template:
            workfiles = self._find_workfile_entities(
                context, template, ["sg_sandbox"], filter_by_user=False
            )

            return [
                work_file["sg_sandbox"] for work_file in workfiles if work_file["sg_sandbox"] is not None
            ]
        else:
            # A publish could be created by user A into user B's publish sandbox.
            # Unfortunately, that publish's relationship with B isn't encapsulated
            # by the PublishFile entity, so we can't extract the information out of Shotgun.
            # we'll have to extract if from the files themselves using the built-in
            # app logic.
            raise NotImplementedError

    def _is_using_sandboxes(self, template):
        """
        Check if a template uses user sandboxes.

        :returns: ``True`` if the template does, ``False`` if not.
        """
        # TODO: It would be nice if this logic was refactored unto the template class in core.
        if "HumanUser" in template.keys:
            return True
        for key in template.keys.values():
            if key.shotgun_entity_type == "HumanUser":
                return True
        return False

    def _find_workfile_entities(self, context, work_template, fields, filter_by_user):
        """
        Find all workfiles entities for a given template and context.

        :param context: Context for the files.
        :type context: :class:`sgtk.Context`
        :param work_template: Template used to search for files.
        :type work_template: :class:`sgtk.Template`
        :param list(str) fields: List of fields that should be retrieved.
        :param bool filter_by_user: If ``True``, only workfiles in user's sandbox will be returned.
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
            filters = [["sg_link", "is", context.project]]

        filters.append(["sg_template", "is", work_template.name])

        if filter_by_user:
            filters.append(["sg_sandbox", "is", context.user])

        return self.parent.shotgun.find(
            self.WORKFILE_ENTITY,
            filters,
            fields=fields
        )
