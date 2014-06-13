# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

class FileFilter(object):
    """
    Encapsulate details about a file filter
    """
    
    WORKFILES_MODE, PUBLISHES_MODE = range(2)
    
    def __init__(self, filter_dict):
        """
        Construction
        """
        self._filter_dict = filter_dict

    def __eq__(self, other):
        """
        Override == operator
        """
        if isinstance(other, FileFilter):
            return self._filter_dict == other._filter_dict
        else:
            return False

    def __ne__(self, other):
        """
        Override != operator
        """
        return not self.__eq__(other)

    @property
    def mode(self):
        # mode determining filter behaviour
        return self._filter_dict.get("mode", FileFilter.WORKFILES_MODE)
        
    @property
    def user(self):
        # user associated with this filter
        return self._filter_dict.get("user", None)
        
    @property
    def menu_label(self):
        # label to be used in the filter menu
        return self._filter_dict.get("menu_label", "Show Files")
        
    @property
    def list_title(self):
        # title to be used in the file list view
        return self._filter_dict.get("list_title", "Available Files")
        
    @property
    def show_in_file_system(self):
        # determines if the 'Show In File System' link should be visible
        return self._filter_dict.get("show_in_file_system", False)
