# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Workfiles 2 related errors.
"""

from .work_area import WorkArea
from sgtk import TankError


class WorkfilesError(TankError):
    """
    Base class for work area related errors.
    """


class MissingTemplatesError(WorkfilesError):
    """
    Raised when one or more templates are missing.
    """

    def __init__(self, missing_templates):
        """
        Constructor.

        :param missing_templates: List of templates that are missing.
        """
        WorkfilesError.__init__(self, self.generate_missing_templates_message(missing_templates))

    @classmethod
    def generate_missing_templates_message(self, missing_templates):
        """
        Generates a warning for when templates are not all configured.
        """
        if len(missing_templates) == WorkArea.NB_TEMPLATE_SETTINGS:
            return "No templates have been defined."
        else:
            # Then take every template except the last one and join them with commas.
            comma_separated_templates = missing_templates[:-1]
            comma_separated_string = ", ".join(comma_separated_templates)

            # If the string is not empty, we'll add the last missing template name.
            if comma_separated_string:
                missing_templates_string = "%s and %s" % (
                    comma_separated_string, missing_templates[-1]
                )
            else:
                missing_templates_string = missing_templates[0]

            is_plural = len(missing_templates) > 1

            return "The template%s %s %s not been defined." % (
                "s" if is_plural else "",
                missing_templates_string,
                "have" if is_plural else "has"
            )
