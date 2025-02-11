# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import json
import os
import unittest
from unittest.mock import MagicMock

from taskgraph import files_changed

PARAMS = {
    "head_repository": "https://hg.mozilla.org/mozilla-central",
    "head_rev": "a14f88a9af7a",
}

FILES_CHANGED = [
    "devtools/client/debugger/new/index.html",
    "devtools/client/inspector/test/browser_inspector_highlighter-eyedropper-events.js",
    "devtools/client/inspector/test/head.js",
    "devtools/client/themes/rules.css",
    "devtools/client/webconsole/test/browser_webconsole_output_06.js",
    "devtools/server/actors/highlighters/eye-dropper.js",
    "devtools/server/actors/object.js",
    "docshell/base/nsDocShell.cpp",
    "dom/tests/mochitest/general/test_contentViewer_overrideDPPX.html",
    "taskcluster/scripts/builder/build-l10n.sh",
]


class FakeResponse:
    def json(self):
        with open(
            os.path.join(os.path.dirname(__file__), "automationrelevance.json")
        ) as f:
            return json.load(f)


class TestGetChangedFiles(unittest.TestCase):
    def setUp(self):
        files_changed.get_changed_files.clear()
        self.old_get = files_changed.requests.get

        def fake_get(url, **kwargs):
            return FakeResponse()

        files_changed.requests.get = fake_get

        self.repo_mock = MagicMock()
        files_changed.get_repository = lambda _: self.repo_mock

    def tearDown(self):
        files_changed.requests.get = self.old_get
        files_changed.get_changed_files.clear()

    def test_get_changed_files_automationrelevance(self):
        """Get_changed_files correctly gets the list of changed files in a push.
        This tests against the production hg.mozilla.org so that it will detect
        any changes in the format of the returned data."""
        self.repo_mock.tool = "hg"
        self.assertEqual(
            sorted(
                files_changed.get_changed_files(
                    PARAMS["head_repository"], PARAMS["head_rev"]
                )
            ),
            FILES_CHANGED,
        )

    def test_get_changed_files_vcs(self):
        """Get_changed_files correctly gets the list of changed files in a push.
        This tests against the production hg.mozilla.org so that it will detect
        any changes in the format of the returned data."""
        self.repo_mock.tool = "git"
        self.repo_mock.get_changed_files = lambda *_, **__: [
            "some/file",
            "some/other/file",
        ]
        self.assertEqual(
            sorted(
                files_changed.get_changed_files(
                    PARAMS["head_repository"],
                    PARAMS["head_rev"],
                )
            ),
            ["some/file", "some/other/file"],
        )


class TestCheck(unittest.TestCase):
    def setUp(self):
        files_changed.get_changed_files[
            PARAMS["head_repository"], PARAMS["head_rev"], None
        ] = FILES_CHANGED

    def tearDown(self):
        files_changed.get_changed_files.clear()

    def test_check_no_params(self):
        self.assertTrue(files_changed.check({}, ["ignored"]))

    def test_check_no_match(self):
        self.assertFalse(files_changed.check(PARAMS, ["nosuch/**"]))

    def test_check_match(self):
        self.assertTrue(files_changed.check(PARAMS, ["devtools/**"]))
