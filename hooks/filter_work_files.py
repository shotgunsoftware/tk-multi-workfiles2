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

HookClass = sgtk.get_hook_baseclass()


class FilterWorkFiles(HookClass):
    """
    Hook that can be used to filter the list of work files found by the app for the current
    Work area
    """

    def execute(self, work_files, **kwargs):
        """
        Main hook entry point

        :param work_files:   List of dictionaries
                             A list of  dictionaries for the current work area within the app.  Each
                             item in the list is a Dictionary of the form:

                             {
                                 "work_file" : {

                                     Dictionary containing information about a single work file.  Valid entries in
                                     this dicitionary are listed below but may not be populated when the hook is
                                     executed!

                                     It is intended that custom versions of this hook should populate these fields
                                     if needed before returning the filtered list

                                     version_number    - version of the work file
                                     name              - name of the work file
                                     task              - task the work file should be associated with
                                     description       - description of the work file
                                     thumbnail         - thumbnail that should be used for the work file
                                     modified_at       - date & time the work file was last modified
                                     modified_by       - Shotgun user entity dictionary for the person who
                                                         last modified the work file
                                 }
                             }


        :returns:            The filtered list of dictionaries of the same form as the input 'work_files'
                             list
        """
        app = self.parent

        # the default implementation just returns the unfiltered list:
        return work_files
