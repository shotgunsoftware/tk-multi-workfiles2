

import sgtk
from sgtk.platform.qt import QtGui

from .ui.crash_dbg_form import Ui_CrashDbgForm

import threading
import random
import time

class SgRunner(threading.Thread):
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
        res = {}
        while True:
            self._lock.acquire()
            try:
                if not self._run:
                    break
            finally:
                self._lock.release()

            """
            s = []
            for tick in range(512):
                time.sleep(0.001)
                multiplier = random.randint(1, 8)
                for i in range(8*multiplier):
                    s.append(tick*i)
            time.sleep(2)
            res = dict((i, c) for i, c in enumerate(s))
            """
            sg_search = self._sg_searches[random.randint(0, len(self._sg_searches)-1)]
            res = self._shotgun.find(sg_search["entity_type"], 
                                     sg_search["filters"],
                                     sg_search["fields"],
                                     sg_search["order"])
        print len(res)

class CrashDbgForm(QtGui.QWidget):
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
        self._ui = Ui_CrashDbgForm()
        self._ui.setupUi(self)

        refresh_action = QtGui.QAction("Refresh", self)
        refresh_action.setShortcut(QtGui.QKeySequence(QtGui.QKeySequence.Refresh))
        refresh_action.triggered.connect(self._on_refresh_triggered)
        self.addAction(refresh_action)

        # create model:
        self._model = QtGui.QStandardItemModel()
        self._ui.tree_view.setModel(self._model)
        self._ui.list_view.setModel(self._model)

        # create sg query threads:
        self._sg_runner_threads = []
        self._sg_runner_threads.append(SgRunner())
        self._sg_runner_threads.append(SgRunner())
        self._sg_runner_threads.append(SgRunner())
        for thread in self._sg_runner_threads:
            thread.start()

    def closeEvent(self, event):
        """
        """
        for thread in self._sg_runner_threads:
            print "Stopping sg runner thread..."
            thread.stop()
            thread.join()
            print " > Stopped!"

        if self._model:
            self._model.deleteLater()
            self._model = None

        return QtGui.QWidget.closeEvent(self, event)
        
        
    def _on_refresh_triggered(self):
        """
        """
        #time.sleep(0.1)
        self._model.clear()
        self._repopulate_model()
        self._repopulate_model()
        self._repopulate_model()
        
        
    def _update_groups(self, group_names):
        """
        """
        new_items = []
        for name in group_names:
            group_item = QtGui.QStandardItem(name)
            new_items.append(group_item)

        if new_items:
            self._model.invisibleRootItem().appendRows(new_items)
    
    def _add_group(self, group_name):
        """
        """
        group_item = QtGui.QStandardItem(group_name)
        self._model.invisibleRootItem().appendRow(group_item)
        return group_item
    
    def _add_files(self, group_item, file_names):
        """
        """
        new_items = []
        for name in file_names:
            item = QtGui.QStandardItem(name)
            new_items.append(item)

        if new_items:
            group_item.appendRows(new_items)

    def _repopulate_model(self):
        """
        """
        search_id = random.randint(0, 19)
        if search_id == 0:
            self._update_groups(["Sequence 01"])
        elif search_id == 1:
            self._update_groups(["123", "Anm - Animation"])
            grp = self._add_group("Anm - Animation")
            self._add_files(grp, ["reviewtest", "reviewtest", "reviewtest", "reviewtest", "launchtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "crashtest", "shouldbreak", "reviewtest", "scene", "reviewtest", "reviewtest"])
        elif search_id == 2:
            self._update_groups(["Anm", "Anm - Animation"])
            grp = self._add_group("Anm - Animation")
            self._add_files(grp, ["reviewtest", "reviewtest", "reviewtest", "reviewtest", "launchtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "crashtest", "shouldbreak", "reviewtest", "scene", "reviewtest", "reviewtest"])
        elif search_id == 3:
            self._update_groups(["Animation"])
            grp = self._add_group("Animation")
            self._add_files(grp, ["reviewtest", "reviewtest", "reviewtest", "reviewtest", "launchtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "crashtest", "shouldbreak", "reviewtest", "scene", "reviewtest", "reviewtest"])
        elif search_id == 4:
            self._update_groups(["shot_010", "Anm - Animation", "Comp - MoreComp", "FX - Effects", "FX - More FX", "Light - EvenMoreLighting", "Light - Lighting", "Light - MoreLighting", "Light - StillMoreLighting", "Light - YetMoreLighting", "More Anim - MoreAnim", "Roto - Roto"])
            grp = self._add_group("Comp - MoreComp")
            self._add_files(grp, ["nopublishes"])
            grp = self._add_group("Light - EvenMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - Lighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - MoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - StillMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - YetMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 5:
            self._update_groups(["Anm", "Anm - Animation"])
        elif search_id == 6:
            self._update_groups(["Animation"])
        elif search_id == 7:
            self._update_groups(["Comp", "Comp - MoreComp"])
            grp = self._add_group("Comp - MoreComp")
            self._add_files(grp, ["nopublishes"])
        elif search_id == 8:
            self._update_groups(["FX", "FX - Effects", "FX - More FX"])
        elif search_id == 9:
            self._update_groups(["Light", "Light - EvenMoreLighting", "Light - Lighting", "Light - MoreLighting", "Light - StillMoreLighting", "Light - YetMoreLighting"])
            grp = self._add_group("Light - EvenMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - Lighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - MoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - StillMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
            grp = self._add_group("Light - YetMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 10:
            self._update_groups(["EvenMoreLighting"])
            grp = self._add_group("EvenMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 11:
            self._update_groups(["Lighting"])
            grp = self._add_group("Lighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 12:
            self._update_groups(["MoreLighting"])
            grp = self._add_group("MoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 13:
            self._update_groups(["StillMoreLighting"])
            grp = self._add_group("StillMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 14:
            self._update_groups(["YetMoreLighting"])
            grp = self._add_group("YetMoreLighting")
            self._add_files(grp, ["testscene", "writenodetestBAD", "writenodeconversiontest", "scene", "writenodetest", "osxreviewtest", "writenodeconversiontestb", "testscene", "sendtoreviewtest", "osxreviewtest", "testscene", "writenodeconversiontest", "testscene", "writenodetestBAD", "sendtoreviewtest", "writenodeconversiontest", "scene1", "writenodeconversiontest"])
        elif search_id == 15:
            self._update_groups(["More Anim", "More Anim - MoreAnim"])
        elif search_id == 16:
            self._update_groups(["Roto", "Roto - Roto"])
        elif search_id == 17:
            self._update_groups(["shot_020", "Light - Lighting"])
        elif search_id == 18:
            self._update_groups(["Light", "Light - Lighting"])
        elif search_id == 19:
            self._update_groups(["The End", "Anm - Animation", "Anm - Animation B", "Comp - Finalize"])
            grp = self._add_group("Anm - Animation")
            self._add_files(grp, ["reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "testscene", "writenodeconversiontest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "scene", "scene", "reviewtest", "sendtoreviewtest", "testscene", "shouldbreak", "reviewtest", "writenodeconversiontest", "reviewtest", "launchtest", "writenodetest", "writenodeconversiontestb", "osxreviewtest", "crashtest", "reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "sendtoreviewtest", "testscene", "nopublishes", "reviewtest", "reviewtest", "osxreviewtest", "testscene", "scene1"])
            grp = self._add_group("Anm - Animation B")
            self._add_files(grp, ["reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "testscene", "writenodeconversiontest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "scene", "scene", "reviewtest", "sendtoreviewtest", "testscene", "shouldbreak", "reviewtest", "writenodeconversiontest", "reviewtest", "launchtest", "writenodetest", "writenodeconversiontestb", "osxreviewtest", "crashtest", "reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "sendtoreviewtest", "testscene", "nopublishes", "reviewtest", "reviewtest", "osxreviewtest", "testscene", "scene1"])
            grp = self._add_group("Comp - Finalize")
            self._add_files(grp, ["reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "testscene", "writenodeconversiontest", "reviewtest", "reviewtest", "reviewtest", "colourspacetest", "scene", "scene", "reviewtest", "sendtoreviewtest", "testscene", "shouldbreak", "reviewtest", "writenodeconversiontest", "reviewtest", "launchtest", "writenodetest", "writenodeconversiontestb", "osxreviewtest", "crashtest", "reviewtest", "writenodetestBAD", "writenodeconversiontest", "reviewtest", "sendtoreviewtest", "testscene", "nopublishes", "reviewtest", "reviewtest", "osxreviewtest", "testscene", "scene1"])



        
        
        
        
        
        
        