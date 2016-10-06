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
Framestore hack while we produce the correct optimizations to the ShotgunModel.
"""

import sgtk
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunEntityModel = shotgun_model.ShotgunEntityModel


class DeferableShotgunEntityModel(ShotgunEntityModel):
    """
    Model that allows to postpone the loading of the data from the model at a later time. It will
    behave as if it was empty until ``ensure_data_loaded`` is called on the model.
    """

    # States for the model.
    UNLOADED, CAN_LOAD, LOADED = range(3)

    def __init__(self, entity_type, filters, hierarchy, fields, parent,
                 download_thumbs=False, schema_generation=0, bg_load_thumbs=True,
                 bg_task_manager=None, defer=False):
        """
        Passthrough to the base class init, but adds the defer parameter to tell if the model
        should allow the loading of the cache immediately or to defer it.
        """
        if defer:
            self._model_state = self.UNLOADED
        else:
            self._model_state = self.CAN_LOAD

        self._entity_type = entity_type
        self._filters = filters
        self._hierarchy = hierarchy
        self._fields = fields

        super(DeferableShotgunEntityModel, self).__init__(
            entity_type, filters, hierarchy, fields, parent,
            download_thumbs, schema_generation, bg_load_thumbs, bg_task_manager
        )

    def ensure_data_loaded(self):
        """
        Ensure that the data has been loaded from the cache. Does nothing if the cache has been
        loaded once.
        """
        if self._model_state == self.UNLOADED:
            self._model_state = self.CAN_LOAD
            self._load_data(self._entity_type, self._filters, self._hierarchy, self._fields)

    def _load_data(self, entity_type, filters, hierarchy, fields):
        """
        Load data from the cache and populates the model.
        """
        if self._model_state == self.CAN_LOAD:
            super(DeferableShotgunEntityModel, self)._load_data(entity_type, filters, hierarchy, fields)
            self._model_state == self.LOADED

    def async_refresh(self):
        """
        Do not refresh the model is we want to defer its loading.
        """
        if self._model_state == self.UNLOADED:
            return

        super(DeferableShotgunEntityModel, self).async_refresh()

    def get_entity_type(self):
        """
        Usually _entity_type is set during _load_data, but it isn't when the loading is deferred
        so we'll re-implement it for this.
        """
        return self._entity_type

    def item_from_entity(self, entity_type, entity_id):
        """
        Same deal as above. __entity_model is not defined and the code crashes if data hasn't been
        cached yet.
        """
        if self._model_state != self.LOADED:
            return
        return super(DeferableShotgunEntityModel, self).item_from_entity(entity_type, entity_id)
