"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------
"""

from operator import itemgetter
from datetime import datetime, timedelta
from pprint import pprint

import tank
from tank.platform.qt import QtCore, QtGui
browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")

from .work_file import WorkFile

class FileListView(browser_widget.BrowserWidget):
    
    # signals
    open_previous_version = QtCore.Signal(WorkFile)
    view_in_shotgun = QtCore.Signal(WorkFile)
    
    def __init__(self, parent=None):
        """
        Construction
        """
        browser_widget.BrowserWidget.__init__(self, parent)
        
        # tweak style
        self.title_style = "none"
        self.set_label("Available Files:")
        
    @property
    def selected_file(self):
        selected_item = self.get_selected_item()
        if selected_item:
            return selected_item.file
        return None

    def get_data(self, data):
        """
        Called by browser widget in worker thread to query the list
        of files to display for the specified context
        """
        result = {"task_groups":{}, "task_name_order":{}}
        
        handler = data["handler"]
        user = data.get("user")
        show_local = data.get("show_local")
        show_publishes = data.get("show_publishes")

        # get some additional info from the handler:
        ctx = handler.get_current_work_area()
        
        result["can_do_new_file"] = handler.can_do_new_file()
        result["have_valid_workarea"] = (ctx and ctx.entity)
        result["have_valid_configuration"] = handler.have_valid_configuration_for_work_area()
        result["current_task_name"] = ctx.task.get("name") if ctx and ctx.task else None
        
        if result["have_valid_workarea"] and result["have_valid_configuration"]:
        
            # get the list of files from the handler:
            files = handler.find_files(user)
            
            # re-pivot this list of files ready to display:
            """
            builds the following structure
            { task_name : { (file)name : { "files" : { 1:file,2:file, ... }, "thumbnail" : path, ... } } }
            """            
            task_groups = {}
            for file in files:
                # first level is task group
                task_name = file.task.get("name") if file.task else "No Task"
                task_group = task_groups.setdefault(task_name, dict())
                
                # next level is name:
                name_group = task_group.setdefault(file.name, dict())
                
                # finally, add file to files:
                file_versions = name_group.setdefault("files", dict())
                file_versions[file.version] = file
                
            # do some pre-processing of file groups:
            filtered_task_groups = {}
            
            task_name_order = {}
            for task, name_groups in task_groups.iteritems():
                name_modified_pairs = []
                
                filtered_name_groups = {}
                
                for name, details in name_groups.iteritems():
                    files_versions = details["files"]
                    
                    # find highest version info:
                    local_versions = [f.version for f in files_versions.values() if f.is_local]
                    if not local_versions and not show_publishes:
                        continue
                    
                    publish_versions = [f.version for f in files_versions.values() if f.is_published]
                    if not publish_versions and not show_local:
                        continue
                    
                    highest_local_version = max(local_versions) if local_versions else -1
                    highest_publish_version = max(publish_versions) if publish_versions else -1
                    highest_version = max(highest_local_version, highest_publish_version)
                    highest_file = files_versions[highest_version]
                    
                    details["highest_local_file"] = files_versions[highest_local_version] if highest_local_version >= 0 else None
                    details["highest_publish_file"] = files_versions[highest_publish_version] if highest_publish_version >= 0 else None
                    
                    # find thumbnail to use:
                    sorted_versions = sorted(files_versions.keys(), reverse=True)
                    thumbnail = None
                    for version in sorted_versions:
                        thumbnail = files_versions[version].thumbnail
                        if thumbnail:
                            break
                    details["thumbnail"] = thumbnail
                    
                    # get file modified time so we can order names:
                    name_modified_pairs.append((name, highest_file.last_modified_time))
                    
                    filtered_name_groups[name] = details
    
                if not filtered_name_groups:
                    # everything in this group was filtered out!
                    continue
                
                filtered_task_groups[task] = filtered_name_groups
    
                # sort names in reverse order of modified date:
                name_modified_pairs.sort(key=itemgetter(1), reverse=True)
                task_name_order[task] = [n for (n, _) in name_modified_pairs]
        
            result["task_groups"] = filtered_task_groups
            result["task_name_order"] = task_name_order
        
        return result
    
    def process_result(self, result):
        """
        Process list of tasks retrieved by get_data on the main thread
        """
        task_groups = result["task_groups"]
        task_name_order = result["task_name_order"]
        current_task_name = result["current_task_name"]

        if not task_groups:
            # build a useful error message using the info we have available:
            msg = ""
            if not result["have_valid_workarea"]:
                msg = "Please select a Work Area to begin..."
            elif not result["have_valid_configuration"]:
                msg = ("Tank File Manager has not been configured for the environment "
                       "being used by the selected Work Area!\n"
                       "Please choose a different Work Area to continue.")
            elif not result["can_do_new_file"]:
                msg = "Couldn't find any files in this Work Area!\nTry selecting a different Work Area."
            else:
                msg = "Couldn't find any files!\nClick the New file button to start work."
            
            self.set_message(msg)
            return
        
        for task_name, name_groups in task_groups.iteritems():
        
            if len(task_groups) > 1 or task_name != current_task_name:
                # add header for task:
                h = self.add_item(browser_widget.ListHeader)
                h.set_title("%s" % (task_name))
            
            ordered_names = task_name_order[task_name]
            for name in ordered_names:
                details = name_groups[name]
                
                files = details["files"]
                highest_local_file = details["highest_local_file"]
                highest_publish_file = details["highest_publish_file"]
                thumbnail = details["thumbnail"]
                
                # get the primary file to use for this item - this is always the file 
                # with the highest version from those available and is the one that will
                # be opened:
                highest_publish_version = highest_publish_file.version if highest_publish_file else 0
                highest_local_version = highest_local_file.version if highest_local_file else 0
                highest_version = max(highest_publish_version, highest_local_version)
                primary_file = files[highest_version]

                # add new item to list:
                item = self._add_file_item(primary_file, highest_publish_file, highest_local_file)
                if not item:
                    continue
                
                # set thumbnail if have one:
                if thumbnail:
                    item.set_thumbnail(thumbnail)

                
                # add context menu:
                item.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

                # if it's a publish then add 'View In Shotgun' item:
                if highest_publish_file:
                    action = QtGui.QAction("View in Shotgun", item)
                    action.triggered.connect(lambda f=highest_publish_file: self._on_show_in_shotgun_action_triggered(f))
                    item.addAction(action)
                
                # if have other publish versions then add them to context menu
                previous_versions = [f.version for f in files.values() if f.version != highest_version]
                if previous_versions:

                    # sort versions into reverse order:
                    previous_versions.sort(reverse=True)
                    
                    # and add first 20 to context menu:
                    for v in previous_versions[:20]:
                        f = files[v]
                        
                        action = QtGui.QAction("Open previous version v%03d" % f.version, item)
                        action.triggered.connect(lambda f=f: self._on_open_action_triggered(f))
                        item.addAction(action)
                   
    def _add_file_item(self, file, highest_publish_file, highest_local_file):
        """
        """
        colour_str = None
        lines = []
        tool_tip = ""
                   
        # work out colour:
        red = "rgb(200, 84, 74)"
        green = "rgb(145, 206, 95)"
        
        if highest_publish_file:
            
            tool_tip = highest_publish_file.publish_description
            if tool_tip:
                tool_tip = "<b>Description</b>:<br>%s" % tool_tip
            else:
                tool_tip = "<i>No description was entered for this publish</i>" 
            
            highest_pub_version = highest_publish_file.version if highest_publish_file else -1
            highest_local_version = highest_local_file.version if highest_local_file else -1
            
            local_is_latest = False
            
            if highest_local_version > highest_pub_version:
                if highest_local_file.last_modified_time and highest_publish_file.last_modified_time:
                    # check file modification time - we only consider a local version to be 'latest' 
                    # if it has a more recent modification time than the published file (with 2mins
                    # tollerance)
                    if highest_local_file.last_modified_time > highest_publish_file.last_modified_time:
                        local_is_latest = True
                    else:
                        diff = highest_publish_file.last_modified_time - highest_local_file.last_modified_time
                        if diff.seconds < 120:
                            local_is_latest = True
                else:
                    # can't compare times so assume local is more recent than publish:
                    local_is_latest = True
            
            if local_is_latest:
                colour_str = green
                tool_tip = "%s<br>- You have the latest version in your work area" % tool_tip
            else:
                colour_str = red
            
        # add item:
        item = self.add_item(browser_widget.ListItem)
        item.file = file

        # set tool tip
        if tool_tip:
            item.setToolTip(tool_tip)
        
        # name & version:
        title_str = "<b>%s, v%03d</b>" % (file.name, file.version)
        if colour_str:    
            title_str = "<span style='color:%s'>%s</span>" % (colour_str, title_str)
        lines.append(title_str)
                
        # last modified date:
        date_str = ""                
        if file.last_modified_time:
            modified_date = file.last_modified_time.date()
            date_str = ""
            time_diff = datetime.now().date() - modified_date
            if time_diff < timedelta(days=1):
                date_str = "Today"
            elif time_diff < timedelta(days=2):
                date_str = "Yesterday"
            else:
                date_str = "on %d%s %s" % (modified_date.day, 
                                        self._day_suffix(modified_date.day), 
                                        modified_date.strftime("%B %Y"))
                
            if not file.is_published:
                lines.append("Last Updated %s" % date_str)
            else:
                lines.append("Published %s" % date_str)

        # last modified by
        if file.modified_by is not None and "name" in file.modified_by:
            last_changed_by_str = "%s" % file.modified_by["name"]
            if not file.is_published:
                lines.append("Updated by %s" % last_changed_by_str)
            else:
                lines.append("Published by %s" % last_changed_by_str)
        
        # build and set details string:
        item.set_details("<br>".join(lines))
        
        return item
                    
    def _day_suffix(self, day):
        """
        Return the suffix for the day of the month
        """
        return ["th", "st", "nd", "rd"][day%10 if not 11<=day<=13 and day%10 < 4 else 0]
              
    def _on_open_action_triggered(self, file):
        """
        Open action triggered from context menu
        """
        self.open_previous_version.emit(file)

    def _on_show_in_shotgun_action_triggered(self, file):
        """
        Show in Shotgun action triggered from context menu
        """
        self.view_in_shotgun.emit(file)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            