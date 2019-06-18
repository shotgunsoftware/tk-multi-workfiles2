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

    def execute(self, work_files_paths, work_template, work_fields, skip_fields, skip_missing_optional_keys=True, **kwargs):
        """
        Main hook entry point

        """
        # the default implementation just returns the unfiltered list:
        return work_files_paths
