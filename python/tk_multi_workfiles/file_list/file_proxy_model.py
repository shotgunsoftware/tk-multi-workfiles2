# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.


import sgtk
from sgtk.platform.qt import QtCore

from ..file_model import FileModel
from ..framework_qtwidgets import HierarchicalFilteringProxyModel
from ..util import get_model_data, get_model_str

class FileProxyModel(HierarchicalFilteringProxyModel):
    """
    """
    def __init__(self, show_work_files=True, show_publishes=True, show_all_versions=False, parent=None):
        """
        """
        HierarchicalFilteringProxyModel.__init__(self, parent)
        
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

    def _is_item_accepted(self, item, parent_accepted):
        """
        """
        file_item = get_model_data(item, FileModel.FILE_ITEM_ROLE)
        if file_item:
            if (not (file_item.is_local and self._show_workfiles)
                and not (file_item.is_published and self._show_publishes)):
                return False

            if not self._show_all_versions:
                src_model = self.sourceModel()
                # need to check if this is the latest version of the file:
                env = get_model_data(item, FileModel.ENVIRONMENT_ROLE)
                all_versions = src_model.get_file_versions(file_item.key, env) or {}

                visible_versions = [v for v, file in all_versions.iteritems() 
                                        if (file.is_local and self._show_workfiles) 
                                            or (file.is_published and self._show_publishes)]

                if not (visible_versions and file_item.version == max(visible_versions)):
                    return False

        # now compare text for item:
        if parent_accepted:
            return True

        reg_exp = self.filterRegExp()
        if reg_exp.isEmpty():
            # early out
            return True

        # check
        if file_item:
            if reg_exp.indexIn(file_item.name) != -1:
                return True
        else:
            if reg_exp.indexIn(item.text()) != -1:
                return True

        # default is to not match:
        return False

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
        left_item = get_model_data(left_src_idx, FileModel.FILE_ITEM_ROLE)
        right_item = get_model_data(right_src_idx, FileModel.FILE_ITEM_ROLE)
        if hasattr(QtCore, "QVariant"):
            # damned PyQt!
            if isinstance(left_item, QtCore.QVariant):
                left_item = left_item.toPyObject()
            if isinstance(right_item, QtCore.QVariant):
                right_item = right_item.toPyObject()

        # handle the case where one or both items are not file items:
        if not left_item:
            if not right_item:
                # sort in alphabetical order:
                is_less_than = get_model_str(left_src_idx).lower() < get_model_str(right_src_idx).lower()
                if self.sortOrder() == QtCore.Qt.AscendingOrder:
                    return is_less_than
                else:
                    return not is_less_than
            else:
                return False
        elif not right_item:
            return True

        if left_item.key != right_item.key:
            # items represent different files but we want to group all file versions together. 
            # Therefore, we find the maximum version for each file and compare those instead.
            left_env = get_model_data(left_src_idx, FileModel.ENVIRONMENT_ROLE)
            left_versions = self.sourceModel().get_file_versions(left_item.key, left_env)
            right_env = get_model_data(right_src_idx, FileModel.ENVIRONMENT_ROLE)            
            right_versions = self.sourceModel().get_file_versions(right_item.key, right_env)
            
            if left_versions and right_versions:
                max_left_version = left_versions[max(left_versions.keys())]
                max_right_version = right_versions[max(right_versions.keys())]
                return max_left_version.compare(max_right_version) < 0

        # just compare the two files!
        return left_item.compare(right_item) < 0




