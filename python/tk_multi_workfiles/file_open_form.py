# Copyright (c) 2014 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Qt widget that presents the user with a list of work files and publishes
so that they can choose one to open
"""

import copy

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from sgtk import TankError

from .ui.file_open_form import Ui_FileOpenForm
from .entity_tree_form import EntityTreeForm
from .my_tasks_form import MyTasksForm
from .file_list_form import FileListForm

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

shotgun_data = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")
ShotgunDataRetriever = shotgun_data.ShotgunDataRetriever

from .find_files import FileFinder
from .file_model import FileModel
from .my_tasks_model import MyTasksModel
from .publishes_proxy_model import PublishesProxyModel
from .work_files_proxy_model import WorkFilesProxyModel, FileProxyModel

class FileOpenForm(QtGui.QWidget):
    """
    UI for opening a publish or work file.  Presents a list of available files to the user
    so that they can choose one to open in addition to any other user-definable actions.
    """
    
    @property
    def exit_code(self):
        return self._exit_code    
    
    def __init__(self, init_callback, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._exit_code = QtGui.QDialog.Rejected
        
        # create the data retriever used to download thumbnails in the background:
        self._sg_data_retriever = ShotgunDataRetriever(self)
        # start it!
        self._sg_data_retriever.start()
        
        # set up the UI
        self._ui = Ui_FileOpenForm()
        self._ui.setupUi(self)
        
        # initialize task trees:
        self._initilize_task_trees()
             
        # initialize the file views:
        self._initilize_file_views()
                
        # hook up all other controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)
        self._ui.open_btn.clicked.connect(self._on_open)

        self.__context_cache = {}

        self._selected_file = None

        # call init callback:
        init_callback(self)
    
    def closeEvent(self, event):
        """
        """
        self._sg_data_retriever.stop()
        return QtGui.QWidget.closeEvent(self, event)

    def _initilize_task_trees(self):
        """
        Initialize the task trees
        """
        app = sgtk.platform.current_bundle()

        # set up 'My Tasks':        
        if app.context.user:
            filters = [["project", "is", app.context.project],
                       ["task_assignees", "is", app.context.user]]
            
            model = MyTasksModel(filters, self)
            model.async_refresh()
            
            # create my tasks form:
            my_tasks_form = MyTasksForm(model, self)
            my_tasks_form.task_selected.connect(self._on_my_task_selected)
            self._ui.task_browser_tabs.addTab(my_tasks_form, "My Tasks")
        
        # set up any defined task trees:
        entities = app.get_setting("entities", [])
        for ent in entities:
            caption = ent.get("caption", None)
            entity_type = ent.get("entity_type")
            filters = ent.get("filters")
            
            # resolve any magic tokens in the filter
            resolved_filters = []
            for filter in filters:
                resolved_filter = []
                for field in filter:
                    if field == "{context.project}":
                        field = app.context.project
                    elif field == "{context.entity}":
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
            model = ShotgunEntityModel(entity_type, resolved_filters, hierarchy, parent=self)
            model.async_refresh()
            
            # create new entity form:
            entity_form = EntityTreeForm(model, caption, self)
            entity_form.entity_selected.connect(self._on_entity_selected)
            self._ui.task_browser_tabs.addTab(entity_form, caption)
        
    def _initilize_file_views(self):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # create the model that represents all files:
        self._file_model = FileModel(self._sg_data_retriever, self)

        # add an 'all files' tab:
        all_files_model = FileProxyModel(show_work_files=True, show_publishes=True, parent=self)
        all_files_model.setSourceModel(self._file_model)
        all_files_model.sort(0)
        all_files_form = FileListForm("All Files", self)
        self._ui.file_browser_tabs.addTab(all_files_form, "All")
        all_files_form.set_model(all_files_model)
        all_files_form.file_selected.connect(self._on_file_selected)
        
        # create the workfiles proxy model & form:
        work_files_model = FileProxyModel(show_work_files=True, show_publishes=False, parent=self)
        work_files_model.setSourceModel(self._file_model)
        work_files_form = FileListForm("Work Files", self)
        work_files_form.set_model(work_files_model)
        self._ui.file_browser_tabs.addTab(work_files_form, "Working")
        work_files_form.file_selected.connect(self._on_file_selected)
            
        # create the publish proxy model & form:
        publishes_model = FileProxyModel(show_work_files=False, show_publishes=True, parent=self)
        publishes_model.setSourceModel(self._file_model)
        publishes_form = FileListForm("Publishes", self)
        publishes_form.set_model(publishes_model)
        self._ui.file_browser_tabs.addTab(publishes_form, "Publishes")
        publishes_form.file_selected.connect(self._on_file_selected)
        
        # create any user-sandbox/configured tabs:
        # (AD) TODO
        
    def _on_file_selected(self, idx):
        """
        """
        while idx and isinstance(idx.model(), QtGui.QSortFilterProxyModel):
            idx = idx.model().mapToSource(idx)
        
        self._selected_file = None
        if idx:
            # extract the file item from the index:
            self._selected_file = idx.data(FileModel.FILE_ITEM_ROLE)
            
        if self._selected_file:
            self._ui.open_btn.setEnabled(True)
        else:
            # disable the open button:
            self._ui.open_btn.setEnabled(False)
            
        #print "Selected File: %s" % self._selected_file
        
    def get_selected_file_details(self):
        """
        """
        if not self._file_model:
            return None
        
        if not self._selected_file:
            return None
        
        key = self._selected_file.key
        info = self._file_model.get_file_info(key)
        if not info:
            return None
        
        versions, context, work_template, publish_template = info
                
                
                
        
        
    """
    Interface on handler
    
    def _on_open_publish(self, publish_file, work_file):
    def _on_open_workfile(self, work_file, publish_file):
    def _on_open_previous_publish(self, file):
    def _on_open_previous_workfile(self, file):
    def _on_new_file(self):
    
    typically, the highest version publish file and the highest version work file
    
    """
        
    def _on_my_task_selected(self, task_index):
        """
        """
        if not task_index or not task_index.isValid():
            return None

        model = task_index.model()
        
        # get the item for the specified index:
        task_item = model.itemFromIndex(task_index)
        
        # and extract the information we need from it:
        sg_data = task_item.get_sg_data()
        step = sg_data.get("step", {})
        step_name = step.get("name")
        task_name = sg_data.get("content")

        # build the search details:
        details = FileFinder.SearchDetails("%s - %s" % (step_name, task_name))
        details.task = {"type":"Task", "id":sg_data["id"]}
        details.is_leaf = True
        
        # refresh files:
        self._file_model.refresh_files([details])
        
    def _on_entity_selected(self, entity_index):
        """
        Called when something has been selected in an entity tree view.  From 
        this selection, a list of publishes and work files can then be found
        which will be used to populate the main file grid/details view.
        """
        if not entity_index:
            return None
        
        # get the item for the specified index:
        entity_item = entity_index.model().itemFromIndex(entity_index)
        
        # first get searches for the entity item:
        search_details = self._get_item_searches(entity_item)

        # refresh files:
        self._file_model.refresh_files(search_details)
        
    def _get_item_searches(self, entity_item):
        """
        """
        item_search_pairs = []

        # get the entities for this item:
        item_entities = self._get_item_entities(entity_item)
        
        model = entity_item.model()
        model_entity_type = model.get_entity_type()
        
        search_details = []
        for name, item, entity in item_entities:
            details = self._get_search_details_for_item(name, item, entity)
            search_details.append(details)
            
            # iterate over children:
            for ri in range(item.rowCount()):
                child_item = item.child(ri)
                child_item_entities = self._get_item_entities(child_item)
                for c_name, c_item, c_entity in child_item_entities:
                    if (c_item.rowCount() == 0
                        and c_entity 
                        and c_entity["type"] == model_entity_type):
                        # add a search for this child item:
                        child_details = self._get_search_details_for_item(c_name, c_item, c_entity)
                        search_details.append(child_details)
                    else:
                        # this is not a leaf item so add it to the children:
                        details.child_entities.append({"name":c_name, "entity":c_entity})
                        
        return search_details

    def _get_item_entities(self, item):
        """
        """
        entities = []
        
        model = item.model()
        item_entity = model.get_entity(item)
        if not item_entity:
            return entities
        
        item_entity = {"type":item_entity["type"], "id":item_entity["id"]}

        collapsed_steps = False
        if item_entity.get("type") == "Step" and model.get_entity_type() == "Task":
            # item represents a Step and not a leaf so special case if children are leaf tasks 
            # as we can collapse step and task together:
            for ri in range(item.rowCount()):
                child_item = item.child(ri)
                child_entity = model.get_entity(child_item)
                if child_entity.get("type") == "Task":
                    # have a leaf level task under a step!
                    name = "%s - %s" % (item.text(), child_item.text())
                    entities.append((name, child_item, child_entity))
                    collapsed_steps = True        

        if not collapsed_steps:
            entities.append((item.text(), item, item_entity))
            
        return entities
        
    def _get_search_details_for_item(self, name, item, entity):
        """
        """
        app = sgtk.platform.current_bundle()
        model = item.model()
        
        details = FileFinder.SearchDetails(name)
        
        entity_type = entity["type"]
        if item.rowCount() == 0 and entity_type == model.get_entity_type():
            details.is_leaf = True
        
        if entity_type == "Task":
            details.task = entity
        elif entity_type == "Step":
            details.step = entity
        else:
            details.entity = entity
            
            # see if we can find a task or step as well:
            parent_item = item.parent()
            while parent_item:
                parent_entity = model.get_entity(parent_item)
                if parent_entity:
                    parent_entity = {"type":parent_entity["type"], "id":parent_entity["id"]}
                    parent_entity_type = parent_entity["type"]
                    if parent_entity_type == "Task":
                        # found a specific task!
                        details.task = parent_entity
                        details.step = None
                        # this is the best we can do so lets stop looking!                        
                        break
                    elif parent_entity_type == "Step":
                        # found a specific step!
                        details.step = parent_entity
                        # don't break as we would prefer to find a task entity!            

                parent_item = parent_item.parent()

        return details
        
    def _get_selected_file(self):
        """
        """
        pass
        
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()
        
    def _on_open(self):
        self._exit_code = QtGui.QDialog.Accepted
        self.close()
        