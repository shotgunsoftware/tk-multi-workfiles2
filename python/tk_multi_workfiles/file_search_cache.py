# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Cache used to store and find file search results.
"""

import sgtk
from .util import Threaded

class FileSearchCache(Threaded):
    """
    Implementation of FileSearchCache class
    """
    class _CachedFileInfo(object):
        """
        Storage for file versions - encapsulates a dictionary if files indexed 
        by their version
        """
        def __init__(self):
            """
            Construction
            """
            self.versions = {}# version:FileItem() 

    class _CacheEntry(object):
        """
        A single cache entry - stores the work area the files were found in together with the
        list of files indexed by the unique file key.
        """
        def __init__(self):
            """
            Construction
            """
            self.work_area = None
            self.is_dirty = True
            self.file_info = {}# FileItem.key:_CachedFileInfo()

    def __init__(self):
        """
        Construction
        """
        Threaded.__init__(self)
        self._cache = {}

    @Threaded.exclusive
    def add(self, work_area, files, is_dirty=None):
        """
        Add the specified files to the cache along with the work area they were found in

        :param work_area:   A WorkArea instance containing information about the work area the 
                            files were found in
        :param files:       A list of the FileItem's representing the files found in the specified
                            work area
        :param is_dirty:    True if this cache entry should be marked as dirty, False if not.  If
                            is_dirty is None then the previous value will be used or True if there
                            is no previous value.
        """
        # find the current entry if there is one - this also returns the cache key:
        key, current_entry = self._find_entry(work_area)
        if is_dirty is None:
            if current_entry:
                # use the current value for the dirty flag:
                is_dirty = current_entry.is_dirty
            else:
                # default dirty to True
                is_dirty = True

        # build the new cache entry from the list of files:
        new_entry = FileSearchCache._CacheEntry()
        new_entry.work_area = work_area
        new_entry.is_dirty = is_dirty
        for file_item in files:
            new_entry.file_info.setdefault(file_item.key, 
                                           FileSearchCache._CachedFileInfo()).versions[file_item.version] = file_item

        # add the new entry to the cache:
        self._cache[key] = new_entry

    @Threaded.exclusive
    def find_file_versions(self, work_area, file_key, clean_only=False):
        """
        Find all file versions for the specified file key and context.

        :param work_area:       The work area to find the file version for
        :param file_key:        A unique file key that can be used to locate all versions of a single file
        :param clean_only:      If False then dirty cache entries will be included in the returned results.  If
                                True then they will be omitted. Defaults to False.
        :returns:               A dictionary {version:FileItem} of all file versions found.
        """
        _, entry = self._find_entry(work_area)
        if not entry:
            # return None as we don't have a cached result for this context!
            return None

        if clean_only and entry.is_dirty:
            return None

        file_info = entry.file_info.get(file_key)
        if not file_info:
            # although we have a cache entry, we don't have any files for the key!
            return {}

        # return a dictionary of version:FileItem entries:
        return dict([(v, f) for v, f in file_info.versions.iteritems()])

    @Threaded.exclusive
    def find(self, entity, user=None):
        """
        Find the list of files and work area for the specified entity and user.

        :param entity:  The entity to return files for
        :param user:    The user to return files for.  If user is None then the user for the current
                        context will be used
        :returns:       Tuple containing (list(FileItem), WorkArea) or None of an entry isn't found
        """
        key = self._construct_key(entity, user)
        entry = self._cache.get(key)
        if not entry:
            return None

        files = []
        for file_info in entry.file_info.values():
            files.extend([f for f in file_info.versions.values()])

        return (files, entry.work_area)

    @Threaded.exclusive
    def set_dirty(self, entity, user=None, is_dirty=True):
        """
        Mark the cache entry for the specified entity and user as being dirty.

        :param entity:      The entity to set the cache entry dirty for
        :param user:        The user to set the cache entry dirty for.  If user is None then the user for
                            the current context will be used.
        :param is_dirty:    True if the entry should be marked as dirty, otherwise False
        """
        key = self._construct_key(entity, user)
        entry = self._cache.get(key)
        if not entry:
            return None
        entry.is_dirty = is_dirty

    @Threaded.exclusive
    def set_work_area_dirty(self, work_area, dirty=True):
        """
        Mark the cache entry for the specified work area as being dirty.

        :param work_area:   The work area to update
        :param dirty:       True if the entry should be marked as dirty, otherwise False
        """
        _, entry = self._find_entry(work_area)
        if not entry:
            return
        entry.is_dirty = dirty

    @Threaded.exclusive
    def clear(self):
        """
        Clear the cache
        """
        self._cache = {}

    def _find_entry(self, work_area):
        """
        Find the current entry for the specified work area if there is one

        :param work_area:   The work area to find the cache entry for
        :returns:           Tuple containing (key, entry) where key is the key into the cache
                            and entry is the cache entry
        """
        if not work_area or not work_area.context:
            return (None, None)
        
        ctx = work_area.context
        key_entity = ctx.task or ctx.step or ctx.entity or ctx.project
        key = self._construct_key(key_entity, ctx.user)
        entry = self._cache.get(key)
        return (key, entry)

    def _construct_key(self, entity, user):
        """
        Construct a cache key from the specified entity and user.

        :param entity:  The entity to construct the cache key with
        :param user:    The user to construct the cache key with
        :returns:       A unique key which can be used to locate the entry in the cache
                        for the specified entity and user
        """
        if not user:
            # use the current user from the app context:
            app = sgtk.platform.current_bundle()
            user = app.context.user

        key_parts = []
        key_parts.append((entity["type"], entity["id"]) if entity else None)
        key_parts.append((user["type"], user["id"]) if user else None)

        # key needs to be hashable to return a tuple of the key parts:
        return tuple(key_parts)


