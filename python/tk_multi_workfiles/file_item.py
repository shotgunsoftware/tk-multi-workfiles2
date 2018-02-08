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

import os
from datetime import datetime, timedelta
import copy

class FileItem(object):
    """
    Encapsulate details about a single version of a work file/publish.  Each instance represents
    a single 'version' but will contain details about both the work/local file and the publish
    for that file if available.
    """

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
        # dictionary
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

    def __init__(self, key, is_work_file=False, work_path=None, work_details=None, 
                 is_published=False, publish_path=None, publish_details=None):
        """
        Construction

        :param key:             Unique key representing all versions of this file
        :param is_work_file:    True if this instance represents a work file
        :param work_path:       Work path on disk of this file
        :param work_details:    Dictionary containing additional information about this work file
        :param is_published:    True if this instance represents a published file
        :param publish_path:    Publish path on disk of this file
        :param publish_details: Dictionary containing additional information about this publish
        """
        self._key = key

        self._is_local = is_work_file
        self._path = work_path
        self._details = work_details or {}

        self._is_published = is_published
        self._publish_path = publish_path
        self._publish_details = publish_details or {}

        self._thumbnail_path = None
        self._thumbnail_image = None

        self._versions = {}

    # ------------------------------------------------------------------------------------------
    # General properties

    @property
    def key(self):
        """
        :returns:   The unique key that matches across all versions of a single file.
        """
        return self._key

    @property
    def name(self):
        """
        :returns:   The name that identifies this file.  This is either the name specified in
                    the details dictionary or if not specified then the file base name
        """
        n = self._details.get("name") or self._publish_details.get("name")
        if not n and self._path:
            n = os.path.basename(self._path)
        return n

    @property
    def version(self):
        """
        :returns:   The version number of this file
        """
        return self._details.get("version") or self._publish_details.get("version", 0)

    @property
    def entity(self):
        """
        :returns:   The Shotgun entity dictionary that this file is associated with
        """
        return self._details.get("entity") or self._publish_details.get("entity")

    @property
    def task(self):
        """
        :returns:   The Shotgun task entity dictionary that this file is associated with.
        """
        return self._details.get("task") or self._publish_details.get("task")

    @property
    def step(self):
        """
        :returns:   The Shotgun step entity dictionary that this file is associated with.
        """
        return self._details.get("step") or self._publish_details.get("step")

    #@property
    def _get_thumbnail_path(self):
        """
        :returns:   The path on disk of the thumbnail for this file
        """
        if self._thumbnail_path is None:
            self._thumbnail_path = self._details.get("thumbnail") or self._publish_details.get("thumbnail")
        return self._thumbnail_path
    #@thumbnail_path.setter
    def _set_thumbnail_path(self, value):
        """
        :param value:   The path on disk that should be used to represent this file
        """
        if value != self.thumbnail_path:
            self._thumbnail_path = value
            self._thumbnail_image = None
    thumbnail_path=property(_get_thumbnail_path, _set_thumbnail_path)

    #@property
    def _get_thumbnail(self):
        """
        :returns:   The thumbnail QPixmap for this file
        """
        return self._thumbnail_image
    #@thumbnail.setter
    def _set_thumbnail(self, value):
        """
        :param value:   The QPixmap that should be used to represent this file
        """
        self._thumbnail_image = value
    thumbnail=property(_get_thumbnail, _set_thumbnail)

    #@property
    def _get_versions(self):
        """
        :returns:   A dictionary of {version:FileItem} containing a map of all other
                    versions of this file
        """
        return self._versions
    #@versions.setter
    def _set_versions(self, value):
        """
        :param value:   A dictionary of {version:FileItem} pairs that represent all other
                        versions of this file
        """
        self._versions = value
    versions=property(_get_versions, _set_versions)

    # ------------------------------------------------------------------------------------------
    # Work file properties

    @property
    def is_local(self):
        """
        :returns:   True if this instance has a local/work file on disk otherwise False
        """
        return self._is_local

    @property
    def path(self):
        """
        :returns:   A string representing the local/work file path of this file
        """
        return self._path
    
    @property
    def modified_at(self):
        """
        :returns:   A datetime instance containing the last modified date of the local/work file
        """
        return self._details.get("modified_at")

    @property
    def modified_by(self):
        """
        :returns:   A Shotgun entity dictionary representing the user who last modified this local/work
                    file
        """
        return self._details.get("modified_by")

    @property
    def editable(self):
        """
        :returns:   True if the local.work file is editable, otherwise False
        """
        return self._details.get("editable", True)

    @property
    def not_editable_reason(self):
        """
        :returns:   A string describing the reason the local/work file is not editable
        """
        return self._details.get("editable_reason") or ""

    # ------------------------------------------------------------------------------------------
    # Published file properties

    @property
    def is_published(self):
        """
        :returns:   True if this instance represents a published file, otherwise False
        """
        return self._is_published

    @property
    def publish_path(self):
        """
        :returns:   A string representing the path to the published file
        """
        return self._publish_path

    @property
    def published_file_id(self):
        """
        :returns:   The id of the PublishedFile entity in Shotgun that represents this published
                    file
        """
        return self._publish_details.get("published_file_entity_id")

    @property
    def publish_description(self):
        """
        :returns:   The Shotgun description of this published file
        """
        return self._publish_details.get("publish_description")

    @property
    def published_at(self):
        """
        :returns:   A datetime instance containing the date this published file was published
        """
        return self._publish_details.get("published_at")

    @property
    def published_by(self):
        """
        :returns:   A Shotgun entity dictionary representing the user who published this file
        """
        return self._publish_details.get("published_by")

    # ------------------------------------------------------------------------------------------
    # Public methods

    def update_from_publish(self, publish):
        """
        Update this instance with details from the specified publish FileItem

        :param publish: A FileItem representing the publish details that this instance should
                        be updated with
        """
        self._is_published = publish._is_published
        self._publish_path = publish._publish_path
        self._publish_details = copy.deepcopy(publish._publish_details or {})

    def update_from_work_file(self, work_file):
        """
        Update this instance with details from the specified work/local FileItem

        :param work_file:   A FileItem representing the work file details that this instance should
                            be updated with
        """
        self._is_local = work_file._is_local
        self._path = work_file._path
        self._details = copy.deepcopy(work_file._details or {})

    def set_not_work_file(self):
        """
        Update this instance to not be a work file
        """
        if self._is_local:
            self._is_local = False

    def set_not_published(self):
        """
        Update this instance to not be a published file
        """
        if self._is_published:
            self._is_published = False

    def format_published_by_details(self, single_line=False):
        """
        Format the publish details as a string to be used in UI elements

        :param single_line: If True then the name and published at details will be on a single line.  If
                            False then they will be spread over multiple lines
        :returns:           A string containing the formatted published by user and date/time
        """
        details_str = ""
        if self.published_by and "name" in self.published_by:
            details_str += self.published_by["name"]
        else:
            details_str += "<i>Unknown</i>"

        if single_line:
            details_str += ", "
        else:
            details_str += "<br>"

        if self.published_at:
            details_str += self._format_modified_date_time_str(self.published_at)
        else:
            details_str += "<i>Unknown</i>"
        return details_str

    def format_modified_by_details(self, single_line=False):
        """
        Format the work file modified details as a string to be used in UI elements

        :param single_line: If True then the name and modified at details will be on a single line.  If
                            False then they will be spread over multiple lines
        :returns:           A string containing the formatted modified by user and date/time
        """
        details_str = ""
        if self.modified_by and "name" in self.modified_by:
            details_str += self.modified_by["name"]
        else:
            details_str += "<i>Unknown</i>"

        if single_line:
            details_str += ", "
        else:
            details_str += "<br>"

        if self.modified_at:
            details_str += self._format_modified_date_time_str(self.modified_at)
        else:
            details_str += "<i>Unknown</i>"

        return details_str

    def format_publish_description(self):
        """
        Format the publish description to be used in UI elements

        :returns:   A string containing the formatted publish description
        """
        if self.publish_description:
            return ("%s" % self.publish_description)
        else:
            return "<i>No description was entered for this publish</i>"

    def format_tooltip(self):
        """
        Format text for a tooltip containing all useful information about
        the file item.  Tooltips look something like this:

            Name, version
            This is the latest version of this file
            ---------------------------------------
            Updated by:
            name, date, time
            (or) ----------------------------------
            Published by:
            name, data, time
            description
            (optional) ----------------------------
            This file is not editable
            not editable reason

        :returns:   Formatted rich-text string that can be used in a Tooltip for the file
                    item
        """
        tooltip = ""

        # figure out the latest version and the latest publish version:
        latest_version = self
        latest_publish_version = self if self.is_published else None
        if self.versions:
            max_version = max(self.versions.iterkeys())
            if max_version > latest_version.version:
                latest_version = self.versions[max_version]

            publish_versions = [f.version for f in self.versions.itervalues() if f.is_published]
            if publish_versions:
                max_pub_version = max(publish_versions)
                if not latest_publish_version or max_pub_version > latest_publish_version.version:
                    latest_publish_version = self.versions[max_pub_version] 

        # add the file name and version:
        tooltip += ("<b>%s, v%03d</b><br>" % (self.name, self.version))

        # add in some text describing if this is the latest version or not.
        if latest_version == self:
            tooltip += "<i>This is the latest version of this file</i>"
        else:
            if latest_version.is_published:
                tooltip += ("<i>A more recent Publish (v%03d) is available</i>" % latest_version.version) 
            elif latest_version.is_local:
                tooltip += ("<i>A more recent Work File (v%03d) is available</i>" % latest_version.version)

        if self.is_published:
            # add in published info
            tooltip += "<hr>"
            tooltip += "<b>Published by:</b><br>"
            tooltip += self.format_published_by_details(single_line=True)
            tooltip += "<br>"
            tooltip += ("<i>%s</i>" % self.format_publish_description())
        elif self.is_local:
            # add in local info:
            tooltip += "<hr>"
            tooltip += "<b>Modified by:</b><br>"
            tooltip += self.format_modified_by_details(single_line=True)

            if latest_publish_version:
                # also add some information about the most recent publish:
                tooltip += "<hr>"
                tooltip += ("<b>Last Published as v%03d by:</b><br>" % latest_publish_version.version)
                tooltip += latest_publish_version.format_published_by_details(single_line=True)
                tooltip += "<br>"
                tooltip += ("<i>%s</i>" % latest_publish_version.format_publish_description())

        # if the file isn't editable then add this to the tooltip as well
        if not self.editable:
            tooltip += "<hr>"
            tooltip += ("<b>The file is not editable</b><br>")
            tooltip += (self.not_editable_reason)

        return tooltip

    def compare(self, other):
        """
        Compare with another FileItem instance and return the result of that compare.  This takes
        into account fuzzy compare when comparing file modified times with published at times to
        accomodate a small tollerance between saving and creating the publish record in Shotgun.

        :param other:    The FileItem instance to compare with
        :returns:        0 if both items are the same, -1 if self < other and +1 if self > other
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
        Determine if this local/work file is more recent than the specified published file

        :param published_file:  The published FileItem instance to compare this local/work file
                                with.
        :returns:               -1 if work file is older than publish
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

    # ------------------------------------------------------------------------------------------
    # Protected methods

    def __repr__(self):
        """
        :returns:   A string representation of this instance - useful for debugging
        """
        return "%s (v%d), is_local:%s, is_publish: %s" % (self.name, self.version, self.is_local, self.is_published)

    def _format_modified_date_time_str(self, date_time):
        """
        Format a data/time into a nice human-friendly string that can be used in UI messages

        :param date_time:   The datetime instance to be formatted
        :reutrns:           A string representing the datetime in a nice format
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

        # format the modified time into a 12-hour am/pm format
        modified_time = date_time.time()
        hour = modified_time.hour
        suffix = "am" if hour < 12 else "pm"
        hour = hour if hour == 12 else hour % 12 # 0-11am, 12pm, 1-11pm
        date_str += (", %d:%02d%s" % (hour, modified_time.minute, suffix))
        return date_str

    def _day_suffix(self, day):
        """
        Figure out the suffix to use for the specified day of the month (e.g. 1st, 3rd, 
        15th, 32nd, etc.)

        :param day: The day of the month
        :returns:   A string containing the shorthand suffix for the day of the month
        """
        return ["th", "st", "nd", "rd"][day%10 if not 11<=day<=13 and day%10 < 4 else 0]


















    
