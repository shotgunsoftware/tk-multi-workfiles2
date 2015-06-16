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

class FileSearchCache(object):
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
            self.file_info = {}# FileItem.key:_CachedFileInfo()

    def __init__(self):
        """
        Construction
        """
        self._cache = {}

    def add(self, work_area, files):
        """
        Add the specified files to the cache along with the work area they were found in

        :param work_area:   A WorkArea instance containing information about the work area the 
                            files were found in
        :param files:       A list of the FileItem's representing the files found in the specified
                            work area
        """
        # first build the cache entry from the list of files:
        entry = FileSearchCache._CacheEntry()
        entry.work_area = work_area
        for file_item in files:
            entry.file_info.setdefault(file_item.key, 
                                       FileSearchCache._CachedFileInfo()).versions[file_item.version] = file_item

        # construct the key:
        key_entity = (work_area.context.task or work_area.context.step 
                      or work_area.context.entity or work_area.context.project)
        key = self._construct_key(key_entity, work_area.context.user)

        # add the entry to the cache:
        self._cache[key] = entry

    def find_file_versions(self, file_key, ctx):
        """
        Find all file versions for the specified file key and context.

        :param file_key:    A unique file key that can be used to locate all versions of a single file
        :param ctx:         The context in which to find the files
        :returns:           A dictionary {version:FileItem} of all file versions found.
        """
        key_entity = ctx.task or ctx.step or ctx.entity or ctx.project
        key = self._construct_key(key_entity, ctx.user)
        entry = self._cache.get(key)
        if not entry:
            # return None as we don't have a cached result for this context!
            return None

        file_info = entry.file_info.get(file_key)
        if not file_info:
            # although we have a cache entry, we don't have any files for the key!
            return {}

        # return a dictionary of version:FileItem entries:
        return dict([(v, f) for v, f in file_info.versions.iteritems()])

    def find(self, entity, user=None):
        """
        Find the list of files and work area for the specified entity and user.

        :param entity:  The entity to return files for
        :param user:    The user to return files for
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

    def _construct_key(self, entity, user):
        """
        Construct a cache key from the specified entity and user.

        :param entity:  The entity to construct the cache key with
        :param user:    The user to construct the cache key with
        :returns:       A unique key which can be used to locate the entry in the cache
                        for the specified entity and user
        """
        # add in defaults for user if they aren't set:
        app = sgtk.platform.current_bundle()
        user = user or app.context.user

        key_parts = []
        key_parts.append((entity["type"], entity["id"]) if entity else None)
        key_parts.append((user["type"], user["id"]) if user else None)

        # key needs to be hashable to return a tuple of the key parts:
        return tuple(key_parts)


