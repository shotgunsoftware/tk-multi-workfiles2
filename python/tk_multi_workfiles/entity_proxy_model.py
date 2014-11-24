# Copyright (c) 2013 Shotgun Software Inc.
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

#shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

class EntityProxyModel(QtGui.QSortFilterProxyModel):
    """
    Filter model to be used in conjunction with SgEntityModel
    """
    
    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        
        # to avoid n^2 characteristics, cache computations
        # as we go through and recurse down. 
        #self._cache = {}
        #self._cache_hits = 0
        
    #def _matching_r(self, search_exp, item):
    #    """
    #    Recursive matching.
    #    """
    #    # use the python memory address as a key - both
    #    # for performance and to avoid keeping references to items
    #    item_hash = str(id(item))
    #    
    #    # check cache - did we already compute the cull state of this node?
    #    if item_hash in self._cache:
    #        self._cache_hits += 1
    #        return self._cache[item_hash]        
    #    
    #    # evaluate this node
    #    if search_exp.indexIn(item.text()) != -1:
    #        # item is matching - exit early - no need
    #        # to search children - because it is a match
    #        # we know we want to show this node
    #        self._cache[item_hash] = True
    #        return True
    #        
    #    # the node wasn't a direct match - however we still
    #    # want to show it if any of its *children* are matching
    #    # so recurse down...
    #    for idx in range(item.rowCount()):
    #        child_item = item.child(idx)
    #        if self._matching_r(search_exp, child_item):
    #            # exit early as soon as we find a match for performance
    #            self._cache[item] = True
    #            return True
    #    
    #    # no sub nodes matches. Keep this result in the cache so that next
    #    # time we need to compute it, we don't need to :)
    #    self._cache[item_hash] = False
    #    return False
    #    
    #def setFilterFixedString(self, pattern):
    #    """
    #    Overridden from base class.
    #    """
    #    # clear cache - now that the search criteria is changing,
    #    # the cache results are no longer valid
    #    app = sgtk.platform.current_bundle()
    #    cache_len = len(self._cache)
    #    if cache_len > 0:
    #        ratio = (float)(self._cache_hits) / (float)(cache_len) * 100.0
    #        app.log_debug("Search efficiency: %s items %4f%% cache hit ratio." % (cache_len, ratio))
    #    
    #    self._cache_hits = 0        
    #    self._cache = {}
    #    
    #    # call base class
    #    return QtGui.QSortFilterProxyModel.setFilterFixedString(self, pattern)
    #    
    #def filterAcceptsRow(self, source_row, source_parent_idx):
    #    """
    #    Overridden from base class.
    #    """
    #    # get the search filter, as specified via setFilterFixedString()
    #    search_exp = self.filterRegExp()
    #    search_exp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    #    
    #    # if there is no search criteria, exit early!
    #    if search_exp.isEmpty():
    #        return True
    #
    #    # look at the node and all its children to see if we should keep or cull.        
    #    model = self.sourceModel()
    #    
    #    # get the actual model index we are testing
    #    if not source_parent_idx.isValid():
    #        # top level item
    #        item = model.invisibleRootItem().child(source_row)
    #    else:
    #        # child item
    #        item_model_idx = source_parent_idx.child(source_row, 0)
    #        item = model.itemFromIndex(item_model_idx)
    #    
    #    # evaluate recursive match
    #    return self._matching_r(search_exp, item)
        
