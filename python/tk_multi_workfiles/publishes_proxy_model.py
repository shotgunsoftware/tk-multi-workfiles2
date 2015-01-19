# Copyright (c) 2014 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.


from sgtk.platform.qt import QtGui, QtCore
from file_model import FileModel

class PublishesProxyModel(QtGui.QSortFilterProxyModel):
    """
    """
    
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        
    def filterAcceptsRow(self, source_row, source_parent_index):
        """
        """
        src_index = self.sourceModel().index(source_row, 0, source_parent_index)
        node_type = src_index.data(FileModel.NODE_TYPE_ROLE)
        if node_type != FileModel.FILE_NODE_TYPE:
            return True
        else:
            file_item = src_index.data(FileModel.FILE_ITEM_ROLE)
            return (file_item and file_item.is_published)
        