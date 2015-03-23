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
Qt widget where the user can enter name, version and file type in order to save the
current work file.  Also give the user the option to select the file to save from
the list of current work files.
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui


from .entity_tree.entity_tree_form import EntityTreeForm
from .my_tasks.my_tasks_form import MyTasksForm
from .file_list.file_list_form import FileListForm

from .find_files import FileFinder
from .file_model import FileModel


from .ui.browser_form import Ui_BrowserForm


class BrowserForm(QtGui.QWidget):
    """
    UI for saving a work file
    """
    create_new_task = QtCore.Signal(object, object)# entity, step
    file_selected = QtCore.Signal(object)# file
    file_double_clicked = QtCore.Signal(object)# file
    file_context_menu_requested = QtCore.Signal(object, QtCore.QPoint)# file, pnt
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        self._file_model = None

        # set up the UI
        self._ui = Ui_BrowserForm()
        self._ui.setupUi(self)
        
        self._ui.file_browser_tabs.currentChanged.connect(self._on_file_tab_changed)
        
    @property
    def work_files_visible(self):
        """
        """
        file_form = self._ui.file_browser_tabs.currentWidget()
        if not file_form:
            return False
        return file_form.work_files_visible

    @property
    def publishes_visible(self):
        """
        """
        file_form = self._ui.file_browser_tabs.currentWidget()
        if not file_form:
            return False
        return file_form.publishes_visible

        
    def closeEvent(self, event):
        """
        """
        # is there any clean-up to be done?
        # (TODO)
        return QtGui.QWidget.closeEvent(self, event)
    
    def set_models(self, my_tasks_model, entity_models, file_model):
        """
        """
        if my_tasks_model:
            # create my tasks form:
            my_tasks_form = MyTasksForm(my_tasks_model, self)
            my_tasks_form.task_selected.connect(self._on_my_task_selected)
            self._ui.task_browser_tabs.addTab(my_tasks_form, "My Tasks")
            my_tasks_form.create_new_task.connect(self._on_create_new_my_task)        
        
        for caption, model in entity_models:
            # create new entity form:
            entity_form = EntityTreeForm(model, caption, self)
            entity_form.entity_selected.connect(self._on_entity_selected)
            self._ui.task_browser_tabs.addTab(entity_form, caption)
            entity_form.create_new_task.connect(self._on_create_new_entity_task)        

        if file_model:
            # attach file model to the file views:
            self._file_model = file_model
            
            # add an 'all files' tab:
            all_files_form = FileListForm("All Files", show_work_files=True, show_publishes=True, parent=self)
            self._ui.file_browser_tabs.addTab(all_files_form, "All")
            all_files_form.set_model(self._file_model)
            all_files_form.file_selected.connect(self._on_file_selected)
            all_files_form.file_double_clicked.connect(self._on_file_double_clicked)
            all_files_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
            
            # create the workfiles proxy model & form:
            work_files_form = FileListForm("Work Files", show_work_files=True, show_publishes=False, parent=self)
            work_files_form.set_model(self._file_model)
            self._ui.file_browser_tabs.addTab(work_files_form, "Working")
            work_files_form.file_selected.connect(self._on_file_selected)
            work_files_form.file_double_clicked.connect(self._on_file_double_clicked)
            work_files_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
                
            # create the publish proxy model & form:
            publishes_form = FileListForm("Publishes", show_work_files=False, show_publishes=True, parent=self)
            publishes_form.set_model(self._file_model)
            self._ui.file_browser_tabs.addTab(publishes_form, "Publishes")
            publishes_form.file_selected.connect(self._on_file_selected)
            publishes_form.file_double_clicked.connect(self._on_file_double_clicked)
            publishes_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)            
            
            # create any user-sandbox/configured tabs:
            # (AD) TODO               
    
    def _on_file_context_menu_requested(self, file, pnt):
        """
        """
        local_pnt = self.sender().mapTo(self, pnt)
        self.file_context_menu_requested.emit(file, local_pnt)
    
    def _on_my_task_selected(self, idx):
        """
        """
        if not idx or not idx.isValid():
            return None
        
        # get the item for the specified index:
        task_item = idx.model().itemFromIndex(idx)
        
        # and extract the information we need from it:
        sg_data = task_item.get_sg_data()
        entity = sg_data.get("entity", {})
        step = sg_data.get("step", {})
        step_name = step.get("name")
        task_name = sg_data.get("content")

        # build the search details:
        details = FileFinder.SearchDetails("%s - %s" % (step_name, task_name))
        details.task = {"type":"Task", "id":sg_data["id"]}
        if entity:
            details.entity = {"type":entity["type"], "id":entity["id"]}
        if step:
            details.step = {"type":step["type"], "id":step["id"]}
        details.is_leaf = True
        
        # refresh files:
        self._file_model.refresh_files([details])
        
    def _on_entity_selected(self, idx):
        """
        Called when something has been selected in an entity tree view.  From 
        this selection, a list of publishes and work files can then be found
        which will be used to populate the main file grid/details view.
        """
        if not idx or not idx.isValid():
            return None
        
        # get the item for the specified index:
        entity_item = idx.model().itemFromIndex(idx)
        
        # first get searches for the entity item:
        search_details = self._get_item_searches(entity_item)

        # refresh files:
        self._file_model.refresh_files(search_details)    

    def _get_item_searches(self, entity_item):
        """
        """
        item_search_pairs = []

        # get the entities for this item:
        item_entities = self._get_search_entities(entity_item)
        
        model = entity_item.model()
        model_entity_type = model.get_entity_type()
        
        search_details = []
        for name, item, entity in item_entities:
            details = self._get_search_details_for_item(name, item, entity)
            search_details.append(details)
            
            # iterate over children:
            for ri in range(item.rowCount()):
                child_item = item.child(ri)
                child_item_entities = self._get_search_entities(child_item)
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

    def _get_search_entities(self, item):
        """
        Based on the current item, get the entities that should be used when
        searching for files.
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

    def _on_create_new_my_task(self, idx):
        """
        """
        if not idx or not idx.isValid():
            # can't create a new task if we don't have one
            # available to base it on
            return
        
        my_tasks_form = self.sender()
        my_tasks_model = idx.model()
        task_item = my_tasks_model.itemFromIndex(idx)
        
        # determine the currently selected task:
        sg_data = task_item.get_sg_data()
        if not sg_data:
            return
        
        entity = sg_data.get("entity", {})
        step = sg_data.get("step", {})

        # emit the signal for this task:
        self.create_new_task.emit(entity, step)
                
    def _on_create_new_entity_task(self, idx):
        """
        """
        if not idx or not idx.isValid():
            # can't create a new task if we don't have one
            # available to base it on
            return
        
        entity_form = self.sender()
        entity_model = idx.model()
        entity_item = entity_model.itemFromIndex(idx)
        
        # determine the currently selected entity:
        entity = entity_model.get_entity(entity_item)
        if not entity:
            return
        
        if entity.get("type") == "Step":
            # can't create tasks on steps!
            return
        
        # if this is a task then assume that the user wants to create a new task
        # for the selected task's linked entity
        step = None
        if entity.get("type") == "Task":
            step = entity.get("step")
            entity = entity.get("entity")
            if not entity:
                return
                        
        # and emit the signal for this task:
        self.create_new_task.emit(entity, step)
    
    def _on_file_tab_changed(self, idx):
        """
        """
        selected_file = None
        
        form = self._ui.file_browser_tabs.widget(idx)
        if form and isinstance(form, FileListForm):
            # get the selected file from the form:
            selected_file = form.selected_file
            
        # update the selected file:
        self.file_selected.emit(selected_file)

    def _on_file_selected(self, idx):
        """
        """
        selected_file = None
        if idx:
            # extract the file item from the index:
            selected_file = idx.data(FileModel.FILE_ITEM_ROLE)

        self.file_selected.emit(selected_file)
        
    def _on_file_double_clicked(self, idx):
        """
        """
        item_type = idx.data(FileModel.NODE_TYPE_ROLE)
        
        if item_type == FileModel.FOLDER_NODE_TYPE:
            # selection is a folder so move into that folder
            # TODO
            pass
        elif item_type == FileModel.FILE_NODE_TYPE:
            # this is a file so perform the default action for the file
            selected_file = idx.data(FileModel.FILE_ITEM_ROLE)
            self.file_double_clicked.emit(selected_file)

            
            