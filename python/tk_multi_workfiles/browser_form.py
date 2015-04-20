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
Qt widget where the user can enter name, version and file type in order to save the
current work file.  Also give the user the option to select the file to save from
the list of current work files.
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui


from .entity_tree.entity_tree_form import EntityTreeForm
from .my_tasks.my_tasks_form import MyTasksForm
from .file_list.file_list_form import FileListForm

from .file_model import FileModel


from .ui.browser_form import Ui_BrowserForm


class BrowserForm(QtGui.QWidget):
    """
    UI for saving a work file
    """
    create_new_task = QtCore.Signal(object, object)# entity, step
    
    work_area_changed = QtCore.Signal(object)#, object, object)# entity, step, task
    
    file_selected = QtCore.Signal(object, object)# file, env
    file_double_clicked = QtCore.Signal(object, object)# file, env
    file_context_menu_requested = QtCore.Signal(object, object, QtCore.QPoint)# file, env, pnt
    
    def __init__(self, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        #self._suppress_entity_selected_signals = False
        self._file_model = None
        self._my_tasks_form = None

        # set up the UI
        self._ui = Ui_BrowserForm()
        self._ui.setupUi(self)
        
        self._ui.file_browser_tabs.currentChanged.connect(self._on_file_tab_changed)
        self._ui.task_browser_tabs.currentChanged.connect(self._on_task_tab_changed)
        
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
            self._my_tasks_form = MyTasksForm(my_tasks_model, self)
            self._my_tasks_form.task_selected.connect(self._on_my_task_selected)
            self._ui.task_browser_tabs.addTab(self._my_tasks_form, "My Tasks")
            self._my_tasks_form.create_new_task.connect(self.create_new_task)        
        
        for caption, model in entity_models:
            # create new entity form:
            entity_form = EntityTreeForm(model, caption, self)
            entity_form.entity_selected.connect(self._on_entity_selected)
            self._ui.task_browser_tabs.addTab(entity_form, caption)
            entity_form.create_new_task.connect(self.create_new_task)        

        if file_model:
            # attach file model to the file views:
            self._file_model = file_model
            
            # add an 'all files' tab:
            all_files_form = FileListForm("All Files", show_work_files=True, show_publishes=True, parent=self)
            self._ui.file_browser_tabs.addTab(all_files_form, "All")
            all_files_form.set_model(self._file_model)
            all_files_form.file_selected.connect(self._on_file_selected)
            all_files_form.file_double_clicked.connect(self.file_double_clicked)
            all_files_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
            
            # create the workfiles proxy model & form:
            work_files_form = FileListForm("Work Files", show_work_files=True, show_publishes=False, parent=self)
            work_files_form.set_model(self._file_model)
            self._ui.file_browser_tabs.addTab(work_files_form, "Working")
            work_files_form.file_selected.connect(self._on_file_selected)
            work_files_form.file_double_clicked.connect(self.file_double_clicked)
            work_files_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
                
            # create the publish proxy model & form:
            publishes_form = FileListForm("Publishes", show_work_files=False, show_publishes=True, parent=self)
            publishes_form.set_model(self._file_model)
            self._ui.file_browser_tabs.addTab(publishes_form, "Publishes")
            publishes_form.file_selected.connect(self._on_file_selected)
            publishes_form.file_double_clicked.connect(self.file_double_clicked)
            publishes_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
            
            # create any user-sandbox/configured tabs:
            # (AD) TODO
    
    def initialize(self, env, file):
        """
        """
        if not env or not env.context or not file:
            return
        
        # update the selected entity in the various task/entity trees:
        ctx_entity = env.context.task or env.context.step or env.context.entity
        if not ctx_entity:
            return
        
        self._update_selected_entity(ctx_entity["type"], ctx_entity["id"], skip_current=False)
        
        # now start a search based off the entity:
        search_label = ctx_entity.get("name")
        if ctx_entity["type"] == "Task" and env.context.step:
            search_label = "%s - %s" % (env.context.step.get("name"), search_label)
        
        details = FileModel.SearchDetails(search_label)
        details.entity = ctx_entity
        details.is_leaf = True
        self._file_model.refresh_files([details])
        
        # Finally, select the file in the file views:
        for ti in range(self._ui.file_browser_tabs.count()):
            widget = self._ui.file_browser_tabs.widget(ti)
            widget.select_file(file, env)

    def select_file(self, file, env):
        """
        """
        for ti in range(self._ui.file_browser_tabs.count()):
            widget = self._ui.file_browser_tabs.widget(ti)
            widget.select_file(file, env)

            
    def _update_selected_entity(self, entity_type, entity_id, skip_current=True):
        """
        """
        current_widget = self._ui.task_browser_tabs.currentWidget()

        # loop through all widgets and update the selection in each one:
        for ti in range(self._ui.task_browser_tabs.count()):
            widget = self._ui.task_browser_tabs.widget(ti)
            
            if skip_current and widget == current_widget:
                continue
            
            # block signals to avoid recursion
            signals_blocked = widget.blockSignals(True)
            try:
                if isinstance(widget, MyTasksForm):
                    if entity_type == "Task":
                        widget.select_task(entity_id)
                    else:
                        widget.select_task(None)
                elif isinstance(widget, EntityTreeForm):
                    widget.select_entity(entity_type, entity_id)
            finally:
                widget.blockSignals(signals_blocked)
    
    def _on_file_context_menu_requested(self, file, env, pnt):
        """
        """
        local_pnt = self.sender().mapTo(self, pnt)
        self.file_context_menu_requested.emit(file, env, local_pnt)
    
    def _on_my_task_selected(self, task):
        """
        """
        #print "my-task selected"
        
        search_details = []
        if task:
            search_label = task.get("content")
            step = task.get("step")
            if step:
                search_label = "%s - %s" % (step.get("name"), search_label) 

            details = FileModel.SearchDetails(search_label)        
            details.entity = task
            details.is_leaf = True
            search_details.append(details)

            # update selection in other tabs to match:
            self._update_selected_entity("Task", task["id"])
            
        else:
            # update selection in other tabs to match:
            self._update_selected_entity(None, None)
        
        # refresh files:
        self._file_model.refresh_files(search_details)
        
        # emit work-area-changed signal:
        self.work_area_changed.emit(task)
        
        
    def _on_entity_selected(self, selection_details):
        """
        Called when something has been selected in an entity tree view.  From 
        this selection, a list of publishes and work files can then be found
        which will be used to populate the main file grid/details view.
        """
        #print "entity selected"

        search_details = []
        
        primary_entity = None
        if selection_details:
            label = selection_details["label"]
            primary_entity = selection_details["entity"]
            children = selection_details["children"]
            # TODO - this needs fixing.
            is_leaf = primary_entity and primary_entity["type"] == "Task"
            
            primary_details = FileModel.SearchDetails(label)
            primary_details.entity = primary_entity
            primary_details.is_leaf = is_leaf
            search_details.append(primary_details)
            
            for child_details in children:
                label = child_details["label"]
                entity = child_details["entity"]
                # TODO - and here!
                is_leaf = entity and entity["type"] == "Task"
                if not is_leaf:
                    primary_details.child_entities.append({"name":label, "entity":entity})
                else:
                    details = FileModel.SearchDetails(label)
                    details.entity = entity
                    details.is_leaf = is_leaf
                    search_details.append(details)

        # update selection in other tabs to match:
        primary_entity = primary_entity or {}
        self._update_selected_entity(primary_entity.get("type"), primary_entity.get("id"))

        # refresh files:
        self._file_model.refresh_files(search_details)    

        # emit work-area-changed signal:
        if len(search_details) > 0:
            self.work_area_changed.emit(search_details[0].entity)
        else:
            self.work_area_changed.emit(None)

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
        
        details = FileModel.SearchDetails(name)
        
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
    
    def _on_file_selected(self, file, env, selection_mode):
        """
        """
        if selection_mode == FileListForm.USER_SELECTED:
            # user changed the selection so try to change the selection in all other 
            # file tabs to match:
            for wi in range(self._ui.file_browser_tabs.count()):
                widget = self._ui.file_browser_tabs.widget(wi)
                if widget == self.sender():
                    continue
                
                # block signals to avoid recursion:
                signals_blocked = widget.blockSignals(True)
                try:
                    widget.select_file(file, env)
                finally:
                    widget.blockSignals(False)
            
        # always emit a file selected signal to allow calling code
        # to react to a visible change in the selection
        self.file_selected.emit(file, env)
    
    def _on_file_tab_changed(self, idx):
        """
        """
        selected_file = None
        env = None
        
        form = self._ui.file_browser_tabs.widget(idx)
        if form and isinstance(form, FileListForm):
            # get the selected file from the form:
            selected_file, env = form.selected_file

        # update the selected file:
        self.file_selected.emit(selected_file, env)

    def _on_task_tab_changed(self, idx):
        """
        """
        selected_idx = None
        
        form = self._ui.task_browser_tabs.widget(idx)
        if form:
            if isinstance(form, MyTasksForm):
                pass
            elif isinstance(form, EntityTreeForm):
                pass
            
            