# Copyright (c) 2015 Shotgun Software Inc.
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
from sgtk import TankError

import random
import time
import gc

import resource
from .sg_published_files_model import SgPublishedFilesModel
shotgun_data = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_data")
BackgroundTaskManager = shotgun_data.BackgroundTaskManager

import threading
from .file_model import FileModel

def monitor_lifetime(obj):
    obj.destroyed.connect(lambda: on_destroyed(type(obj).__name__))

def on_destroyed(name):
    print "%s destroyed" % name

class SignalWait(QtCore.QObject):

    def __init__(self, count=1):
        QtCore.QObject.__init__(self)
        self._count=count
        self._loop = QtCore.QEventLoop(self)
        monitor_lifetime(self._loop)

    def wait(self):
        if self._count > 0:
            self._loop.exec_()

    def finish(self):
        self._count -= 1
        print "Finish count: %d" % self._count
        if self._count == 0:
            self._loop.exit()


class WorkFiles(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)

    @staticmethod
    def show_file_open_dlg():
        """
        """
        handler = WorkFiles()
        handler._show_file_open_dlg()

    @staticmethod
    def show_file_save_dlg():
        """
        """
        handler = WorkFiles()
        handler._show_file_save_dlg()

    @staticmethod
    def run_crash_test():
        handler = WorkFiles()
        handler._run_crash_test()

    def _show_file_open_dlg(self):
        """
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_open_form import FileOpenForm
            #app.engine.show_dialog("File Open", app, FileOpenForm)
            app.engine.show_modal("File Open", app, FileOpenForm)
        except:
            app.log_exception("Failed to create File Open dialog!")
            return

    def _show_file_save_dlg(self):
        """
        """
        app = sgtk.platform.current_bundle()
        try:
            from .file_save_form import FileSaveForm
            res, file_save_ui = app.engine.show_modal("File Save", app, FileSaveForm)
        except:
            app.log_exception("Failed to create File Save dialog!")
            return

    def _run_crash_test(self):
        """
        """
        num_objects_before = len(gc.get_objects())
        bytes_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0

        self._run_simple_test()
        #self._run_sg_model_test()
        #self._run_test_THREADS()
        
        gc.collect()

        bytes_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0/1024.0
        num_objects_after = len(gc.get_objects())
        
        bytes_diff = bytes_after - bytes_before
        obj_diff = num_objects_after - num_objects_before
        
        print ("Memory before: %0.2fMb, current: %0.2fMb, leaked: %0.2fMb (%d new Python objects)" 
                % (bytes_before, bytes_after, bytes_diff, obj_diff))

    def _run_simple_test(self):
        """
        """
        dummy_search_details = []
        dummy_search_details.append([{'is_leaf': False, 'name': 'Sequence 01', 'child_entities': [{'name': '123', 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}}, {'name': 'shot_010', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}}, {'name': 'shot_020', 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}}, {'name': 'The End', 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}}, {'name': '\xd0\xa0\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xd0\xb8 \xd0\xb2\xd1\x8b\xd1\x81\xd1\x82\xd1\x80\xd0\xb5\xd0\xbb\xd0\xb0', 'entity': {'type': 'Shot', 'id': 916, 'name': '\xd0\xa0\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xd0\xb8 \xd0\xb2\xd1\x8b\xd1\x81\xd1\x82\xd1\x80\xd0\xb5\xd0\xbb\xd0\xb0'}}], 'entity': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}}])
        dummy_search_details.append([{'is_leaf': False, 'name': '123', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 230}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Anm', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 230}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 914, 'name': '123'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 230}}])
        dummy_search_details.append([{'is_leaf': False, 'name': 'shot_010', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 178}}, {'is_leaf': True, 'name': 'Comp - MoreComp', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreComp', 'step': {'type': 'Step', 'id': 8, 'name': 'Comp'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 233}}, {'is_leaf': True, 'name': 'FX - Effects', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Effects', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 235}}, {'is_leaf': True, 'name': 'FX - More FX', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'More FX', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 243}}, {'is_leaf': True, 'name': 'Light - EvenMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'EvenMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 252}}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/b84f1f336e085adf634588b1e5dbdbb073ae0f52/199e51cb1f23779739ad03503396843f7fdf1db0/Screen_Shot_2014-12-08_at_11.49.18_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1435962178&Signature=hMIG76Ejcba5Fxk3zZR4qOCes1s%3D', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 232}}, {'is_leaf': True, 'name': 'Light - MoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 242}}, {'is_leaf': True, 'name': 'Light - StillMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'StillMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 253}}, {'is_leaf': True, 'name': 'Light - YetMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'YetMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 251}}, {'is_leaf': True, 'name': 'More Anim - MoreAnim', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreAnim', 'step': {'type': 'Step', 'id': 17, 'name': 'More Anim'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 255}}, {'is_leaf': True, 'name': 'Roto - Roto', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Roto', 'step': {'type': 'Step', 'id': 3, 'name': 'Roto'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 254}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Anm', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 178}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 178}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Comp', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Comp - MoreComp', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreComp', 'step': {'type': 'Step', 'id': 8, 'name': 'Comp'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 233}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'FX', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'FX - Effects', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Effects', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 235}}, {'is_leaf': True, 'name': 'FX - More FX', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'More FX', 'step': {'type': 'Step', 'id': 6, 'name': 'FX'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 243}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Light', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Light - EvenMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'EvenMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 252}}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/b84f1f336e085adf634588b1e5dbdbb073ae0f52/199e51cb1f23779739ad03503396843f7fdf1db0/Screen_Shot_2014-12-08_at_11.49.18_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1435962178&Signature=hMIG76Ejcba5Fxk3zZR4qOCes1s%3D', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 232}}, {'is_leaf': True, 'name': 'Light - MoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 242}}, {'is_leaf': True, 'name': 'Light - StillMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'StillMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 253}}, {'is_leaf': True, 'name': 'Light - YetMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'YetMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 251}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'EvenMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'EvenMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 252}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': 'https://sg-media-usor-01.s3.amazonaws.com/b84f1f336e085adf634588b1e5dbdbb073ae0f52/199e51cb1f23779739ad03503396843f7fdf1db0/Screen_Shot_2014-12-08_at_11.49.18_t.jpg?AWSAccessKeyId=AKIAIFHY52V77FIVWKLQ&Expires=1435962178&Signature=hMIG76Ejcba5Fxk3zZR4qOCes1s%3D', 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}, {'type': 'HumanUser', 'id': 40, 'name': 'Tank Experimentation'}], 'type': 'Task', 'id': 232}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'MoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 242}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'StillMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'StillMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 253}}])
        dummy_search_details.append([{'is_leaf': True, 'name': 'YetMoreLighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'YetMoreLighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'ip', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 251}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'More Anim', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'More Anim - MoreAnim', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'MoreAnim', 'step': {'type': 'Step', 'id': 17, 'name': 'More Anim'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 255}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Roto', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Roto - Roto', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 874, 'name': 'shot_010'}, 'content': 'Roto', 'step': {'type': 'Step', 'id': 3, 'name': 'Roto'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 254}}])
        dummy_search_details.append([{'is_leaf': False, 'name': 'shot_020', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 244}}])
        dummy_search_details.append([{'is_leaf': None, 'name': 'Light', 'child_entities': [], 'entity': None}, {'is_leaf': True, 'name': 'Light - Lighting', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 918, 'name': 'shot_020'}, 'content': 'Lighting', 'step': {'type': 'Step', 'id': 7, 'name': 'Light'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 244}}])
        dummy_search_details.append([{'is_leaf': False, 'name': 'The End', 'child_entities': [], 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}}, {'is_leaf': True, 'name': 'Anm - Animation', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}, 'content': 'Animation', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 239}}, {'is_leaf': True, 'name': 'Anm - Animation B', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}, 'content': 'Animation B', 'step': {'type': 'Step', 'id': 5, 'name': 'Anm'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 240}}, {'is_leaf': True, 'name': 'Comp - Finalize', 'child_entities': [], 'entity': {'project': {'type': 'Project', 'id': 67, 'name': 'Another Demo Project'}, 'entity.Shot.sg_sequence': {'type': 'Sequence', 'id': 11, 'name': 'Sequence 01'}, 'image': None, 'entity': {'type': 'Shot', 'id': 917, 'name': 'The End'}, 'content': 'Finalize', 'step': {'type': 'Step', 'id': 8, 'name': 'Comp'}, 'sg_status_list': 'wtg', 'task_assignees': [{'type': 'HumanUser', 'id': 42, 'name': 'Alan Dann\xc3\xa9\xc3\xa8\xc3\xaa\xc3\xab\xc4\x97\xc4\x99'}], 'type': 'Task', 'id': 241}}])
        dummy_search = dummy_search_details[random.randint(0, len(dummy_search_details)-1)]

        file_model = FileModel(None, parent=None)

        threads = []
        threads.append(WorkFiles.Runner())
        threads.append(WorkFiles.Runner())
        for thread in threads:
            thread.start()

        #for _ in range(10):
        while True:
            dummy_search = dummy_search_details[random.randint(0, len(dummy_search_details)-1)]

            searches = []
            for ds in dummy_search:
                search = FileModel.SearchDetails(ds["name"])
                search.entity = ds["entity"]
                search.is_leaf = ds["is_leaf"]
                search.child_entities = ds["child_entities"]
                searches.append(search)
    
            file_model.set_entity_searches(searches)
            
        for thread in threads:
            thread.stop()
            thread.join()
            
        file_model.destroy()
        file_model.deleteLater()

    class Runner(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self._lock = threading.Lock()
            self._run = True
            self._sg_searches = [
                {"entity_type":"Task",
                "filters":[['project', 'is', {'type': 'Project', 'name': 'Another Demo Project', 'id': 67}], ['entity', 'type_is', 'Asset']],
                "fields":['project', 'code', 'description', 'image', 'entity.Asset.sg_asset_type', 'entity', 'content', 'step', 'sg_status_list', 'task_assignees', 'name'],
                "order":[]},
                {"entity_type":"Task",
                "filters":[['project', 'is', {'type': 'Project', 'name': 'Another Demo Project', 'id': 67}], ['entity', 'type_is', 'Shot']],
                "fields":['project', 'entity.Shot.sg_sequence', 'code', 'description', 'image', 'entity', 'content', 'step', 'sg_status_list', 'task_assignees', 'name'],
                "order":[]}
                ]
            self._thread_local = threading.local()

        @property
        def _shotgun(self):
            self._lock.acquire()
            try:
                if not hasattr(self._thread_local, "sg"):
                    self._thread_local.sg = sgtk.util.shotgun.create_sg_connection()
                return self._thread_local.sg
            finally:
                self._lock.release()

        def stop(self):
            self._lock.acquire()
            try:
                self._run = False
            finally:
                self._lock.release()
                
        def run(self):
            while True:
                self._lock.acquire()
                try:
                    if not self._run:
                        break
                finally:
                    self._lock.release()

                sg_search = self._sg_searches[random.randint(0, len(self._sg_searches)-1)]
                res = self._shotgun.find(sg_search["entity_type"], 
                                         sg_search["filters"],
                                         sg_search["fields"],
                                         sg_search["order"])


    def _run_sg_model_test(self):
        """
        """
        
        bg_task_manager = BackgroundTaskManager(None, max_threads=16, start_processing=True)
        monitor_lifetime(bg_task_manager)

        num_models = 8
        num_refreshes = 8

        wait = SignalWait(num_models*num_refreshes)#1)
        bg_task_manager.task_group_finished.connect(wait.finish)
        monitor_lifetime(wait)

        models = []
        for i in range(num_models):
            model = self._create_sg_model(i, bg_task_manager)
            model.counter = num_refreshes
            models.append(model)
            model.data_refreshed.connect(self._on_publish_model_refreshed)
            model.data_refresh_fail.connect(self._on_publish_model_refresh_failed)
            model.refresh()
            
        print "%d models created!" % len(models)
        
        wait.wait()
        print "Finished waiting!"
        wait.deleteLater()

        for model in models:
            model.destroy()
            model.deleteLater()

        bg_task_manager.shut_down()
        bg_task_manager.deleteLater()
        print "Everything done!"


    def _run_test_THREADS(self):
        """
        """
        bg_task_manager = BackgroundTaskManager(None, max_threads=32, start_processing=True)
        monitor_lifetime(bg_task_manager)
        
        wait = SignalWait(1)
        monitor_lifetime(wait)
        bg_task_manager.task_group_finished.connect(wait.finish)

        # create a load of tasks:
        task_group = bg_task_manager.next_group_id()
        tasks = []
        for i in range(10):
            #self._do_some_work()
            tasks.append(bg_task_manager.add_task(self._do_some_work, group=task_group))

        if False:
            for i in range(10):
                time.sleep(random.randint(0, 100)/100.0)
                task_to_stop = tasks[random.randint(0, len(tasks))]
                print "Stopping task %d" % task_to_stop 
                bg_task_manager.stop_task(task_to_stop)

        # create some models:
        models = []
        for i in range(8):
            model = self._create_sg_model(i, bg_task_manager)
            model.data_refreshed.connect(wait.finish)
            models.append(model)
            #model.refresh()

        wait.wait()
        print "Finished waiting!"
        
        wait.deleteLater()
        wait = None

        for model in models:
            model.destroy()
            model.deleteLater()
        models = []
        
        bg_task_manager.shut_down()
        bg_task_manager.deleteLater()
        bg_task_manager = None
        print "Everything done!"


    def _create_sg_model(self, uid, bg_task_manager):
        """
        """
        app = sgtk.platform.current_bundle()
        publish_filters = []
        if app.context.entity:
            publish_filters.append(["entity", "is", app.context.entity])
        if app.context.task:
            publish_filters.append(["task", "is", app.context.task])
        elif app.context.step:
            publish_filters.append(["task.Task.step", "is", app.context.step])
        fields = ["id", "description", "version_number", "image", "created_at", "created_by", "name", "path", "task"]

        model = SgPublishedFilesModel(uid, bg_task_manager, parent=None)
        monitor_lifetime(model)
        model.load_data(filters=publish_filters, fields=fields)
        return model


    def _do_some_work(self, **kwargs):
        # sleep for a fraction of a second:
        time.sleep(random.randint(0, 100)/100.0/2.0)
        
        a = [0] * 1000
        
        rects = []
        for i in range(100):
            rects.append(QtCore.QRect(0, 0, 10, 10))
            
        icons = []
        for i in range(100):
            icons.append(QtCore.QIcon())
            
        #for i in range(100):
        #    obj = QObject()
        
        return {"a":a, "rectangles":rects, "icons":icons}
    

    def _on_publish_model_refreshed(self, data_changed):
        """
        """
        model = self.sender()
        print "Model %d [%d] refreshed" % (model.uid, model.counter)
        model.counter -= 1
        if model.counter == 0:
            return

        # wait a random amount of time...
        time.sleep(random.randint(0, 100)/100.0)

        model.refresh()
        
    def _on_publish_model_refresh_failed(self, msg):
        print "REFRESH FAILED: %s" % msg


    #def _get_usersandbox_users(self):
    #    """
    #    Find all available user sandbox users for the 
    #    current work area.
    #    """
    #    if not self._work_area_template:
    #        return
    #    
    #    # find 'user' keys to skip when looking for sandboxes:
    #    user_keys = ["HumanUser"]
    #    for key in self._work_area_template.keys.values():
    #        if key.shotgun_entity_type == "HumanUser":
    #            user_keys.append(key.name)
    #    
    #    # use the fields for the current context to get a list of work area paths:
    #    self._app.log_debug("Searching for user sandbox paths skipping keys: %s" % user_keys)
    #    
    #    try:
    #        fields = self._context.as_template_fields(self._work_area_template)
    #    except TankError:
    #        # fields could not be resolved from the context! This can happen because
    #        # the context does not have any structure on disk / path cache but is a 
    #        # "shotgun-only" context which was created from for example a task.
    #        work_area_paths = []
    #    else:
    #        # got our fields. Now get the paths.
    #        work_area_paths = self._app.sgtk.paths_from_template(self._work_area_template, fields, user_keys)
    #    
    #    # from paths, find a unique list of user ids:
    #    user_ids = set()
    #    for path in work_area_paths:
    #        # to find the user, we have to construct a context
    #        # from the path and then inspect the user from this
    #        path_ctx = self._app.sgtk.context_from_path(path)
    #        user = path_ctx.user
    #        if user: 
    #            user_ids.add(user["id"])
    #    
    #    # look these up in the user cache:
    #    user_details = self._user_cache.get_user_details_for_ids(user_ids)
    #    
    #    # return all valid user details:
    #    return [details for details in user_details.values() if details]

