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


from sgtk.platform.qt import QtCore


class TestCreateCaseInsensitiveRegex(Workfiles2TestBase):
    """
    Tests for the create_case_insensitive_regex utility function.
    """

    def setUp(self):
        """
        Set up the test fixtures.
        """
        super().setUp()

        # Get the function from the imported module
        self.create_case_insensitive_regex = (
            self.tk_multi_workfiles.util.create_case_insensitive_regex
        )

    def test_returns_valid_regex_object(self):
        """
        Test that the function returns a valid regex object.
        """
        result = self.create_case_insensitive_regex("test")

        # Should return either QRegExp or QRegularExpression
        if hasattr(QtCore, "QRegularExpression"):
            self.assertIsInstance(result, QtCore.QRegularExpression)
        else:
            self.assertIsInstance(result, QtCore.QRegExp)

    def test_case_insensitive_matching_lowercase_pattern(self):
        """
        Test that the regex matches case-insensitively with a lowercase pattern.
        """
        regex = self.create_case_insensitive_regex("cat")

        # Test matching - should match regardless of case
        if hasattr(QtCore, "QRegularExpression"):
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
        if hasattr(QtCore, "QRegularExpression"):
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
        if hasattr(QtCore, "QRegularExpression"):
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
        if hasattr(QtCore, "QRegularExpression"):
            self.assertIsInstance(regex, QtCore.QRegularExpression)
            self.assertTrue(regex.isValid())
        else:
            self.assertIsInstance(regex, QtCore.QRegExp)
            self.assertTrue(regex.isValid())

    def test_pattern_with_spaces(self):
        """
        Test that the regex handles patterns with spaces correctly.
        """
        regex = self.create_case_insensitive_regex("my asset")

        if hasattr(QtCore, "QRegularExpression"):
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

        if hasattr(QtCore, "QRegularExpression"):
            self.assertEqual(regex.pattern(), pattern)
        else:
            self.assertEqual(regex.pattern(), pattern)

    def test_case_insensitive_option_is_set_pyside6(self):
        """
        Test that CaseInsensitiveOption is set for PySide6/QRegularExpression.
        """
        if not hasattr(QtCore, "QRegularExpression"):
            self.skipTest("QRegularExpression not available (PySide2 environment)")

        regex = self.create_case_insensitive_regex("test")

        # Check that CaseInsensitiveOption is set
        options = regex.patternOptions()
        self.assertTrue(
            options & QtCore.QRegularExpression.CaseInsensitiveOption,
            "CaseInsensitiveOption should be set for QRegularExpression",
        )

    def test_case_sensitivity_pyside2(self):
        """
        Test that case sensitivity is set correctly for PySide2/QRegExp.
        """
        if hasattr(QtCore, "QRegularExpression"):
            self.skipTest(
                "Testing PySide2 behavior, but QRegularExpression is available"
            )

        regex = self.create_case_insensitive_regex("test")

        # Check case sensitivity setting
        self.assertEqual(
            regex.caseSensitivity(),
            QtCore.Qt.CaseInsensitive,
            "QRegExp should be case insensitive",
        )
