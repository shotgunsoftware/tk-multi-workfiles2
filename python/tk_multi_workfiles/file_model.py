# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import weakref
import time

import sgtk
from sgtk.platform.qt import QtGui, QtCore
from sgtk import TankError

from .file_finder import FileFinder
from .user_cache import g_user_cache
from .file_search_cache import FileSearchCache

class TreeItem(object):
    """
    """
    def __init__(self):
        self._node = None

    @property
    def index(self):
        if not self._node or not self._node():
            return QtCore.QModelIndex()
        return self._node().index

    @property
    def model(self):
        if not self._node or not self._node():
            return None
        return self._node().model
        
        

class _TreeNode(object):
    """
    """
    def __init__(self, model, item, parent_node):
        self._model = weakref.ref(model) if model else None
        self.parent = parent_node
        self.children = []
        self.item = item
        if self.item:
            self.item._node = weakref.ref(self)

    @property
    def index(self):
        """
        """
        model = self.model
        if not model:
            return QtCore.QModelIndex()
        return model._index_for_node(self)
    
    @property
    def model(self):
        return self._model() if self._model else None

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        """
        """
        QtCore.QAbstractItemModel.__init__(self, parent)
        self._root_nodes = []
        
        self._root_node = _TreeNode(self, None, None)

    def item(self, index):
        """
        """
        pass

    def _index_for_node(self, node):
        """
        """
        if node == self._root_node:
            # we've reached the root!
            return QtCore.QModelIndex()
        
        # get the parent index:
        parent_index = self._index_for_node(node.parent)
        row = node.parent.children.index(node)
        index = QtCore.QModelIndex(row, 0, parent_index)
        return index

    def index(self, row, column, parent):
        """
        """
        parent_node = parent.internalPointer() if parent else self._root_node
        if parent_node and row < len(parent_node.children):
            return self.createIndex(row, column, parent_node.children[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        """
        """
        if not index.isValid():
            return QtCore.QModelIndex()
        node = index.internalPointer()
        if not node or node.parent is None:
            return QtCore.QModelIndex()
        try:
            row = node.parent.children.index(node)
            return self.createIndex(row, 0, node.parent)
        except ValueError:
            return QtCore.QModelIndex()

    def reset(self):
        """
        """
        self.beginResetModel()
        self._root_node.children = []
        # (AD) - do we need to call the base class?
        QtCore.QAbstractItemModel.reset(self)
        self.endResetModel()

    def rowCount(self, parent):
        """
        """
        node = parent.internalPointer() if parent else self._root_node
        return len(node.children) if node else 0

    def append_row(self, item, parent_idx=QtCore.QModelIndex()):
        """
        """
        return self._insert_rows(None, [item], parent_idx)

    def append_rows(self, items, parent_idx=QtCore.QModelIndex()):
        """
        """
        return self._insert_rows(None, items, parent_idx)

    def insert_row(self, row, item, parent_idx=QtCore.QModelIndex()):
        """
        """
        return self._insert_rows(row, [item], parent_idx)
    
    def insert_rows(self, row, items, parent_idx=QtCore.QModelIndex()):
        """
        """
        return self._insert_rows(row, items, parent_idx)

    def remove_row(self, row, parent_idx=QtCore.QModelIndex()):
        """
        """
        return self._remove_rows(row, 1, parent_idx)

    def remove_rows(self, row, count, parent_idx=QtCore.QModelIndex()):
        """
        """
        return self._remove_rows(row, count, parent_idx)

    def clear(self):
        """
        """
        self.clear_children()

    def clear_children(self, parent_idx=QtCore.QModelIndex()):
        """
        """
        parent_node = parent_idx.internalPointer() if parent_idx else self._root_node
        if not parent_node:
            return

        for ri in range(len(parent_node.children)):
            child_index = self.index(ri, 0, parent_idx)
            self.clear_children(child_index)

        self._remove_rows(0, len(parent_node.children), parent_idx)

    def _insert_rows(self, insert_idx, items, parent_idx):
        """
        """
        parent_node = parent_idx.internalPointer() if parent_idx else self._root_node
        if not parent_node:
            return False
        
        if insert_idx is None:
            insert_idx = len(parent_node.children)
        else:
            insert_idx = max(0, min(insert_idx, len(parent_node.children)))

        # create the new nodes and add them to the model:
        self.beginInsertRows(parent_idx, insert_idx, insert_idx + len(items) - 1)
        try:
            new_nodes = [_TreeNode(self, item, parent_node) for item in items]
            parent_node.children = (parent_node.children[:insert_idx] 
                                    + new_nodes 
                                    + parent_node.children[insert_idx:])
        finally:
            self.endInsertRows()

        return True
    
    def _remove_rows(self, row, count, parent_idx):
        """
        """
        parent_node = parent_idx.internalPointer() if parent_idx else self._root_node
        if not parent_node:
            return False
        
        last_row = min(row + count - 1, len(parent_node.children))
        if last_row < row:
            # nothing to remove as the rows aren't in the list!
            return True

        # create the new nodes and add them to the model:
        self.beginRemoveRows(parent_idx, row, last_row)
        try:
            parent_node.children = (parent_node.children[:row] 
                                    + parent_node.children[last_row+1:])
        finally:
            self.endInsertRows()





class FileModel(QtGui.QStandardItemModel):
    """
    """
    class SearchDetails(object):
        """
        Storage of details needed to search for files.
        """
        def __init__(self, name=None):
            self.name = name
            self.entity = None
            self.child_entities = []
            self.is_leaf = False

        def __repr__(self):
            return ("%s\n"
                    " - Entity: %s\n"
                    " - Is leaf: %s\n%s"
                    % (self.name, self.entity, self.is_leaf, self.child_entities))

    # enumeration of node types in model:
    (FILE_NODE_TYPE, GROUP_NODE_TYPE, FOLDER_NODE_TYPE) = range(3)

    # enumeration of search status:
    (SEARCHING, SEARCH_COMPLETED, SEARCH_FAILED) = range(3)

    # additional data roles defined for thie model:
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    NODE_TYPE_ROLE = _BASE_ROLE     + 1     # type of node in model (e.g. FILE_NODE_TYPE)
    FILE_ITEM_ROLE = _BASE_ROLE     + 2     # FileItem data
    WORK_AREA_ROLE = _BASE_ROLE     + 3     # WorkArea data
    SEARCH_STATUS_ROLE = _BASE_ROLE + 4     # search status data
    SEARCH_MSG_ROLE = _BASE_ROLE    + 5     # search message data

    DATA_INDEX_ROLE = _BASE_ROLE    + 6

    class _BaseItemData(object):
        def __init__(self, typ):
            self.item_type = typ

    class _BaseItem(QtGui.QStandardItem):
        """
        """
        def __init__(self, data_index, text=None):
            """
            """
            QtGui.QStandardItem.__init__(self, text or "")
            QtGui.QStandardItem.setData(self, data_index, FileModel.DATA_INDEX_ROLE)

        @property
        def item_data_index(self):
            return QtGui.QStandardItem.data(self, FileModel.DATA_INDEX_ROLE)

        @property
        def item_data(self):
            # note, going through self.model() has a tendency to crash so instead we get
            # the QModelIndex of the item in the model and then the model from that!
            idx = self.index()
            if idx.isValid():
                return idx.model()._item_data.get(self.item_data_index)

        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.NODE_TYPE_ROLE:
                item_data = self.item_data
                return item_data.item_type if item_data else None
                #return self._type
            else:
                # just return the default implementation:
                return QtGui.QStandardItem.data(self, role)

        def setData(self, value, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.NODE_TYPE_ROLE:
                # do nothing as the data can't be set:
                pass
            else:
                # call the base implementation:
                QtGui.QStandardItem.setData(self, value, role) 

    class _FileItemData(_BaseItemData):
        def __init__(self, file_item, work_area):
            FileModel._BaseItemData.__init__(self, typ=FileModel.FILE_NODE_TYPE)
            self.file_item = file_item
            self.work_area = work_area

    class _FileItem(QtGui.QStandardItem):
        """
        """
        def __init__(self, file_item, work_area):
            """
            """
            name = ("%s, v%0d" % (file_item.name, file_item.version)) if file_item else ""
            QtGui.QStandardItem.__init__(self, name)
            self._file_item = file_item
            self._work_area = work_area

        @property
        def file_item(self):
            return self._file_item

        @property
        def environment(self):
            return self._work_area

    class _FileItem_BAD(_BaseItem):
        """
        """
        #def __init__(self, file_item, environment):
        #    """
        #    """
        #    FileModel._BaseItem.__init__(self, typ=FileModel.FILE_NODE_TYPE)
        #    self._file_item = file_item
        #    self._environment = environment
        @property
        def file_item(self):
            item_data = self.item_data
            return item_data.file_item if item_data else None

        @property
        def environment(self):
            item_data = self.item_data
            return item_data.work_area if item_data else None

        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == QtCore.Qt.DisplayRole:
                file_item = self.file_item
                return ("%s, v%0d" % (file_item.name, file_item.version)) if file_item else ""
            elif role == FileModel.FILE_ITEM_ROLE:
                return self.file_item
            elif role == FileModel.WORK_AREA_ROLE:
                return self.environment
            else:
                # just return the default implementation:
                return FileModel._BaseItem.data(self, role)

        def setData(self, value, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == QtCore.Qt.DisplayRole:
                # do nothing as it can't be set!
                pass
            elif role == FileModel.FILE_ITEM_ROLE:
                item_data = self.item_data
                if item_data:
                    item_data.file_item = value
                    self.emitDataChanged()
            elif role == FileModel.WORK_AREA_ROLE:
                item_data = self.item_data
                if item_data:
                    item_data.work_area = value
                    self.emitDataChanged()
            else:
                # call the base implementation:
                FileModel._BaseItem.setData(self, value, role) 

    class _FolderItemData(_BaseItemData):
        def __init__(self, entity):
            FileModel._BaseItemData.__init__(self, typ=FileModel.FOLDER_NODE_TYPE)
            self.entity = entity

    class _FolderItem(_BaseItem):
        """
        """
        @property
        def entity(self):
            item_data = self.item_data
            return item_data.entity if item_data else None

    class _GroupItemData(_BaseItemData):
        def __init__(self, key, work_area=None):
            FileModel._BaseItemData.__init__(self, typ=FileModel.GROUP_NODE_TYPE)
            self.search_status = FileModel.SEARCH_COMPLETED
            self.search_msg = ""
            self.work_area = work_area
            self.key = key

    class _GroupItem(QtGui.QStandardItem):
        def __init__(self, key, text=None):
            """
            """
            QtGui.QStandardItem.__init__(self, text or "")
            self._key = key
            self._search_status = FileModel.SEARCH_COMPLETED
            self._search_msg = ""
            self._work_area = None

        @property
        def key(self):
            return self._key

        #@property
        def _get_work_area(self):
            return self._work_area
        #@work_area.setter
        def _set_work_area(self, work_area):
            self._work_area = work_area
            #self.emitDataChanged()
        work_area=property(_get_work_area, _set_work_area)

        def set_search_status(self, status, msg=None):
            """
            """
            self._search_status = status
            self._search_msg = msg
            #self.emitDataChanged()

    class _GroupItem_BAD(_BaseItem):
        """
        """
        @property
        def key(self):
            item_data = self.item_data
            return item_data.key if item_data else None

        #@property
        def _get_work_area(self):
            item_data = self.item_data
            return item_data.work_area if item_data else None
        #@work_area.setter
        def _set_work_area(self, work_area):
            item_data = self.item_data
            if item_data:
                item_data.work_area = work_area
                self.emitDataChanged()
        work_area=property(_get_work_area, _set_work_area)

        def set_search_status(self, status, msg=None):
            """
            """
            item_data = self.item_data
            if item_data:
                item_data.search_status = status
                item_data.search_msg = msg
                self.emitDataChanged()

        def data(self, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.SEARCH_STATUS_ROLE:
                item_data = self.item_data
                return item_data.search_status if item_data else FileModel.SEARCH_COMPLETED
            elif role == FileModel.SEARCH_MSG_ROLE:
                item_data = self.item_data
                return item_data.search_msg if item_data else ""
            elif role == FileModel.WORK_AREA_ROLE:
                item_data = self.item_data
                return item_data.work_area if item_data else None
            else:
                # just return the default implementation:
                return FileModel._BaseItem.data(self, role)

        def setData(self, value, role=QtCore.Qt.UserRole+1):
            """
            """
            if role == FileModel.SEARCH_STATUS_ROLE:
                item_data = self.item_data
                if item_data:
                    item_data.search_status = value
                    self.emitDataChanged()
            elif role == FileModel.SEARCH_MSG_ROLE:
                item_data = self.item_data
                if item_data:
                    item_data.search_msg = value
                    self.emitDataChanged()
            elif role == FileModel.WORK_AREA_ROLE:
                item_data = self.item_data
                if item_data:
                    item_data.work_area = value
                    self.emitDataChanged()
            else:
                # call the base implementation:
                FileModel._BaseItem.setData(self, value, role) 

    # Signal emitted when the available sandbox users have changed
    available_sandbox_users_changed = QtCore.Signal(object)

    def __init__(self, sg_data_retriever, parent):
        """
        Construction
        """
        #TreeModel.__init__(self, parent)
        QtGui.QStandardItemModel.__init__(self, parent)

        self._next_item_data_index = 0
        self._item_data = {}
        self._all_files = []
        self._all_envs = []

        # sg data retriever is used to download thumbnails in the background
        self._sg_data_retriever = sg_data_retriever
        if self._sg_data_retriever:
            self._sg_data_retriever.work_completed.connect(self._on_data_retriever_work_completed)
            self._sg_data_retriever.work_failure.connect(self._on_data_retriever_work_failed)

        # details about the current entities and users that are represented
        # in this model.
        self._current_searches = []
        self._current_users = [g_user_cache.current_user]
        self._entity_work_areas = {}
        self._in_progress_searches = {}
        self._search_cache = FileSearchCache()
        self._file_to_item_map = {}
        self._pending_thumbnail_requests = {}

        # we'll need a file finder to be able to find files:
        self._finder = FileFinder(parent=self)
        self._finder.files_found.connect(self._on_finder_files_found)
        self._finder.publishes_found.connect(self._on_finder_publishes_found)
        self._finder.search_completed.connect(self._on_finder_search_completed)
        self._finder.search_failed.connect(self._on_finder_search_failed)
        self._finder.work_area_found.connect(self._on_finder_work_area_found)
        
        self._all_items = []
        
        self._dbg_file = None#open("/Users/Alan_Dann/worfiles_v2_dbg.txt", "w")
        
        #self.setItemPrototype(FileModel._CustomItem(""))

    class TreeItem(object):
        def __init__(self, name):
            self.name = name

    def _update_groups(self):
        """
        """
        #self.clear()
        if self.invisibleRootItem().hasChildren():
            self.invisibleRootItem().removeRows(0, self.invisibleRootItem().rowCount())

        new_items = []

        for search in self._current_searches:
            for user in self._current_users:
                group_item = QtGui.QStandardItem(search.name)
                new_items.append(group_item)
                #self.appendRow(group_item)
                #self.invisibleRootItem().appendRows([group_item])
                #group_item = FileModel.TreeItem(search.name)
                #self.append_row(group_item)

        if new_items:
            self.invisibleRootItem().appendRows(new_items)

    def _process_files(self, files, environment, parent_item, have_local=True, have_publishes=True):
        """
        """
        new_items = []
        
        for file_item in files:
            #name = ("%s, v%0d" % (file_item.name, file_item.version)) if file_item else ""
            model_item = QtGui.QStandardItem(file_item.name)
            #model_item = FileModel.TreeItem(name)
            new_items.append(model_item)
            #parent_item.appendRows([model_item])

        if new_items:
            #parent_idx = ?
            #self.append_rows(new_items, parent_idx)
            parent_item.appendRows(new_items)

    def _add_new_group(self, name, group_key, environment):
        """
        """
        group_item = QtGui.QStandardItem(name)
        self.invisibleRootItem().appendRows([group_item])
        
        #group_item = FileModel.TreeItem(name)
        #self.append_row(group_item)
        return group_item

    def _add_new_group_BAD(self, name, group_key, environment):
        # we don't have a group item for this search so lets add one now:
        group_item = self._add_group_item(name, group_key, environment)
        # (TODO) need to insert it into the right place in the list!
        #self.invisibleRootItem().appendRow(group_item)
        self.invisibleRootItem().appendRows([group_item])










    def get_file_versions(self, key, env):
        """
        """
        return self._search_cache.find_file_versions(key, env.context)

    def item_from_file(self, file_item):
        """
        """
        if not file:
            return None

        # find the model item using the file-to-item map:
        _, model_item_ref = self._file_to_item_map.get(id(file_item), (None, None))
        if not model_item_ref:
            return None

        return model_item_ref()

    # Interface for modifying the entities in the model:
    def set_entity_searches(self, searches):
        """
        """
        #print "Setting entity searches on model to: %s" % [s.name for s in searches if s]
        # stop any in-progress searches:
        self._stop_in_progress_searches()
        self._current_searches = searches or []

        # update groups:
        self._update_groups()

        # start searches for all items/users in the model:
        self._start_searches()

    # Interface for modifying the users in the model:
    def set_users(self, users):
        """
        """
        #print "Setting users on model to: %s" % [u["name"] for u in users if u]
        # stop any in-progress searches:
        self._stop_in_progress_searches()

        self._current_users = list(users or [])
        if g_user_cache.current_user:
            # we _always_ search for the current user:
            user_ids = [user["id"] for user in self._current_users]
            if g_user_cache.current_user["id"] not in user_ids:
                self._current_users.insert(0, g_user_cache.current_user)

        # update groups:
        self._update_groups()

        # start searches for all items/users in the model:
        self._start_searches()

    def async_refresh(self):
        """
        """
        # stop any current searches:
        self._stop_in_progress_searches()
        # and restart all searches:
        self._start_searches()

    def clear(self):
        """
        """
        # stop all current searches:
        self._stop_in_progress_searches()
        # any pending thumbnail requests can be discarded:
        self._pending_thumbnail_requests = {}
        
        # clear all item data:
        self._item_data = {}

        self._all_items = []

        QtGui.QStandardItemModel.clear(self)

        # clear all items in a bottom-up fashion:
        #self._clear_children_r(self.invisibleRootItem())

        # clean up the file-to-item map
        self._cleanup_file_to_item_map()

    def _safe_remove_row(self, row, parent_item=None):
        """
        """
        # get the item and safey remove all children of the item:
        item = parent_item.child(row) if parent_item else self.item(row, 0)
        if not item:
            return
        self._clear_children_r(item)
        data_idx = item.item_data_index if isinstance(item, FileModel._BaseItem) else None
        item = None

        if parent_item:
            # remove row from parent:
            parent_item.removeRow(row)
        else:
            # must be a root row:
            self.removeRow(row)
            
        if data_idx in self._item_data:
            del self._item_data[data_idx]

    def _clear_children_r(self, parent_item):
        """
        """
        num_rows = parent_item.rowCount()
        if num_rows == 0:
            return
        
        #print "Clearing %d child rows of parent %s" % (parent_item.rowCount(), parent_item)
        data_to_remove = []
        for row in range(num_rows):
            child_item = parent_item.child(row)
            if child_item:
                #print "Processing child %s" % child_item
                self._clear_children_r(child_item)
            else:
                print "NO CHILD ROW TO REMOVE!"
                
            # keep track of data:
            if isinstance(child_item, FileModel._BaseItem):
                data_to_remove.append(child_item.item_data_index)

        # and clear all children:
        parent_item.removeRows(0, num_rows)
        # and remove the data:
        for data_idx in data_to_remove:
            if data_idx in self._item_data:
                del self._item_data[data_idx]

    def destroy(self):
        """
        """
        # clear the model:
        self.clear()

        # disconnect from the data retriever:
        if self._sg_data_retriever:
            self._sg_data_retriever.work_completed.disconnect(self._on_data_retriever_work_completed)
            self._sg_data_retriever.work_failure.disconnect(self._on_data_retriever_work_failed)
            self._sg_data_retriever = None

        # clean up the cache:
        if self._search_cache:
            self._search_cache.clear()
            self._search_cache = None

        # disconnect and clean up the file finder:
        if self._finder:
            self._finder.files_found.disconnect(self._on_finder_files_found)
            self._finder.publishes_found.disconnect(self._on_finder_publishes_found)
            self._finder.search_completed.disconnect(self._on_finder_search_completed)
            self._finder.search_failed.disconnect(self._on_finder_search_failed)
            self._finder.work_area_found.disconnect(self._on_finder_work_area_found)
            self._finder.shut_down()
            self._finder = None
            
        if self._dbg_file:
            self._dbg_file.close()

    # ------------------------------------------------------------------------------------------
    # protected methods

    def _group_items(self):
        """
        """
        for ri in range(self.invisibleRootItem().rowCount()):
            child_item = self.invisibleRootItem().child(ri)
            if isinstance(child_item, FileModel._GroupItem):
                yield child_item

    def _file_items(self, parent_item):
        """
        """
        for ri in range(parent_item.rowCount()):
            child_item = parent_item.child(ri)
            if isinstance(child_item, FileModel._FileItem):
                yield child_item

    def _entity_key(self, entity_dict):
        """
        """
        if not entity_dict:
            return (None, None)
        else:
            return (entity_dict.get("type"), entity_dict.get("id"))

    def _start_searches(self):
        """
        """
        if not self._current_searches:
            # nothing to do!
            return

        # get existing groups:
        group_map = {}
        for group_item in self._group_items():
            group_map[group_item.key] = group_item

        for search in self._current_searches:
            if not search.entity:
                continue

            # update all existing group items for this entity and all users to indicate
            # that we are searching for files
            entity_key = self._entity_key(search.entity)
            for user in self._current_users:
                user_key = self._entity_key(user)
                group_key = (entity_key, user_key)
                group_item = group_map.get(group_key)
                if group_item:
                    group_item.set_search_status(FileModel.SEARCHING)

            # and actually start the search:
            #search_id = self._finder.begin_search(search.entity, self._current_users)
            #self._in_progress_searches[search_id] = search
            #print "Started search %d..." % search_id

            self._in_progress_searches[0] = search
            res = self._finder.do_inline_search(search.entity, self._current_users)
            for file_items, work_area in res:
                self._on_finder_files_found(0, file_items, work_area)
                self._on_finder_search_completed(0)
                

    def _stop_in_progress_searches(self):
        """
        """
        search_ids = self._in_progress_searches.keys()
        self._in_progress_searches = {}
        for id in search_ids:
            self._finder.stop_search(id)


    def _update_groups_BAD(self):
        """
        """
        self._dbg_write("Updating groups")
        
        #self.clear()
        
        # get existing groups:
        group_map = {}
        for group_item in self._group_items():
            group_map[group_item.key] = group_item

        valid_group_keys = set()
        if self._current_searches and self._current_users:

            # get details about the users to run searches for:
            current_user_key = self._entity_key(g_user_cache.current_user)
            have_current_user = False
            for user in self._current_users:
                if self._entity_key(user) == current_user_key:
                    have_current_user = True
                    break
            primary_user_key = current_user_key if have_current_user else self._entity_key(self._current_users[0])

            # iterate over the searches, making sure that group nodes exist as needed
            previous_valid_row = -1
            for search in self._current_searches:
                if not search.entity:
                    # this search doesn't represent an entity so we won't need to search
                    # for files.  In which case we can just add a group item with the
                    # correct name and be done with it!  We also only need one of these
                    # rather than (potentially) one per user!
                    continue

                entity_key = self._entity_key(search.entity)

                # iterate over each user for this group:
                for user in self._current_users:
                    user_key = self._entity_key(user)
                    group_key = (entity_key, user_key)

                    # see if we already have an item for this group:
                    group_item = group_map.get(group_key)

                    if not group_item:
                        # we don't have a group node for this entity/user combination:
                        cached_result = self._search_cache.find(search.entity, user)
                        if (user_key == primary_user_key or cached_result):
                            # always add a group for the primary user or if we already have a cached result:
                            #group_item = FileModel._GroupItem(search.name, group_key)
                            group_item = self._add_group_item(search.name, group_key)
                            #self.insertRow(previous_valid_row + 1, group_item)
                            self.invisibleRootItem().appendRows([group_item])

                            if cached_result:
                                # we have a cached result so populate the group:
                                files, environment = cached_result
                                self._process_files(files, environment, group_item)
                                group_item.work_area = environment

                    if group_item:
                        # make sure the name and entity children are up-to-date:
                        self._update_group_child_entity_items(group_item, search.child_entities or [])

                        # keep track of the last valid group row:
                        previous_valid_row = group_item.row()

                        # and keep track of this group item:
                        valid_group_keys.add(group_key)

        # remove any groups that are no longer needed:
        for group_key, group_item in group_map.iteritems():
            if group_key not in valid_group_keys:
                self._safe_remove_row(group_item.row())

        # and clean up the file-to-item map:
        self._cleanup_file_to_item_map()
        
        self._dbg_write(" > Finished updating groups")

    def _add_group_item(self, name, group_key, work_area=None):
        """
        """
        #item_data_idx = self._next_item_data_index
        #self._next_item_data_index += 1
        #self._item_data[item_data_idx] = FileModel._GroupItemData(group_key, work_area)
        #item = FileModel._GroupItem(item_data_idx, name)
        item = FileModel._GroupItem(group_key, name)
        #item = QtGui.QStandardItem(name)
        #self._all_items.append(item)
        return item
    
    def _add_file_item(self, file_item, work_area):
        """
        """
        #item_data_idx = self._next_item_data_index
        #self._next_item_data_index += 1
        #self._item_data[item_data_idx] = FileModel._FileItemData(file_item, work_area)
        #item = FileModel._FileItem(item_data_idx)
        item = FileModel._FileItem(file_item, work_area)
        #name = ("%s, v%0d" % (file_item.name, file_item.version)) if file_item else ""
        #item = QtGui.QStandardItem(name)
        #self._all_items.append(item)
        return item
        
    def _add_folder_item(self, name, entity):
        """
        """
        item_data_idx = self._next_item_data_index
        self._next_item_data_index += 1
        self._item_data[item_data_idx] = FileModel._FolderItemData(entity)
        item = FileModel._FolderItem(item_data_idx, name)
        #self._all_items.append(item)
        return item
        

    def _update_group_child_entity_items(self, parent_item, child_details):
        """
        """
        return
        self._dbg_write("Updating group child entity items...")

        # build a map from the entity key to row for all folder items:
        current_entity_row_map = {}
        for ri in range(parent_item.rowCount()):
            child_item = parent_item.child(ri)
            if isinstance(child_item, FileModel._FolderItem):
                child_name = child_item.text()
                child_entity = child_item.entity
                child_key = (child_name, self._entity_key(child_entity))
                current_entity_row_map[child_key] = ri

        # figure out which entities we need to add:
        valid_entity_keys = set()
        entities_to_add = []
        for details in child_details:
            child_name = details.get("name", "Entity")
            child_entity = details.get("entity")
            child_key = (child_name, self._entity_key(child_entity))
            if child_key in valid_entity_keys:
                # don't add the same entity twice!
                continue
            valid_entity_keys.add(child_key)
            if child_key not in current_entity_row_map:
                entities_to_add.append((child_name, child_entity))

        # figure out which rows to remove...
        rows_to_remove = set([row for key, row in current_entity_row_map.iteritems() if key not in valid_entity_keys])
        # and remove them:
        for row in sorted(rows_to_remove, reverse=True):
            self._safe_remove_row(row, parent_item)

        # finally, add in new rows:
        if entities_to_add:
            new_rows = []
            for name, entity in entities_to_add:
                #folder_item = FileModel._FolderItem(name, entity)
                folder_item = self._add_folder_item(name, entity)
                #folder_item.setIcon(QtGui.QIcon(":/tk-multi-workfiles2/folder_512x400.png"))
                new_rows.append(folder_item)
            parent_item.appendRows(new_rows)

        self._dbg_write(" > Finished Updating group child entity items!")

    def _dbg_write(self, msg):
        if self._dbg_file:
            self._dbg_file.write("%s\n" % msg)
            self._dbg_file.flush()

    def _process_files_BAD(self, files, environment, parent_item, have_local=True, have_publishes=True):
        """
        """
        if not have_local and not have_publishes:
            # nothing to do then!
            return
        self._dbg_write("Processing %d found files for item '%s'" % (len(files), parent_item.text()))

        self._dbg_write(" > Getting info from existing items...")

        # get details about existing items:
        existing_file_item_map = {}
        prev_local_file_versions = set()
        prev_publish_file_versions = set()

        for model_item in self._file_items(parent_item):
            self._dbg_write("   > A")
            #data_idx = model_item.item_data_index
            #item_data = self._item_data.get(data_idx)
            #if not item_data:
            #    continue
            #file_item = item_data.file_item

            #continue

            file_item = model_item.file_item
            self._dbg_write("   > B")
            file_version_key = (file_item.key, file_item.version)
            self._dbg_write("   > C")
            existing_file_item_map[file_version_key] = (file_item, model_item)
            if file_item.is_local:
                prev_local_file_versions.add(file_version_key)
            if file_item.is_published:
                prev_publish_file_versions.add(file_version_key)

        self._dbg_write(" > Determining valid files...")

        # build a list of existing files that we should keep in the model:
        file_versions_to_keep = set()
        if have_local and not have_publishes:
            # keep all publishes that aren't local
            file_versions_to_keep = prev_publish_file_versions
        elif not have_local and have_publishes:
            # keep all local that aren't publishes
            file_versions_to_keep = prev_local_file_versions
        valid_files = dict([(k, v[0]) for k, v in existing_file_item_map.iteritems() if k in file_versions_to_keep])

        self._dbg_write(" > Matching files against items...")

        # match files against existing items:
        updated_items = []
        files_to_add = []
        for file_item in files:
            file_version_key = (file_item.key, file_item.version)
            current_file, model_item = existing_file_item_map.get(file_version_key, (None, None))
            if current_file and model_item:
                # update the existing file:
                if file_item.is_published:
                    current_file.update_from_publish(file_item)
                if file_item.is_local:
                    current_file.update_from_work_file(file_item)
                updated_items.append(model_item)
            else:
                # file not in model yet so we'll need to add it:
                files_to_add.append(file_item)

            # add to the list of valid files:
            valid_files[file_version_key] = file_item

            ## if this is from a published file then we want to retrieve the thumbnail
            ## if one is available:
            if file_item.is_published and file_item.thumbnail_path and not file_item.thumbnail:
                # request the thumbnail using the data retriever:
                #request_id = self._sg_data_retriever.request_thumbnail(file_item.thumbnail_path, 
                #                                                       "PublishedFile", 
                #                                                       file_item.published_file_id,
                #                                                       "image")
                #self._pending_thumbnail_requests[request_id] = (file_item, environment)
                pass

        self._dbg_write(" > Calculating dead items...")

        # figure out if any existing items are no longer needed:
        valid_file_versions = set(valid_files.keys())
        file_versions_to_remove = set(existing_file_item_map.keys()) - valid_file_versions
        rows_to_remove = set([v[1].row() for k, v in existing_file_item_map.iteritems() if k in file_versions_to_remove])

        # update any files that are no longer in the corresponding set but which aren't going to be removed:
        if have_local:
            for file_version_key in (prev_local_file_versions - valid_file_versions) - file_versions_to_remove:
                file_item, model_item = existing_file_item_map[file_version_key]
                file_item.set_not_work_file()
                updated_items.append(model_item)
        if have_publishes:
            for file_version_key in (prev_publish_file_versions - valid_file_versions) - file_versions_to_remove:
                file_item, model_item = existing_file_item_map[file_version_key]
                file_item.set_not_published()
                updated_items.append(model_item)

        self._dbg_write(" > Updating the cache...")

        # update the cache - it's important this is done _before_ adding/updating the model items:
        self._search_cache.add(environment, valid_files.values())
        self._all_files.extend(valid_files.values())
        self._all_envs.append(environment)

        self._dbg_write(" > Removing %d items..." % len(rows_to_remove))

        """
        # now lets remove, add and update items as needed:
        # 1. Remove items that are no longer needed:
        if rows_to_remove:
            self._dbg_write(" > Removing %d file items..." % len(rows_to_remove))
            for row in sorted(rows_to_remove, reverse=True):
                self._dbg_write("   > Removing row %d" % row)
                self._safe_remove_row(row, parent_item)
                self._dbg_write("     Done!")
                
        self._dbg_write(" > Adding %d items..." % len(files_to_add))
        """
        # 2. Add new items:
        if files_to_add:
            self._dbg_write(" > Appending %d new file items..." % len(files_to_add))
            new_items = []
            for file_item in files_to_add:
                self._dbg_write("   > Appending new file item for %s, v%03d" % (file_item.name, file_item.version))
                #model_item = FileModel._FileItem(file_item, environment)
                model_item = self._add_file_item(file_item, environment)
                #parent_item.appendRow(model_item)
                new_items.append(model_item)
                # add to file-item map:
                #self._file_to_item_map[id(file_item)] = (file_item, weakref.ref(model_item))
                self._dbg_write("     Done!")
            if new_items:
                parent_item.appendRows(new_items)
                
        self._dbg_write(" > Updating %d items..." % len(updated_items))
        """
        # 3. Emit data changed for any updated model items:
        if updated_items:
            self._dbg_write(" > Emitting data changed signal for %d modified file items..." % len(updated_items))
            for model_item in updated_items:
                file_item = model_item.file_item
                self._dbg_write("   > Emitting data changed signal for file item for %s, v%03d" % (file_item.name, file_item.version))
                self.dataChanged.emit(model_item.index(), model_item.index())
                self._dbg_write("     Done!")
        """
        self._dbg_write(" > Cleaning up file-to-item map!")

        # and clean up the file-to-item map:
        self._cleanup_file_to_item_map()

        self._dbg_write(" > Finished processing found files!")

    def _cleanup_file_to_item_map(self):
        """
        Cleanup the file-to-item map by removing any entries that are no longer
        valid (this also disconnects the model from the FileItem.data_changed signal)
        """
        new_file_to_item_map = {}
        for k, v in self._file_to_item_map.iteritems():
            file_item, model_item_ref = v
            if model_item_ref() is not None:
                # model item still exists so keep it in map:
                new_file_to_item_map[k] = (file_item, model_item_ref)

        self._file_to_item_map = new_file_to_item_map

    def _on_finder_work_area_found(self, search_id, work_area):
        """
        Called when the finder has found a work area for the search.
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        search = self._in_progress_searches[search_id]
        entity_key = self._entity_key(search.entity)

        # keep track of work area for this entity:
        self._entity_work_areas[entity_key] = work_area

        # consolidate list of sandbox users for all current work areas:
        have_user_sandboxes = False
        users_by_id = {}
        handled_entities = set()
        for search in self._in_progress_searches.values():
            entity_key = self._entity_key(search.entity)
            if entity_key in handled_entities:
                continue
            handled_entities.add(entity_key)

            area = self._entity_work_areas.get(entity_key)
            if area and area.contains_user_sandboxes:
                have_user_sandboxes = True
                for user in area.sandbox_users:
                    if user:
                        users_by_id[user["id"]] = user

        # and current user is _always_ available:
        if g_user_cache.current_user:
            users_by_id[g_user_cache.current_user["id"]] = g_user_cache.current_user

        if have_user_sandboxes:
            self.available_sandbox_users_changed.emit(users_by_id.values())

    def _on_finder_files_found(self, search_id, file_list, environment):
        """
        Called when the finder has found some files.
        """
        print "Found %d files for search %s, user '%s'" % (len(file_list), search_id, environment.context.user["name"])
        self._process_found_files(search_id, file_list, environment, have_local=True, have_publishes=False)
    
    def _on_finder_publishes_found(self, search_id, file_list, environment):
        """
        """
        print "Found %d publishes for search %s, user '%s'" % (len(file_list), search_id, environment.context.user["name"])
        self._process_found_files(search_id, file_list, environment, have_local=False, have_publishes=True)

    def _process_found_files(self, search_id, file_list, environment, have_local, have_publishes):
        """
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return
        search = self._in_progress_searches[search_id]
        search_user = environment.context.user

        # find the group item for this search:
        group_key = (self._entity_key(search.entity), self._entity_key(search_user))
        found_group = False
        for group_item in self._group_items():
            if group_item.key == group_key:
                found_group = True
                break

        if found_group:
            # and make sure the environment is up-to-date:
            group_item.work_area = environment
        else:
            if not file_list:
                # no files so don't bother creating a group!
                return

            group_item = self._add_new_group(search.name, group_key, environment)

            ## we don't have a group item for this search so lets add one now:
            #group_item = self._add_group_item(search.name, group_key, environment)
            ## (TODO) need to insert it into the right place in the list!
            ##self.invisibleRootItem().appendRow(group_item)
            #self.invisibleRootItem().appendRows([group_item])

            # add children
            self._update_group_child_entity_items(group_item, search.child_entities or [])

        # process files:
        self._process_files(file_list, environment, group_item, have_local, have_publishes)

    def _on_finder_search_completed(self, search_id):
        """
        Called when the finder search is completed
        """
        print "Search %s completed" % search_id
        self._process_search_completion(search_id, FileModel.SEARCH_COMPLETED)

    def _on_finder_search_failed(self, search_id, error_msg):
        """
        Called when the finder search fails for some reason!
        """
        print "Search %d failed - %s" % (search_id, error_msg)
        self._process_search_completion(search_id, FileModel.SEARCH_FAILED, error_msg)

    def _process_search_completion(self, search_id, status, error_msg=None):
        """
        """
        if search_id not in self._in_progress_searches:
            # ignore result
            return

        search = self._in_progress_searches[search_id]
        del(self._in_progress_searches[search_id])

        group_map = {}
        for group_item in self._group_items():
            group_map[group_item.key] = group_item

        entity_key = self._entity_key(search.entity)
        for user in self._current_users:
            group_key = (entity_key, self._entity_key(user))
            group_item = group_map.get(group_key)
            if not group_item:
                continue
            group_item.set_search_status(status, error_msg)

    def _on_data_retriever_work_completed(self, uid, request_type, data):
        """
        """
        if uid not in self._pending_thumbnail_requests:
            return
        file_item, env = self._pending_thumbnail_requests[uid]
        del(self._pending_thumbnail_requests[uid])
        
        thumb_path = data.get("thumb_path")
        if not thumb_path:
            return

        # create a pixmap for the path:
        thumb = self._build_thumbnail(thumb_path)
        if not thumb:
            return

        # update the thumbnail on the file for this item:
        # (AD) - THIS ISN'T GOING TO WORK AS THE MODEL ITEM IS NO LONGER EMITTING THE DATA
        # CHANGED SIGNAL - NEED TO FIX!
        file_item.thumbnail = thumb
    
        # See of there are any work file versions of this file that don't have a
        # thumbnail that could make use of this thumbnail:
        file_versions = self.get_file_versions(file_item.key, env) or {}
        
        for v, file_version in sorted(file_versions.iteritems(), reverse=True):
            if (v > file_version.version 
                or file_version.is_published 
                or (not file_version.is_local)
                or file_version.thumbnail_path
                or file_version.thumbnail):
                continue

            # we can use the thumbnail for this version of the work file - yay!             
            file_version.thumbnail = thumb

    def _build_thumbnail(self, thumb_path):
        """
        """
        # load the thumbnail
        thumb = QtGui.QPixmap(thumb_path)
        if not thumb or thumb.isNull():
            return
        
        # make sure the thumbnail is a good size with the correct aspect ratio:
        MAX_WIDTH = 576#96
        MAX_HEIGHT = 374#64
        ASPECT = float(MAX_WIDTH)/MAX_HEIGHT
        
        thumb_sz = thumb.size()
        thumb_aspect = float(thumb_sz.width())/thumb_sz.height()
        max_thumb_sz = QtCore.QSize(MAX_WIDTH, MAX_HEIGHT)
        if thumb_aspect >= ASPECT:
            # scale based on width:
            if thumb_sz.width() > MAX_WIDTH:
                thumb_sz *= (float(MAX_WIDTH)/thumb_sz.width())
            else:
                max_thumb_sz *= (float(thumb_sz.width())/MAX_WIDTH)
        else:
            # scale based on height:
            if thumb_sz.height() > MAX_HEIGHT:
                thumb_sz *= (float(MAX_HEIGHT)/thumb_sz.height())
            else:
                max_thumb_sz *= (float(thumb_sz.height())/MAX_HEIGHT)

        if thumb_sz != thumb.size():
            thumb = thumb.scaled(thumb_sz.width(), thumb_sz.height(), 
                                 QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        # create base pixmap with the correct aspect ratio that the thumbnail will fit in
        # and fill it with a transparent colour:
        thumb_base = QtGui.QPixmap(max_thumb_sz)
        thumb_base.fill(QtGui.QColor(QtCore.Qt.transparent))

        # create a painter to paint into this pixmap:
        painter = QtGui.QPainter(thumb_base)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            # paint the thumbnail into this base making sure it's centered:
            diff = max_thumb_sz - thumb.size()
            offset = diff/2
            brush = QtGui.QBrush(thumb)
            painter.setBrush(brush)
            painter.translate(offset.width(), offset.height())
            painter.drawRect(0, 0, thumb.width(), thumb.height())
        finally:
            painter.end()
        
        return thumb_base
    
    def _on_data_retriever_work_failed(self, uid, error_msg):
        """
        """
        if uid in self._pending_thumbnail_requests:
            del(self._pending_thumbnail_requests[uid])
        #print "Failed to find thumbnail for id %s: %s" % (uid, error_msg)        




