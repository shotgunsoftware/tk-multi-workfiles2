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
Various utility methods used by the app code
"""
import sgtk
from sgtk.platform.qt import QtCore, QtGui

def value_to_str(value):
    """
    Safely convert the value to a string - handles QtCore.QString if usign PyQt

    :param value:    The value to convert to a Python str
    :returns:        A Python string representing the value
    """
    if value == None:
        return ""

    # handle PyQt.QVariant
    if hasattr(QtCore, "QVariant") and isinstance(value, QtCore.QVariant):
        value = value.toPyObject()

    if isinstance(value, unicode):
        # encode to str utf-8
        return value.encode("utf-8")
    elif isinstance(value, str):
        # it's a string anyway so just return
        return value
    elif hasattr(QtCore, "QString") and isinstance(value, QtCore.QString):
        # running PyQt!
        # QtCore.QString inherits from str but supports 
        # unicode, go figure!  Lets play safe and return
        # a utf-8 string
        return str(value.toUtf8())
    else:
        # For everything else, just return as string
        return str(value)

def get_model_data(item_or_index, role=QtCore.Qt.DisplayRole):
    """
    Safely get the Qt model data for the specified item or index.  This handles QVariant
    types returned when using PyQt instead of PySide.

    :param item_or_index:   The QStandardModelItem or QModelIndex to retrieve data for
    :param role:            The Qt data role to return data for
    :returns:               The data for the specified item or index.
    """
    data = item_or_index.data(role)
    if hasattr(QtCore, "QVariant") and isinstance(data, QtCore.QVariant):
        # handle PyQt!
        data = data.toPyObject()
    return data

def get_model_str(item_or_index, role=QtCore.Qt.DisplayRole):
    """
    Safely get the Qt model data as a Python string for the specified item or index.  This 
    handles QVariant types returned when using PyQt instead of PySide.

    :param item_or_index:   The QStandardModelItem or QModelIndex to retrieve a string for
    :param role:            The Qt data role to return as a string
    :returns:               A Python string representing the data for the specified item 
                            or index.
    """
    data = get_model_data(item_or_index, role)
    return value_to_str(data)

def map_to_source(idx, recursive=True):
    """
    """
    src_idx = idx
    while src_idx.isValid() and isinstance(src_idx.model(), QtGui.QAbstractProxyModel):
        src_idx = src_idx.model().mapToSource(src_idx)
        if not recursive:
            break
    return src_idx

def get_source_model(model, recursive=True):
    """
    """
    src_model = model
    while src_model and isinstance(src_model, QtGui.QAbstractProxyModel):
        src_model = src_model.sourceModel()
        if not recursive:
            break
    return src_model

def set_widget_property(widget, property_name, property_value, refresh_style=True, refresh_children=False):
    """
    Set a Qt property on a widget and if requested, also ensure that the style 
    sheet is refreshed

    :param widget:              The widget to set the property on
    :param property_name:       The name of the property to set
    :param property_value:      The value to set the property to
    :param refresh_style:       If True then the widgets style will be refreshed
    :param refresh_children:    If True and refresh_style is also True then the style
                                of any child widgets will also be refreshed
    """
    # set the property:
    widget.setProperty(property_name, property_value)

    # and if needed, refresh the style:
    if refresh_style:
        refresh_widget_style_r(widget, refresh_children)

def refresh_widget_style_r(widget, refresh_children=False):
    """
    Recursively refresh the style sheet of the widget and optionally it's children
    by unpolishing and repolishing the widgets style.

    :param widget:              The widget to refresh the style of
    :param refresh_children:    If True then the style of any child widgets will also 
                                be refreshed
    """
    widget.style().unpolish(widget)
    widget.ensurePolished()
    if not refresh_children:
        return

    for child in widget.children():
        if not isinstance(child, QtGui.QWidget):
            continue
        refresh_widget_style_r(child, refresh_children)

_monitored_qobjects = {}

def monitor_qobject_lifetime(obj, name=""):
    """
    """
    msg = type(obj).__name__
    if name:
        msg = "%s [%s]" % (msg, name)
    global _monitored_qobjects
    uid = len(_monitored_qobjects)
    _monitored_qobjects[uid] = msg
    obj.destroyed.connect(lambda: _on_qobject_destroyed(msg, uid))

def report_non_destroyed_qobjects():
    """
    """
    app = sgtk.platform.current_bundle()
    global _monitored_qobjects
    app.log_debug("%d monitored QObjects have not been destroyed!" % len(_monitored_qobjects))
    for msg in _monitored_qobjects.values():
        app.log_debug(" - %s" % msg)
    _monitored_qobjects = {}

def _on_qobject_destroyed(name, uid):
    """
    """
    app = sgtk.platform.current_bundle()
    app.log_debug("%s destroyed" % name)
    global _monitored_qobjects
    if uid in _monitored_qobjects:
        del _monitored_qobjects[uid]



    
    

