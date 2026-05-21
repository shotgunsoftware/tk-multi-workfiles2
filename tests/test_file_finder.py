# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from unittest.mock import MagicMock, patch

from tank_test.tank_test_base import setUpModule  # noqa
from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa

from sgtk import TankError


class TestReconcileFilesystemForContext(Workfiles2TestBase):
    """Tests for FileFinder._reconcile_filesystem_for_context."""

    def setUp(self):
        super().setUp()
        FileFinder = self.tk_multi_workfiles.file_finder.FileFinder
        self._finder = FileFinder()

    def tearDown(self):
        self._finder = None
        super().tearDown()

    def test_returns_false_when_context_has_no_entity(self):
        """Return False when context has no task, entity, or project."""
        ctx = MagicMock()
        ctx.task = None
        ctx.entity = None
        ctx.project = None

        result = self._finder._reconcile_filesystem_for_context(ctx)

        self.assertFalse(result)

    def test_returns_true_on_successful_create_filesystem_structure(self):
        """Return True when create_filesystem_structure succeeds."""
        ctx = MagicMock()
        ctx.task = {"type": "Task", "id": 1}
        ctx.entity = None
        ctx.project = None

        with patch.object(
            self._finder._app.sgtk, "create_filesystem_structure"
        ) as mock_cfs:
            result = self._finder._reconcile_filesystem_for_context(ctx)

        self.assertTrue(result)

    def test_passes_correct_args_to_create_filesystem_structure(self):
        """Forward entity type, id, and engine name to create_filesystem_structure."""
        ctx = MagicMock()
        ctx.task = {"type": "Task", "id": 42}
        ctx.entity = None
        ctx.project = None

        with patch.object(
            self._finder._app.sgtk, "create_filesystem_structure"
        ) as mock_cfs:
            self._finder._reconcile_filesystem_for_context(ctx)

        mock_cfs.assert_called_once_with(
            "Task", 42, engine=self._finder._app.engine.instance_name
        )

    def test_uses_entity_when_task_is_none(self):
        """Fall back to context.entity when task is None."""
        ctx = MagicMock()
        ctx.task = None
        ctx.entity = {"type": "Asset", "id": 7}
        ctx.project = None

        with patch.object(
            self._finder._app.sgtk, "create_filesystem_structure"
        ) as mock_cfs:
            result = self._finder._reconcile_filesystem_for_context(ctx)

        mock_cfs.assert_called_once_with(
            "Asset", 7, engine=self._finder._app.engine.instance_name
        )
        self.assertTrue(result)

    def test_uses_project_when_task_and_entity_are_none(self):
        """Fall back to context.project when both task and entity are None."""
        ctx = MagicMock()
        ctx.task = None
        ctx.entity = None
        ctx.project = {"type": "Project", "id": 3}

        with patch.object(
            self._finder._app.sgtk, "create_filesystem_structure"
        ) as mock_cfs:
            result = self._finder._reconcile_filesystem_for_context(ctx)

        mock_cfs.assert_called_once_with(
            "Project", 3, engine=self._finder._app.engine.instance_name
        )
        self.assertTrue(result)

    def test_returns_false_and_logs_warning_on_exception(self):
        """Return False and log a warning when create_filesystem_structure raises."""
        ctx = MagicMock()
        ctx.task = {"type": "Task", "id": 1}
        ctx.entity = None
        ctx.project = None

        with patch.object(
            self._finder._app.sgtk,
            "create_filesystem_structure",
            side_effect=Exception("disk error"),
        ):
            with patch.object(self._finder._app, "log_warning") as mock_warn:
                result = self._finder._reconcile_filesystem_for_context(ctx)

        self.assertFalse(result)
        mock_warn.assert_called_once()


class TestFindWorkFilesReconcile(Workfiles2TestBase):
    """Tests for the reconcile-retry logic in FileFinder._find_work_files."""

    def setUp(self):
        super().setUp()
        FileFinder = self.tk_multi_workfiles.file_finder.FileFinder
        self._finder = FileFinder()

    def tearDown(self):
        self._finder = None
        super().tearDown()

    def test_first_call_succeeds_no_reconcile(self):
        """Return files normally when as_template_fields succeeds on the first call."""
        ctx = MagicMock()
        ctx.as_template_fields.return_value = {}

        with patch.object(
            self._finder._app.sgtk,
            "paths_from_template",
            return_value=["/a/b.ma"],
        ):
            with patch.object(
                self._finder._app.sgtk, "create_filesystem_structure"
            ) as mock_cfs:
                result = self._finder._find_work_files(ctx, self.work_template, [])

        self.assertEqual(result, ["/a/b.ma"])
        mock_cfs.assert_not_called()

    def test_reconcile_returns_false_returns_empty_list(self):
        """Return [] when first as_template_fields raises and reconcile returns False."""
        ctx = MagicMock()
        ctx.as_template_fields.side_effect = TankError("stale")

        with patch.object(
            self._finder,
            "_reconcile_filesystem_for_context",
            return_value=False,
        ):
            result = self._finder._find_work_files(ctx, self.work_template, [])

        self.assertEqual(result, [])

    def test_reconcile_succeeds_retry_succeeds_returns_files(self):
        """Return files when reconcile succeeds and the retry resolves fields."""
        ctx = MagicMock()
        ctx.as_template_fields.side_effect = [TankError("first"), {}]

        with patch.object(
            self._finder,
            "_reconcile_filesystem_for_context",
            return_value=True,
        ):
            with patch.object(
                self._finder._app.sgtk,
                "paths_from_template",
                return_value=["/c/d.ma"],
            ):
                result = self._finder._find_work_files(ctx, self.work_template, [])

        self.assertEqual(result, ["/c/d.ma"])

    def test_reconcile_succeeds_retry_raises_tank_error_logs_and_returns_empty(self):
        """Return [] and log debug when reconcile succeeds but retry still raises TankError."""
        ctx = MagicMock()
        ctx.as_template_fields.side_effect = [TankError("first"), TankError("second")]

        with patch.object(
            self._finder,
            "_reconcile_filesystem_for_context",
            return_value=True,
        ):
            with patch.object(self._finder._app, "log_debug") as mock_debug:
                result = self._finder._find_work_files(ctx, self.work_template, [])

        self.assertEqual(result, [])
        mock_debug.assert_called_once()
