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

from .ui.file_open_form import Ui_FileOpenForm
from .entity_tree_form import EntityTreeForm
from .file_list_form import FileListForm

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

from .file_model import FileModel, FileModelOverlayWidget
from .publishes_proxy_model import PublishesProxyModel
from .work_files_proxy_model import WorkFilesProxyModel

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
        
        # set up the UI
        self._ui = Ui_FileOpenForm()
        self._ui.setupUi(self)
        
        # initialize task trees:
        self._initilize_task_trees()
        
        # add my-tasks
        # ...
             
        # initialize the file views:
        self._initilize_file_views()
                
        # hook up all other controls:
        self._ui.cancel_btn.clicked.connect(self._on_cancel)

        # call init callback:
        init_callback(self)

    def _initilize_task_trees(self):
        """
        Initialize the task trees
        """
        app = sgtk.platform.current_bundle()
        
        # set up the task trees:
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
            entity_form = EntityTreeForm(model, self)
            entity_form.entity_selected.connect(self._on_entity_selected)
            self._ui.task_browser_tabs.addTab(entity_form, caption)
        
    def _initilize_file_views(self):
        """
        """
        app = sgtk.platform.current_bundle()
        
        # create the model that represents files:
        self._file_model = FileModel(self)

        all_files_form = FileListForm(self)
        self._ui.file_browser_tabs.addTab(all_files_form, "All")
        all_files_form.set_model(self._file_model)
        
        # create the workfiles proxy model & form:
        work_files_model = WorkFilesProxyModel(self)
        work_files_model.setSourceModel(self._file_model)
        work_files_form = FileListForm(self)
        work_files_form.set_model(work_files_model)
        self._ui.file_browser_tabs.addTab(work_files_form, "Working")

        # create the publish proxy model & form:
        publishes_model = PublishesProxyModel(self)
        publishes_model.setSourceModel(self._file_model)
        publishes_form = FileListForm(self)
        publishes_form.set_model(publishes_model)
        self._ui.file_browser_tabs.addTab(publishes_form, "Publishes")
        
        
    def _on_entity_selected(self, entity_index):
        """
        Called when something has been selected in an entity tree view.  From 
        this selection, a list of publishes and work files can then be found
        which will be used to populate the main file grid/details view.
        """
        if not entity_index:
            return None
        
        app = sgtk.platform.current_bundle()
        
        # get the item for the specified index:
        entity_item = entity_index.model().itemFromIndex(entity_index)
        
        # find the publish filters and context for this item:
        publish_filters = self._extract_publish_filters(entity_item)
        context = self._extract_context(entity_item)

        # finally, update the file model for the filters and context:
        self._file_model.refresh_files(publish_filters, context)

        
    def _extract_context(self, entity_item):
        """
        """
        app = sgtk.platform.current_bundle()

        # get the list of entities for the item:
        entities = entity_item.model().get_entities(entity_item)
            
        # from the list of entities, extract a context:
        context_project = None
        context_entity = None
        context_task = None
        for entity in entities:
            entity_type = entity.get("type")
            if entity_type == "Task":
                context_task = context_task or entity
            elif entity_type == "Project":
                context_project = context_project or entity
            elif entity_type:
                context_entity = context_entity or entity
                
        entity_to_use = context_task or context_entity or context_project
        context = None
        if entity_to_use:
            try:
                context = app.sgtk.context_from_entity(entity_to_use["type"], entity_to_use["id"])
            except TankError, e:
                app.log_debug("Failed to create context from entity '%s'" % entity_to_use)
                
        return context

    def _extract_publish_filters(self, entity_item):
        """
        """
        app = sgtk.platform.current_bundle()

        # get the list of filters for the item:
        entity_model = entity_item.model()
        filters = entity_model.get_filters(entity_item)
        entity_type = entity_model.get_entity_type()
        
        # if we are on a leaf item then sg_data will represent a 
        # specific entity so add this to the filters:
        sg_data = entity_item.get_sg_data()
        if sg_data:
            filters = [["id", "is", sg_data["id"]]] + filters

        # all filters will be relative to the PublishedFile
        # entity so we need to extend the filters to either the 
        # linked entity or task:
        link_field = "task" if entity_type == "Task" else "entity"
        publish_filters = []
        for filter in copy.deepcopy(filters):
            filter[0] = "%s.%s.%s" % (link_field, entity_type, filter[0])
            publish_filters.append(filter)
            
        return publish_filters
        
        
    def _on_cancel(self):
        """
        Called when the cancel button is clicked
        """
        self._exit_code = QtGui.QDialog.Rejected        
        self.close()
        
        