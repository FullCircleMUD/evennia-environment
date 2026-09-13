# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-environment, run via ``python runtests.py``.

Only the scaffold smoke test so far. Every case the library commits to lives in
docs/test-plan.md, and a test lands here once its case is agreed there.
"""

from unittest import TestCase

import evennia_environment


class ScaffoldTests(TestCase):
    """The install and the test runner work end to end."""

    def test_sc_01_package_imports_and_reports_its_version(self):
        """SC-01"""
        self.assertEqual(evennia_environment.__version__, "0.0.1")
