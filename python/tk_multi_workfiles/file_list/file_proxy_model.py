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
    Proxy model used to sort and filter the file model
    """
    filtering_changed = QtCore.Signal()

    def __init__(self, parent, filters, show_work_files=True, show_publishes=True):
        """
        Construction

        :param filters:         A FileFilters instance containing the filter settings to be used when
                                filtering this proxy model
        :param show_work_files: True if work files should be shown, otherwise False
        :param show_publishes:  True if publishes should be shown, otherwise False
        :param parent:          The parent QObject of this proxy model 
        """
        HierarchicalFilteringProxyModel.__init__(self, parent)

        # debug - disable caching!
        #self.enable_caching(False)

        self._filters = filters
        if self._filters:
            self._filters.reg_exp_changed.connect(self._on_filters_reg_exp_changed)

        self._show_publishes = show_publishes
        self._show_workfiles = show_work_files

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

    def setFilterRegExp(self, reg_exp):
        """
        Overriden from base class - sets the filter regular expression by
        updating the regex in the FileFilters instance.
        
        :param reg_exp:    The QRegExp expression instance to set
        """
        # update the filter string in the filters instance.  This will result
        # in the filters.changed signal being emitted which will in turn update
        # the regex in this model.
        self._filters.filter_reg_exp = reg_exp

    def _on_filters_reg_exp_changed(self, reg_exp):
        """
        Slot triggered when something on the FileFilters instance changes.  Invalidates
        the proxy model so that the filtering is re-run.
        """
        if reg_exp != self.filterRegExp():
            HierarchicalFilteringProxyModel.setFilterRegExp(self, reg_exp)
        self.invalidateFilter()

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

        work_area_user_id = None
        filtered_user_ids = set(u["id"] for u in self._filters.users if u)

        # try to get the work area user
        work_area = get_model_data(src_idx, FileModel.WORK_AREA_ROLE)
        if work_area and work_area.context and work_area.context.user:
            work_area_user_id = work_area.context.user["id"]

        # get the file item and see if it should be filtered:
        file_item = get_model_data(src_idx, FileModel.FILE_ITEM_ROLE)
        if file_item:

            # Filter based on showing work files, publishes or both:
            if (not (file_item.is_local and self._show_workfiles)
                and not (file_item.is_published and self._show_publishes)):
                return False

            # Get the file owner
            file_user_id = None
            if file_item.is_published:
                file_user_id = file_item.published_by.get("id")
            elif file_item.is_local:
                file_user_id = file_item.modified_by.get("id")

            # Ensure the file owner is in the list of filtered users
            if file_user_id and file_user_id not in filtered_user_ids:
                return False

            # Filter the list of versions to compare by the same rules
            versions_to_compare = { v:f for v, f in file_item.versions.iteritems() 
                                        if (f.is_local and f.modified_by.get("id")
                                            in filtered_user_ids and self._show_workfiles) 
                                        or (f.is_published and f.published_by.get("id")
                                            in filtered_user_ids and self._show_publishes) }

            # If the publish area doesn't contain a user sandbox....
            if not work_area.publish_area_contains_user_sandboxes:
                # Filter out files not owned by the current user. This is to avoid
                # files showing up in multiple groups...
                if file_item.is_published and file_user_id != work_area_user_id:
                    return False

                # Filter the published versions to the ones owned by the current user
                versions_to_compare = { v:f for v, f in versions_to_compare.iteritems()
                                            if not (f.is_published and f.published_by.get("id") != work_area_user_id) }

            # If the work area doesn't contain a user sandbox....
            if not work_area.work_area_contains_user_sandboxes:
                # Filter out files not owned by the current user. This is to avoid
                # files showing up in multiple groups...
                if file_item.is_local and file_user_id != work_area_user_id:
                    return False

                # Filter the work versions to the ones owned by the current user
                versions_to_compare = { v:f for v, f in versions_to_compare.iteritems()
                                            if not (f.is_local and f.modified_by.get("id") != work_area_user_id) }

            if not self._filters.show_all_versions:
                # Filter based on latest version - need to check if this is the latest 
                # version of the file:
                if not versions_to_compare or file_item.version != max(versions_to_compare.keys()):
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
        Overriden from base class - called to compare two indexes when the model is being 
        sorted.

        :param left_src_idx:    The left index in the source model to compare
        :param right_src_idx:   The right index in the source model to compare
        :returns:               True of the source item for the left index is considered 
                                less than the source item for the right index, otherwise
                                False
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
            if left_item.versions and right_item.versions:
                max_left_version = left_item.versions[max(left_item.versions.keys())]
                max_right_version = right_item.versions[max(right_item.versions.keys())]
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




