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

from ..file_model import FileModel
from .file_group_widget import FileGroupWidget
from .file_widget import FileWidget
from ..util import get_model_data, get_model_str
from ..framework_qtwidgets import GroupedListViewItemDelegate

class FileListItemDelegate(GroupedListViewItemDelegate):

    def __init__(self, view):
        """
        :param view: The view this delegate is for.
        """
        GroupedListViewItemDelegate.__init__(self, view)
        
        self._item_widget = None
        self._folder_icon = QtGui.QPixmap(":/tk-multi-workfiles2/folder_512x400.png")

    def create_group_widget(self, parent):
        return FileGroupWidget(parent)

    def _get_painter_widget(self, model_index, parent):
        """
        """
        if not model_index.isValid():
            return None
        if not self._item_widget:
            self._item_widget = FileWidget(parent)
        return self._item_widget

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Overriden method called before painting to allow the delegate to set up the
        widget for the specified model index.

        :param widget:          The widget that will be used to paint with
        :param model_index:     The QModelIndex representing the index in the model that is
                                being painted
        :param style_options:   The style options that should be used to paint the widget for
                                the index
        """
        if not isinstance(widget, FileWidget):
            # this class only paints FileWidget widgets
            return

        # get the data for the model index:
        label = ""
        subtitle = ""
        icon = None
        show_subtitle = False
        item_type = get_model_data(model_index, FileModel.NODE_TYPE_ROLE)
        if item_type == FileModel.FILE_NODE_TYPE:

            is_publish = False
            is_editable = True
            show_subtitle = True
            file_item = get_model_data(model_index, FileModel.FILE_ITEM_ROLE)
            if file_item:
                # build labels:
                label = "<b>%s<b>" % file_item.name
                subtitle += "v%03d" % file_item.version
                if file_item.is_published:
                    subtitle += "<br>%s" % file_item.format_published_by_details()
                elif file_item.is_local:
                    subtitle += "<br>%s" % file_item.format_modified_by_details()

                # retrieve the icon:
                icon = file_item.thumbnail
                is_publish = file_item.is_published
                is_editable = file_item.editable

            widget.set_is_publish(is_publish)
            widget.set_is_editable(is_editable)

        elif item_type == FileModel.FOLDER_NODE_TYPE:
            # get the lavel from the index and use the default folder icon
            label = get_model_str(model_index)
            icon = self._folder_icon
        else:
            # just use the label from the standard display role:
            label = get_model_str(model_index)

        # update the widget:
        widget.title = label
        widget.subtitle = subtitle
        widget.set_show_subtitle(show_subtitle)
        widget.set_thumbnail(icon)
        widget.selected = (style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected

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
