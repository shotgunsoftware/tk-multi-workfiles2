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


class FileProxyModel(QtGui.QSortFilterProxyModel):
    """
    """
    
    def __init__(self, show_work_files=True, show_publishes=True, show_all_versions=False, parent=None):
        """
        """
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        
        self._show_all_versions = show_all_versions
        self._show_publishes = show_publishes
        self._show_workfiles = show_work_files

    @property
    def show_all_versions(self):
        return self._show_all_versions
    @show_all_versions.setter
    def show_all_versions(self, show):
        self._show_all_versions = show
        self.invalidateFilter()
        
    @property
    def show_publishes(self):
        return self._show_publishes
    @show_publishes.setter
    def show_publishes(self, show):
        self._show_publishes = show
        self.invalidateFilter()
        
    @property
    def show_work_files(self):
        return self._show_workfiles
    @show_work_files.setter
    def show_work_files(self, show):
        self._show_workfiles = show
        self.invalidateFilter()
        
    def filterAcceptsRow(self, src_row, src_parent_idx):
        """
        """
        # get the source index for the row:
        src_model = self.sourceModel()
        if not src_model:
            return True
        
        src_idx = src_model.index(src_row, 0, src_parent_idx)
        if not src_idx:
            return True
        
        # get the file item from the idx:
        file_item = src_idx.data(FileModel.FILE_ITEM_ROLE)
        if not file_item:
            # always accept other items
            return True
        
        accept_row = False
        if file_item.is_local and self._show_workfiles:
            accept_row = True
        if file_item.is_published and self._show_publishes:
            accept_row = True
        if not accept_row:
            return False
        
        if not self._show_all_versions:
            # need to check if this is the latest version of the file:
            all_versions = src_model.get_file_versions(file_item.key)
            
            visible_versions = [v for v, item in all_versions.iteritems() 
                                    if (item.is_local and self._show_workfiles) 
                                        or (item.is_published and self._show_publishes)]
            
            if not visible_versions or file_item.version != max(visible_versions):
                return False
        
        return True
            
    def lessThan(self, left, right):
        """
        """
        left_item = left.data(FileModel.FILE_ITEM_ROLE)
        right_item = right.data(FileModel.FILE_ITEM_ROLE)
        
        if left.parent() != right.parent():
            print "EH?!"
            return True
        
        # handle the case where one or both items are not file items:
        if not left_item:
            if not right_item:
                return left.data() < right.data()
            else:
                return False
        elif not right_item:
            return True
        
        if left_item.is_published == right_item.is_published:
            left_updated = right_updated = None
            if self._show_workfiles:
                if left_item.is_local:
                    left_updated = left_item.modified_at
                if right_item.is_local:
                    right_updated = right_item.modified_at
                    
            if self._show_publishes:
                if left_item.is_published:
                    left_updated = max(left_updated, left_item.published_at) if left_updated else left_item.published_at 
                if right_item.is_published:
                    right_updated = max(right_updated, right_item.published_at) if right_updated else right_item.published_at
            
            return left_updated < right_updated    
                        
        elif left_item.is_published:
            return right_item.compare_with_publish(left_item) >= 0
        else:
            return left_item.compare_with_publish(right_item) < 0
        
        #return left_item.name < right_item.name
        #return left_item.version < right_item.version
        





class WorkFilesProxyModel(QtGui.QSortFilterProxyModel):
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
            return (file_item and file_item.is_local)