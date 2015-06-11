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
    filtering_changed = QtCore.Signal()

    def __init__(self, filters, show_work_files=True, show_publishes=True, parent=None):#, show_all_versions=False, filtered_users=None, parent=None):
        """
        """
        HierarchicalFilteringProxyModel.__init__(self, parent)
        
        self._filters = filters
        if self._filters:
            self._filters.changed.connect(self._on_filters_changed)
        
        #self._show_all_versions = show_all_versions
        self._show_publishes = show_publishes
        self._show_workfiles = show_work_files
        #self._filtered_user_ids = set()
        #self.set_filtered_users(filtered_users)

    def _on_filters_changed(self):
        """
        """
        if self._filters.filter_reg_exp != self.filterRegExp():
            HierarchicalFilteringProxyModel.setFilterRegExp(self, self._filters.filter_reg_exp)
        self.invalidateFilter()

    ##@property
    #def _get_show_all_versions(self):
    #    return self._show_all_versions
    ##@show_all_versions.setter
    #def _set_show_all_versions(self, show):
    #    if show != self._show_all_versions:
    #        self._show_all_versions = show
    #        self.invalidateFilter()
    #        self.filtering_changed.emit()
    #show_all_versions=property(_get_show_all_versions, _set_show_all_versions)

    #@property
    def _get_show_publishes(self):
        return self._show_publishes
    #@show_publishes.setter
    def _set_show_publishes(self, show):
        self._show_publishes = show
        self.invalidateFilter()
    show_publishes=property(_get_show_publishes, _set_show_publishes)

    #@property
    def _get_show_work_files(self):
        return self._show_workfiles
    #@show_work_files.setter
    def _set_show_work_files(self, show):
        self._show_workfiles = show
        self.invalidateFilter()
    show_work_files=property(_get_show_work_files, _set_show_work_files)

    #def set_filtered_users(self, users):
    #    """
    #    """
    #    if users:
    #        self._filtered_user_ids = set([user["id"] for user in users if user])
    #    else:
    #        self._filtered_user_ids = set()
    #    self.invalidateFilter()

    def setFilterRegExp(self, reg_exp):
        """
        """
        # update the filter string in the filters instance.  This will result
        # in the filters.changed signal being emitted which will in turn update
        # the regex in this model.
        self._filters.filter_reg_exp = reg_exp
        #if reg_exp != self.filterRegExp():
        #    HierarchicalFilteringProxyModel.setFilterRegExp(self, reg_exp)
        #    self.filtering_changed.emit()

    def _is_row_accepted(self, src_row, src_parent_idx, parent_accepted):
        """
        Overriden from base class - determines if the specified row should be accepted or not by
        the filter.

        :param src_row:         The row in the source model to filter
        :param src_parent_idx:  The parent QModelIndex instance to filter
        :param parent_accepted: True if a parent item has been accepted by the filter
        :returns:               True if this index should be accepted, otherwise False
        """
        src_idx = self.sourceModel().index(src_row, 0, src_parent_idx)
        if not src_idx.isValid():
            return False

        file_item = get_model_data(src_idx, FileModel.FILE_ITEM_ROLE)
        if file_item:
            ## Filter based on showing work files, publishes or both:
            if (not (file_item.is_local and self._show_workfiles)
                and not (file_item.is_published and self._show_publishes)):
                return False

            work_area = get_model_data(src_idx, FileModel.WORK_AREA_ROLE)
            # Filter based on user
            #if work_area.context and work_area.context.user:
            #    if work_area.context.user["id"] not in self._filtered_user_ids:
            #        return False

            if not self._filters.show_all_versions:
                # Filter based on latest version.
                src_model = self.sourceModel()
                # need to check if this is the latest version of the file:
                all_versions = src_model.get_file_versions(file_item.key, work_area) or {}

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
            if reg_exp.indexIn(get_model_str(src_idx)) != -1:
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
            left_env = get_model_data(left_src_idx, FileModel.WORK_AREA_ROLE)
            left_versions = self.sourceModel().get_file_versions(left_item.key, left_env)
            right_env = get_model_data(right_src_idx, FileModel.WORK_AREA_ROLE)            
            right_versions = self.sourceModel().get_file_versions(right_item.key, right_env)
            
            if left_versions and right_versions:
                max_left_version = left_versions[max(left_versions.keys())]
                max_right_version = right_versions[max(right_versions.keys())]
                return max_left_version.compare(max_right_version) < 0

        # compare the two files!
        compare_res = left_item.compare(right_item)
        if compare_res != 0:
            return compare_res < 0

        # exactly the same modified dates so compare names:
        # - Note, files are sorted in reverse-date order (newest first) but we want files
        # with exactly the same modified date & time (an edge case) to be in alphabetical
        # order.  Because of this we reverse this comparison.
        return not (left_item.name < right_item.name)




