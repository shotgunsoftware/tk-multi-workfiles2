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

from .file_model import FileModel
from .file_model_overlay_widget import FileModelOverlayWidget

from .ui.file_list_form import Ui_FileListForm

from .file_tile import FileTile
from .group_header_widget import GroupHeaderWidget

shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")
WidgetDelegate = shotgun_view.WidgetDelegate

class GroupListViewItemDelegate(WidgetDelegate):
    """
    """
    def __init__(self, view):
        """
        """
        WidgetDelegate.__init__(self, view)
        
        self._group_widget = None
        self._group_widget_size = None
        self._item_widget = None
        self._item_widget_size = None
    
    # ------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
        
    def _create_group_widget(self, parent):
        """
        """
        raise NotImplementedError()
    
    def _create_item_widget(self, parent):
        """
        """
        raise NotImplementedError()
        
    # ------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------
        
    def _get_painter_widget(self, model_index, parent):
        """
        """
        # need to look at the index to determine the type of widget to return.
        
        
        if not model_index.isValid():
            return None
        
        parent_index = model_index.parent()
        if parent_index == self.view.rootIndex():
            # we need a group widget:
            if not self._group_widget:
                self._group_widget = self._create_group_widget(parent)
                self._group_widget_size = self._group_widget.size()
            return self._group_widget
        elif parent_index.isValid() and parent_index.parent() == self.view.rootIndex():
            # we need an item widget:
            if not self._item_widget:
                self._item_widget = self._create_item_widget(parent)
                self._item_widget_size = self._item_widget.size()
            return self._item_widget
    
    def _create_editor_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        
        #print "CREATING EDITOR WIDGET"
        
        parent_index = model_index.parent()
        if parent_index == self.view.rootIndex():
            return self._create_group_widget(parent)
        elif parent_index.isValid() and parent_index.parent() == self.view.rootIndex():
            return self._create_item_widget(parent)
            
    def sizeHint(self, style_options, model_index):
        """
        """
        # for group widgets this should return the complete width of the view.
        
        if not model_index.isValid():
            return QtCore.QSize()
        
        # ensure we have a painter widget for this model index:
        self._get_painter_widget(model_index, self.view)
        
        parent_index = model_index.parent()
        if parent_index == self.view.rootIndex():
            return self._group_widget_size
        elif parent_index.isValid() and parent_index.parent() == self.view.rootIndex():
            return self._item_widget_size
        
        return QtCore.QSize()
        
        

class TestItemDelegate(GroupListViewItemDelegate):

    def __init__(self, view):
        GroupListViewItemDelegate.__init__(self, view)

    def _create_group_widget(self, parent):
        """
        """
        return GroupHeaderWidget(parent)
    
    def _create_item_widget(self, parent):
        """
        """
        return FileTile(parent)

    def _setup_widget(self, widget, model_index, style_options):
        """
        """
        if isinstance(widget, GroupHeaderWidget):
            # update group widget:
            widget.label = model_index.data()
        elif isinstance(widget, FileTile):
            # update item widget:
            widget.title = model_index.data()
            widget.selected = (style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected 

    def _on_before_paint(self, widget, model_index, style_options):
        """
        """
        self._setup_widget(widget, model_index, style_options) 

    def _on_before_selection(self, widget, model_index, style_options):
        """
        """
        self._setup_widget(widget, model_index, style_options)
        
    def setModelData(self, editor, model, model_index):
        pass

class FileListForm(QtGui.QWidget):
    """
    """
    
    def __init__(self, search_label, parent=None):
        """
        Construction
        """
        QtGui.QWidget.__init__(self, parent)
        
        # set up the UI
        self._ui = Ui_FileListForm()
        self._ui.setupUi(self)
        
        self._ui.search_ctrl.set_placeholder_text("Search %s" % search_label)
        
        self._overlay_widget = FileModelOverlayWidget(parent = self._ui.view_pages)
        
        self._ui.details_radio_btn.setEnabled(False) # (AD) - temp
        self._ui.details_radio_btn.toggled.connect(self._on_view_toggled)
        
        item_delegate = TestItemDelegate(self._ui.file_list_view)
        self._ui.file_list_view.setItemDelegate(item_delegate)
        
                
    def _on_view_toggled(self, checked):
        """
        """
        if self._ui.details_radio_btn.isChecked():
            self._ui.view_pages.setCurrentWidget(self._ui.details_page)
        else:
            self._ui.view_pages.setCurrentWidget(self._ui.list_page)
            
    def set_model(self, model):
        """
        """
        self._ui.file_list_view.setModel(model)
        self._ui.file_details_view.setModel(model)
        self._overlay_widget.set_model(model)
        