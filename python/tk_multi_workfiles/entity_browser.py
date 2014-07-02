# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import os
import sys
import threading

from tank.platform.qt import QtCore, QtGui

browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

class EntityBrowserWidget(browser_widget.BrowserWidget):
    """
    A simple browser list widget that displays a list of entities for the user to select from.
    """
    
    def __init__(self, parent=None):
        """
        Construction
        
        :param parent:    The parent widget for this widget
        """
        browser_widget.BrowserWidget.__init__(self, parent)

        # cache the settings we're going to use:
        app = tank.platform.current_bundle()
        self.__entity_types_to_load = app.get_setting("sg_entity_types", [])
        self.__entity_type_filters = app.get_setting("sg_entity_type_filters", {})
        self.__entity_type_extra_fields = app.get_setting("sg_entity_type_extra_display_fields", {})
        
        # only load this once!
        self._current_user = None
        self._current_user_loaded = False
        
    @property
    def selected_entity(self):
        """
        The selected entity from the browser widget
        """
        selected_item = self.get_selected_item()
        if selected_item:
            return selected_item.sg_data
        return None

    def get_data(self, data):
        """
        Executed in a background worker thread from the entity browser widget to retrieve entity
        information to display.
        
        :param data:    data passed into the widget from the app
        :returns:       Retrieved and processed entity data that will be used to populate 
                        the widget on the main UI thread
        """
        current_entity = data.get("entity")
            
        if not self._current_user_loaded:
            self._current_user = tank.util.get_current_user(self._app.tank)
            self._current_user_loaded = True

        query_fields = ["code", "description", "image"]

        sg_data = []
        if data["own_tasks_only"]:

            if self._current_user is not None:
                # my stuff
                tasks = self._app.shotgun.find("Task", 
                                               [ ["project", "is", self._app.context.project], 
                                                 ["task_assignees", "is", self._current_user ]], 
                                                 ["entity"]
                                               )
                
                # get all the entities that are associated with entity types that 
                # we are interested in.
                entities_to_load = {}
                for x in tasks:
                    if x["entity"]:
                        # task linked to an entity. Get the type of entity and process
                        task_et_type = x["entity"]["type"]
                        if task_et_type in self.__entity_types_to_load:
                            if task_et_type not in entities_to_load:
                                entities_to_load[task_et_type] = []
                            entities_to_load[task_et_type].append(x["entity"]["id"])

                # now load data for those
                for et in entities_to_load:
                    
                    # get entities from shotgun:
                    filter = ["id", "in"]
                    filter.extend(entities_to_load[et])
                    entities = self._app.shotgun.find(et, 
                                                      [ filter ],
                                                      query_fields + self.__entity_type_extra_fields.get(et, {}).values(),  
                                                      [{"field_name": "code", "direction": "asc"}])
                                        
                    # append to results:
                    sg_data.append({"type":et, "data":entities})
        else:
            # load all entities
            for et in self.__entity_types_to_load:
                
                sg_filters = [ ["project", "is", self._app.context.project] ]
                
                if et in self.__entity_type_filters:
                    # have a custom filter specified in the settings!
                    sg_filters.extend( self.__entity_type_filters[et] )
                
                # get entities from shotgun:
                entities = self._app.shotgun.find(et, 
                                                  sg_filters, 
                                                  query_fields + self.__entity_type_extra_fields.get(et, {}).values(),
                                                  [{"field_name": "code", "direction": "asc"}])
                                
                # append to results:
                sg_data.append({"type":et, "data":entities})
        
        return {"data": sg_data, "current_entity" : current_entity}


    def process_result(self, result):
        """
        Process results from the 'get_data' call and populate the browser widget
        with a list of entities to display
        
        :param result:  The result from the 'get_data' call containing all the entity information
                        retrieved from Shotgun
        """

        if len(result.get("data")) == 0:
            self.set_message("No matching items found!")
            return
        
        current_entity = result.get("current_entity")

        item_to_select = None        
        for item in result.get("data"):
            i = self.add_item(browser_widget.ListHeader)
            i.set_title("%ss" % tank.util.get_entity_type_display_name(self._app.tank, item.get("type")))

            for d in item["data"]:
                entity_type = d.get("type")
                
                i = self.add_item(browser_widget.ListItem)

                # build the details text to display:
                details = "<b>%s %s</b>" % (tank.util.get_entity_type_display_name(self._app.tank, entity_type), 
                                            d.get("code"))
                
                # retrieve any extra info to display in the UI.  extra_fields is a dictionary of 'label:field'
                # pairs for the current entity type.
                extra_fields = self.__entity_type_extra_fields.get(entity_type, {})
                extra_info = ", ".join(["%s: %s" % (label, str(d.get(field))) 
                                        for label, field in extra_fields.iteritems()])
                if extra_info:
                    details += "<br>(%s)" % extra_info

                # add in description:
                details += "<br>%s" % (d.get("description") or "No description")
                
                i.set_details(details)
                i.sg_data = d
                if d.get("image"):
                    i.set_thumbnail(d.get("image"))
                    
                if (d and current_entity 
                    and d["id"] == current_entity.get("id") 
                    and entity_type == current_entity.get("type")):
                    item_to_select = i
            
            if item_to_select:
                self.select(item_to_select)

        
        