# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Wrapper for the various widgets used from frameworks so that they can be used
easily from within Qt Designer
"""

import sgtk

# search widget:
search_widget = sgtk.platform.import_framework(
    "tk-framework-qtwidgets", "search_widget"
)
SearchWidget = search_widget.SearchWidget

# elided text label:
elided_label = sgtk.platform.import_framework("tk-framework-qtwidgets", "elided_label")
ElidedLabel = elided_label.ElidedLabel

# navigation and breadcrumb controls:
navigation = sgtk.platform.import_framework("tk-framework-qtwidgets", "navigation")
NavigationWidget = navigation.NavigationWidget
BreadcrumbWidget = navigation.BreadcrumbWidget
Breadcrumb = navigation.Breadcrumb

# Grouped list view, widget base class and delegates:
views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")
GroupedItemView = views.GroupedItemView

# hierarchical filtering proxy model:
models = sgtk.platform.import_framework("tk-framework-qtwidgets", "models")
HierarchicalFilteringProxyModel = models.HierarchicalFilteringProxyModel

overlay_widget = sgtk.platform.import_framework(
    "tk-framework-qtwidgets", "overlay_widget"
)

filtering = sgtk.platform.import_framework("tk-framework-qtwidgets", "filtering")
FilterMenu = filtering.FilterMenu
FilterMenuButton = filtering.FilterMenuButton
FilterItemTreeProxyModel = filtering.FilterItemTreeProxyModel
delegates = sgtk.platform.import_framework("tk-framework-qtwidgets", "delegates")
ViewItemDelegate = delegates.ViewItemDelegate

sg_qicons = sgtk.platform.import_framework("tk-framework-qtwidgets", "sg_qicons")
SGQIcon = sg_qicons.SGQIcon

shotgun_menus = sgtk.platform.import_framework(
    "tk-framework-qtwidgets", "shotgun_menus"
)
ShotgunMenu = shotgun_menus.ShotgunMenu

message_box = sgtk.platform.import_framework("tk-framework-qtwidgets", "message_box")
MessageBox = message_box.MessageBox
