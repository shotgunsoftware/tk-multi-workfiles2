#!/usr/bin/env bash
# 
# Copyright (c) 2008 Shotgun Software, Inc
# ----------------------------------------------------

echo "building user interfaces..."
pyside-uic --from-imports select_work_area_form.ui > ../python/tk_multi_workfiles/ui/select_work_area_form.py
pyside-uic --from-imports work_files_form.ui > ../python/tk_multi_workfiles/ui/work_files_form.py

pyside-uic --from-imports change_version_form.ui > ../python/tk_multi_workfiles/ui/change_version_form.py
pyside-uic --from-imports save_as_form.ui > ../python/tk_multi_workfiles/ui/save_as_form.py

echo "building resources..."
pyside-rcc resources.qrc > ../python/tk_multi_workfiles/ui/resources_rc.py
