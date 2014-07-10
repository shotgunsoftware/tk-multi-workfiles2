# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from operator import itemgetter
from datetime import datetime, timedelta
from pprint import pprint

import tank
from tank.platform.qt import QtCore, QtGui
browser_widget = tank.platform.import_framework("tk-framework-widget", "browser_widget")
from .file_item_form import FileItemForm

from .file_item import FileItem
from .file_filter import FileFilter

class FileListView(browser_widget.BrowserWidget):
    
    # signals - note, 'object' is used to avoid 
    # issues with PyQt when None is passed as PyQt 
    # doesn't allow None to be passed to classes 
    # other than object (an exception is raised)
    open_previous_workfile = QtCore.Signal(object)#FileItem
    open_previous_publish = QtCore.Signal(object)#FileItem
    view_in_shotgun = QtCore.Signal(object)#FileItem
    
    NO_TASK_NAME = "No Task"
    
    def __init__(self, parent=None):
        """
        Construction
        """
        browser_widget.BrowserWidget.__init__(self, parent)
        
        self._current_filter = {}
        
        # tweak style
        self.title_style = "none"
        
        self._update_title()  
    
    @property
    def selected_published_file(self):
        selected_item = self.get_selected_item()
        if selected_item:
            return selected_item.published_file
        return None

    @property
    def selected_work_file(self):
        selected_item = self.get_selected_item()
        if selected_item:
            return selected_item.work_file
        return None
    
    # Enable to force all work to be done in the main thread
    # which can help when debugging
    # IMPORTANT - set this to False before releasing!!!
    DEBUG_GET_DATA_IN_MAIN_THREAD=False
    
    def get_data(self, data):
        """
        Called by browser widget in worker thread to query the list
        of files to display for the specified context
        """
        if FileListView.DEBUG_GET_DATA_IN_MAIN_THREAD:
            # debug only - _get_data will be called first in
            # process_result which runs in the main thread
            return data
        else:
            return self._get_data(data)
        
    def _get_data(self, data):
        """
        Retrieve the list of files to display as well as the various display and grouping options required
        to build the file list.
        
        :param data:    Dictionary containing:
                        handler - A 'WorkFiles' instance containing the main application business logic
                        filter - The current 'FileFilter' instance being applied to the list
                        
        :returns:       Dictionary containing the various display & grouping options required to build the
                        file list as well as the list of files organised by task.
                        
        """
        result = {"task_groups":{}, "task_name_order":{}}
        
        handler = data["handler"]
        filter = data.get("filter")
        mode = filter.mode
        
        # get some additional info from the handler:
        ctx = handler.get_current_work_area()
        
        result["can_do_new_file"] = handler.can_do_new_file()
        result["have_valid_workarea"] = (ctx and (ctx.entity or ctx.project))
        result["have_valid_configuration"] = handler.have_valid_configuration_for_work_area()
        result["current_task_name"] = ctx.task.get("name") if ctx and ctx.task else None
        result["can_change_work_area"] = handler.can_change_work_area()
        result["filter"] = filter
        result["task_order"] = []
        
        if result["have_valid_workarea"] and result["have_valid_configuration"]:
        
            # get the list of files from the handler:
            files = handler.find_files(filter)
            
            # re-pivot this list of files ready to display:
            # 
            # builds the following structure
            # { task_name : { (file)name : { "files" : { 1:file,2:file, ... }, "thumbnail" : path, ... } } }
                        
            task_groups = {}
            for file in files:
                # first level is task group
                task_name = file.task.get("name") if file.task else FileListView.NO_TASK_NAME
                task_group = task_groups.setdefault(task_name, dict())
                
                # next level is name:
                name_group = task_group.setdefault(file.name, dict())
                
                # finally, add file to files:
                file_versions = name_group.setdefault("files", dict())
                file_versions[file.version] = file
                
            # do some pre-processing of file groups:
            filtered_task_groups = {}
            
            task_modified_pairs = []
            task_name_order = {}
            for task, name_groups in task_groups.iteritems():
                name_modified_pairs = []
                
                filtered_name_groups = {}
                
                for name, details in name_groups.iteritems():
                    files_versions = details["files"]
                    
                    # find highest version info:
                    local_versions = [f.version for f in files_versions.values() if f.is_local]
                    if mode == FileFilter.WORKFILES_MODE and not local_versions:
                        # don't have a version of this file to display!
                        continue
                    
                    publish_versions = [f.version for f in files_versions.values() if f.is_published]
                    if mode == FileFilter.PUBLISHES_MODE and not publish_versions:
                        # don't have a version of this file to display!
                        continue
                    
                    highest_local_version = -1
                    if local_versions:
                        highest_local_version = max(local_versions)
                        details["highest_local_file"] = files_versions[highest_local_version]
                        
                    highest_publish_version = -1
                    if publish_versions:
                        highest_publish_version = max(publish_versions)
                        details["highest_publish_file"] = files_versions[highest_publish_version]
                    
                    # find thumbnail to use:
                    sorted_versions = sorted(files_versions.keys(), reverse=True)
                    thumbnail = None
                    for version in sorted_versions:
                        # skip any versions that are greater than the one we are looking for
                        # Note: we shouldn't choose a thumbnail for versions that aren't
                        # going to be displayed so filter these out
                        if ((mode == FileFilter.WORKFILES_MODE and version > highest_local_version)
                            or (mode == FileFilter.PUBLISHES_MODE and version > highest_publish_version)):
                            continue
                        thumbnail = files_versions[version].thumbnail
                        if thumbnail:
                            # special case - update the thumbnail!
                            if mode == FileFilter.WORKFILES_MODE and version < highest_local_version:
                                files_versions[highest_local_version].set_thumbnail(thumbnail)
                            break
                    details["thumbnail"] = thumbnail
                    
                    # update group with details:
                    filtered_name_groups[name] = details

                    # determine when this file was last updated (modified or published)
                    # this is used to sort the files in the list:
                    last_updated = None
                    if mode == FileFilter.WORKFILES_MODE and highest_local_version >= 0:
                        last_updated = files_versions[highest_local_version].modified_at
                    if highest_publish_version >= 0:
                        published_at = files_versions[highest_publish_version].published_at
                        last_updated = max(last_updated, published_at) if last_updated else published_at
                    
                    name_modified_pairs.append((name, last_updated))
    
                if not filtered_name_groups:
                    # everything in this group was filtered out!
                    continue
                
                filtered_task_groups[task] = filtered_name_groups
    
                # sort names in reverse order of modified date:
                name_modified_pairs.sort(key=itemgetter(1), reverse=True)
                task_name_order[task] = [n for (n, _) in name_modified_pairs]
                
                task_modified_pairs.append((task, max([m for (_, m) in name_modified_pairs])))
        
            # sort tasks in reverse order of modified date:
            task_modified_pairs.sort(key=itemgetter(1), reverse=True)
            task_order = [n for (n, _) in task_modified_pairs]
        
            result["task_groups"] = filtered_task_groups
            result["task_name_order"] = task_name_order
            result["task_order"] = task_order
        
        return result
    
    def process_result(self, result):
        """
        Process list of tasks retrieved by get_data on the main thread
        
        :param result:  Dictionary containing the various display & grouping options required to build the
                        file list as well as the list of files organised by task.        
        """
        if FileListView.DEBUG_GET_DATA_IN_MAIN_THREAD:
            # gathering of data was not done in the get_data stage so we
            # should do it here instead - this method gets called in the 
            # main thread
            result = self._get_data(result)
        
        task_groups = result["task_groups"]
        task_name_order = result["task_name_order"]
        task_order = result["task_order"]
        current_task_name = result["current_task_name"]
        self._current_filter = result["filter"]
        
        self._update_title()
        
        if not task_groups:
            # build a useful error message using the info we have available:
            msg = ""
            if not result["can_change_work_area"]:
                if not result["have_valid_workarea"]:
                    msg = "The current Work Area is not valid!"
                elif not result["have_valid_configuration"]:
                    msg = ("Shotgun File Manager has not been configured for the environment "
                           "being used by the selected Work Area!")
                elif not result["can_do_new_file"]:
                    msg = "Couldn't find any files in this Work Area!"
                else:
                    msg = "Couldn't find any files!\nClick the New file button to start work."
            else:
                if not result["have_valid_workarea"]:
                    msg = "The current Work Area is not valid!"
                elif not result["have_valid_configuration"]:
                    msg = ("Shotgun File Manager has not been configured for the environment "
                           "being used by the selected Work Area!\n"
                           "Please choose a different Work Area to continue.")
                elif not result["can_do_new_file"]:
                    msg = "Couldn't find any files in this Work Area!\nTry selecting a different Work Area."
                else:
                    msg = "Couldn't find any files!\nClick the New file button to start work."
            self.set_message(msg)
            return
        
        for task_name in task_order:
            name_groups = task_groups[task_name]
        
            if (len(task_groups) > 1 
                or (task_name != current_task_name
                    and task_name != FileListView.NO_TASK_NAME 
                    and current_task_name == None)):
                # add header for task:
                h = self.add_item(browser_widget.ListHeader)
                h.set_title("%s" % (task_name))
            
            ordered_names = task_name_order[task_name]
            for name in ordered_names:
                details = name_groups[name]
                
                files = details["files"]
                highest_local_file = details.get("highest_local_file")
                highest_publish_file = details.get("highest_publish_file")
                thumbnail = details["thumbnail"]
                
                # add new item to list:
                item = self._add_file_item(highest_publish_file, highest_local_file)
                if not item:
                    continue
                
                # set thumbnail if have one:
                if thumbnail:
                    item.set_thumbnail(thumbnail)
                
                # add context menu:
                item.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

                # if it's a publish then add 'View In Shotgun' item:
                if highest_publish_file:
                    action = QtGui.QAction("View latest Publish in Shotgun", item)
                    # (AD) - the '[()]' syntax in action.triggered[()].connect looks weird right!
                    # 'triggered' is a QtCore.SignalInstance which actually defines multiple
                    # signals: triggered() & triggered(bool).  PySide will correctly determine which
                    # one to use but PyQt gets confused and calls the (bool) version instead which
                    # causes problems for us...  Luckily, Qt lets us use the argument list () to 
                    # index into the SignalInstance object to force the use of the non-bool version - yay!
                    action.triggered[()].connect(lambda f=highest_publish_file: self._on_show_in_shotgun_action_triggered(f))
                    item.addAction(action)

                # build context menu for all publish versions:                
                published_versions = [f.version for f in files.values() if f.is_published and isinstance(f.version, int)]
                if published_versions:
                    
                    published_versions.sort(reverse=True)
                    
                    publishes_action = QtGui.QAction("Open Publish Read-Only", item)
                    publishes_sm = QtGui.QMenu(item)
                    publishes_action.setMenu(publishes_sm)
                    item.addAction(publishes_action)    
                     
                    for v in published_versions[:20]:
                        f = files[v]
                        msg = ("v%03d" % f.version)
                        action = QtGui.QAction(msg, publishes_sm)
                        # see above for explanation of [()] syntax in action.triggered[()].connect...
                        action.triggered[()].connect(lambda f=f: self._on_open_publish_action_triggered(f))
                        publishes_sm.addAction(action)
                     
                # build context menu for all work files:
                wf_versions = [f.version for f in files.values() if f.is_local and isinstance(f.version, int)]
                if wf_versions:
                    
                    wf_versions.sort(reverse=True)
                    
                    wf_action = QtGui.QAction("Open Work File", item)
                    wf_sm = QtGui.QMenu(item)
                    wf_action.setMenu(wf_sm)
                    item.addAction(wf_action)    
                     
                    for v in wf_versions[:20]:
                        f = files[v]
                        msg = ("v%03d" % f.version)
                        action = QtGui.QAction(msg, wf_sm)
                        # see above for explanation of [()] syntax in action.triggered[()].connect...
                        action.triggered[()].connect(lambda f=f: self._on_open_workfile_action_triggered(f))
                        wf_sm.addAction(action)                

    def _update_title(self):
        """
        Update the list title depending on the mode
        """
        if not self._current_filter:
            return
        self.set_label(self._current_filter.list_title)
                               
    def _add_file_item(self, latest_published_file, latest_work_file):
        """
        Add an item to the file list given the latest publish & work files
        
        :param latest_published_file:    The latest published version of the file to be added
        :param latest_work_file:         The latest work/local version of the file to be added
        """
        details = ""
        tooltip = ""
                   
        # colours for item titles:
        red = "rgb(200, 84, 74)"
        green = "rgb(145, 206, 95)"
        
        current_mode = self._current_filter.mode
        
        file = None
        editable = True
        not_editable_reason = ""
        if current_mode == FileFilter.WORKFILES_MODE:
            file = latest_work_file
            
            title_colour = None
            if latest_published_file:
                if file.compare_with_publish(latest_published_file) >= 0:
                    # work file is most recent
                    title_colour = green
                    tooltip += "This is the latest version of this file"
                else:
                    # published file is most recent
                    title_colour = red
                    tooltip += "<b>A more recent published version of this file is available:</b>"
                    tooltip += "<br>"
                    tooltip += ("<br><b>Version v%03d</b>" % latest_published_file.version)
                    tooltip += "<br>" + latest_published_file.format_published_by_details()
                    tooltip += "<br>"
                    tooltip += "<br><b>Description:</b>"
                    tooltip += "<br>" + latest_published_file.format_publish_description()
            else:
                tooltip += "This file has never been published"

            if file.version is not None:
                details = "<b>%s, v%03d</b>" % (file.name, file.version)
            else:
                details = "<b>%s</b>" % (file.name)
            if title_colour:    
                details = "<span style='color:%s'>%s</span>" % (title_colour, details)
            details += "<br>" + file.format_modified_by_details()
            
            editable = file.editable
            not_editable_reason = file.not_editable_reason
                
        elif current_mode == FileFilter.PUBLISHES_MODE:
            file = latest_published_file
            
            title_colour = None
            tooltip += "<b>Description:</b>"
            tooltip += "<br>" + file.format_publish_description()
            
            tooltip += "<hr>"
            if latest_work_file:
                if latest_work_file.compare_with_publish(file) <= 0:
                    # published file is most recent
                    title_colour = green
                    tooltip += "This is the latest version of this file"
                else:
                    # work file is most recent
                    #title_colour = red
                    tooltip += "<b>A more recent version of this file was found in your work area:</b>"
                    tooltip += "<br>"
                    #tooltip += "<br><b>Details:</b>"
                    tooltip += ("<br><b>Version v%03d</b>" % latest_work_file.version)
                    
                    tooltip += "<br>" + latest_work_file.format_modified_by_details()
            else:
                title_colour = green
                tooltip += "This is the latest version of this file"
            
            details = "<b>%s, v%03d</b>" % (file.name, file.version)
            if title_colour:    
                details = "<span style='color:%s'>%s</span>" % (title_colour, details)
            
            details += "<br>" + file.format_published_by_details()
            
            editable = file.editable
            not_editable_reason = file.not_editable_reason
        else:
            raise TankError("Display mode is not recognised!")
            
        # update editable info on the tooltip
        if not editable:
            tooltip += "<hr>"   
            tooltip += "Read-only: " + not_editable_reason
        
        # add item:
        item = self.add_item(FileItemForm) 
        item.published_file = latest_published_file
        item.work_file = latest_work_file

        # set tool tip
        item.setToolTip(tooltip)
        
        # build and set details string:
        item.set_details(details)
        
        item.set_is_editable(editable, not_editable_reason)
        
        return item
                   
    def _on_open_workfile_action_triggered(self, file):
        """
        Open action triggered from context menu
        """
        self.open_previous_workfile.emit(file)

    def _on_open_publish_action_triggered(self, file):
        """
        Open action triggered from context menu
        """
        self.open_previous_publish.emit(file)

    def _on_show_in_shotgun_action_triggered(self, file):
        """
        Show in Shotgun action triggered from context menu
        """
        self.view_in_shotgun.emit(file)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            