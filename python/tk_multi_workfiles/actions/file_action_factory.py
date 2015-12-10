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
File open menu factory.
"""
import sgtk

from .action import SeparatorAction, ActionGroup

from .interactive_open_action import InteractiveOpenAction

from .open_workfile_actions import OpenWorkfileAction
from .open_workfile_actions import ContinueFromWorkFileAction
from .open_workfile_actions import CopyAndOpenFileInCurrentWorkAreaAction

from .open_publish_actions import OpenPublishAction
from .open_publish_actions import ContinueFromPublishAction
from .open_publish_actions import CopyAndOpenPublishInCurrentWorkAreaAction

from .new_file_action import NewFileAction

from .show_in_filesystem_action import ShowWorkFileInFileSystemAction, ShowPublishInFileSystemAction
from .show_in_filesystem_action import ShowWorkAreaInFileSystemAction, ShowPublishAreaInFileSystemAction
from .show_in_shotgun_action import ShowPublishInShotgunAction, ShowLatestPublishInShotgunAction

from .custom_file_action import CustomFileAction

from ..work_area import WorkArea
from ..file_item import FileItem
from ..user_cache import g_user_cache


class FileActionFactory(object):
    """
    Builder for the file open menu. Based on the current selection, the build will enumerate a list of actions,
    grouped actions and seperators that should be displayed in the UI.
    """

    def get_actions(self, file, work_area, file_model, workfiles_visible=True, publishes_visible=True):
        """
        Retrives the list of actions for the given file.

        :param file: FileItem instance representing the selection in the browser.
        :param work_area: WorkArea instance representing the context associate with the file.
        :param file_model: A FileModel instance.
        :param workfiles_visible: True if workfiles are visible.
        :param publishes_visible: True if publishes are visible.

        :returns: List of Actions.
        """
        return self.__get_actions(file, work_area, file_model, workfiles_visible, publishes_visible, first_level=True)

    def __get_actions(self, file, work_area, file_model, workfiles_visible, publishes_visible, first_level):
        """
        Retrives the list of actions for the given file, recursively.

        :param file: FileItem instance representing the selection in the browser.
        :param work_area: WorkArea instance representing the context associate with the file.
        :param file_model: A FileModel instance.
        :param workfiles_visible: True if workfiles are visible, False otherwise.
        :param publishes_visible: True if publishes are visible, False otherwise.
        :param first_level: True if we are at the root of the actions list, False otherwise.

        :returns: List of Actions.
        """
        if not file or not work_area or not file_model:
            return []

        app = sgtk.platform.current_bundle()

        # determine if this file is in a different users sandbox:
        in_other_users_sandbox = (work_area.contains_user_sandboxes
                                  and work_area.context.user and g_user_cache.current_user
                                  and work_area.context.user["id"] != g_user_cache.current_user["id"])

        # determine if this file is in a different work area:
        user_work_area = work_area
        change_work_area = (work_area.context != app.context)
        if change_work_area and in_other_users_sandbox:
            user_work_area = work_area.create_copy_for_user(g_user_cache.current_user)
            change_work_area = (user_work_area.context != app.context)

        # and if it's possible to copy this file to the work area:
        can_copy_to_work_area = False
        if change_work_area and app.context:
            current_env = WorkArea(app.context)
            can_copy_to_work_area = current_env.work_template is not None
            # (AD) TODO - it's possible the work template for the current work area has different requirements than
            # the source work area (e.g. it may require a name where the source work template doesn't!)  This should
            # probably check that file.path is translatable to the current work area (contains all the required keys)
            # in addition to the simple check it's currently doing.

        # get the list of file versions for the file:
        file_versions = file.versions
        current_user_file_versions = {}
        if in_other_users_sandbox:
            # build a file key by extracting fields from the path:
            template = None
            path = None
            if file.path and user_work_area.work_area_contains_user_sandboxes:
                path = file.path
                template = user_work_area.work_template
            elif file.publish_path and user_work_area.publish_area_contains_user_sandboxes:
                path = file.publish_path
                template = user_work_area.publish_template

            if template and path:
                fields = template.get_fields(path)
                ctx_fields = user_work_area.context.as_template_fields(template)
                fields.update(ctx_fields)
                file_key = FileItem.build_file_key(fields, template, user_work_area.version_compare_ignore_fields)
                current_user_file_versions = file_model.get_cached_file_versions(file_key, user_work_area) or {}
        else:
            # not using sandboxes so the two lists of versions are the same
            current_user_file_versions = file_versions

        actions = []

        # Default Open is only at the root level.
        if first_level:
            # add the interactive 'open' action.  This is the
            # default/generic open action that gets run whenever someone
            # double-clicks on a file or just hits the 'Open' button
            actions.append(InteractiveOpenAction(file, file_versions, work_area, workfiles_visible, publishes_visible))

        if file.is_local:
            # if workfiles_visible and file.is_local:
            # all actions available when selection is a work file

            # ------------------------------------------------------------------
            actions.append(SeparatorAction())

            # add the general open action - this just opens the file in-place.
            actions.append(OpenWorkfileAction(file, file_versions, work_area))

            if in_other_users_sandbox:
                # file is in another user sandbox so add appropriate actions:
                actions.append(ContinueFromWorkFileAction(file, current_user_file_versions, work_area))

                if change_work_area and can_copy_to_work_area:
                    actions.append(CopyAndOpenFileInCurrentWorkAreaAction(file, current_user_file_versions, work_area))

            else:
                # file isn't in a different sandbox so add regular open actions:
                if file.editable:
                    # determine if this version is the latest:
                    all_versions = [v for v, f in file_versions.iteritems()]
                    max_version = max(all_versions) if all_versions else 0
                    if file.version != max_version:
                        actions.append(ContinueFromWorkFileAction(file, file_versions, work_area))

                if change_work_area and can_copy_to_work_area:
                    actions.append(CopyAndOpenFileInCurrentWorkAreaAction(file, file_versions, work_area))

        if file.is_published:
            # all actions available when selection is a work file:

            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
            actions.append(OpenPublishAction(file, file_versions, work_area))
            if file.path:
                # file has a local path so it's possible to carry copy it to the local work area!
                actions.append(ContinueFromPublishAction(file, current_user_file_versions, work_area))

                if change_work_area and can_copy_to_work_area:
                    actions.append(CopyAndOpenPublishInCurrentWorkAreaAction(file, current_user_file_versions, work_area))

        # If we are at the first level of the menu, we will show previous versions of the current file,
        # if available.
        if first_level:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
            self.__append_previous_versions_actions(
                actions, file, work_area, file_model, workfiles_visible, publishes_visible, pick_locals=True
            )

            self.__append_previous_versions_actions(
                actions, file, work_area, file_model, workfiles_visible, publishes_visible, pick_locals=False
            )

        # A New File can only be created from the first level of the menu.
        if first_level and not in_other_users_sandbox:
            if NewFileAction.can_do_new_file(work_area):
                # New file action

                # ------------------------------------------------------------------
                actions.append(SeparatorAction())
                actions.append(NewFileAction(file, file_versions, work_area))

        # query for any custom actions:
        custom_actions = CustomFileAction.get_action_details(file, file_versions, work_area,
                                                             workfiles_visible, publishes_visible)
        if custom_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
        for action_dict in custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("caption") or name
            custom_action = CustomFileAction(name, label, file, file_versions, work_area,
                                             workfiles_visible, publishes_visible)
            actions.append(custom_action)

        # finally add the 'show in' actions:
        show_in_actions = []
        if file.is_local:
            show_in_actions.append(ShowWorkFileInFileSystemAction(file, file_versions, work_area))
        else:
            if work_area.work_area_template:
                show_in_actions.append(ShowWorkAreaInFileSystemAction(file, file_versions, work_area))

        if file.is_published:
            show_in_actions.append(ShowPublishInFileSystemAction(file, file_versions, work_area))
            show_in_actions.append(ShowPublishInShotgunAction(file, file_versions, work_area))
        else:
            if work_area.publish_area_template:
                show_in_actions.append(ShowPublishAreaInFileSystemAction(file, file_versions, work_area))

            # see if we have any publishes:
            publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
            if publish_versions:
                show_in_actions.append(ShowLatestPublishInShotgunAction(file, file_versions, work_area))

        if show_in_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
            actions.extend(show_in_actions)

        return actions

    def __append_previous_versions_actions(self, actions, file, work_area, file_model, workfiles_visible, publishes_visible, pick_locals):
        """
        Retrives the list of actions for all the previous versions of a given type.

        :param file: FileItem instance representing the selection in the browser.
        :param work_area: WorkArea instance representing the context associate with the file.
        :param file_model: A FileModel instance.
        :param workfiles_visible: True if workfiles are visible, False otherwise.
        :param publishes_visible: True if publishes are visible, False otherwise.
        :param pick_locals: True if we want to show previous actions for workfiles, False if we want them for publishes.

        :returns: List of Actions.
        """
        # Pick the right verion type.
        if pick_locals:
            previous_versions = [item for item in file.versions.values() if file.version > item.version and item.is_local]
        else:
            previous_versions = [item for item in file.versions.values() if file.version > item.version and item.is_published]

        # If there are no previous versions to show, return an empty list.
        if not previous_versions:
            return 

        previous_versions_actions = []
        # Gives us the last ten versions, from the latest to the earliest.
        for item in previous_versions[-1:-11:-1]:
            version_actions = self.__get_actions(
                item, work_area, file_model,
                workfiles_visible, publishes_visible,
                first_level=False
            )
            previous_versions_actions.append(ActionGroup("Version %d" % item.version, version_actions))

        actions.append(
            ActionGroup("Previous Work Files" if pick_locals else "Previous Publishes", previous_versions_actions)
        )
