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

"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui.my_tasks_form import Ui_MyTasksForm

overlay_module = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")

shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")
WidgetDelegate = shotgun_view.WidgetDelegate

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel

from .task_widget import TaskWidget
from .entity_proxy_model import EntityProxyModel

class MyTaskItemDelegate(WidgetDelegate):
    """
    """
    def __init__(self, view):
        """
        """
        WidgetDelegate.__init__(self, view)
        
        self._paint_widget = None
        self._widget_sz = None

    # ------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
        
    def _get_painter_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        
        if not self._paint_widget:
            self._paint_widget = TaskWidget(parent)
            self._widget_sz = self._paint_widget.size() 
            
        return self._paint_widget
    
    def _create_editor_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        
        return TaskWidget(parent)
        
    def sizeHint(self, style_options, model_index):
        """
        """
        if not model_index.isValid():
            return QtCore.QSize()

        self._get_painter_widget(model_index, self.view)
        
        return self._widget_sz or QtCore.QSize()
        
    def _on_before_paint(self, widget, model_index, style_options):
        """
        """
        self._setup_widget(widget, model_index, style_options) 

    #def _on_before_selection(self, widget, model_index, style_options):
    #    """
    #    """
    #    self._setup_widget(widget, model_index, style_options)

    def _setup_widget(self, widget, model_index, style_options):
        """
        """
        model = model_index.model()
        if not model:
            return
        
        while isinstance(model, QtGui.QAbstractProxyModel):
            model_index = model.mapToSource(model_index)
            model = model.sourceModel()
        
        item = model.itemFromIndex(model_index)
        if not item:
            return

        sg_data = item.get_sg_data()
        
        # set the thumbnail to the icon for the item:
        widget.set_thumbnail(item.icon())
        
        # set entity info:        
        entity = sg_data.get("entity")
        entity_name = entity.get("name")
        entity_type = entity.get("type")
        entity_type_icon = ShotgunEntityModel.get_entity_icon(entity_type) if entity_type else None
        widget.set_entity(entity_name, entity_type, entity_type_icon)
        
        # set task info:
        task_name = sg_data.get("content")
        task_type_icon = ShotgunEntityModel.get_entity_icon("Task")
        widget.set_task(task_name, task_type_icon)
        
        # set 'other' info:
        other_text = None
        widget.set_other(other_text)
                
        # finally, update the selected state of the widget:
        widget.set_selected((style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected) 


                  
class MyTasksForm(QtGui.QWidget):
    """
    """
    
    task_selected = QtCore.Signal(object)
    create_new_task = QtCore.Signal()
    
    def __init__(self, model, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_MyTasksForm()
        self._ui.setupUi(self)
        
        self._ui.search_ctrl.set_placeholder_text("Search My Tasks")
        
        # connect up controls:
        self._ui.search_ctrl.search_edited.connect(self._on_search_changed)        
        self._ui.new_task_btn.clicked.connect(self._on_new_task)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = overlay_module.ShotgunModelOverlayWidget(None, self._ui.task_tree)
        self._overlay_widget.set_model(model)

        item_delegate = MyTaskItemDelegate(self._ui.task_tree)
        self._ui.task_tree.setItemDelegate(item_delegate)

        # create a filter proxy model between the source model and the task tree view:
        self._filter_model = EntityProxyModel(["content", {"entity":"name"}], self)
        self._filter_model.setSourceModel(model)
        self._ui.task_tree.setModel(self._filter_model)

        # connect to the selection model for the tree view:
        selection_model = self._ui.task_tree.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
        
    def _on_search_changed(self, search_text):
        """
        """
        # update the proxy filter search text:
        filter_reg_exp = QtCore.QRegExp(search_text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)
        self._filter_model.setFilterRegExp(filter_reg_exp)

    def _on_selection_changed(self, selected, deselected):
        """
        """
        selected_index = None
        
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 1:
            # extract the selected model index from the selection:
            selected_index = self._filter_model.mapToSource(selected_indexes[0])
            
        # emit selection_changed signal:            
        self.task_selected.emit(selected_index)
        
    def _on_new_task(self):
        """
        """
        self.create_new_task.emit()
        
        
        
                