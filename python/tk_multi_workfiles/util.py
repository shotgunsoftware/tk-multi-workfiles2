# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtCore

def value_to_str(value):
    """
    safely convert the value to a string - handles
    QtCore.QString if usign PyQt
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
    """
    data = item_or_index.data(role)
    if hasattr(QtCore, "QVariant") and isinstance(data, QtCore.QVariant):
        # handle PyQt!
        data = data.toPyObject()
    return data

def get_model_str(item_or_index, role=QtCore.Qt.DisplayRole):
    """
    """
    data = get_model_data(item_or_index, role)
    return value_to_str(data)