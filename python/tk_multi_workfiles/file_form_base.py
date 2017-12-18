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

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")

from .file_model import FileModel
from .my_tasks.my_tasks_model import MyTasksModel
from .scene_operation import get_current_path, SAVE_FILE_AS_ACTION
from .file_item import FileItem
from .work_area import WorkArea
from .actions.new_task_action import NewTaskAction
from .user_cache import g_user_cache
from .util import monitor_qobject_lifetime, resolve_filters, get_sg_entity_name_field

logger = sgtk.platform.get_logger(__name__)


class ShotgunUpdatableEntityModel(ShotgunEntityModel):
    def __init__(self, entity_type, filters, hierarchy, fields, *args, **kwargs):
        self._entity_type = entity_type
        self._original_filters = filters
        self._hierarchy = hierarchy
        self._fields = fields
        super(ShotgunUpdatableEntityModel, self).__init__(
            entity_type,
            filters,
            hierarchy,
            fields,
            *args,
            **kwargs
        )

    def update_filters(self, extra_filters):
        filters = self._original_filters[:] # Copy the list to not update the reference
        filters.append(extra_filters)
        logger.info("Refreshing data with %s -> %s" % (extra_filters, filters))
        self._load_data(
            self._entity_type,
            filters,
            self._hierarchy,
            self._fields
        )
        self.async_refresh()

    def item_from_entity(self, entity_type, entity_id):
        """
        """
        logger.info("Looking for %s %s..." % (entity_type, entity_id))
        self.ensure_data_is_loaded()
        # If dealing with the primary entity type this model represent, just
        # call the base implementation.
        if entity_type == self.get_entity_type():
            return super(ShotgunUpdatableEntityModel, self).item_from_entity(
                entity_type, entity_id
            )
        # If not dealing with the primary entity type, we need to traverse the
        # model to find the entity
        # If the model is empty, just bail out
        if not self.rowCount():
            return None
        parent_list = [self.invisibleRootItem()]
        while parent_list:
            parent = parent_list.pop()
            logger.info("Checking items under %s" % parent)
            for row_i in range(parent.rowCount()):
                item = parent.child(row_i)
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                entity = self.get_entity(item)
                logger.info("Got %s from %s" % (entity, item))
                if entity and entity["type"] == entity_type and entity["id"] == entity_id:
                    return item
                if item.hasChildren():
                    logger.info("Adding %s to parent list" % item)
                    parent_list.append(item)

    def item_from_field_value(self, item_field_value):
        logger.info("Looking for %s" % item_field_value)
        self.ensure_data_is_loaded()
        if not self.rowCount():
            return None
        parent_list = [self.invisibleRootItem()]
        while parent_list:
            parent = parent_list.pop()
            logger.info("Checking items under %s" % parent)
            for row_i in range(parent.rowCount()):
                item = parent.child(row_i)
                if self.canFetchMore(item.index()):
                    self.fetchMore(item.index())
                value = item.data(self.SG_ASSOCIATED_FIELD_ROLE)
                logger.info("Got %s from %s" % (value, item))
                if value == item_field_value:
                    return item
                if item.hasChildren():
                    logger.info("Adding %s to parent list" % item)
                    parent_list.append(item)



class FileFormBase(QtGui.QWidget):
    """
    Implementation of file form base class.  Contains initialisation and functionality
    used by both the File Open & File Save dialogs.
    """
    def __init__(self, parent, use_deferred_queries=False):
        """
        Construction

        :param parent:  The parent QWidget for this form
        """
        QtGui.QWidget.__init__(self, parent)

        self._current_file = None
        self._deferred_queries = {}

        # create a single instance of the task manager that manages all
        # asynchrounous work/tasks.
        self._bg_task_manager = BackgroundTaskManager(self, max_threads=8)
        monitor_qobject_lifetime(self._bg_task_manager, "Main task manager")
        self._bg_task_manager.start_processing()

        shotgun_globals.register_bg_task_manager(self._bg_task_manager)

        # build the various models:
        self._my_tasks_model = self._build_my_tasks_model()
        self._entity_models, self._deferred_queries = self._build_entity_models(use_deferred_queries)
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
        for _, model in self._entity_models:
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

    def _build_entity_models(self, use_deferred_queries=False):
        """
        Build all entity models to be used by the file open/save dialogs.

        :returns:   A list of ShotgunEntityModel instances for each entity (and hierarchy) defined
                    in the app configuration
        """
        app = sgtk.platform.current_bundle()

        entity_models = []
        deferred_queries = {}

        # set up any defined task trees:
        entities = app.get_setting("entities", [])
        for ent in entities:
            caption = ent.get("caption", None)
            entity_type = ent.get("entity_type")
            filters = ent.get("filters", [])
            hierarchy = ent.get("hierarchy", [])

            linked_entity_type = None
            if use_deferred_queries and entity_type == "Task":
                # If dealing with Tasks, we don't want to retrieve all of them and
                # end up with a huge data set. So we retrieve the entities they could
                # be linked to, and retrieve Tasks for these entities only when we
                # need them.
                # Retrieve the linked entity type from the filters
                for filter in filters:
                    if filter[0] == "entity" and filter[1] == "type_is":
                        linked_entity_type = filter[2]
                        break
                if linked_entity_type:
                    # If we found the linked entity type, we need to change the
                    # request which will be send to the ShotgunModel
                    # TODO: find a way to apply the filter that we might have at
                    # the task level (e.g. sg_status_list is "ip") to the retrieved
                    # files.
                    unlinked_filters = []
                    search_pattern = re.compile("^entity\.%s\.(.+)" % linked_entity_type)
                    for filter in filters:
                        m = re.match(search_pattern, filter[0])
                        if m:
                            unlinked_filters.append([m.group(1), filter[1], filter[2]])
                    # tweak the hierarchy
                    unlinked_hierarchy = []
                    for part in hierarchy:
                        m = re.match(search_pattern, part)
                        if m:
                            unlinked_hierarchy.append(m.group(1))
                        elif part == "entity":
                            # Replace with the Entity name
                            unlinked_hierarchy.append(
                                get_sg_entity_name_field(linked_entity_type)
                            )
                    deferred_queries[linked_entity_type] = {
                        "label": caption,
                        "query": {
                            "entity_type": "Task",
                            "filters": filters,
                            "fields": hierarchy,
                        }
                    }
                    logger.debug("Replacing %s with %s" % (filters, unlinked_filters))
                    filters = unlinked_filters
                    logger.debug("Replacing %s with %s" % (hierarchy, unlinked_hierarchy))
                    hierarchy = unlinked_hierarchy
                    entity_type = linked_entity_type

            # Check the hierarchy to use for the model for this entity:
            if not hierarchy:
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

            model = ShotgunUpdatableEntityModel(
                entity_type,
                resolved_filters,
                hierarchy,
                fields,
                parent=self,
                bg_task_manager=self._bg_task_manager
            )
            monitor_qobject_lifetime(model, "Entity Model")
            entity_models.append((caption, model))
            model.async_refresh()

        return entity_models, deferred_queries

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
        for _, entity_model in self._entity_models:
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

    def _apply_step_filters(self, step_filters):
        logger.info("Step filter %s" % step_filters)
        for _, model in self._entity_models:
            model.update_filters(step_filters)
