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
search_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "search_widget")
SearchWidget = search_widget.SearchWidget

# elided text label:
elided_label = sgtk.platform.import_framework("tk-framework-qtwidgets", "elided_label")
ElidedLabel = elided_label.ElidedLabel

# navigation and breadcrumb controls:
navigation = sgtk.platform.import_framework("tk-framework-qtwidgets", "navigation")
NavigationWidget = navigation.NavigationWidget
BreadcrumbWidget = navigation.BreadcrumbWidget
Breadcrumb = navigation.Breadcrumb

# Spinner/busy widget:
spinner_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "spinner_widget")
SpinnerWidget = spinner_widget.SpinnerWidget

# Grouped list view, widget base class and delegates:
views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")
GroupedListView = views.GroupedListView
GroupWidgetBase = views.GroupWidgetBase
GroupedListViewItemDelegate = views.GroupedListViewItemDelegate
WidgetDelegate = views.WidgetDelegate

# hierarchical filtering proxy model:
models = sgtk.platform.import_framework("tk-framework-qtwidgets", "models")
HierarchicalFilteringProxyModel = models.HierarchicalFilteringProxyModel

overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
