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


class PublishesProxyModel(QtGui.QSortFilterProxyModel):
    """
    """
    
    def __init__(self, parent=None):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        
        
    def filterAcceptsRow(self, source_row, source_parent_index):
        """
        """
        item = None
        if source_parent_index.isValid():
            source_index = source_parent_index.child(source_row, 0)
            item = self.sourceModel().itemFromIndex(source_index)
        else:
            item = self.sourceModel().itemFromIndex(self.sourceModel().index(source_row, 0))
        
        return (item and item.file_item.is_published) or False
        