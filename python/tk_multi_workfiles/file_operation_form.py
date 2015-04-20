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

class FileOperationForm(QtGui.QWidget):
    """
    """
    class CreateNewTaskEvent(object):
        """
        """
        def __init__(self, entity, step):
            self.entity = entity
            self.step = step
            self.task_created = False
    
    create_new_task = QtCore.Signal(CreateNewTaskEvent)    
    
    
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

    def clean_up(self):
        """
        """
        # clear up the various data models:
        
        # stop the shotgun data retriever:
        self._sg_data_retriever.stop()

    def refresh_all_async(self):
        """
        """
        if self._my_tasks_model:
            self._my_tasks_model.async_refresh()
            
        for _, entity_model in self._entity_models:
            entity_model.async_refresh()

    def closeEvent(self, event):
        """
        """
        self.clean_up()
        return QtGui.QWidget.closeEvent(self, event)

    def _build_my_tasks_model(self):
        """
        """
        app = sgtk.platform.current_bundle()

        # set up 'My Tasks':
        show_my_tasks = app.get_setting("show_my_tasks", True)
        if not show_my_tasks:
            return None
        
        this_user = sgtk.util.get_current_user(app.sgtk)
        if not this_user:
            return None
        
        # filter my tasks based on the current project and user:
        filters = [["project", "is", app.context.project],
                   ["task_assignees", "is", this_user]]
        
        model = MyTasksModel(filters, self)
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
        create_event = FileOperationForm.CreateNewTaskEvent(entity, step)
        self.create_new_task.emit(create_event)
        if create_event.task_created:
            self._refresh_all_async()

    def _get_current_file(self, env):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # get the current file path:
        try:
            current_path = get_current_path(app, SAVE_FILE_AS_ACTION, env.context)
        except Exception, e:
            return None
        
        if not current_path:
            return None
        
        # figure out if it's a publish or a work file:
        is_publish = ((not env.work_template or env.work_template.validate(current_path))
                      and env.publish_template != env.work_template
                      and env.publish_template and env.publish_template.validate(current_path))

        # build fields dictionary and construct key: 
        fields = env.context.as_template_fields(env.work_template)
        base_template = env.publish_template if is_publish else env.work_template
        if base_template.validate(current_path):
            template_fields = base_template.get_fields(current_path)
            fields = dict(chain(template_fields.iteritems(), fields.iteritems()))

        file_key = FileItem.build_file_key(fields, env.work_template, 
                                           env.version_compare_ignore_fields + ["version"])

        # extract details from the fields:
        details = {}
        for key_name in ["name", "version"]:
            if key_name in fields:
                details[key_name] = fields[key_name]

        # build the file item (note that this will be a very minimal FileItem instance)!
        file_item = FileItem(path = current_path if not is_publish else None,
                             publish_path = current_path if is_publish else None,
                             is_local = not is_publish,
                             is_published = is_publish,
                             details = fields,
                             key = file_key)
        
        return file_item

    