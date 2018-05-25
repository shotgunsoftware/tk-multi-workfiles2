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
from sgtk.platform.qt import QtCore, QtGui

from .framework_qtwidgets import HierarchicalFilteringProxyModel

from .util import get_model_str

class EntityProxyModel(HierarchicalFilteringProxyModel):
    """
    """
    
    def __init__(self, parent, compare_sg_fields=None):
        """
        """
        HierarchicalFilteringProxyModel.__init__(self, parent)
        self._compare_fields = compare_sg_fields

    def setFilterFixedString(self, pattern):
        """
        Overriden base class method to set the filter fixed string
        """
        # ensure model is fully loaded before we attempt any searching
        self.sourceModel().ensure_data_is_loaded()

        # call base class
        return super(EntityProxyModel, self).setFilterFixedString(pattern)

    def setFilterRegExp(self, reg_exp):
        """
        Overriden base class method to set the filter regular expression
        """
        # ensure model is fully loaded before we attempt any searching
        self.sourceModel().ensure_data_is_loaded()

        # call base class
        return super(EntityProxyModel, self).setFilterRegExp(reg_exp)

    def ensure_data_is_loaded(self, index=None):
        """
        Recursively processes the model and ensures that all data
        has been loaded into the shotgun model contained by the proxy model.

        :param index: Model index for which to recursively load data.
                      If set to None, the entire tree will be loaded.
        :type index: :class:`~PySide.QtCore.QModelIndex`
        """
        # convert proxy indices to internal model indices
        source_index = self.mapToSource(index) if index else None

        return self.sourceModel().ensure_data_is_loaded(source_index)

    def _is_row_accepted(self, src_row, src_parent_idx, parent_accepted):
        """
        Overriden from base class - determines if the specified row should be accepted or not by
        the filter.

        :param src_row:         The row in the source model to filter
        :param src_parent_idx:  The parent QModelIndex instance to filter
        :param parent_accepted: True if a parent item has been accepted by the filter
        :returns:               True if this index should be accepted, otherwise False
        """
        # if the parent is accepted then this node is accepted by default:
        if parent_accepted:
            return True

        reg_exp = self.filterRegExp()
        if not reg_exp or reg_exp.isEmpty():
            # early out
            return True

        src_idx = self.sourceModel().index(src_row, 0, src_parent_idx)
        if not src_idx.isValid():
            return False

        # test to see if the item 'text' matches:
        if reg_exp.indexIn(get_model_str(src_idx)) != -1:
            # found a match so early out!
            return True

        if self._compare_fields:
            # see if we have sg data:
            item = src_idx.model().itemFromIndex(src_idx)
            sg_data = item.get_sg_data()
            if sg_data:
                return self._sg_data_matches_r(sg_data, self._compare_fields, reg_exp)

        # default is to not match!
        return False

    def _sg_data_matches_r(self, sg_data, compare_fields, reg_exp):
        """
        """
        if isinstance(compare_fields, list):
            # e.g. ["one", "two", {"three":"four", "five":["six", "seven"]}]
            for cf in compare_fields:
                if isinstance(cf, dict):
                    # e.g. {"three":"four", "five":["six", "seven"]}
                    for key, value in cf.iteritems():
                        data = sg_data.get(key)
                        if data:
                            if self._sg_data_matches_r(data, value, reg_exp):
                                return True
                else:
                    # e.g. "one"
                    if self._sg_data_matches_r(sg_data, cf, reg_exp):
                        return True
        else:
            # e.g. "one"
            val = sg_data.get(compare_fields)
            if val != None and reg_exp.indexIn(str(val)) != -1:
                return True
            
        return False
