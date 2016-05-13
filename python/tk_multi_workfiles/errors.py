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

from sgtk import TankError


class WorkfilesError(TankError):
    """
    Base class for work area related errors.
    """


class WorkAreaSettingsNotFoundError(WorkfilesError):
    """
    Raised when no settings for the workfiles 2 app are found in an environment.
    """

    def __init__(self):
        """
        Constructor.
        """
        WorkfilesError.__init__(
            self,
            "The Shotgun File Manager hasn't been setup."
        )


class UnconfiguredTemplatesError(WorkfilesError):
    """
    Raised when one or more templates are not configured.
    """

    def __init__(self, missing_templates):
        """
        Constructor.

        :param missing_templates: List of templates that are missing.
        """
        if len(missing_templates) == 4:
            WorkfilesError.__init__(self, "No templates have been defined.")
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

            WorkfilesError.__init__(
                self,
                "The template%s %s %s not been defined." % (
                    "s" if is_plural else "",
                    missing_templates_string,
                    "have" if is_plural else "has"
                )
            )