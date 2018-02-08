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
import threading

import sgtk
from sgtk.platform.qt import QtCore, QtGui


class Threaded(object):
    """
    Threaded base class that contains a threading.Lock member and an
    'exclusive' function decorator that implements exclusive access
    to the contained code using the lock
    """
    def __init__(self):
        """
        Construction
        """
        self._lock = threading.Lock()

    @staticmethod
    def exclusive(func):
        """
        Static method intended to be used as a function decorator in derived
        classes.  Use it by doing:

            @Threaded.exclusive
            def my_method(self, ...):
                ...

        :param func:    Function to decorate/wrap
        :returns:       Wrapper function that executes the function inside the acquired lock
        """
        def wrapper(self, *args, **kwargs):
            """
            Internal wrapper method that executes the function with the specified arguments
            inside the acquired lock

            :param *args:       The function parameters
            :param **kwargs:    The function named parameters
            :returns:           The result of the function call
            """
            self._lock.acquire()
            try:
                return func(self, *args, **kwargs)
            finally:
                self._lock.release()

        return wrapper

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

def get_sg_entity_name_field(entity_type):
    """
    :returns: A string, the field holding the Entity name for a given Entity type.
    """
    # Please note that similar method was added in tk-core v0.18.121 but we have
    # our own copy of it to not introduce a dependency just for this.
    # Deal with some known special cases and assume "code" for anything else.
    return {
        "Project": "name",
        "Task": "content",
        "HumanUser": "name",
        "Note": "subject",
        "Department": "name",
        "Delivery": "title",
    }.get(entity_type, "code")

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
    Map the specified index to it's source model.  This can be done recursively to map
    back through a chain of proxy models to the source model at the beginning of the chain

    :param idx:         The index to map from
    :param recursive:   If true then the function will recurse up the model chain until it
                        finds an index belonging to a model that doesn't derive from 
                        QAbstractProxyModel.  If false then it will just return the index
                        from the imediate parent model.
    :returns:           QModelIndex in the source model or the first model in the chain that
                        isn't a proxy model if recursive is True.
    """
    src_idx = idx
    while src_idx.isValid() and isinstance(src_idx.model(), QtGui.QAbstractProxyModel):
        src_idx = src_idx.model().mapToSource(src_idx)
        if not recursive:
            break
    return src_idx

def get_source_model(model, recursive=True):
    """
    Return the source model for the specified model.  If recursive is True then this will return
    the first model in the model chain that isn't a proxy model.

    :param model:       The model to get the source model from
    :param recursive:   If True then recurse up the model chain until we find a model that isn't
                        derived from QAbstractProxyModel.  If false then just return the immediate
                        parent model.
    :returns:           The source model or the first non-proxy model if recursive is True
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

# storage for any tracked qobjects
_g_monitored_qobjects = {}

def monitor_qobject_lifetime(obj, name=""):
    """
    Debug method to help track the lifetime of a QObject derived instance.  Hooks into
    the instances destroyed signal to report when the QObject has been destroyed.

    :param obj:     The QObject instance to monitor
    :param name:    An optional name to be appended to the debug output, useful for identifying
                    a specific instance of a class.
    """
    msg = type(obj).__name__
    if name:
        msg = "%s [%s]" % (msg, name)
    global _g_monitored_qobjects
    uid = len(_g_monitored_qobjects)
    _g_monitored_qobjects[uid] = msg
    obj.destroyed.connect(lambda m=msg, u=uid: _on_qobject_destroyed(m, u))

def _on_qobject_destroyed(name, uid):
    """
    Slot triggered whenever a monitored qobject is destroyed - reports to debug that the object
    was destroyed.

    :param name:    Name of the instance that was destroyed
    :param uid:     Unique id of the QObject used to look it up in the monitored list
    """
    app = sgtk.platform.current_bundle()
    app.log_debug("%s destroyed" % name)
    global _g_monitored_qobjects
    if uid in _g_monitored_qobjects:
        del _g_monitored_qobjects[uid]

def report_non_destroyed_qobjects(clear_list = True):
    """
    Report any monitored QObjects that have not yet been destroyed.  Care should be taken to
    account for QObjects that are pending destruction via deleteLater signals that may be 
    pending.

    :param clear_list:  If true then the list of monitored QObjects will be cleared after
                        this function has reported them.
    """
    app = sgtk.platform.current_bundle()
    global _g_monitored_qobjects
    app.log_debug("%d monitored QObjects have not been destroyed!" % len(_g_monitored_qobjects))
    for msg in _g_monitored_qobjects.values():
        app.log_debug(" - %s" % msg)
    if clear_list:
        _g_monitored_qobjects = {}


def get_template_user_keys(template):
    """
    Finds the keys in a template that relate to the HumanUser entity.

    :param template: Template to look for HumanUser related keys.

    :returns: A list of key names.
    """
    # find all 'user' keys in the template:
    user_keys = set()
    if "HumanUser" in template.keys:
        user_keys.add("HumanUser")
    for key in template.keys.values():
        if key.shotgun_entity_type == "HumanUser":
            user_keys.add(key.name)
    return user_keys


def resolve_filters(filters):
    """
    
    When passed a list of filters, it will resolve strings found in the filters using the context
    example: '{context.user}' could get resolved to {'type': 'HumanUser', 'id': 86, 'name': 'Philip Scadding'} 
    
    :param filters: a list of filters as found in the info.yml config
    should be in the format: [[task_assignees, is, '{context.user}'],[sg_status_list, not_in, [fin,omt]]]
    
    :return: A List of filters for use with the shotgun api
    """
    app = sgtk.platform.current_bundle()

    resolved_filters = []
    for filter in filters:
        if type(filter) is dict:
            resolved_filter = {
                "filter_operator": filter["filter_operator"],
                "filters": resolve_filters(filter["filters"])}
        else:
            resolved_filter = []
            for field in filter:
                if field == "{context.entity}":
                    field = app.context.entity
                elif field == "{context.step}":
                    field = app.context.step
                elif field == "{context.task}":
                    field = app.context.task
                elif field == "{context.user}":
                    field = app.context.user
                resolved_filter.append(field)
        resolved_filters.append(resolved_filter)
    return resolved_filters
