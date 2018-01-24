# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from ..framework_qtwidgets import WidgetDelegate
from ..util import map_to_source, set_widget_property

from ..ui.entity_widget import Ui_entity_frame

logger = sgtk.platform.get_logger(__name__)

class EntityItemWidget(QtGui.QFrame):
    def __init__(self, *args, **kargs):
        super(EntityItemWidget, self).__init__(*args, **kargs)
        self._ui = Ui_entity_frame()
        self._ui.setupUi(self)

    def set_text(self, text):
        self._ui.title_label.setText(text)

    def set_details_text(self, text):
        self._ui.detail_label.setText(text)

    def set_icon(self, icon):
        """
        """
        geom = self._ui.icon_label.geometry()
        self._set_label_image(self._ui.icon_label, icon, geom.width(), geom.height())

    def _set_label_image(self, label, image, w, h):
        """
        """
        if not image:
            # make sure it's cleared
            label.setPixmap(QtGui.QPixmap())
            return

        pm = image
        if isinstance(pm, QtGui.QIcon):
            # extract the largest pixmap from the icon:
            max_sz = max([(sz.width(), sz.height()) for sz in image.availableSizes()] or [(256, 256)])
            pm = image.pixmap(max_sz[0], max_sz[1])

        # and scale the pm if needed:
        scaled_pm = pm
        if pm.width() > w or pm.height() > h:
            scaled_pm = pm.scaled(w, h, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)

        label.setPixmap(scaled_pm)

class EntityItemDelegate(WidgetDelegate):

    def __init__(self, view):
        """
        Constructor
        """
        super(EntityItemDelegate, self).__init__(view)

    def _create_widget(self, parent):
        """
        Returns the widget to be used when drawing items
        """
        widget = EntityItemWidget(parent)
        return widget

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called when a cell is about to be painted.
        """
        src_index = map_to_source(model_index)
        if not src_index or not src_index.isValid():
            return

        model = src_index.model()
        if not model:
            return

        item = model.itemFromIndex(src_index)
        if not item:
            return

        sg_data = item.get_sg_data() or {}
        widget.set_text(item.text())
        widget.set_details_text(
            sg_data.get("step", {}).get("name") or ""
        )
        widget.set_icon(item.icon())
        # Set a selected property in case we want to style the selected state
        selected = (
            (style_options.state & QtGui.QStyle.State_Selected) == QtGui.QStyle.State_Selected
        )
        set_widget_property(
            widget,
            "selected",
            selected,
            refresh_style=True,
            refresh_children=True
        )
        # Enable/disable the widget to pick the right style.
        enabled = (
            (style_options.state & QtGui.QStyle.State_Enabled) == QtGui.QStyle.State_Enabled
        )
        widget.setEnabled(enabled)

    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        if not model_index.isValid():
            return QtCore.QSize()
        # hint to the delegate system how much space our widget needs
        return QtCore.QSize(100, 20)
