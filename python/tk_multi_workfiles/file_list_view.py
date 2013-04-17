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

class FileListView(browser_widget.BrowserWidget):
    
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
        
        handler = data.get("handler")
        user = data.get("user")
        
        only_show_local = not data.get("publishes")
        only_show_publishes = (user == None)
        
        if handler:
            # get the list of files from the handler:
            files = handler.find_files(user)
            ctx = handler.get_current_work_area()
            current_task_name = ctx.task.get("name") if ctx and ctx.task else None
            
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
                files = name_group.setdefault("files", dict())
                files[file.version] = file
                
            # do some pre-processing of file groups:
            filtered_task_groups = {}
            
            task_name_order = {}
            for task, name_groups in task_groups.iteritems():
                name_modified_pairs = []
                
                filtered_name_groups = {}
                
                for name, details in name_groups.iteritems():
                    files = details["files"]
                    
                    # find highest version info:
                    local_versions = [f.version for f in files.values() if f.is_local]
                    if not local_versions and only_show_local:
                        continue
                    
                    publish_versions = [f.version for f in files.values() if f.is_published]
                    if not publish_versions and only_show_publishes:
                        continue
                    
                    highest_local_version = max(local_versions) if local_versions else -1
                    highest_publish_version = max(publish_versions) if publish_versions else -1
                    highest_version = max(highest_local_version, highest_publish_version)
                    highest_file = files[highest_version]
                    
                    details["highest_local_version"] = highest_local_version
                    details["highest_publish_version"] = highest_publish_version
                    
                    # find thumbnail to use:
                    sorted_versions = sorted(files.keys(), reverse=True)
                    thumbnail = None
                    for version in sorted_versions:
                        thumbnail = files[version].thumbnail
                        if thumbnail:
                            break
                    details["thumbnail"] = thumbnail
                    
                    # get file modified time so we can order names:
                    name_modified_pairs.append((name, highest_file.last_modified_time))
                    
                    filtered_name_groups[name] = details

                if not filtered_name_groups:
                    # everyting in this group was filtered out!
                    continue
                
                filtered_task_groups[task] = filtered_name_groups

                # sort names in reverse order of modified date:
                name_modified_pairs.sort(key=itemgetter(1), reverse=True)
                task_name_order[task] = [n for (n, _) in name_modified_pairs]
        
            result["task_groups"] = filtered_task_groups
            result["task_name_order"] = task_name_order
            result["current_task_name"] = current_task_name
        
        return result
    
    def process_result(self, result):
        """
        Process list of tasks retrieved by get_data on the main thread
        """
        task_groups = result["task_groups"]
        task_name_order = result["task_name_order"]
        current_task_name = result["current_task_name"]

        if not task_groups:
            self.set_message("Couldn't find any files! Click the new file button to start work.")
            return
        
        #pprint(task_groups)
        
        for task_name, name_groups in task_groups.iteritems():
        
            if len(task_groups) > 1 or task_name != current_task_name:
                # add header for task:
                h = self.add_item(browser_widget.ListHeader)
                h.set_title("%s" % (task_name))
            
            ordered_names = task_name_order[task_name]
            for name in ordered_names:
                details = name_groups[name]
                
                files = details["files"]
                highest_local_version = details["highest_local_version"]
                highest_publish_version = details["highest_publish_version"]
                thumbnail = details["thumbnail"]
                
                # get the primary file to use for this item:
                highest_version = max(highest_local_version, highest_publish_version)
                primary_file = files[highest_version]

                # add new item to list:
                item = self.add_item(browser_widget.ListItem)
                item.file = primary_file
                
                # set item details:
                details_str = self._build_details_string(primary_file, highest_publish_version, highest_local_version)
                item.set_details(details_str)

                # set thumbnail if have one:
                if thumbnail:
                    item.set_thumbnail(thumbnail)

                """
                # if have other publish versions then add them to context menu
                publish_versions = [v for v, f in files.iteritems() if f.is_published]
                if publish_versions:
                    # sort into reverse order:
                    publish_versions = sorted(publish_versions, reverse=True)

                    # use action context menu:                    
                    item.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
                    
                    max_menu_items = 10
                    for i, version in enumerate(publish_versions):
                        if i >= max_menu_items:
                            break
                        
                        action = QtGui.QAction("Open publish v%03d read-only" % version, item)
                        action.triggered.connect(lambda f = files[version]: self._on_open_action_triggered(f))
                        item.addAction(action)
                """
                    
    def _build_details_string(self, file, highest_publish_version, highest_local_version):
        """
        
        """
        
        lines = []
        
        # name:
        lines.append("<b>%s</b>" % file.name)
        
        # version:
        red = "rgb(200, 84, 74)"
        green = "rgb(145, 206, 95)"
        
        version_desc = ""
        colour_str = None
        if highest_local_version < 0:
            # no local version
            colour_str = red
            version_desc = " - work file doesn't exist"
          
        elif highest_publish_version < 0:
            # no publish version
            version_desc = " - never been published"
    
        elif highest_publish_version == highest_local_version:
            # local version is publish version (very rarely happens!)
            version_desc = " - work file is the most recent publish"
            colour_str = green
            
        elif highest_publish_version < highest_local_version:
            # local version is newer than publish
            version_desc = " - work file is newer than latest publish (v%03d)" % highest_publish_version 
        
        else:#highest_publish_version > highest_local_version:
            # publish is newer than local version
            version_desc = " - work file is older than the latest publish (v%03d)" % highest_publish_version
            colour_str = red

        lines.append("<b>Version:</b> v%03d%s" % (highest_local_version, version_desc))
        
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
        lines.append("Last Updated %s" % date_str)

        # last modified by
        if file.modified_by is not None and "name" in file.modified_by:
            last_changed_by_str = "%s" % file.modified_by["name"]
            lines.append("Last Changed by %s" % last_changed_by_str)
    
        # build details string:
        details_str = "<br>".join(lines)
        
        if colour_str:    
            details_str = "<p style='color:%s'>%s</p>" % (colour_str, details_str)
            
        return details_str
                    
    def _day_suffix(self, day):
        """
        Return the suffix for the day of the month
        """
        return ["th", "st", "nd", "rd"][day%10 if not 11<=day<=13 and day%10 < 4 else 0]
                    
                    
    def _on_open_action_triggered(self, file):
        print "%s" % file
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            