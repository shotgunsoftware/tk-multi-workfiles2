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
"""

import sgtk
from sgtk.platform.qt import QtCore, QtGui

views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")
GroupedListViewItemDelegate = views.GroupedListViewItemDelegate

from ..file_model import FileModel
from .file_group_widget import FileGroupWidget
from .file_tile import FileTile

class FileListItemDelegate(GroupedListViewItemDelegate):

    def __init__(self, view):
        GroupedListViewItemDelegate.__init__(self, view)
        
        self._item_widget = None

    def create_group_widget(self, parent):
        return FileGroupWidget(parent)

    def _get_painter_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        if not self._item_widget:
            self._item_widget = FileTile(parent)
        return self._item_widget

    def _on_before_paint(self, widget, model_index, style_options):
        """
        """
        if not isinstance(widget, FileTile):
            # this class only paints FileTile widgets
            return
        
        label = ""
        icon = None
        is_publish = False
        is_editable = True
        not_editable_reason = None
        
        file_item = model_index.data(FileModel.FILE_ITEM_ROLE)
        if file_item:
            # build label:
            label = "<b>%s, v%03d</b>" % (file_item.name, file_item.version)
            if file_item.is_published:
                label += "<br>%s" % file_item.format_published_by_details()
            elif file_item.is_local:
                label += "<br>%s" % file_item.format_modified_by_details()

            # retrieve the icon:                
            icon = file_item.thumbnail
            is_publish = file_item.is_published
            is_editable = file_item.editable
            not_editable_reason = file_item.not_editable_reason
        else:
            label = model_index.data()
            icon = model_index.data(QtCore.Qt.DecorationRole)

        # update widget:
        widget.title = label
        widget.set_thumbnail(icon)
        widget.selected = (style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected
        widget.set_is_publish(is_publish)
        widget.set_is_editable(is_editable, not_editable_reason)

    def sizeHint(self, style_options, model_index):
        """
        """
        if not model_index.isValid():
            return QtCore.QSize()
        
        if model_index.parent() != self.view.rootIndex():
            return self._get_painter_widget(model_index, self.view).size()
        else:
            # call base class:
            return GroupedListViewItemDelegate.sizeHint(self, style_options, model_index)