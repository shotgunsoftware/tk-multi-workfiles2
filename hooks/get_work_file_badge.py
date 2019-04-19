# Copyright (c) 2019 Shotgun Software Inc.
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


class GetWorkFileBadge(HookClass):
    """
    Hook that can be used to filter the list of work files found by the app for the current
    Work area
    """

    def execute(self, work_file_details, work_file_path, **kwargs):
        """
        Main hook entry point

        :param work_file:       Dictionary
                                A dictionary for the work file to generate a badge for containing
                                the following keys:
                                    - task
                                    - modified_by
                                    - name
                                    - modified_at
                                    - entity
                                    - version
                                    - thumbnail
                                    - description

        :param work_file_path:  String
                                The path to the work file on disk.


        :returns:           A QPixmap or QColor to use for the badge, if a badge should be applied,
                            otherwise None.  If a QColor is returned, a circular "dot" badge will be
                            generated using that color.
        """
        # the default implementation always returns None.
        return None
