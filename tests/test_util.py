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
Unit tests for utility functions in tk_multi_workfiles.util module.
"""

from tank_test.tank_test_base import setUpModule  # noqa
from workfiles2_test_base import Workfiles2TestBase
from workfiles2_test_base import tearDownModule  # noqa


class TestCreateCaseInsensitiveRegex(Workfiles2TestBase):
    """
    Tests for the create_case_insensitive_regex utility function.
    """

    def setUp(self):
        """
        Set up the test fixtures.
        """
        super().setUp()

        # Import QtCore after engine is started (Qt modules aren't available until then)
        from sgtk.platform.qt import QtCore

        self.QtCore = QtCore

        # Use the engine's has_qt6 property - same detection used by the production code
        import sgtk

        engine = sgtk.platform.current_engine()
        self.is_qt6 = engine.has_qt6

        # Get the function from the imported module
        self.create_case_insensitive_regex = (
            self.tk_multi_workfiles.util.create_case_insensitive_regex
        )

    def test_returns_valid_regex_object(self):
        """
        Test that the function returns a valid regex object based on Qt version.
        """
        result = self.create_case_insensitive_regex("test")

        # Qt6+ should return QRegularExpression, Qt5 should return QRegExp
        if self.is_qt6:
            self.assertIsInstance(result, self.QtCore.QRegularExpression)
        else:
            self.assertIsInstance(result, self.QtCore.QRegExp)

    def test_case_insensitive_matching_lowercase_pattern(self):
        """
        Test that the regex matches case-insensitively with a lowercase pattern.
        """
        regex = self.create_case_insensitive_regex("cat")

        # Test matching - should match regardless of case
        if self.is_qt6:
            # PySide6/QRegularExpression
            self.assertTrue(regex.match("cat").hasMatch())
            self.assertTrue(regex.match("Cat").hasMatch())
            self.assertTrue(regex.match("CAT").hasMatch())
            self.assertTrue(regex.match("cAt").hasMatch())
        else:
            # PySide2/QRegExp
            self.assertTrue(regex.exactMatch("cat"))
            self.assertTrue(regex.exactMatch("Cat"))
            self.assertTrue(regex.exactMatch("CAT"))
            self.assertTrue(regex.exactMatch("cAt"))

    def test_case_insensitive_matching_uppercase_pattern(self):
        """
        Test that the regex matches case-insensitively with an uppercase pattern.
        """
        regex = self.create_case_insensitive_regex("CAT")

        # Test matching - should match regardless of case
        if self.is_qt6:
            # PySide6/QRegularExpression
            self.assertTrue(regex.match("cat").hasMatch())
            self.assertTrue(regex.match("Cat").hasMatch())
            self.assertTrue(regex.match("CAT").hasMatch())
        else:
            # PySide2/QRegExp
            self.assertTrue(regex.exactMatch("cat"))
            self.assertTrue(regex.exactMatch("Cat"))
            self.assertTrue(regex.exactMatch("CAT"))

    def test_case_insensitive_matching_mixed_case_pattern(self):
        """
        Test that the regex matches case-insensitively with a mixed-case pattern.
        """
        regex = self.create_case_insensitive_regex("CaT")

        # Test matching - should match regardless of case
        if self.is_qt6:
            # PySide6/QRegularExpression
            self.assertTrue(regex.match("cat").hasMatch())
            self.assertTrue(regex.match("CAT").hasMatch())
            self.assertTrue(regex.match("CaT").hasMatch())
        else:
            # PySide2/QRegExp
            self.assertTrue(regex.exactMatch("cat"))
            self.assertTrue(regex.exactMatch("CAT"))
            self.assertTrue(regex.exactMatch("CaT"))

    def test_empty_pattern(self):
        """
        Test that the function handles an empty pattern.
        """
        regex = self.create_case_insensitive_regex("")

        # Empty pattern should be valid
        if self.is_qt6:
            self.assertIsInstance(regex, self.QtCore.QRegularExpression)
            self.assertTrue(regex.isValid())
        else:
            self.assertIsInstance(regex, self.QtCore.QRegExp)
            self.assertTrue(regex.isValid())

    def test_pattern_with_spaces(self):
        """
        Test that the regex handles patterns with spaces correctly.
        """
        regex = self.create_case_insensitive_regex("my asset")

        if self.is_qt6:
            self.assertTrue(regex.match("my asset").hasMatch())
            self.assertTrue(regex.match("My Asset").hasMatch())
            self.assertTrue(regex.match("MY ASSET").hasMatch())
        else:
            self.assertTrue(regex.exactMatch("my asset"))
            self.assertTrue(regex.exactMatch("My Asset"))
            self.assertTrue(regex.exactMatch("MY ASSET"))

    def test_pattern_preserved(self):
        """
        Test that the original pattern is preserved in the regex.
        """
        pattern = "TestPattern"
        regex = self.create_case_insensitive_regex(pattern)

        if self.is_qt6:
            self.assertEqual(regex.pattern(), pattern)
        else:
            self.assertEqual(regex.pattern(), pattern)

    def test_case_insensitive_option_is_set_qt6(self):
        """
        Test that CaseInsensitiveOption is set for Qt6/QRegularExpression.
        """
        if not self.is_qt6:
            self.skipTest("Test only applicable to Qt6+ environment")

        regex = self.create_case_insensitive_regex("test")

        # Check that CaseInsensitiveOption is set
        options = regex.patternOptions()
        self.assertTrue(
            options & self.QtCore.QRegularExpression.CaseInsensitiveOption,
            "CaseInsensitiveOption should be set for QRegularExpression",
        )

    def test_case_sensitivity_qt5(self):
        """
        Test that case sensitivity is set correctly for Qt5/QRegExp.
        """
        if self.is_qt6:
            self.skipTest("Test only applicable to Qt5 environment")

        regex = self.create_case_insensitive_regex("test")

        # Check case sensitivity setting
        self.assertEqual(
            regex.caseSensitivity(),
            self.QtCore.Qt.CaseInsensitive,
            "QRegExp should be case insensitive",
        )
