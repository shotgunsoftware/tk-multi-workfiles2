# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Unit tests for the EntityTreeProxyModel class.
"""

from tank_test.tank_test_base import setUpModule  # noqa
from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa

from unittest.mock import Mock


class TestEntityTreeProxyModel(Workfiles2TestBase):
    """
    Test the EntityTreeProxyModel class to ensure proper sorting behavior.
    """

    def setUp(self):
        """
        Set up the test fixtures.
        """
        super().setUp()

        # Import QtCore after engine is started (Qt modules aren't available until then)
        from sgtk.platform.qt import QtCore

        self.QtCore = QtCore

        # Import the class we need to test
        self.EntityTreeProxyModel = (
            self.tk_multi_workfiles.entity_tree.entity_tree_proxy_model.EntityTreeProxyModel
        )

    def test_init_sets_case_insensitive_sorting(self):
        """
        Test that __init__ sets case insensitive sorting.
        """
        # Create the proxy model (parent=None is valid for Qt objects)
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Verify case insensitive sorting is set
        self.assertEqual(
            proxy_model.sortCaseSensitivity(), self.QtCore.Qt.CaseInsensitive
        )
        self.assertFalse(proxy_model._only_show_my_tasks)

    def test_setSourceModel_with_my_tasks_model_does_not_enable_sorting(self):
        """
        Test that setSourceModel does NOT enable automatic sorting for MyTasksModel.
        """
        # Create the proxy model
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Import the actual MyTasksModel class
        MyTasksModel = self.tk_multi_workfiles.my_tasks.my_tasks_model.MyTasksModel

        # Create a mock that is an instance of MyTasksModel
        mock_my_tasks_model = Mock(spec=MyTasksModel)

        # Set the source model
        proxy_model.setSourceModel(mock_my_tasks_model)

        # Verify that dynamic sorting was NOT enabled (should remain False by default)
        self.assertFalse(proxy_model.dynamicSortFilter())

    def test_setSourceModel_with_entity_model_enables_sorting(self):
        """
        Test that setSourceModel enables automatic sorting for non-MyTasksModel (Assets/Shots).
        """
        # Create the proxy model
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Create a mock entity model (not MyTasksModel)
        mock_entity_model = Mock()

        # Set the source model
        proxy_model.setSourceModel(mock_entity_model)

        # Verify that dynamic sorting WAS enabled
        self.assertTrue(proxy_model.dynamicSortFilter())
        # Verify the sort order is ascending
        self.assertEqual(proxy_model.sortOrder(), self.QtCore.Qt.AscendingOrder)

    def test_setSourceModel_with_none_does_nothing(self):
        """
        Test that setSourceModel handles None gracefully.
        """
        # Create the proxy model
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Set source model to None (should not crash)
        proxy_model.setSourceModel(None)

        # Dynamic sorting should remain disabled
        self.assertFalse(proxy_model.dynamicSortFilter())

    def test_only_show_my_tasks_property_getter(self):
        """
        Test the only_show_my_tasks property getter.
        """
        # Create the proxy model
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Initial value should be False
        self.assertFalse(proxy_model.only_show_my_tasks)

    def test_only_show_my_tasks_property_setter_triggers_invalidation(self):
        """
        Test the only_show_my_tasks property setter triggers proper model updates.
        """
        # Create the proxy model
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Create a mock source model
        mock_source_model = Mock()
        mock_source_model.ensure_data_is_loaded = Mock()
        proxy_model.setSourceModel(mock_source_model)

        # Set to True
        proxy_model.only_show_my_tasks = True

        # Verify it was set
        self.assertTrue(proxy_model.only_show_my_tasks)
        # Verify ensure_data_is_loaded was called
        mock_source_model.ensure_data_is_loaded.assert_called_once()

    def test_only_show_my_tasks_property_setter_no_change_does_not_invalidate(self):
        """
        Test that setting only_show_my_tasks to the same value doesn't trigger updates.
        """
        # Create the proxy model
        proxy_model = self.EntityTreeProxyModel(None, None)

        # Create a mock source model
        mock_source_model = Mock()
        mock_source_model.ensure_data_is_loaded = Mock()
        proxy_model.setSourceModel(mock_source_model)

        # Set to True first time
        proxy_model.only_show_my_tasks = True
        mock_source_model.ensure_data_is_loaded.reset_mock()

        # Setting to the same value should not call ensure_data_is_loaded again
        proxy_model.only_show_my_tasks = True
        mock_source_model.ensure_data_is_loaded.assert_not_called()
