"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""
import os
from datetime import datetime, timedelta

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

    """
    General details
    """
    @property
    def name(self):
        n = self._details.get("name")
        if not n and self._path:
            n = os.path.basename(self._path)
        return n
        
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
        return self._details.get("published_file_id")
    
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
        if self.published_at:
            details_str += ("Published %s" % self._format_modified_date_time_str(self.published_at))
        else:
            details_str += "Published on: <i>Unknown</i>"
        details_str += "<br>"
        if self.published_by and "name" in self.published_by:
            details_str += ("Published by %s" % self.published_by["name"])
        else:
            details_str += "Published by: <i>Unknown</i>"
        return details_str

    def format_modified_by_details(self):
        """
        Format the modified details as a string to
        be used in UI elements
        """
        details_str = ""
        if self.modified_at:
            details_str += ("Last updated %s" % self._format_modified_date_time_str(self.modified_at))
        else:
            details_str += "Last updated: <i>Unknown</i>"
        details_str += "<br>"
        if self.modified_by and "name" in self.modified_by:
            details_str += ("Updated by %s" % self.modified_by["name"])
        else:
            details_str += "Updated by: <i>Unknown</i>"            
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
    
    def is_more_recent_than_publish(self, published_file):
        """
        Determine if this (local) file is more recent than
        the specified published file
        """
        if not self.is_local or not published_file.is_published:
            return False
        
        local_is_latest = False
        if self.version >= published_file.version:
            if self.modified_at and published_file.published_at:
                # check file modification time - we only consider a local version to be 'latest' 
                # if it has a more recent modification time than the published file (with 2mins
                # tollerance)
                if self.modified_at > published_file.published_at:
                    local_is_latest = True
                else:
                    diff = published_file.published_at - self.modified_at
                    if diff.seconds < 120:
                        local_is_latest = True
            else:
                # can't compare times so assume local is more recent than publish:
                local_is_latest = True
                
        return local_is_latest
    
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
            date_str = "on %d%s %s" % (modified_date.day, 
                                    self._day_suffix(modified_date.day), 
                                    modified_date.strftime("%B %Y"))

        modified_time = date_time.time()                
        date_str += (" at %d:%02d%s" % (modified_time.hour % 12, modified_time.minute, "pm" if modified_time.hour > 12 else "am"))
        return date_str
    
    def _day_suffix(self, day):
        """
        Return the suffix for the day of the month
        """
        return ["th", "st", "nd", "rd"][day%10 if not 11<=day<=13 and day%10 < 4 else 0]

    def set_thumbnail(self, thumbnail):
        """
        """
        self._details["thumbnail"] = thumbnail


















    
