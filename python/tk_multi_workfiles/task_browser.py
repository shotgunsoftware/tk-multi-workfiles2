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


class TaskBrowserWidget(browser_widget.BrowserWidget):

    def __init__(self, parent=None):
        browser_widget.BrowserWidget.__init__(self, parent)
        
        # only load this once!
        self._current_user = None
        self._current_user_loaded = False
        self._status_name_lookup = None
        app = tank.platform.current_bundle()
        self.__task_filters = app.get_setting("sg_task_filters", [])
        
    @property
    def selected_task(self):
        selected_item = self.get_selected_item()
        if selected_item:
            return selected_item.sg_data
        return None
        
    def grab_task(self):
        
        try:
            task_id = self.sender().parent().sg_data["id"]
            task_assignees = self.sender().parent().sg_data["task_assignees"]
        except:
            QtGui.QMessageBox.critical(self, "Cannot Resolve Task!", "Cannot resolve this task!")            
            return
            
        res = QtGui.QMessageBox.question(self, 
                                         "Assign yourself to this task?", 
                                         "Assign yourself to this task?",
                                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel)
        if res == QtGui.QMessageBox.Ok:
            task_assignees.append(self._current_user)
            self._app.shotgun.update("Task", task_id, {"task_assignees": task_assignees})
        
        # ask widget to refresh itself
        self.clear()
        self.load(self._current_data)
        
        

    def get_data(self, data):
        
        self._current_data = data
        
        if not self._current_user_loaded:
            self._current_user = tank.util.get_current_user(self._app.tank)
            self._current_user_loaded = True
        
        # first get a list of all statuses if we haven't already!
        # make a dictionary keyed by short status code with values of long status codes.
        if self._status_name_lookup is None:
            self._status_name_lookup = {}
            for x in self._app.shotgun.find("Status", [], ["code", "name"]):
                self._status_name_lookup[ x.get("code") ] = x.get("name")
        
        # start building output data structure        
        output = {}
        output["associated_entity"] = data["entity"]
        output["current_task"] = data.get("task")
        output["can_create_tasks"] = data.get("can_create_tasks", False)

        # gather all the fields to pull
        fields = ["content", "task_assignees", "image", "sg_status_list", "step.Step.list_order"]
        extra_fields = self._app.get_setting("task_extra_display_fields", [])
        fields.extend(extra_fields)

        if data["own_tasks_only"]:
            
            if self._current_user is None:
                output["tasks"] = []
                output["users"] = []
                
            else:
                # get my stuff
                output["users"] = [ self._current_user ]
                output["tasks"] = self._app.shotgun.find("Task", 
                                                    [ ["project", "is", self._app.context.project],
                                                      ["entity", "is", data["entity"]], 
                                                      ["step", "is_not", None],
                                                      ["task_assignees", "is", self._current_user ]], 
                                                    fields)
        else:
            # get all tasks
            sg_filters = [ ["project", "is", self._app.context.project],
                           ["step", "is_not", None],
                           ["entity", "is", data["entity"] ] ]
            sg_filters.extend( self.__task_filters )               
            
            output["tasks"] = self._app.shotgun.find("Task", 
                                                sg_filters, 
                                                fields)
        
            # get all the users where tasks are assigned.
            user_ids = []
            for task in output["tasks"]:
                user_ids.extend( [ x["id"] for x in task.get("task_assignees", []) ] )
            
            if len(user_ids) > 0:
                # use super weird filter syntax....
                sg_filter = ["id", "in"]
                sg_filter.extend(user_ids)
                output["users"] = self._app.shotgun.find("HumanUser", [ sg_filter ], ["image"])
            else:
                output["users"] = []

        # sort tasks so that they are in the correct (step.Step.list_order) order:
        output["tasks"].sort(key=lambda v:(v.get("step.Step.list_order") or sys.maxint, v.get("content")))
        
        return output
                    
    def process_result(self, result):
        
        entity_data = result["associated_entity"]
        tasks = result["tasks"]
        can_create_tasks = result["can_create_tasks"]
        
        entity_str = "%s %s" % (entity_data.get("type", "Unknown"), entity_data.get("code", "Unknown"))

        if len(tasks) == 0:
            msg = ""
            if can_create_tasks:
                msg = "No Tasks found!\nClick the 'New Task' button below to create a Task."
            else:
                msg = ("No Tasks found!\nYou can create tasks by navigating to '%s' "
                       "inside of Shotgun, selecting the tasks tab and then clicking "
                       "the + button." % entity_str)
            self.set_message(msg)
            
        else:

            current_task = result.get("current_task")
            item_to_select = None        
            
            for d in tasks:
                i = self.add_item(browser_widget.ListItem)
                
                details = []

                # figure out the name to display for the task
                task_name = "<b>Task: %s</b>" % d.get("content", "")
                extra_fields = self._app.get_setting("task_extra_display_fields", [])
                extra_data = [d.get(f) for f in extra_fields]
                name_extension = ", ".join([str(item) for item in extra_data if item != None])

                if name_extension:
                    task_name = task_name + " (%s)" % name_extension

                details.append(task_name)

                # now try to look up the proper status name
                status_short_name = d.get("sg_status_list")
                # get the long name, fall back on short name if not found
                status_name = self._status_name_lookup.get(status_short_name, status_short_name)
                details.append("Status: %s" % status_name)
                
                names = [ x.get("name", "Unknown") for x in d.get("task_assignees", []) ]
                names_str = ", ".join(names)
                details.append("Assigned to: %s" % names_str)
                
                i.set_details("<br>".join(details))
                
                i.sg_data = d
                i.setToolTip("Double click to set context.")
                
                # add a grab task action
                if self._current_user: # not None
                    if d.get("task_assignees"):
                        assigned_user_ids = [ x["id"] for x in d.get("task_assignees") ]
                    else:
                        assigned_user_ids = []
                        
                    if self._current_user["id"] not in assigned_user_ids:
                        # are are not assigned to this task. add ability to grab it                
                        i.grab_action = QtGui.QAction("Add %s as an assignee to this task." % self._current_user["name"], i)
                        i.grab_action.triggered.connect(self.grab_task)                       
                        i.addAction(i.grab_action)
                        i.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)                
                
                # finally look up the thumbnail for the first user assigned to the task
                task_assignees = d.get("task_assignees", [])
                if len(task_assignees) > 0:
                    user_id = task_assignees[0]["id"]
                    # is this user id in our users dict? In that case we have their thumb!
                    for u in result["users"]:
                        if u["id"] == user_id:
                            # if they have a thumb, assign!
                            if u.get("image"):
                                i.set_thumbnail(u.get("image"))
                            break            
                
                if d and current_task and d["id"] == current_task.get("id"):
                    item_to_select = i
            
            if item_to_select:
                self.select(item_to_select)
                
        