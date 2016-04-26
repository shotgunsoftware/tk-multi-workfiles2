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

    __nb_versions_in_menu = 10

    def __init__(self, work_area, file_model, workfiles_visible=True, publishes_visible=True):
        """
        Constructor.

        :param work_area: WorkArea instance representing the context associate with the file.
        :param file_model: A FileModel instance.
        :param workfiles_visible: True if workfiles are visible. Defauls to True.
        :param publishes_visible: True if publishes are visible. Defauls to True.
        """
        self._work_area = work_area
        self._file_model = file_model
        self._workfiles_visible = workfiles_visible
        self._publishes_visible = publishes_visible

        app = sgtk.platform.current_bundle()

        # determine if this file is in a different users sandbox:
        self._in_other_users_sandbox = (
            work_area.contains_user_sandboxes
            and work_area.context.user and g_user_cache.current_user
            and work_area.context.user["id"] != g_user_cache.current_user["id"]
        )

        # determine if this file is in a different work area:
        # Normally, the work area where a file is being opened is the one it will be opened from. However,
        # when working with user sandboxes, the context will change since the user won't be the same.
        self._user_work_area = work_area
        # Change work area tracks if the current context is different than the context of the file
        # being opened.
        self._change_work_area = (work_area.context != app.context)
        if self._change_work_area and self._in_other_users_sandbox:
            self._user_work_area = work_area.create_copy_for_user(g_user_cache.current_user)
            self._change_work_area = (self._user_work_area.context != app.context)

        # and if it's possible to copy this file to the work area:
        self._can_copy_to_work_area = False
        if self._change_work_area and app.context:
            # no need to try/except this WorkArea object creation, since if we're here it means the
            # context is fully configured.
            current_env = WorkArea(app.context)
            self._can_copy_to_work_area = current_env.work_template is not None
            # (AD) TODO - it's possible the work template for the current work area has different requirements than
            # the source work area (e.g. it may require a name where the source work template doesn't!)  This should
            # probably check that file.path is translatable to the current work area (contains all the required keys)
            # in addition to the simple check it's currently doing.

    def get_actions(self, file_item):
        """
        Retrives the list of actions for the given file

        :param file_item: File item we wish to retrieve the file versions from.

        :returns: List of Actions.
        """
        actions = []

        current_user_file_versions = self._get_current_user_file_versions(file_item)

        # add the interactive 'open' action.  This is the
        # default/generic open action that gets run whenever someone
        # double-clicks on a file or just hits the 'Open' button
        actions.append(
            InteractiveOpenAction(
                file_item,
                current_user_file_versions,
                self._work_area,
                self._workfiles_visible,
                self._publishes_visible
            )
        )

        # Creates Open actions for a workfile.
        actions.extend(self._create_local_file_actions(file_item, current_user_file_versions))
        # Creates open actions for publishes.
        actions.extend(self._create_published_file_actions(file_item, current_user_file_versions))
        # Creates actions for previous versions of the current file.
        actions.extend(self._create_previous_versions_actions_menus(file_item))
        # Creates a New action.
        actions.extend(self._create_new_file_action())
        # Creates actions provided by the custom_ ctions hook.
        actions.extend(self._create_custom_actions(file_item, current_user_file_versions))
        # Creates actions that allow to shot the files the OS's file browser or in Shotgun.
        actions.extend(self._create_show_in_actions(file_item, current_user_file_versions))

        return actions

    def _get_current_user_file_versions(self, file_item):
        """
        Retrieves the list of versions that are owned by the current user.

        :param file_item: File item we wish to retrieve the file versions from.

        :returns: List of file versions owned by the current user.
        """

        # get the list of file versions for the file
        current_user_file_versions = {}
        if self._in_other_users_sandbox:
            # build a file key by extracting fields from the path:
            template = None
            path = None
            if file_item.path and self._user_work_area.work_area_contains_user_sandboxes:
                path = file_item.path
                template = self._user_work_area.work_template
            elif file_item.publish_path and self._user_work_area.publish_area_contains_user_sandboxes:
                path = file_item.publish_path
                template = self._user_work_area.publish_template

            if template and path:
                fields = template.get_fields(path)
                ctx_fields = self._user_work_area.context.as_template_fields(template)
                fields.update(ctx_fields)
                file_key = FileItem.build_file_key(fields, template, self._user_work_area.version_compare_ignore_fields)
                current_user_file_versions = self._file_model.get_cached_file_versions(file_key, self._user_work_area) or {}
        else:
            # not using sandboxes so the two lists of versions are the same
            current_user_file_versions = file_item.versions

        return current_user_file_versions

    def _create_local_file_actions(self, file_item, file_versions):
        """
        Creates a list of actions if the file item is a local file.

        :param file_item: File item to generate actions for.
        :param file_versions: Filtered list of file versions for the current user.

        :returns: List of actions.
        """

        actions = []

        if not file_item.is_local:
            return actions

        # all actions available when selection is a work file
        # ------------------------------------------------------------------
        actions.append(SeparatorAction())

        # add the general open action - this just opens the file in-place.
        actions.append(OpenWorkfileAction(file_item, file_versions, self._work_area))

        if self._in_other_users_sandbox:
            # file is in another user sandbox so add appropriate actions:
            actions.append(ContinueFromWorkFileAction(file_item, file_versions, self._work_area))

            if self._change_work_area and self._can_copy_to_work_area:
                actions.append(CopyAndOpenFileInCurrentWorkAreaAction(file_item, file_versions, self._work_area))

        else:
            # file isn't in a different sandbox so add regular open actions:
            if file_item.editable:
                # determine if this version is the latest:
                all_versions = [v for v, f in file_versions.iteritems()]
                max_version = max(all_versions) if all_versions else 0
                if file_item.version != max_version:
                    actions.append(ContinueFromWorkFileAction(file_item, file_versions, self._work_area))

            if self._change_work_area and self._can_copy_to_work_area:
                actions.append(CopyAndOpenFileInCurrentWorkAreaAction(file_item, file_versions, self._work_area))

        return actions

    def _create_published_file_actions(self, file_item, file_versions):
        """
        Creates a list of actions if the file item is a published file.

        :param file_item: File item to generate actions for.
        :param file_versions: Filtered list of file versions for the current user.

        :returns: List of actions.
        """
        actions = []
        if not file_item.is_published:
            return actions

        # all actions available when selection is a work file:
        # ------------------------------------------------------------------
        actions.append(SeparatorAction())
        actions.append(OpenPublishAction(file_item, file_versions, self._work_area))
        if file_item.path:
            # file has a local path so it's possible to carry copy it to the local work area!
            actions.append(ContinueFromPublishAction(file_item, file_versions, self._work_area))

            if self._change_work_area and self._can_copy_to_work_area:
                actions.append(CopyAndOpenPublishInCurrentWorkAreaAction(file_item, file_versions, self._work_area))

        return actions

    def _create_previous_versions_actions_menus(self, file_item):
        """
        Creates a list of previous versions menus if the file item has previous versions.

        :param file_item: File item to generate actions for.

        :returns: List of actions.
        """
        actions = []
        # ------------------------------------------------------------------
        actions.append(SeparatorAction())

        actions.extend(
            self._create_previous_versions_actions_menu(
                "Previous Work Files",
                [item for item in file_item.versions.itervalues() if file_item.version > item.version and item.is_local]
            )
        )

        actions.extend(
            self._create_previous_versions_actions_menu(
                "Previous Publishes",
                [item for item in file_item.versions.itervalues() if file_item.version > item.version and item.is_published],
            )
        )

        return actions

    def _create_previous_versions_actions_menu(self, label, previous_versions):
        """
        Creates a menu of actions if the file has previous versions.

        :param label: Name of the menu.
        :previous_versions: List of versions to generate a menu for.

        :returns: List of menu of actions.
        """
        if not previous_versions:
            return []

        version_versions_actions = self._create_previous_versions_actions(
            previous_versions
        )
        return [ActionGroup(label, version_versions_actions)]

    def _create_previous_versions_actions(self, previous_versions):
        """
        Creates a list of actions for all the previous versions of a given type.

        :param file_versions: List of previous versions to create menu actions for in the Previous
            Versions sub-menu.

        :returns: List of Actions.
        """
        previous_versions_actions = []

        # Gives us the last ten versions, from the latest to the earliest.
        for previous_file_item in previous_versions[-1: -self.__nb_versions_in_menu - 1: -1]:

            current_user_file_versions = self._get_current_user_file_versions(previous_file_item)

            version_actions = []
            # Retrieve all the actions for a version submenu. We're not interested into New, the default Open or
            # previous version actions for this sub menu, so we won't add them here.
            version_actions.extend(self._create_local_file_actions(previous_file_item, current_user_file_versions))
            version_actions.extend(self._create_published_file_actions(previous_file_item, current_user_file_versions))
            version_actions.extend(self._create_custom_actions(previous_file_item, current_user_file_versions))
            version_actions.extend(self._create_show_in_actions(previous_file_item, current_user_file_versions))

            previous_versions_actions.append(ActionGroup("Version %d" % previous_file_item.version, version_actions))

        return previous_versions_actions

    def _create_new_file_action(self):
        """
        Creates a list of actions to create a new file.

        :returns: List of actions.
        """
        # You can't create files in other users sandbox. The work area also needs to be configured
        # accordingly.
        if self._in_other_users_sandbox or not NewFileAction.can_do_new_file(self._work_area):
            return []

        actions = []
        # ------------------------------------------------------------------
        actions.append(SeparatorAction())
        actions.append(NewFileAction(self._work_area))

        return actions

    def _create_custom_actions(self, file_item, file_versions):
        """
        Creates a list of custom actions

        :param file_item: File item to generate actions for.

        :returns: List of actions.
        """
        actions = []
        # query for any custom actions:
        custom_actions = CustomFileAction.get_action_details(file_item, file_versions, self._work_area,
                                                             self._workfiles_visible, self._publishes_visible)
        if custom_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
        for action_dict in custom_actions:
            name = action_dict.get("name")
            label = action_dict.get("caption") or name
            custom_action = CustomFileAction(name, label, file_item, file_versions, self._work_area,
                                             self._workfiles_visible, self._publishes_visible)
            actions.append(custom_action)

        return actions

    def _create_show_in_actions(self, file_item, file_versions):
        """
        Creates a list of actions to show the file item in Shotgun or on the file system.

        :param file_item: File item to generate actions for.
        :param file_versions: Filtered list of file versions for the current user.

        :returns: List of actions.
        """
        show_in_actions = []
        if file_item.is_local:
            show_in_actions.append(ShowWorkFileInFileSystemAction(file_item, file_versions, self._work_area))
        else:
            if self._work_area.work_area_template:
                show_in_actions.append(ShowWorkAreaInFileSystemAction(file_item, file_versions, self._work_area))

        if file_item.is_published:
            show_in_actions.append(ShowPublishInFileSystemAction(file_item, file_versions, self._work_area))
            show_in_actions.append(ShowPublishInShotgunAction(file_item, file_versions, self._work_area))
        else:
            if self._work_area.publish_area_template:
                show_in_actions.append(ShowPublishAreaInFileSystemAction(file_item, file_versions, self._work_area))

            # see if we have any publishes:
            publish_versions = [v for v, f in file_versions.iteritems() if f.is_published]
            if publish_versions:
                show_in_actions.append(ShowLatestPublishInShotgunAction(file_item, file_versions, self._work_area))

        actions = []
        if show_in_actions:
            # ------------------------------------------------------------------
            actions.append(SeparatorAction())
            actions.extend(show_in_actions)

        return actions
