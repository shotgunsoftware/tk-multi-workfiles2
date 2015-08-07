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
from .util import value_to_str
from .ui.browser_form import Ui_BrowserForm
from .framework_qtwidgets import Breadcrumb

from .file_list.file_proxy_model import FileProxyModel
from .file_filters import FileFilters
from .util import monitor_qobject_lifetime

class BrowserForm(QtGui.QWidget):
    """
    UI for saving a work file
    """
    class _EntityTabBreadcrumb(Breadcrumb):
        def __init__(self, label, tab_index):
            Breadcrumb.__init__(self, label)
            self.tab_index = tab_index

    create_new_task = QtCore.Signal(object, object)# entity, step
    work_area_changed = QtCore.Signal(object, list)# entity, breadcrumbs
    breadcrumbs_dropped = QtCore.Signal(list)# breadcrumbs
    file_selected = QtCore.Signal(object, object)# file, env
    file_double_clicked = QtCore.Signal(object, object)# file, env
    file_context_menu_requested = QtCore.Signal(object, object, QtCore.QPoint)# file, env, pnt
    
    def __init__(self, parent):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)

        self._enable_show_all_versions = True
        self._enable_user_filtering = True
        self._file_model = None
        self._my_tasks_form = None
        self._entity_tree_forms = []
        self._file_browser_forms = []

        # set up the UI
        self._ui = Ui_BrowserForm()
        self._ui.setupUi(self)

        self._ui.file_browser_tabs.currentChanged.connect(self._on_file_tab_changed)
        self._ui.task_browser_tabs.currentChanged.connect(self._on_task_tab_changed)

        self._file_filters = FileFilters(parent=None)
        monitor_qobject_lifetime(self._file_filters, "Browser file filters")
        self._file_filters.users_changed.connect(self._on_file_filters_users_changed)

    def shut_down(self):
        """
        Help the gc by cleaning up as much as possible when this widget is finished with
        """
        signals_blocked = self.blockSignals(True)
        try:
            # clean up my tasks form:
            if self._my_tasks_form:
                self._my_tasks_form.shut_down()
                self._my_tasks_form = None

            # clean up entity forms:
            for entity_form in self._entity_tree_forms:
                entity_form.shut_down()
            self._entity_tree_forms = []

            # clean up file forms:
            for file_form in self._file_browser_forms:
                file_form.shut_down()
            self._file_browser_forms = []
            self._file_model = None

            # clean up the file filters:
            self._file_filters = None
        finally:
            self.blockSignals(signals_blocked)

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

    def enable_show_all_versions(self, enable):
        """
        """
        if self._enable_show_all_versions == enable:
            return
        
        self._enable_show_all_versions = enable
        for ti in range(self._ui.file_browser_tabs.count()):
            widget = self._ui.file_browser_tabs.widget(ti)
            widget.enable_show_all_versions(self._enable_show_all_versions)

    def enable_user_filtering(self, enable):
        """
        """
        if self._enable_user_filtering == enable:
            return
        self._enable_user_filtering = enable
        for ti in range(self._ui.file_browser_tabs.count()):
            widget = self._ui.file_browser_tabs.widget(ti)
            widget.enable_user_filtering(self._enable_user_filtering)

    def set_models(self, my_tasks_model, entity_models, file_model):
        """
        """
        app = sgtk.platform.current_bundle()
        allow_task_creation = app.get_setting("allow_task_creation")

        if my_tasks_model:
            # create my tasks form:
            self._my_tasks_form = MyTasksForm(my_tasks_model, allow_task_creation, parent=self)
            self._my_tasks_form.task_selected.connect(self._on_my_task_selected)
            self._ui.task_browser_tabs.addTab(self._my_tasks_form, "My Tasks")
            self._my_tasks_form.create_new_task.connect(self.create_new_task)

        for caption, model in entity_models:
            # create new entity form:
            entity_form = EntityTreeForm(model, caption, allow_task_creation, parent=self)
            entity_form.entity_selected.connect(self._on_entity_selected)
            self._ui.task_browser_tabs.addTab(entity_form, caption)
            entity_form.create_new_task.connect(self.create_new_task)
            self._entity_tree_forms.append(entity_form)

        if file_model:
            # attach file model to the file views:
            self._file_model = file_model
            self._file_model.available_sandbox_users_changed.connect(self._on_available_sandbox_users_changed)
            self._file_model.set_users(self._file_filters.users)

            # add an 'all files' tab:
            all_files_form = FileListForm(self, "All Files", self._file_filters, show_work_files=True, show_publishes=True)
            self._ui.file_browser_tabs.addTab(all_files_form, "All")
            all_files_form.enable_show_all_versions(self._enable_show_all_versions)
            all_files_form.enable_user_filtering(self._enable_user_filtering)
            all_files_form.set_model(self._file_model)
            all_files_form.file_selected.connect(self._on_file_selected)
            all_files_form.file_double_clicked.connect(self.file_double_clicked)
            all_files_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
            self._file_browser_forms.append(all_files_form)

            # create the workfiles only tab:
            work_files_form = FileListForm(self, "Work Files", self._file_filters, show_work_files=True, show_publishes=False)
            self._ui.file_browser_tabs.addTab(work_files_form, "Working")
            work_files_form.enable_show_all_versions(self._enable_show_all_versions)
            work_files_form.enable_user_filtering(self._enable_user_filtering)
            work_files_form.set_model(self._file_model)
            work_files_form.file_selected.connect(self._on_file_selected)
            work_files_form.file_double_clicked.connect(self.file_double_clicked)
            work_files_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
            self._file_browser_forms.append(work_files_form)

            # create the publishes only tab:
            publishes_form = FileListForm(self, "Publishes", self._file_filters, show_work_files=False, show_publishes=True)
            self._ui.file_browser_tabs.addTab(publishes_form, "Publishes")
            publishes_form.enable_show_all_versions(self._enable_show_all_versions)
            publishes_form.enable_user_filtering(self._enable_user_filtering)
            publishes_form.set_model(self._file_model)
            publishes_form.file_selected.connect(self._on_file_selected)
            publishes_form.file_double_clicked.connect(self.file_double_clicked)
            publishes_form.file_context_menu_requested.connect(self._on_file_context_menu_requested)
            self._file_browser_forms.append(publishes_form)

    def select_work_area(self, context):
        """
        """
        if not context:
            return

        # update the selected entity in the various task/entity trees:
        ctx_entity = context.task or context.step or context.entity
        if not ctx_entity:
            return

        self._update_selected_entity(ctx_entity["type"], ctx_entity["id"], skip_current=False)

        if self._file_model:
            # now start a new file search based off the entity:
            search_label = ctx_entity.get("name")
            if ctx_entity["type"] == "Task" and context.step:
                search_label = "%s - %s" % (context.step.get("name"), search_label)
    
            details = FileModel.SearchDetails(search_label)
            details.entity = ctx_entity
            details.is_leaf = True
            self._file_model.set_entity_searches([details])

    def select_file(self, file, context):
        """
        """
        # try to select the file in all file browser tabs:
        for ti in range(self._ui.file_browser_tabs.count()):
            widget = self._ui.file_browser_tabs.widget(ti)
            widget.select_file(file, context)

    def navigate_to(self, breadcrumb_trail):
        """
        """
        if not breadcrumb_trail or not isinstance(breadcrumb_trail[0], BrowserForm._EntityTabBreadcrumb):
            return

        # change the entity tabs to the correct index:
        self._ui.task_browser_tabs.setCurrentIndex(breadcrumb_trail[0].tab_index)

        # update the widget navigation:
        self._ui.task_browser_tabs.currentWidget().navigate_to(breadcrumb_trail[1:])

    # ------------------------------------------------------------------------------------------
    # protected methods

    def _on_available_sandbox_users_changed(self, users):
        """
        """
        #print "Available sandbox users: %s" % [u["name"].split()[0] for u in users if u]
        self._file_filters.available_users = users

    def _on_file_filters_users_changed(self, users):
        """
        """
        #print "File filter users: %s" % [u["name"].split()[0] for u in users if u]
        if self._file_model:
            self._file_model.set_users(users)

    def _emit_work_area_changed(self, entity, child_breadcrumb_trail):
        """
        """
        # build breadcrumb trail for the current selection in the UI:
        breadcrumb_trail = []

        tab_index = self._ui.task_browser_tabs.currentIndex()
        tab_label = value_to_str(self._ui.task_browser_tabs.tabText(tab_index))
        breadcrumb_trail.append(BrowserForm._EntityTabBreadcrumb(tab_label, tab_index))

        # append child breadcrumbs:
        breadcrumb_trail.extend(child_breadcrumb_trail)

        self.work_area_changed.emit(entity, breadcrumb_trail)

    def _update_selected_entity(self, entity_type, entity_id, skip_current=True):
        """
        """
        current_widget = self._ui.task_browser_tabs.currentWidget()

        # loop through all widgets and update the selection in each one:
        for ti in range(self._ui.task_browser_tabs.count()):
            widget = self._ui.task_browser_tabs.widget(ti)
            
            if skip_current and widget == current_widget:
                continue

            if isinstance(widget, MyTasksForm):
                if entity_type == "Task":
                    widget.select_task(entity_id)
                else:
                    widget.select_task(None)
            elif isinstance(widget, EntityTreeForm):
                widget.select_entity(entity_type, entity_id)

    def _on_file_context_menu_requested(self, file, env, pnt):
        """
        """
        local_pnt = self.sender().mapTo(self, pnt)
        self.file_context_menu_requested.emit(file, env, local_pnt)
    
    def _on_my_task_selected(self, task, breadcrumb_trail):
        """
        """
        # ignore if the sender isn't the current tab:
        if self._ui.task_browser_tabs.currentWidget() != self.sender():
            return

        self._on_selected_task_changed(task, breadcrumb_trail)
        if task:
            self._update_selected_entity("Task", task["id"])
        else:
            self._update_selected_entity(None, None)

    def _on_selected_task_changed(self, task, breadcrumb_trail):
        """
        """
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

        # refresh files:
        if self._file_model:
            self._file_model.set_entity_searches(search_details)

        # emit work-area-changed signal:
        self._emit_work_area_changed(task, breadcrumb_trail)

    def _on_entity_selected(self, selection_details, breadcrumb_trail):
        """
        Called when something has been selected in an entity tree view.  From 
        this selection, a list of publishes and work files can then be found
        which will be used to populate the main file grid/details view.
        """
        # ignore if the sender isn't the current tab:
        if self._ui.task_browser_tabs.currentWidget() != self.sender():
            return

        selected_entity = self._on_selected_entity_changed(selection_details, breadcrumb_trail)
        if selected_entity:
            self._update_selected_entity(selected_entity["type"], selected_entity["id"])
        else:
            self._update_selected_entity(None, None)

    def _on_selected_entity_changed(self, selection_details, breadcrumb_trail):
        """
        """
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

        # refresh files:
        if self._file_model:
            p_details = []
            for search in search_details:
                p_details.append({"name":search.name, 
                       "entity":search.entity, 
                       "is_leaf":search.is_leaf, 
                       "child_entities":search.child_entities})

            self._file_model.set_entity_searches(search_details)

        # emit work-area-changed signal:
        self._emit_work_area_changed(primary_entity or None, breadcrumb_trail)
        
        return primary_entity

    def _on_file_selected(self, file, env, selection_mode):
        """
        """
        # ignore if the sender isn't the current file tab:
        if self._ui.file_browser_tabs.currentWidget() != self.sender():
            return

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
                    widget.select_file(file, env.context if env else None)
                finally:
                    widget.blockSignals(signals_blocked)

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
        form = self._ui.task_browser_tabs.widget(idx)
        if isinstance(form, MyTasksForm):
            # retrieve the selected task from the form and emit a work-area changed signal:
            task, breadcrumb_trail = form.get_selection()
            #self._emit_work_area_changed(task, breadcrumb_trail)
            self._on_selected_task_changed(task, breadcrumb_trail)
            
        elif isinstance(form, EntityTreeForm):
            # retrieve the selection from the form and emit a work-area changed signal:
            selection, breadcrumb_trail = form.get_selection()
            #selected_entity = selection.get("entity") if selection else None
            #self._emit_work_area_changed(selected_entity, breadcrumb_trail)
            self._on_selected_entity_changed(selection, breadcrumb_trail)




