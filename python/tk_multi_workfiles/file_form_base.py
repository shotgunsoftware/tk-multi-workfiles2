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
import random

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

from .util import dbg_connect_to_destroyed

import threading
import random

class SgRunner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self._run = True
        self._sg_searches = [
            {"entity_type":"Task",
            "filters":[['project', 'is', {'type': 'Project', 'name': 'Another Demo Project', 'id': 67}], ['entity', 'type_is', 'Asset']],
            "fields":['project', 'code', 'description', 'image', 'entity.Asset.sg_asset_type', 'entity', 'content', 'step', 'sg_status_list', 'task_assignees', 'name'],
            "order":[]},
            {"entity_type":"Task",
            "filters":[['project', 'is', {'type': 'Project', 'name': 'Another Demo Project', 'id': 67}], ['entity', 'type_is', 'Shot']],
            "fields":['project', 'entity.Shot.sg_sequence', 'code', 'description', 'image', 'entity', 'content', 'step', 'sg_status_list', 'task_assignees', 'name'],
            "order":[]}
            ]
        self._thread_local = threading.local()

    @property
    def _shotgun(self):
        self._lock.acquire()
        try:
            if not hasattr(self._thread_local, "sg"):
                self._thread_local.sg = sgtk.util.shotgun.create_sg_connection()
            return self._thread_local.sg
        finally:
            self._lock.release()

    def stop(self):
        self._lock.acquire()
        try:
            self._run = False
        finally:
            self._lock.release()
            
    def run(self):
        while True:
            self._lock.acquire()
            try:
                if not self._run:
                    break
            finally:
                self._lock.release()

            sg_search = self._sg_searches[random.randint(0, len(self._sg_searches)-1)]
            res = self._shotgun.find(sg_search["entity_type"], 
                                     sg_search["filters"],
                                     sg_search["fields"],
                                     sg_search["order"])

class FileFormBase(QtGui.QWidget):
    """
    """
    def __init__(self, parent):
        """
        """
        QtGui.QWidget.__init__(self, parent)

        self._current_file = None

        # create a single instance of the shotgun data retriever:
        self._sg_data_retriever = None#ShotgunDataRetriever()
        #dbg_connect_to_destroyed(self._sg_data_retriever, "Primary data retriever")
        #self._sg_data_retriever.start()

        # build the various models:
        self._my_tasks_model = None#self._build_my_tasks_model()
        self._entity_models = []#self._build_entity_models()
        self._file_model = QtGui.QStandardItemModel()#None#self._build_file_model()

        # ---------------------------------------------------------------
        # DEBUG TEST
        self._sg_runner_threads = []
        self._sg_runner_threads.append(SgRunner())
        self._sg_runner_threads.append(SgRunner())
        for thread in self._sg_runner_threads:
            thread.start()

        #self._dbg_model = QtGui.QStandardItemModel()

        # ---------------------------------------------------------------

        
            

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
            #self._file_model.destroy()
            # note, it's important we call deleteLater here otherwise PySide won't
            # actually clean up the model correctly!
            self._file_model.deleteLater()
            self._file_model = None
        if self._my_tasks_model:
            self._my_tasks_model.destroy()
            self._my_tasks_model.deleteLater()
            self._my_tasks_model = None
        for _, model in self._entity_models:#entity_models:
            model.destroy()
            model.deleteLater()
        self._entity_models = []

        for thread in self._sg_runner_threads:
            print "Stopping sg runner thread..."
            thread.stop()
            thread.join()
            print " > Stopped!"
        #self._dbg_model.deleteLater()

        # stop the shotgun data retriever:
        if self._sg_data_retriever:
            self._sg_data_retriever.stop()
            self._sg_data_retriever.deleteLater()
            self._sg_data_retriever = None

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

        model = MyTasksModel(filters, extra_display_fields, parent=None, bg_task_manager=None)
        dbg_connect_to_destroyed(model, "My Tasks Model")
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

            model = ShotgunEntityModel(entity_type, resolved_filters, hierarchy, fields, parent=None, 
                                       bg_task_manager=None)
            dbg_connect_to_destroyed(model, "Entity Model")
            entity_models.append((caption, model))
            model.async_refresh()
            
        return entity_models

    def _build_file_model(self):
        """
        """
        file_model = FileModel(self._sg_data_retriever, parent=None)
        dbg_connect_to_destroyed(file_model, "File Model")
        return file_model
    
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

    g_counter = 0
    def _refresh_all_async(self):
        """
        """
        #print "Refreshing"

        self._dbg_re_populate_model()
        return

        if random.randint(0, 100) > 50:
            if self._my_tasks_model:
                self._my_tasks_model.async_refresh()
            for _, entity_model in self._entity_models:
                entity_model.async_refresh()
            if self._file_model:
                self._file_model.async_refresh()

        dummy_search_details = []
        dummy_search_details.append([{'is_leaf': False, 'name': 'Sequence 01', 'child_entities': [{'name': '123', 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}}, {'name': 'shot_010', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}}, {'name': 'shot_020', 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}}, {'name': 'The End', 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}}, {'name': '\xd0\xa0\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xd0\xb8 \xd0\xb2\xd1\x8b\xd1\x81\xd1\x82\xd1\x80\xd0\xb5\xd0\xbb\xd0\xb0', 'entity': {'type': 'Shot', 'id': 916, 'name': '\xd0\xa0\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xd0\xb8 \xd0\xb2\xd1\x8b\xd1\x81\xd1\x82\xd1\x80\xd0\xb5\xd0\xbb\xd0\xb0'}}], 'entity': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}}])
        dummy_search_details.append([{'is_leaf': False, 'name': '123', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 230}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Anm', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 230}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 230}}])
        dummy_search_details.append([{'is_leaf': False, 'name': 'shot_010', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 178}}, {'is_leaf': True, 'name': 'Comp - MoreComp', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreComp', 'step': {'type': 'Step', 'id': 8, 'name': 'Comp'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 233}}, {'is_leaf': True, 'name': 'FX - Effects', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Effects', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 235}}, {'is_leaf': True, 'name': 'FX - More FX', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'More FX', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 243}}, {'is_leaf': True, 'name': 'Light - EvenMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'EvenMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 252}}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/b84f1f336e085adf634588b1e5dbdbb073ae0f52/199e51cb1f23779739ad03503396843f7fdf1db0/Screen_Shot_2014-12-08_at_11.49.18_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1435962178&Signature=hMIG76Ejcba5Fxk3zZR4qOCes1s%3D', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 232}}, {'is_leaf': True, 'name': 'Light - MoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 242}}, {'is_leaf': True, 'name': 'Light - StillMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'StillMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 253}}, {'is_leaf': True, 'name': 'Light - YetMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'YetMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 251}}, {'is_leaf': True, 'name': 'More Anim - MoreAnim', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreAnim', 'step': {'type': 'Step', 'id': 17, 'name': 'More Anim'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 255}}, {'is_leaf': True, 'name': 'Roto - Roto', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Roto', 'step': {'type': 'Step', 'id': 3, 'name': 'Roto'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 254}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Anm', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 178}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 178}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Comp', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Comp - MoreComp', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreComp', 'step': {'type': 'Step', 'id': 8, 'name': 'Comp'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 233}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'FX', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'FX - Effects', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Effects', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 235}}, {'is_leaf': True, 'name': 'FX - More FX', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'More FX', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 243}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Light', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Light - EvenMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'EvenMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 252}}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/b84f1f336e085adf634588b1e5dbdbb073ae0f52/199e51cb1f23779739ad03503396843f7fdf1db0/Screen_Shot_2014-12-08_at_11.49.18_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1435962178&Signature=hMIG76Ejcba5Fxk3zZR4qOCes1s%3D', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 232}}, {'is_leaf': True, 'name': 'Light - MoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 242}}, {'is_leaf': True, 'name': 'Light - StillMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'StillMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 253}}, {'is_leaf': True, 'name': 'Light - YetMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'YetMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 251}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'EvenMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'EvenMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 252}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/b84f1f336e085adf634588b1e5dbdbb073ae0f52/199e51cb1f23779739ad03503396843f7fdf1db0/Screen_Shot_2014-12-08_at_11.49.18_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1435962178&Signature=hMIG76Ejcba5Fxk3zZR4qOCes1s%3D', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 232}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'MoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 242}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'StillMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'StillMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 253}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'YetMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'YetMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 251}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'More Anim', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'More Anim - MoreAnim', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreAnim', 'step': {'type': 'Step', 'id': 17, 'name': 'More Anim'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 255}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Roto', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Roto - Roto', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Roto', 'step': {'type': 'Step', 'id': 3, 'name': 'Roto'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 254}}])
        dummy_search_details.append([{'is_leaf': False, 'name': 'shot_020', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 244}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Light', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 244}}])
        dummy_search_details.append([{'is_leaf': False, 'name': 'The End', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 239}}, {'is_leaf': True, 'name': 'Anm - Animation B', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}, 'content': 'Animation B', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 240}}, {'is_leaf': True, 'name': 'Comp - Finalize', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}, 'content': 'Finalize', 'step': {'type': 'Step', 'id': 8, 'name': 'Comp'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 241}}])

        #dummy_search = dummy_search_details[random.randint(0, len(dummy_search_details)-1)]
        dummy_search = dummy_search_details[FileFormBase.g_counter]
        FileFormBase.g_counter += 1
        
        searches = []
        for ds in dummy_search:
            search = FileModel.SearchDetails(ds["name"])
            search.entity = ds["entity"]
            search.is_leaf = ds["is_leaf"]
            search.child_entities = ds["child_entities"]
            searches.append(search)

        self._file_model.set_entity_searches(searches)

    def _dbg_update_groups(self, group_names):
        """
        """
        self._file_model.clear()
        
        new_items = []
        for name in group_names:
            group_item = QtGui.QStandardItem(name)
            new_items.append(group_item)

        if new_items:
            self._file_model.invisibleRootItem().appendRows(new_items)
    
    def _dbg_add_group(self, group_name):
        """
        """
        group_item = QtGui.QStandardItem(group_name)
        self._file_model.invisibleRootItem().appendRow(group_item)
        return group_item
    
    def _dbg_add_files(self, group_item, file_names):
        """
        """
        new_items = []
        for name in file_names:
            item = QtGui.QStandardItem(name)
            new_items.append(item)

        if new_items:
            group_item.appendRows(new_items)

    def _dbg_re_populate_model(self):
        """
        """
        search_id = random.randint(0, 19)
        if search_id == 0:
            self._dbg_update_groups(["Sequence 01"])
        elif search_id == 1:
            self._dbg_update_groups(["123", "Anm - Animation"])
            grp = self._dbg_add_group("Anm - Animation")
            self._dbg_add_files(grp, ["reviewtest", "reviewtest", "reviewtest", "reviewtest", "launchtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "crashtest", "shouldbreak", "reviewtest", "scene", "reviewtest", "reviewtest"])
        elif search_id == 2:
            self._dbg_update_groups(["Anm", "Anm - Animation"])
            grp = self._dbg_add_group("Anm - Animation")
            self._dbg_add_files(grp, ["reviewtest", "reviewtest", "reviewtest", "reviewtest", "launchtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "crashtest", "shouldbreak", "reviewtest", "scene", "reviewtest", "reviewtest"])
        elif search_id == 3:
            self._dbg_update_groups(["Animation"])
            grp = self._dbg_add_group("Animation")
            self._dbg_add_files(grp, ["reviewtest", "reviewtest", "reviewtest", "reviewtest", "launchtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "crashtest", "shouldbreak", "reviewtest", "scene", "reviewtest", "reviewtest"])
        elif search_id == 4:
            self._dbg_update_groups(["shot_010", "Anm - Animation", "Comp - MoreComp", "FX - Effects", "FX - More FX", "Light - EvenMoreLighting", "Light - Lighting", "Light - MoreLighting", "Light - StillMoreLighting", "Light - YetMoreLighting", "More Anim - MoreAnim", "Roto - Roto"])
            grp = self._dbg_add_group("Comp - MoreComp")
            self._dbg_add_files(grp, ["nopublishes"])
            grp = self._dbg_add_group("Light - EvenMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - Lighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - MoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - StillMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - YetMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 5:
            self._dbg_update_groups(["Anm", "Anm - Animation"])
        elif search_id == 6:
            self._dbg_update_groups(["Animation"])
        elif search_id == 7:
            self._dbg_update_groups(["Comp", "Comp - MoreComp"])
            grp = self._dbg_add_group("Comp - MoreComp")
            self._dbg_add_files(grp, ["nopublishes"])
        elif search_id == 8:
            self._dbg_update_groups(["FX", "FX - Effects", "FX - More FX"])
        elif search_id == 9:
            self._dbg_update_groups(["Light", "Light - EvenMoreLighting", "Light - Lighting", "Light - MoreLighting", "Light - StillMoreLighting", "Light - YetMoreLighting"])
            grp = self._dbg_add_group("Light - EvenMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - Lighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - MoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - StillMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._dbg_add_group("Light - YetMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 10:
            self._dbg_update_groups(["EvenMoreLighting"])
            grp = self._dbg_add_group("EvenMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 11:
            self._dbg_update_groups(["Lighting"])
            grp = self._dbg_add_group("Lighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 12:
            self._dbg_update_groups(["MoreLighting"])
            grp = self._dbg_add_group("MoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 13:
            self._dbg_update_groups(["StillMoreLighting"])
            grp = self._dbg_add_group("StillMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 14:
            self._dbg_update_groups(["YetMoreLighting"])
            grp = self._dbg_add_group("YetMoreLighting")
            self._dbg_add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 15:
            self._dbg_update_groups(["More Anim", "More Anim - MoreAnim"])
        elif search_id == 16:
            self._dbg_update_groups(["Roto", "Roto - Roto"])
        elif search_id == 17:
            self._dbg_update_groups(["shot_020", "Light - Lighting"])
        elif search_id == 18:
            self._dbg_update_groups(["Light", "Light - Lighting"])
        elif search_id == 19:
            self._dbg_update_groups(["The End", "Anm - Animation", "Anm - Animation B", "Comp - Finalize"])
            grp = self._dbg_add_group("Anm - Animation")
            self._dbg_add_files(grp, ["reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "testscene", "writenodeconversiontest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "scene", "scene", "reviewtest", "sendtoreviewtest", "testscene", "shouldbreak", "reviewtest", "writenodeconversiontest", "reviewtest", "launchtest", "writenodetest", "writenodeconversiontestb", "osxreviewtest", "crashtest", "reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "sendtoreviewtest", "testscene", "nopublishes", "reviewtest", "reviewtest", "osxreviewtest", "testscene", "scene1"])
            grp = self._dbg_add_group("Anm - Animation B")
            self._dbg_add_files(grp, ["reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "testscene", "writenodeconversiontest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "scene", "scene", "reviewtest", "sendtoreviewtest", "testscene", "shouldbreak", "reviewtest", "writenodeconversiontest", "reviewtest", "launchtest", "writenodetest", "writenodeconversiontestb", "osxreviewtest", "crashtest", "reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "sendtoreviewtest", "testscene", "nopublishes", "reviewtest", "reviewtest", "osxreviewtest", "testscene", "scene1"])
            grp = self._dbg_add_group("Comp - Finalize")
            self._dbg_add_files(grp, ["reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "testscene", "writenodeconversiontest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "scene", "scene", "reviewtest", "sendtoreviewtest", "testscene", "shouldbreak", "reviewtest", "writenodeconversiontest", "reviewtest", "launchtest", "writenodetest", "writenodeconversiontestb", "osxreviewtest", "crashtest", "reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "sendtoreviewtest", "testscene", "nopublishes", "reviewtest", "reviewtest", "osxreviewtest", "testscene", "scene1"])



    def _get_current_file(self):
        """
        """
        if not self._current_file:
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

            self._current_file = self._fileitem_from_path(current_path, env)
        return self._current_file

    def _fileitem_from_path(self, path, env):
        """
        """
        if not path or not env or not env.work_template:
            return None

        # figure out if it's a publish or a work file:
        is_publish = False
        if env.work_template and env.work_template.validate(path):
            is_publish = False
        elif env.publish_template and env.publish_template.validate(path):
            is_publish = True
        else:
            # it's neither or we don't have a template that validates against it:
            return None

        # build fields dictionary and construct key:
        fields = env.context.as_template_fields(env.work_template)

        base_template = env.publish_template if is_publish else env.work_template
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
        
        

    