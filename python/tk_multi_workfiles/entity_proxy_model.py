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


class HierarchicalFilteringProxyModel(QtGui.QSortFilterProxyModel):
    """
    """
    def __init__(self, parent=None):
        """
        """
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        
        self._cached_regexp = None
        self._filter_dirty = True
        self._accepted_cache = {}
        self._child_accepted_cache = {}

    def invalidateFilter(self):
        """
        """
        self._filter_dirty = True
        QtGui.QSortFilterProxyModel.invalidateFilter(self)

    def filterAcceptsRow(self, src_row, src_parent_idx):
        """
        """
        reg_exp = self.filterRegExp()
        if self._filter_dirty or reg_exp != self._cached_regexp:
            # clear the cache as the search filter has changed
            self._accepted_cache = {}
            self._child_accepted_cache = {}
            self._cached_regexp = reg_exp
            self._filter_dirty = False
        
        # get the source index for the row:
        src_model = self.sourceModel()
        src_idx = src_model.index(src_row, 0, src_parent_idx)
        src_item = src_model.itemFromIndex(src_idx)
        
        # first, see if any children of this item are known to already be accepted
        child_accepted = self._child_accepted_cache.get(id(src_item), None)
        if child_accepted == True:
            # child is accepted so this item must also be accepted
            return True

        # next, we need to determine if the parent item has been accepted.  To do this,
        # search up the hierarchy stopping at the first parent that we know for sure if
        # it has been accepted or not.
        upstream_items = []
        current_idx = src_idx
        parent_accepted = False
        while current_idx and current_idx.isValid():
            item = src_model.itemFromIndex(current_idx)
            accepted = self._accepted_cache.get(id(item), None)
            if accepted != None:
                parent_accepted = accepted
                break
            upstream_items.append(item)
            current_idx = current_idx.parent()
            
        # now update the accepted status for items that we don't know
        # for sure:
        for item in reversed(upstream_items):
            accepted = self._is_item_accepted(item, parent_accepted)
            self._accepted_cache[id(item)] = accepted
            parent_accepted = accepted

        if src_item.hasChildren():
            # the parent acceptance doesn't mean that it is filtered out as this
            # depends if there are any children accepted:            
            return self._is_child_accepted_r(src_item, reg_exp, parent_accepted)
        else:
            return parent_accepted  

    def _is_child_accepted_r(self, item, reg_exp, parent_accepted):
        """
        """
        # check to see if any children of this item are known to have been accepted:
        child_accepted = self._child_accepted_cache.get(id(item), None)
        if child_accepted != None:
            # we already computed this so just return the result
            return child_accepted
        
        # need to recursively iterate over children looking for one that is accepted:
        child_accepted = False
        for ci in range(item.rowCount()):
            child_item = item.child(ci)
            
            # check if child item is in cache:
            accepted = self._accepted_cache.get(id(child_item), None)
            if accepted == None:
                # it's not so lets see if it's accepted and add to the cache:
                accepted = self._is_item_accepted(child_item, parent_accepted)
                self._accepted_cache[id(child_item)] = accepted

            if child_item.hasChildren():
                child_accepted = self._is_child_accepted_r(child_item, reg_exp, accepted)
            else:
                child_accepted = accepted
                
            if child_accepted:
                # found a child that was accepted so we can stop searching
                break

        # cache if any children were accepted:
        self._child_accepted_cache[id(item)] = child_accepted     
        return child_accepted    
    
    def _is_item_accepted(self, item, parent_accepted):
        """
        """
        raise NotImplementedError()

class EntityProxyModel(HierarchicalFilteringProxyModel):
    """
    """
    
    def __init__(self, compare_sg_fields=None, parent=None):
        """
        """
        HierarchicalFilteringProxyModel.__init__(self, parent)
        self._compare_fields = compare_sg_fields
                   
    def _is_item_accepted(self, item, parent_accepted):
        """
        """
        # if the parent is accepted then this node is accepted by default:
        if parent_accepted:
            return True 
        
        reg_exp = self.filterRegExp()
        if reg_exp.isEmpty():
            # early out
            return True        
        
        # test to see if the item 'text' matches:
        if reg_exp.indexIn(item.text()) != -1:
            # found a match so early out!
            return True

        if self._compare_fields:
            # see if we have sg data:
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
            if val and reg_exp.indexIn(val) != -1:
                return True
            
        return False
