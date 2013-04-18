"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import os

class WorkFile(object):
    """
    Encapsulate details about a work file
    """
    def __init__(self, path, publish_path, is_local, is_published, details):
        """
        Construction
        """
        self._path = path
        self._publish_path = publish_path
        self._is_local = is_local
        self._is_published = is_published
        self._details = details

    @property
    def name(self):
        n = self._details.get("name")
        if not n and self._path:
            n = os.path.basename(self._path)
        return n
              
    @property
    def path(self):
        return self._path
        
    @property
    def publish_path(self):
        return self._publish_path
                
    @property
    def is_local(self):
        return self._is_local
        
    @property
    def is_published(self):
        return self._is_published
        
    @property
    def version(self):
        return self._details.get("version")
    
    @property
    def entity(self):
        return self._details.get("entity")
    
    @property
    def task(self):
        return self._details.get("task")
    
    @property
    def thumbnail(self):
        return self._details.get("thumbnail")
    
    @property
    def last_modified_time(self):
        return self._details.get("modified_time")

    @property
    def modified_by(self):
        return self._details.get("modified_by")
    
    @property
    def publish_description(self):
        return self._details.get("publish_description")
    
