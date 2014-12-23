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

from .task_widget import TaskWidget

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
        widget.set_selected((style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected) 

class MyTasksForm(QtGui.QWidget):
    """
    """
    
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
        #self._ui.new_task_btn.clicked.connect(self._on_new_task)
        
        # create the overlay 'busy' widget:
        self._overlay_widget = overlay_module.ShotgunModelOverlayWidget(None, self._ui.task_tree)
        self._overlay_widget.set_model(model)

        item_delegate = MyTaskItemDelegate(self._ui.task_tree)
        self._ui.task_tree.setItemDelegate(item_delegate)

        #self._proxy_model = EntityProxyModel(self)
        #self._proxy_model.setSourceModel(entity_model)
        self._ui.task_tree.setModel(model)


        # connect to the selection model for the tree view:
        #selection_model = self._ui.task_tree.selectionModel()
        #if selection_model:
        #    #selection_model.selectionChanged.connect(self._on_selection_changed)
        #    pass        