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

from .actions.file_action import SeparatorFileAction
from .actions.file_action_factory import FileActionFactory

class FileOpenForm(QtGui.QWidget):
    """
    UI for opening a publish or work file.  Presents a list of available files to the user
    so that they can choose one to open in addition to any other user-definable actions.
    """
    
    perform_action = QtCore.Signal(object, object, object, object) # action, file, file_versions, environment
    create_new_task = QtCore.Signal(object, object)
    
    @property
    def exit_code(self):
        return self._exit_code    
    
    def __init__(self, init_callback, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        self._exit_code = QtGui.QDialog.Rejected
        self._my_tasks_model = None
        self._entity_models = []
        
        # create the action factory - this is used to generate actions
        # for the selected file
        self._action_factory = FileActionFactory()
        
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
        
        self._file_list_forms = []
        self._ui.file_browser_tabs.currentChanged.connect(self._on_file_tab_changed)

        self.__context_cache = {}
        
        self._selected_file = None
        self._default_open_action = None
        self._on_selected_file_changed()

        # call init callback:
        init_callback(self)

    def select_entity(self, entity):
        """
        :param entity:  The entity or task to select in the current tree/my tasks view.  If it can't be found
                        then attempt to switch tabs if it can be found in a different tab! 
        """
        pass

    def refresh_all(self):
        """
        """
        # refresh the entity models:
        self._my_tasks_model.async_refresh()
        for model in self._entity_models:
            model.async_refresh()

    
    def closeEvent(self, event):
        """
        """
        # stop the sg data retriever used to download thumbnails:
        self._sg_data_retriever.stop()
        
        # stop any model updates and background workers:
        for model in self._entity_models:
            # TODO!
            pass
        self._entity_models = []
        
        #self._my_tasks_model.
        #self._file_model.
        
        return QtGui.QWidget.closeEvent(self, event)

    def _initilize_task_trees(self):
        """
        Initialize the task trees
        """
        app = sgtk.platform.current_bundle()

        # set up 'My Tasks':
        show_my_tasks = app.get_setting("show_my_tasks_view", True)
        if show_my_tasks:
            this_user = sgtk.util.get_current_user(app.sgtk)
            if this_user:
                # filter my tasks based on the current project and user:
                filters = [["project", "is", app.context.project],
                           ["task_assignees", "is", this_user]]
                
                self._my_tasks_model = MyTasksModel(filters, self)
                self._my_tasks_model.async_refresh()
                
                # create my tasks form:
                my_tasks_form = MyTasksForm(self._my_tasks_model, self)
                my_tasks_form.task_selected.connect(self._on_my_task_selected)
                self._ui.task_browser_tabs.addTab(my_tasks_form, "My Tasks")
                my_tasks_form.create_new_task.connect(self._on_create_new_my_task)
        
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
            self._entity_models.append(model)
            model.async_refresh()
            
            # create new entity form:
            entity_form = EntityTreeForm(model, caption, self)
            entity_form.entity_selected.connect(self._on_entity_selected)
            self._ui.task_browser_tabs.addTab(entity_form, caption)
            entity_form.create_new_task.connect(self._on_create_new_entity_task)

    def _initilize_file_views(self):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # create the model that represents all files:
        self._file_model = FileModel(self._sg_data_retriever, self)

        # add an 'all files' tab:
        all_files_form = FileListForm("All Files", show_work_files=True, show_publishes=True, parent=self)
        self._ui.file_browser_tabs.addTab(all_files_form, "All")
        all_files_form.set_model(self._file_model)
        all_files_form.file_selected.connect(self._on_file_selected)
        all_files_form.file_double_clicked.connect(self._on_file_double_clicked)
        all_files_form.file_context_menu_requested.connect(self._on_show_file_context_menu)
        
        # create the workfiles proxy model & form:
        work_files_form = FileListForm("Work Files", show_work_files=True, show_publishes=False, parent=self)
        work_files_form.set_model(self._file_model)
        self._ui.file_browser_tabs.addTab(work_files_form, "Working")
        work_files_form.file_selected.connect(self._on_file_selected)
        work_files_form.file_double_clicked.connect(self._on_file_double_clicked)
        work_files_form.file_context_menu_requested.connect(self._on_show_file_context_menu)
            
        # create the publish proxy model & form:
        publishes_form = FileListForm("Publishes", show_work_files=False, show_publishes=True, parent=self)
        publishes_form.set_model(self._file_model)
        self._ui.file_browser_tabs.addTab(publishes_form, "Publishes")
        publishes_form.file_selected.connect(self._on_file_selected)
        publishes_form.file_double_clicked.connect(self._on_file_double_clicked)
        publishes_form.file_context_menu_requested.connect(self._on_show_file_context_menu)
        
        # create any user-sandbox/configured tabs:
        # (AD) TODO
        
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

        # and emit the signal for this task:
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


    def _on_file_tab_changed(self, idx):
        """
        """
        selected_file = None
        
        form = self._ui.file_browser_tabs.widget(idx)
        if form and isinstance(form, FileListForm):
            # get the selected file from the form:
            selected_file = form.selected_file
            
        # update the selected file:        
        self._selected_file = selected_file 
        self._on_selected_file_changed()
        

    def _on_file_selected(self, idx):
        """
        """
        self._selected_file = None
        if idx:
            # extract the file item from the index:
            self._selected_file = idx.data(FileModel.FILE_ITEM_ROLE)
            
        if self._selected_file:
            self._ui.open_btn.setEnabled(True)
        else:
            # disable the open button:
            self._ui.open_btn.setEnabled(False)
            
        self._on_selected_file_changed()
        
    def _on_file_double_clicked(self, idx):
        """
        """
        item_type = idx.data(FileModel.NODE_TYPE_ROLE)
        
        if item_type == FileModel.FOLDER_NODE_TYPE:
            # selection is a folder so move into that folder
            pass
        elif item_type == FileModel.FILE_NODE_TYPE:
            # this is a file so perform the default action for the file
            file = idx.data(FileModel.FILE_ITEM_ROLE)
            #self._selected_file = file
            #self._on_selected_file_changed()
            self._on_open()
            # TODO

    def _on_selected_file_changed(self):
        """
        """
        # get the available actions for this file:
        file_actions = []
        if self._selected_file:
            info = self._file_model.get_file_info(self._selected_file.key)
            if info:
                file_versions, environment = info
                file_actions = self._action_factory.get_actions(self._selected_file, file_versions, environment)
        
        if not file_actions:
            # disable both the open and open options buttons:
            self._ui.open_btn.setEnabled(False)
            self._ui.open_options_btn.setEnabled(False)
            return
        
        # update the open button:
        self._ui.open_btn.setEnabled(True)
        self._ui.open_btn.setText(file_actions[0].label)
        self._default_open_action = file_actions[0]
        
        # if we have more than one action then update the open options button:
        if len(file_actions) > 1:
            # enable the button:
            self._ui.open_options_btn.setEnabled(True)
            
            # build the menu and add the actions to it:
            menu = self._ui.open_options_btn.menu()
            if not menu:
                menu = QtGui.QMenu(self._ui.open_options_btn)
                self._ui.open_options_btn.setMenu(menu)
            menu.clear()
            self._populate_open_menu(menu, self._selected_file, file_actions[1:])
        else:
            # just disable the button:
            self._ui.open_options_btn.setEnabled(False)

    def _on_show_file_context_menu(self, file, pnt):
        """
        """
        if not file:
            return
        
        # get the file actions:
        file_actions = []
        info = self._file_model.get_file_info(file.key)
        if info:
            file_versions, environment = info
            file_actions = self._action_factory.get_actions(file, file_versions, environment)
        
        if not file_actions:
            return

        # build the context menu:
        context_menu = QtGui.QMenu(self.sender())
        self._populate_open_menu(context_menu, file, file_actions[1:])
        
        # map the point to a global position:
        pnt = self.sender().mapToGlobal(pnt)
        
        # finally, show the context menu:
        context_menu.exec_(pnt)

    def _populate_open_menu(self, menu, file, file_actions):
        """
        """
        add_separators = False
        for action in file_actions:
            if isinstance(action, SeparatorFileAction):
                if add_separators:
                    menu.addSeparator()
                    
                # ensure that we only add separators after at least one action item and
                # never more than one!
                add_separators = False
            else:
                q_action = QtGui.QAction(action.label, menu)
                q_action.triggered[()].connect(lambda a=action, f=file: self._on_open_action_triggered(a, f))
                menu.addAction(q_action)
                add_separators = True

    """
    Interface on handler
    
    def _on_open_publish(self, publish_file, work_file):
    def _on_open_workfile(self, work_file, publish_file):
    def _on_open_previous_publish(self, file):
    def _on_open_previous_workfile(self, file):
    def _on_new_file(self):
    
    typically, the highest version publish file and the highest version work file
    
    """        
        
    def _on_open(self):
        """
        """
        if not self._default_open_action:
            return
        
        self._on_open_action_triggered(self._default_open_action, self._selected_file)

    def _on_open_action_triggered(self, action, file):
        """
        """
        if (not action
            or not file
            or not self._file_model):
            # can't do anything!
            return
        
        # get the item info for the selected item:
        info = self._file_model.get_file_info(file.key)
        if not info:
            return
        file_versions, environment = info
        
        # emit signal to perform the default action.  This may result in the dialog
        # being closed so no further work should be attempted after this call
        self.perform_action.emit(action, file, file_versions, environment)

    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected
        self.close()










