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
from itertools import chain

import sgtk
from sgtk.platform.qt import QtCore, QtGui

shotgun_data = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")
ShotgunDataRetriever = shotgun_data.ShotgunDataRetriever

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel
from .file_model import FileModel
from .my_tasks.my_tasks_model import MyTasksModel

from .scene_operation import get_current_path, save_file, SAVE_FILE_AS_ACTION
from .file_item import FileItem

from .work_area import WorkArea

from .actions.new_task_action import NewTaskAction

from .user_cache import g_user_cache

class FileFormBase(QtGui.QWidget):
    """
    """
    def __init__(self, parent=None):
        """
        """
        QtGui.QWidget.__init__(self, parent)

        # create a single instance of the shotgun data retriever:        
        self._sg_data_retriever = ShotgunDataRetriever(self)
        self._sg_data_retriever.start()
        
        # build the various models:
        self._my_tasks_model = self._build_my_tasks_model()
        self._entity_models = self._build_entity_models()
        self._file_model = FileModel(self._sg_data_retriever, self)
        
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

    def clean_up(self):
        """
        """
        # clear up the various data models:
        self._file_model.clear()
        
        # stop the shotgun data retriever:
        self._sg_data_retriever.stop()

    def closeEvent(self, event):
        """
        """
        self.clean_up()
        return QtGui.QWidget.closeEvent(self, event)

    def _build_my_tasks_model(self):
        """
        """
        if not g_user_cache.current_user:
            return None

        app = sgtk.platform.current_bundle()
        show_my_tasks = app.get_setting("show_my_tasks", True)
        if not show_my_tasks:
            return None

        # filter my tasks based on the current project and user:
        filters = [["project", "is", app.context.project],
                   ["task_assignees", "is", g_user_cache.current_user]]

        # get any extra display fields we'll need to retrieve:
        extra_display_fields = app.get_setting("my_tasks_extra_display_fields")

        model = MyTasksModel(filters, extra_display_fields, self)
        model.async_refresh()
        return model 
        
    def _build_entity_models(self):
        """
        """
        app = sgtk.platform.current_bundle()
        
        entity_models = []
        
        # set up any defined task trees:
        entities = app.get_setting("entities", [])
        for ent in entities:
            caption = ent.get("caption", None)
            entity_type = ent.get("entity_type")
            filters = ent.get("filters")
            
            # resolve any magic tokens in the filter
            # Note, we always filter on the current project as the app needs templates
            # in the config to be able to find files and there is currently no way to 
            # get these from a config belonging to a different project!
            resolved_filters = [["project", "is", app.context.project]]
            for filter in filters:
                resolved_filter = []
                for field in filter:
                    if field == "{context.entity}":
                        field = app.context.entity
                    elif field == "{context.step}":
                        field = app.context.step
                    elif field == "{context.task}":
                        field = app.context.task
                    elif field == "{context.user}":
                        field = app.context.user
                    resolved_filter.append(field)
                resolved_filters.append(resolved_filter)
                            
            hierarchy = ent.get("hierarchy")
            
            # create an entity model for this query:
            fields = ["image", "description", "project", "name", "code"]
            if entity_type == "Task":
                fields += ["step", "entity", "content", "sg_status_list", "task_assignees"]
            model = ShotgunEntityModel(entity_type, resolved_filters, hierarchy, parent=self, fields=fields)
            entity_models.append((caption, model))
            model.async_refresh()
            
        return entity_models
    
    def _on_create_new_task(self, entity, step):
        """
        """
        action = NewTaskAction(entity, step)
        if action.execute(self):
            self._refresh_all_async()

    def _on_refresh_triggered(self, checked=False):
        """
        """
        self._refresh_all_async()

    def _refresh_all_async(self):
        """
        """
        if self._my_tasks_model:
            self._my_tasks_model.async_refresh()
        for _, entity_model in self._entity_models:
            entity_model.async_refresh()
        if self._file_model:
            self._file_model.async_refresh()
        
    def _get_current_file(self):
        """
        """
        app = sgtk.platform.current_bundle()

        # build environment details for this context:
        try:
            env = WorkArea(app.context)
        except Exception, e:
            return None

        # get the current file path:
        try:
            current_path = get_current_path(app, SAVE_FILE_AS_ACTION, env.context)
        except Exception, e:
            return None

        return self._fileitem_from_path(current_path, env)
    
    def _fileitem_from_path(self, path, env):
        """
        """
        if not path or not env:
            return None
        
        # figure out if it's a publish or a work file:
        is_publish = ((not env.work_template or env.work_template.validate(path))
                      and env.publish_template != env.work_template
                      and env.publish_template and env.publish_template.validate(path))

        # build fields dictionary and construct key: 
        fields = env.context.as_template_fields(env.work_template)
        base_template = env.publish_template if is_publish else env.work_template
        if base_template.validate(path):
            template_fields = base_template.get_fields(path)
            fields = dict(chain(template_fields.iteritems(), fields.iteritems()))

        file_key = FileItem.build_file_key(fields, env.work_template, 
                                           env.version_compare_ignore_fields)

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
        
        

    