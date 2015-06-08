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

import os
from datetime import datetime, timedelta

class FileItem(QtCore.QObject):
    """
    Encapsulate details about a work file
    """
    
    data_changed = QtCore.Signal()
    
    @staticmethod
    def build_file_key(fields, template, ignore_fields = None):
        """
        Build a unique key from the specified fields and template.  This will be used to determine 
        if multiple files are actually just versions of the same file.

        For example, the following inputs:
        
            fields: {"sg_asset_type":"Character", "Asset":"Fred", "Step":"Anm", "name":"test", "version":3, "sub_name":"TheCat"}
            template: /assets/{sg_asset_type}/{Asset}/{Step}/work/maya/{Asset}_{Step}[_{name}]_v{version}.{maya_ext}
            ignore_fields: ["version"]
            
            Notes: 
            - The template key maya_ext has a default value of 'mb'
            
        Will generate the file key:
        
            (('Asset', 'Fred'), ('Step', 'Anm'), ('maya_ext':'mb'), ('name', 'test'), ('sg_asset_type', 'Character'))

            Notes: 
            - 'version' is skipped because it was specified in the ignore_fields
            - 'sub_name' is skipped because it isn't a valid key in the template
            - Although 'maya_ext' wasn't included in the input fields, it is added to the file key as 
              it has a default value in the template 
        
        :param fields:          A dictionary of fields extracted from a file path
        :param template:        The template that represents the files this key will be 
                                used to compare.
        :param ignore_fields:   A list of fields to ignore when constructing the key.
                                Typically this will contain at least 'version' but it 
                                may also contain other fields (e.g. user initials in
                                the file name).
        :returns:               An immutable 'key' that can be used for comparison and
                                as the key in a dictionary (e.g. a string).
        """
        ignore_fields = ignore_fields or []
        # always want to ignore 'version' and 'extension' if they are present in the fields
        # dicrionary
        ignore_fields += ["version", "extension"]

        # populate the file key from the fields passed in that are included in
        # the template, skipping the ignore fields:
        file_key = {}
        template_keys = template.keys
        for name, value in fields.iteritems():
            if name in ignore_fields:
                # skip fields that are explicitly ignored
                continue

            if name not in template_keys:
                # skip fields that aren't included in the template
                continue

            file_key[name] = value
            
        # add in any 'default' values from the template that aren't explicitely ignored
        # or weren't specified in the input fields:
        for key in template_keys.values():
            if (key.name not in ignore_fields
                and key.default != None
                and key.name not in file_key):
                file_key[key.name] = key.default 
        
        # return an immutable representation of the sorted dictionary:
        # e.g. (('sequence', 'Sequence01'), ('shot', 'shot_010'), ('name', 'foo'))
        return tuple(sorted(file_key.iteritems()))
    
    def __init__(self, path, publish_path, is_local, is_published, details, key):
        """
        Construction
        """
        QtCore.QObject.__init__(self)
        
        self._path = path
        self._publish_path = publish_path
        self._is_local = is_local
        self._is_published = is_published
        self._details = details
        self._key = key
        self._thumbnail_image = None

    def update(self, path=None, publish_path=None, is_local=None, is_published=None, details=None):
        """
        """
        data_changed = False
        if path != None:
            self._path = path
            data_changed = True
        if is_local != None:
            self._is_local = is_local
            data_changed = True
        if publish_path != None:
            self._publish_path = publish_path
            data_changed = True
        if is_published != None:
            self._is_published = is_published
            data_changed = True
        if details:
            self._details.update(dict([(k, v) for k, v in details.iteritems() if v != None]))
            data_changed = True
            
        if data_changed:
            self.data_changed.emit()

    def __repr__(self):
        return "%s (v%d), is_local:%s, is_publish: %s" % (self.name, self.version, self.is_local, self.is_published)

    """
    General details
    """
    @property
    def details(self):
        return self._details
    
    @property
    def name(self):
        n = self._details.get("name")
        if not n and self._path:
            n = os.path.basename(self._path)
        return n
        
    @property
    def version(self):
        return self._details.get("version", 0)
    
    @property
    def entity(self):
        return self._details.get("entity")
    
    @property
    def task(self):
        return self._details.get("task")
    
    @property
    def thumbnail_path(self):
        return self._details.get("thumbnail")
    @thumbnail_path.setter
    def thumbnail_path(self, value):
        if value != self._details.get("thumbnail"):
            self._details["thumbnail"] = value
            self._thumbnail_image = None
            self.data_changed.emit()

    @property
    def thumbnail(self):
        return self._thumbnail_image
    @thumbnail.setter
    def thumbnail(self, value):
        self._thumbnail_image = value
        self.data_changed.emit()

    @property
    def key(self):
        # a unique key that matches across all versions of a single file.
        return self._key

    """
    Work file details
    """
    @property
    def is_local(self):
        return self._is_local
    
    @property
    def path(self):
        return self._path
    
    @property
    def modified_at(self):
        return self._details.get("modified_at")

    @property
    def modified_by(self):
        return self._details.get("modified_by")
    
    @property
    def editable(self):
        return self._details.get("editable", True)
    
    @property
    def not_editable_reason(self):
        """
        Return the reason the file is not editable.
        """
        return self._details.get("editable_reason") or ""
    
    """
    Published file details
    """
    @property
    def is_published(self):
        return self._is_published
    
    @property
    def publish_path(self):
        return self._publish_path
        
    @property
    def published_file_id(self):
        return self._details.get("published_file_entity_id")
    
    @property
    def publish_description(self):
        return self._details.get("publish_description")
    
    @property
    def published_at(self):
        return self._details.get("published_at")

    @property
    def published_by(self):
        return self._details.get("published_by")
    
    def format_published_by_details(self):
        """
        Format the publish details as a string to
        be used in UI elements
        """
        details_str = ""
        if self.published_by and "name" in self.published_by:
            details_str += self.published_by["name"]#("Published by %s" % self.published_by["name"])
        else:
            details_str += "<i>Unknown</i>"#"Published by: <i>Unknown</i>"
        details_str += "<br>"
        if self.published_at:
            details_str += self._format_modified_date_time_str(self.published_at)#("Published %s" % self._format_modified_date_time_str(self.published_at))
        else:
            details_str += "<i>Unknown</i>"#"Published on: <i>Unknown</i>"
        return details_str

    def format_modified_by_details(self):
        """
        Format the modified details as a string to
        be used in UI elements
        """
        details_str = ""
        if self.modified_by and "name" in self.modified_by:
            details_str += self.modified_by["name"]#("Updated by %s" % self.modified_by["name"])
        else:
            details_str += "<i>Unknown</i>"   

        details_str += "<br>"
        
        if self.modified_at:
            details_str += self._format_modified_date_time_str(self.modified_at)#("Last updated %s" % self._format_modified_date_time_str(self.modified_at))
        else:
            details_str += "<i>Unknown</i>"#"Last updated: <i>Unknown</i>"
         
        return details_str
    
    def format_publish_description(self):
        """
        Format the publish description to be used
        in UI elements
        """
        if self.publish_description:
            return ("%s" % self.publish_description)
        else:
            return "<i>No description was entered for this publish</i>"
    
    def compare(self, other):
        """
        """
        if self.is_published != other.is_published:
            # exactly one of the two files is published so we are comparing
            # a work file with a published file
            if self.is_published:
                return other.compare_with_publish(self) * -1
            else:
                return self.compare_with_publish(other)

        # see if the files are the same key:
        if self.key == other.key:
            # see if we can get away with just comparing versions:
            if self.version > other.version:
                return 1
            elif self.version < other.version:
                return -1
            else:
                # same version so we'll need to look further!
                pass

        # handle if both are publishes or if both are local:
        diff = timedelta()
        if self.is_published:
            # both are publishes so just compare publish times:
            if not self.published_at or not other.published_at:
                # can't compare!
                return 0
            diff = self.published_at - other.published_at
        else:
            # both are local so compare modified times:
            if not self.modified_at or not other.modified_at:
                # can't compare!
                return 0
            diff = self.modified_at - other.modified_at
            
        zero = timedelta(seconds=0)
        if diff < zero:
            return -1
        elif diff > zero:
            return 1
        else:
            return 0
    
    def compare_with_publish(self, published_file):
        """
        Determine if this (local) file is more recent than
        the specified published file
        
        :returns:    -1 if work file is older than publish
                      0 if work file is exactly the same time as publish
                      1 if work file is more recent than publish
        """
        if not self.is_local or not published_file.is_published:
            return -1
        
        # if the two files have identical keys then start by comparing versions:
        if self.key == published_file.key:
            if self.path == published_file.publish_path:
                # they are the same file!
                return 0
            
            # If the versions are different then we can just compare the versions:
            if self.version > published_file.version:
                return 1
            elif self.version < published_file.version:
                return -1

        # ok, so different files or both files have the same version in which case we
        # use fuzzy compare to determine which is more recent - note that this will never
        # return '0' as the files could still have different contents - in this case, the
        # work file is favoured over the publish!
        local_is_latest = False
        if self.modified_at and published_file.published_at:
            # check file modification time - we only consider a local version to be 'latest' 
            # if it has a more recent modification time than the published file (with 2mins
            # tollerance)
            if self.modified_at > published_file.published_at:
                local_is_latest = True
            else:
                diff = published_file.published_at - self.modified_at
                if diff < timedelta(seconds=120):
                    local_is_latest = True
        else:
            # can't compare times so assume local is more recent than publish:
            local_is_latest = True
            
        return 1 if local_is_latest else -1
    
    def _format_modified_date_time_str(self, date_time):
        """
        
        """
        modified_date = date_time.date()
        date_str = ""
        time_diff = datetime.now().date() - modified_date
        if time_diff < timedelta(days=1):
            date_str = "Today"
        elif time_diff < timedelta(days=2):
            date_str = "Yesterday"
        else:
            date_str = "%d%s %s" % (modified_date.day, 
                                    self._day_suffix(modified_date.day), 
                                    modified_date.strftime("%b %Y"))

        modified_time = date_time.time()                
        date_str += (", %d:%02d%s" % (modified_time.hour % 12, modified_time.minute, 
                                        "pm" if modified_time.hour > 12 else "am"))
        return date_str
    
    def _day_suffix(self, day):
        """
        Return the suffix for the day of the month
        """
        return ["th", "st", "nd", "rd"][day%10 if not 11<=day<=13 and day%10 < 4 else 0]


















    
