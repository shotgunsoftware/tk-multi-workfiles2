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
Base class for the file-open & file-save forms.  Contains common code for setting up
models etc. and common signals/operations (e.g creating a task)
"""
import sys
import re

from itertools import chain

import sgtk
from sgtk.platform.qt import QtCore, QtGui

task_manager = sgtk.platform.import_framework("tk-framework-shotgunutils", "task_manager")
BackgroundTaskManager = task_manager.BackgroundTaskManager

shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")

from .entity_models import ShotgunExtendedEntityModel, ShotgunDeferredEntityModel
from .file_model import FileModel
from .my_tasks.my_tasks_model import MyTasksModel
from .scene_operation import get_current_path, SAVE_FILE_AS_ACTION
from .file_item import FileItem
from .work_area import WorkArea
from .actions.new_task_action import NewTaskAction
from .user_cache import g_user_cache
from .util import monitor_qobject_lifetime, resolve_filters, get_sg_entity_name_field
from .step_list_filter import get_saved_step_filter


class FileFormBase(QtGui.QWidget):
    """
    Implementation of file form base class.  Contains initialisation and functionality
    used by both the File Open & File Save dialogs.
    """
    def __init__(self, parent):
        """
        Construction

        :param parent:  The parent QWidget for this form
        """
        QtGui.QWidget.__init__(self, parent)

        self._current_file = None

        # create a single instance of the task manager that manages all
        # asynchrounous work/tasks.
        self._bg_task_manager = BackgroundTaskManager(self, max_threads=8)
        monitor_qobject_lifetime(self._bg_task_manager, "Main task manager")
        self._bg_task_manager.start_processing()

        shotgun_globals.register_bg_task_manager(self._bg_task_manager)

        # build the various models:
        self._my_tasks_model = self._build_my_tasks_model()
        self._entity_models = self._build_entity_models()
        self._file_model = self._build_file_model()

        # add refresh action with appropriate keyboard shortcut:
        refresh_action = QtGui.QAction("Refresh", self)
        refresh_action.setShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Refresh))
        refresh_action.triggered.connect(self._on_refresh_triggered)
        self.addAction(refresh_action)

        # on OSX, also add support for F5 (the default for OSX is Cmd+R)
        if sys.platform == "darwin":
            osx_f5_refresh_action = QtGui.QAction("Refresh (F5)", self)
            osx_f5_refresh_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F5))
            osx_f5_refresh_action.triggered.connect(self._on_refresh_triggered)
            self.addAction(osx_f5_refresh_action)

    def closeEvent(self, event):
        """
        Overriden method triggered when the widget is closed.  Cleans up as much as possible
        to help the GC.

        :param event:   Close event
        """

        # clear up the various data models:
        if self._file_model:
            self._file_model.destroy()
        if self._my_tasks_model:
            self._my_tasks_model.destroy()
        for _, _, model in self._entity_models:
            model.destroy()
        self._entity_models = []

        # and shut down the task manager
        if self._bg_task_manager:
            shotgun_globals.unregister_bg_task_manager(self._bg_task_manager)
            self._bg_task_manager.shut_down()
            self._bg_task_manager = None

        return QtGui.QWidget.closeEvent(self, event)

    def _build_my_tasks_model(self):
        """
        Build the My Tasks to be used by the file open/save dialogs.

        :returns:   An instance of MyTasksModel that represents all tasks assigned to the
                    current user in the current project.  If the current user is not known
                    or the My Tasks view is disabled in the config then this returns None
        """
        if not g_user_cache.current_user:
            # can't show my tasks if we don't know who 'my' is!
            return None

        app = sgtk.platform.current_bundle()
        show_my_tasks = app.get_setting("show_my_tasks", True)
        if not show_my_tasks:
            return None

        # get any extra display fields we'll need to retrieve:
        extra_display_fields = app.get_setting("my_tasks_extra_display_fields")
        # get the my task filters from the config.
        my_tasks_filters = app.get_setting("my_tasks_filters")

        # create the model:
        model = MyTasksModel(app.context.project,
                             g_user_cache.current_user,
                             extra_display_fields,
                             my_tasks_filters,
                             parent=self,
                             bg_task_manager=self._bg_task_manager)
        monitor_qobject_lifetime(model, "My Tasks Model")
        model.async_refresh()
        return model

    def _build_entity_models(self):
        """
        Build all entity models to be used by the file open/save dialogs.

        :returns:   A list of ShotgunEntityModel instances for each entity (and hierarchy) defined
                    in the app configuration
        """
        app = sgtk.platform.current_bundle()

        entity_models = []

        # Retrieve the step filter which was saved to apply it to Tasks
        step_filter = get_saved_step_filter()

        # set up any defined task trees:
        entities = app.get_setting("entities", [])
        for ent in entities:
            caption = ent.get("caption", None)
            entity_type = ent.get("entity_type")
            filters = ent.get("filters") or []
            hierarchy = ent.get("hierarchy", [])
            step_filter_on = ent.get("step_filter_on")
            sub_query = ent.get("sub_hierarchy", [])
            deferred_query = None
            if sub_query:
                step_filter_on = entity_type # Ensure this is not wrongly set
                # The target entity type for the sub query.
                sub_entity_type = sub_query.get("entity_type", "Task")
                # Optional filters for the sub query.
                sub_filters = resolve_filters(sub_query.get("filters") or [])
                # A list of fields to retrieve in the sub query.
                sub_hierarchy = sub_query.get("hierarchy") or []
                # The SG field allowing linking the sub query Entity to its
                # parent Entity.
                sub_link_field = sub_query.get("link_field", "entity")
                deferred_query = {
                    "entity_type": sub_entity_type,
                    "filters": sub_filters,
                    "hierarchy": sub_hierarchy,
                    "link_field": sub_link_field,
                }
            # Check the hierarchy to use for the model for this entity:
            if not hierarchy:
                app = sgtk.platform.current_bundle()
                app.log_error(
                    "No hierarchy found for entity type '%s' - at least one level of "
                    "hierarchy must be specified in the app configuration.  Skipping!" % entity_type
                )
                continue

            # resolve any magic tokens in the filter
            # Note, we always filter on the current project as the app needs templates
            # in the config to be able to find files and there is currently no way to
            # get these from a config belonging to a different project!
            resolved_filters = []

            # we always filter within the current project as it's not currently possible
            # to manage work files across projects (as we can't access the other project's
            # templates and folder schema).
            #
            # Note that this currently doesn't work for non-project entities!
            if entity_type == "Project":
                # special case if the entity type is 'Project' - this will show only
                # the current project in the tree!
                resolved_filters.append(["id", "is", app.context.project["id"]])
            else:
                # filter entities on the current project:
                resolved_filters.append(["project", "is", app.context.project])

            resolved_filters.extend(resolve_filters(filters))

            # Create an entity model for this query:
            fields = []
            if entity_type == "Task":
                # Add so we can filter tasks assigned to the user only on the client side.
                fields += ["task_assignees"]

            if deferred_query:
                model = ShotgunDeferredEntityModel(
                    entity_type,
                    resolved_filters,
                    hierarchy,
                    fields,
                    deferred_query=deferred_query,
                    parent=self,
                    bg_task_manager=self._bg_task_manager
                )
            else:
                model = ShotgunExtendedEntityModel(
                    entity_type,
                    resolved_filters,
                    hierarchy,
                    fields,
                    parent=self,
                    bg_task_manager=self._bg_task_manager
                )
            monitor_qobject_lifetime(model, "Entity Model")
            entity_models.append((caption, step_filter_on, model))
            if model.supports_step_filtering:
                model.load_and_refresh(step_filter)
            else:
                model.async_refresh()

        return entity_models

    def _build_file_model(self):
        """
        Build the single file model to be used by the file open/save dialogs.

        :returns:   A FileModel instance that represents all the files found for a set of entities
                    and users.
        """
        file_model = FileModel(self._bg_task_manager, parent=self)
        monitor_qobject_lifetime(file_model, "File Model")
        return file_model

    def _on_create_new_task(self, entity, step):
        """
        Slot triggered when the user requests that a new task be created.  If a task is created then
        all models will be immediately refreshed.

        :param entity:  The entity the task should be created for
        :param step:    The initial step to select in the new task dialog.
        """
        action = NewTaskAction(entity, step)
        if action.execute(self):
            self._refresh_all_async()

    def _on_refresh_triggered(self, checked=False):
        """
        Slot triggered when a refresh is requested via the refresh keyboard shortcut

        :param checked:    True if the refresh action is checked - ignored
        """
        app = sgtk.platform.current_bundle()
        app.log_debug("Synchronizing remote path cache...")
        app.sgtk.synchronize_filesystem_structure()
        app.log_debug("Path cache up to date!")
        self._refresh_all_async()

    def _refresh_all_async(self):
        """
        Asynchrounously refresh all models.
        """
        if self._my_tasks_model:
            self._my_tasks_model.async_refresh()
        for _, _, entity_model in self._entity_models:
            entity_model.async_refresh()
        if self._file_model:
            self._file_model.async_refresh()

    def _get_current_file(self):
        """
        Get a FileItem representing the currently open file/scene

        :returns:   A FileItem representing the current file if possible, otherwise None
        """
        if not self._current_file:
            app = sgtk.platform.current_bundle()

            # build environment details for this context:
            try:
                work_area = WorkArea(app.context)
            except Exception, e:
                return None

            # get the current file path:
            try:
                current_path = get_current_path(app, SAVE_FILE_AS_ACTION, work_area.context)
            except Exception, e:
                return None

            self._current_file = self._fileitem_from_path(current_path, work_area)
        return self._current_file

    def _fileitem_from_path(self, path, work_area):
        """
        Build a FileItem from the specified path and work area

        :param path:        The path of the file to construct a FileItem for
        :param work_area:   A WorkArea instance representing the work area the file is in
        :returns:           A FileItem representing the specified path in the specified work area
        """
        if not path or not work_area:
            return None

        # figure out if it's a publish or a work file:
        is_publish = False
        if work_area.work_template and work_area.work_template.validate(path):
            is_publish = False
        elif work_area.publish_template and work_area.publish_template.validate(path):
            is_publish = True
        else:
            # it's neither or we don't have a template that validates against it:
            return None

        # build fields dictionary and construct key:
        fields = work_area.context.as_template_fields(work_area.work_template)

        base_template = work_area.publish_template if is_publish else work_area.work_template
        template_fields = base_template.get_fields(path)
        fields = dict(chain(template_fields.iteritems(), fields.iteritems()))

        file_key = FileItem.build_file_key(fields, work_area.work_template,
                                           work_area.version_compare_ignore_fields)

        # extract details from the fields:
        details = {}
        for key_name in ["name", "version"]:
            if key_name in fields:
                details[key_name] = fields[key_name]

        # build the file item (note that this will be a very minimal FileItem instance)!
        file_item = FileItem(key = file_key,
                             is_work_file = not is_publish,
                             work_path = path if not is_publish else None,
                             work_details = fields if not is_publish else None,
                             is_published = is_publish,
                             publish_path = path if is_publish else None,
                             publish_details = fields if is_publish else None)

        return file_item

    def _apply_step_filtering(self, step_filter):
        """
        Apply the given step filters to all Entity models.

        :param step_filter: A Shotgun Step filter, directly usable in
                            a Shotgun query.
        """
        # Please note that this could be optimized: we're applying step filters
        # to all models, even if, for example, the changes in the filters are only
        # for Shot Steps, so models containing only Asset Tasks do not need to be
        # refreshed.
        for _, _, model in self._entity_models:
            if model.supports_step_filtering:
                model.update_filters(step_filter)
