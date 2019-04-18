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

    def execute(self, publish, **kwargs):
        """
        Main hook entry point

        :param publish:   Dictionary
                            A dictionary for the publish to generate a badge for, in the form:

                            {
                                "sg_publish" : {Shotgun entity dictionary for a Published File entity}
                            }


        :returns:            A QPixmap to use as the badge, if a badge should be applied, otherwise None
        """
        # the default implementation just returns None:
        return None
