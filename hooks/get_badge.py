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
from sgtk.platform.qt import QtGui

HookClass = sgtk.get_hook_baseclass()


class GetBadge(HookClass):
    """
    Hook that can be used to generate badges for display on publishes and work files.
    """

    def get_publish_badge(self, publish_details, publish_path, **kwargs):
        """
        Generate a badge for a publish.

        :param dict publish_details: A dictionary for the publish to generate a badge for.
            Keys may include:
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

        :param str publish_path: The path to the publish on disk.



        :returns: A QPixmap or QColor to use for the badge, if a badge should be applied, otherwise
            None.  If a QColor is returned, a circular "dot" badge will be generated using that
            color.
        """
        # the default implementation always returns None.
        return None

    def get_work_file_badge(self, work_file_details, work_file_path, **kwargs):
        """
        Generate a badge for a work file.

        :param dict work_file_details: A dictionary for the work file to generate a badge for.
            Keys may include:
                - task
                - step
                - modified_by
                - name
                - modified_at
                - entity
                - version
                - thumbnail
                - editable
                - editable_reason

        :param str work_file_path: The path to the work file on disk.


        :returns: A QPixmap or QColor to use for the badge, if a badge should be applied, otherwise
            None.  If a QColor is returned, a circular "dot" badge will be generated using that
            color.
        """
        # the default implementation always returns None.
        return None

    def generate_badge_pixmap(self, badge_color):
        """
        Generate a badge QPixmap from a QColor. This hook method is used to generate a badge image
        when a badge hook returns a QColor. Thus, by overloading this method, it's possible to
        customize what the generated badges will look like when get_work_file_badge or
        get_publish_badge return a QColor.

        :param QColor badge_color: The color of the badge to generate a pixmap for.

        :returns: A QPixmap of the badge to be used.
        """
        # We want to multiply the color onto the (white) badge_default dot to
        # generate a nice looking badge.
        badge = QtGui.QPixmap(":/tk-multi-workfiles2/badge_default.png")
        painter = QtGui.QPainter()
        painter.begin(badge)
        try:
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(badge.rect(), badge_color)
        finally:
            painter.end()
        return badge
