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
            
    def lessThan(self, left_src_idx, right_src_idx):
        """
        """
        if not left_src_idx.parent().isValid():
            # this is a root item so just leave the items in row 
            # order they are in in the source model:
            if self.sortOrder() == QtCore.Qt.AscendingOrder:
                return left_src_idx.row() < right_src_idx.row()
            else:
                return right_src_idx.row() < left_src_idx.row()

        # get the items:        
        left_item = left_src_idx.data(FileModel.FILE_ITEM_ROLE)
        right_item = right_src_idx.data(FileModel.FILE_ITEM_ROLE)

        # handle the case where one or both items are not file items:
        if not left_item:
            if not right_item:
                # sort in alphabetical order:
                if self.sortOrder() == QtCore.Qt.AscendingOrder:
                    return left_src_idx.data().lower() < right_src_idx.data().lower()
                else:
                    return right_src_idx.data().lower() < left_src_idx.data().lower()
            else:
                return False
        elif not right_item:
            return True

        if left_item.key != right_item.key:
            # items represent different files but we want to group all file versions together. 
            # Therefore, we find the maximum version for each file and compare those instead.
            left_versions = self.sourceModel().get_file_versions(left_item.key)
            right_versions = self.sourceModel().get_file_versions(right_item.key)
            
            max_left_version = left_versions[max(left_versions.keys())]
            max_right_version = right_versions[max(right_versions.keys())]
            
            return max_left_version.compare(max_right_version) < 0
        else:
            # items represent the same file so lets just compare them:
            return left_item.compare(right_item) < 0




