# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
"""

class EnvironmentDetails(object):
    def __init__(self):
        self.context = None
        self.work_area_template = None
        self.work_template = None
        self.publish_area_template = None
        self.publish_template = None
        
    def __repr__(self):
        return ("CTX: %s\n - Work Area: %s\n - Work: %s\n - Publish Area: %s\n - Publish: %s" 
                % (self.context, 
                   self.work_area_template, self.work_template, 
                   self.publish_area_template, self.publish_template)
                )