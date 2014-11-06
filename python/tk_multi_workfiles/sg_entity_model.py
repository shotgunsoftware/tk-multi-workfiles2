# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtGui

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model") 
ShotgunOverlayModel = shotgun_model.ShotgunOverlayModel

class SgEntityModel(shotgun_model.ShotgunModel):
    """
    This model represents the data which is displayed inside one of the treeview tabs
    on the left hand side.
    """
    
    def __init__(self, parent, overlay_widget, entity_type, filters, hierarchy):
        """
        Constructor
        """
        ## folder icon
        #self._default_icon = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Folder.png"))    

        # shotgun entity icons
        self._entity_icons = {}
        #self._entity_icons["Shot"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Shot_dark.png"))
        #self._entity_icons["Asset"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Asset_dark.png"))
        #self._entity_icons["EventLogEntry"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_EventLogEntry_dark.png"))
        #self._entity_icons["Group"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Group_dark.png"))
        #self._entity_icons["HumanUser"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_HumanUser_dark.png"))
        #self._entity_icons["Note"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Note_dark.png"))
        #self._entity_icons["Project"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Project_dark.png"))
        #self._entity_icons["Sequence"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Sequence_dark.png"))
        #self._entity_icons["Task"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Task_dark.png"))
        #self._entity_icons["Ticket"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Ticket_dark.png"))
        #self._entity_icons["Version"] = QtGui.QIcon(QtGui.QPixmap(":/res/icon_Version_dark.png"))

        ShotgunOverlayModel.__init__(self, 
                                     parent, 
                                     #overlay_widget, 
                                     download_thumbs=False,
                                     schema_generation=0)
        fields=["image", "sg_status_list", "description"]
        self._load_data(entity_type, filters, hierarchy, fields)
    
    def async_refresh(self):
        """
        Trigger an asynchronous refresh of the model
        """
        self._refresh_data()        
    
    def _populate_default_thumbnail(self, item):
        """
        Whenever an item is constructed, this methods is called. It allows subclasses to intercept
        the construction of a QStandardItem and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in load_data()
        """
        found_icon = False
        
        # get the associated field data with this node
        field_data = shotgun_model.get_sanitized_data(item, self.SG_ASSOCIATED_FIELD_ROLE)
        # get the full sg data for this node (leafs only)
        sg_data = shotgun_model.get_sg_data(item)     
        
        # {'name': 'sg_sequence', 'value': {'type': 'Sequence', 'id': 11, 'name': 'bunny_080'}}
        field_value = field_data["value"]
        
        if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
            # this is an intermediate node which is an entity type link
            if field_value.get("type") in self._entity_icons:
                # use sg icon!
                item.setIcon(self._entity_icons[ field_value.get("type") ])
                found_icon = True
        
        elif sg_data:
            # this is a leaf node!  
            if sg_data.get("type") in self._entity_icons:
                # use sg icon!
                item.setIcon(self._entity_icons[ sg_data.get("type") ])
                found_icon = True
        
        # for all items where we didn't find the icon, fall back onto the default
        if not found_icon:
            #item.setIcon(self._default_icon)
            pass
                

        
        
        