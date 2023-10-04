# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from datetime import datetime, timedelta

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from tank_vendor import six

HookClass = sgtk.get_hook_baseclass()


class UIConfig(HookClass):
    """Hook to customize customize the main file view."""

    # List describing the published file info to display for an item.
    PUBLISHED_FILE_DETAILS = [
        {"attr": "version", "default": "No version set", "format": "v%03d"},
        {"attr": "published_by", "field": "name", "default": "<i>Unknown</i>"},
        {"attr": "published_at", "default": "<i>Unknown</i>"},
    ]

    # List describing the workfile info to display for an item.
    WORK_FILE_DETAILS = [
        {"attr": "version", "default": "No version set", "format": "v%03d"},
        {"attr": "modified_by", "default": "<i>Unknown</i>"},
        {"attr": "modified_at", "default": "<i>Unknown</i>"},
    ]

    def get_item_background_color(self, item):
        """Returns the brush to use to draw the background for this widget

        :param item: The model item
        :type item: :class:`sgkt.platofrm.qt.QtGui.QStandardItem`

        :return: The QBrush.
        :rtype: :class:`sgtk.platform.qt.QtGui.QBrush`
        """

        parent = item.index().parent()
        if parent.isValid():
            return QtGui.QApplication.palette().midlight()
        return None

    def get_task_item_thumbnail(self, item):
        """
        Returns the data to display for this model index item's thumbnail.

        This is for the Task model and form view.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The item thumbnail.
        :rtype: :class:`sgtk.platform.qt.QtGui.QPixmap`
        """

        thumbnail = item.data(QtCore.Qt.DecorationRole)
        if not thumbnail:
            thumbnail = QtGui.QPixmap()
        return thumbnail

    def get_task_item_title(self, item):
        """
        Returns the data to display for this model index item's title.

        This is for the Task model and form view.

        No title is shown for Task items.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The title for this item.
        :rtype: string
        """
        return None

    def get_task_item_subtitle(self, item):
        """
        Returns the data to display for this model index item's subtitle.

        This is for the Task model and form view.

        No subtitle is shown for Task items.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The subtitle for this item.
        :rtype: string
        """
        return None

    def get_task_item_details(self, item):
        """
        Returns the details data to display for this model index item.

        This is for the Task model and form view.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The details for this item.
        :rtype: list<str>
        """

        detail_items = [
            "<small>{entity::icon}<small>",
            "<big>{content::icon}</big>",
        ]
        extra_display_fields = self.parent.get_setting("my_tasks_extra_display_fields")
        detail_items.extend(
            ["{{{f}}}".format(f=field) for field in extra_display_fields]
        )

        details = "<br/>".join(detail_items)
        sg_data = item.get_sg_data()

        return (details, sg_data)

    def get_task_item_icons(self, item):
        """
        Returns the icon data to display for this model index item.

        This is for the Task model and form view.

        No icons are shown for Task items.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The icon data to display.
        :rtype: dict, for e.g.:
            {
                "float-top-left": :class:`sgtk.platform.qt.QtGui.QPixmap`,
                "float-top-right": :class:`sgtk.platform.qt.QtGui.QPixmap`,
                "float-bottom-left": :class:`sgtk.platform.qt.QtGui.QPixmap`,
                "float-bottom-right": :class:`sgtk.platform.qt.QtGui.QPixmap`,
            }
        """
        return {}

    def get_task_item_width(self, item):
        """
        Returns the width for this item. This may be used by the delegate to help
        draw the item as desired. NOTE: if the ViewItemDelegate has a fixed width
        set up, this method will not affect the row width.

        This is for the Task model and form view.

        None is returned to signal to use the default width by the delegate.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The item rect display width
        :rtype: int
        """

        return None

    def get_task_item_separator(self, item):
        """
        Returns True to indicate the item has a separator, else False. This may be
        used to indicate to the delegate to draw a line separator for the item or not.

        This is for the Task model and form view.

        No separator is shown for Task items.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: True to indicate the item has a separator, else False.
        :rtype: bool
        """

        return False

    def get_item_thumbnail(self, item):
        """
        Returns the data to display for this model index item's thumbnail.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The item thumbnail.
        :rtype: :class:`sgtk.platform.qt.QtGui.QPixmap`
        """

        return item.data(QtCore.Qt.DecorationRole)

    def get_item_title(self, item):
        """
        Returns the data to display for this model index item's title.

        The current implementation will display a ttile for both a header and data item.
        The header title displays the sandbox user name (if sandbox users enabled) that
        is passed via the `extra_data` key `sandbox_user_name`.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The title for this item.
        :rtype: string
        """

        file_item = item.data(item.model().FILE_ITEM_ROLE)
        if file_item:
            return "<b>{}</b>".format(file_item.name)

        if is_header(item):
            title_str = "<span style='font: 14px'>{} </span>".format(
                item.data(QtCore.Qt.DisplayRole)
            )

            sandbox_user_name = item.data(item.model().GROUP_SANDBOX_USER)
            if sandbox_user_name:
                user_str = (
                    "<span style='font: 10px; color: rgb(0, 178, 236);'> (%s Files)</span>"
                    % sandbox_user_name
                )
            else:
                user_str = ""

            return "{title}{user}".format(title=title_str, user=user_str)

        # Default title
        return "<b>{}</b>".format(item.data(QtCore.Qt.DisplayRole))

    def get_item_subtitle(self, item):
        """
        Returns the data to display for this model index item's subtitle.

        This current implementation wil display a subtitle for header items
        that pass a `search_msg` key-value in `extra_data`.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The subtitle for this item.
        :rtype: string
        """

        if is_header(item):
            search_msg = item.data(item.model().SEARCH_MSG_ROLE)
            if search_msg:
                return "<span style='font: 11px; color: grey;'>{}</span>".format(
                    search_msg
                )

        return None

    def get_item_details(self, item):
        """
        Returns the details data to display for this model index item.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The details for this item.
        :rtype: list<str>
        """

        details = []

        file_item = item.data(item.model().FILE_ITEM_ROLE)
        if file_item:
            # Get the detail item descriptor based on whether the item is a published.
            # or local workfile
            detail_items = (
                self.PUBLISHED_FILE_DETAILS
                if file_item.is_published
                else self.WORK_FILE_DETAILS
            )

            # Extract the details from the item based on the details descriptor.
            for detail_item in detail_items:
                if hasattr(file_item, detail_item["attr"]):
                    detail_value = getattr(
                        file_item, detail_item["attr"]
                    ) or detail_item.get("default")
                    value = display_value(detail_value, detail_item.get("field"))

                    if value:
                        value = (
                            detail_item.get("format") % value
                            if detail_item.get("format")
                            else str(value)
                        )
                        details.append(value)

        return details

    def get_item_icons(self, item):
        """
        Returns the icon data to display for this model index item.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The icon data to display.
        :rtype: dict, for e.g.:
            {
                "float-top-left": :class:`sgtk.platform.qt.QtGui.QPixmap`,
                "float-top-right": :class:`sgtk.platform.qt.QtGui.QPixmap`,
                "float-bottom-left": :class:`sgtk.platform.qt.QtGui.QPixmap`,
                "float-bottom-right": :class:`sgtk.platform.qt.QtGui.QPixmap`,
            }
        """

        result = {}

        file_item = item.data(item.model().FILE_ITEM_ROLE)
        if file_item:
            if not file_item.editable:
                result["float-top-right"] = QtGui.QPixmap(
                    ":/tk-multi-workfiles2/padlock.png"
                )

            if file_item.is_published:
                result["float-bottom-right"] = QtGui.QPixmap(
                    ":/tk-multi-workfiles2/publish_icon.png"
                )

            if file_item.badge:
                result["float-bottom-left"] = file_item.badge

        return result

    def get_item_separator(self, item):
        """
        Returns True to indicate the item has a separator, else False. This may be
        used to indicate to the delegate to draw a line separator for the item or not.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: True to indicate the item has a separator, else False.
        :rtype: bool
        """

        # Only group headers have a separator.
        return is_header(item)

    def get_item_width(self, item):
        """
        Returns the width for this item. This may be used by the delegate to help
        draw the item as desired. NOTE: if the ViewItemDelegate has a fixed width
        set up, this method will not affect the row width.

        :param item: The model item.
        :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

        :return: The item rect display width
        :rtype: int
        """

        # Set the width to 300 for non-header items and set to -1 for header items to
        # expand to the full available width.
        return -1 if is_header(item) else 290


def is_header(item):
    """
    Helper method to check if an item is a group header.

    :param item: The model item.
    :type item: :class:`FileModelItem` | :class:`GroupModelItem` | :class:`FolderModelItem`

    :return: True if the item is a group header item, else False.
    :rtype: bool
    """

    node_type = item.data(item.model().NODE_TYPE_ROLE)
    return node_type == item.model().GROUP_NODE_TYPE


def display_value(raw_value, dict_field=None):
    """
    Helper method to display user friendly values.

    :param raw_value: The value to format and display.
    :param dict_field: A key to extract the data from, for values of type dict.

    :return: The processed value to display.
    """

    if isinstance(raw_value, datetime):
        return format_modified_date_time_str(raw_value)

    if isinstance(raw_value, dict):
        if dict_field is None:
            # Attemp to return a display field, if it does not exist, just return the raw value.
            dict_field = "name"

        if isinstance(dict_field, six.string_types):
            return raw_value.get(dict_field, raw_value)

        if isinstance(dict_field, list):
            value = raw_value
            for field in dict_field:
                if isinstance(value, dict) and field in value:
                    value = value[field]
                else:
                    # Invalid chained field
                    return raw_value

            return display_value(value)

    if isinstance(raw_value, list):
        values = []
        for value in raw_value:
            values.append(display_value(value))

        return "\n".join(values)

    # Value type not supported, just returning the original value.
    return raw_value


def format_modified_date_time_str(date_time):
    """
    Format a data/time into a nice human-friendly string that can be used in UI messages

    :param date_time: The datetime instance to be formatted
    :return: A string representing the datetime in a nice format
    """

    modified_date = date_time.date()
    date_str = ""
    time_diff = datetime.now().date() - modified_date
    if time_diff < timedelta(days=1):
        date_str = "Today"
    elif time_diff < timedelta(days=2):
        date_str = "Yesterday"
    else:
        date_str = "%d%s %s" % (
            modified_date.day,
            day_suffix(modified_date.day),
            modified_date.strftime("%b %Y"),
        )

    # format the modified time into a 12-hour am/pm format
    modified_time = date_time.time()
    hour = modified_time.hour
    suffix = "am" if hour < 12 else "pm"
    hour = hour if hour == 12 else hour % 12  # 0-11am, 12pm, 1-11pm
    date_str += ", %d:%02d%s" % (hour, modified_time.minute, suffix)
    return date_str


def day_suffix(day):
    """
    Figure out the suffix to use for the specified day of the month (e.g. 1st, 3rd,
    15th, 32nd, etc.)

    :param day: The day of the month
    :return: A string containing the shorthand suffix for the day of the month
    """

    return ["th", "st", "nd", "rd"][
        day % 10 if not 11 <= day <= 13 and day % 10 < 4 else 0
    ]
