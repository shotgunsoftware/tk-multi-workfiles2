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


class GetPublishBadge(HookClass):
    """
    Hook that can be used to filter the list of work files found by the app for the current
    Work area
    """

    def execute(self, publish_details, publish_path, **kwargs):
        """
        Main hook entry point

        :param publish:         Dictionary
                                A dictionary for the publish to generate a badge for, containing the
                                following keys:
                                    - task
                                    - modified_by
                                    - name
                                    - modified_at
                                    - published_at
                                    - thumbnail
                                    - publish_description
                                    - published_by
                                    - version
                                    - entity

        :param publish_path:    String
                                The path to the publish on disk.



        :returns:           A QPixmap or QColor to use for the badge, if a badge should be applied,
                            otherwise None.  If a QColor is returned, a circular "dot" badge will be
                            generated using that color.
        """
        # the default implementation always returns None.
        return None
