"""Unit tests for the Paver asset tasks."""

import ddt
import os
from paver.easy import call_task
from paver.easy import path

from .utils import PaverTestCase

ROOT_PATH = path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
TEST_THEME = ROOT_PATH / "common/test/test-theme"  # pylint: disable=invalid-name


@ddt.ddt
class TestPaverAssetTasks(PaverTestCase):
    """
    Test the Paver asset tasks.
    """
    @ddt.data(
        [""],
        ["--force"],
        ["--debug"],
        ["--system=lms"],
        ["--system=lms --force"],
        ["--system=studio"],
        ["--system=studio --force"],
        ["--system=lms,studio"],
        ["--system=lms,studio --force"],
    )
    @ddt.unpack
    def test_compile_sass(self, options):
        """
        Test the "compile_sass" task.
        """
        parameters = options.split(" ")
        system = []
        if "--system=studio" not in parameters:
            system += ["lms"]
        if "--system=lms" not in parameters:
            system += ["studio"]
        debug = "--debug" in parameters
        force = "--force" in parameters
        self.reset_task_messages()
        call_task('pavelib.assets.compile_sass', options={"system": system, "debug": debug, "force": force})
        expected_messages = []
        if "lms" in system:
            if force:
                expected_messages.append("rm -rf common/static/css/*.css")
            expected_messages.append("libsass common/static/sass")

            if force:
                expected_messages.append("rm -rf lms/static/css/*.css")
            expected_messages.append("libsass lms/static/sass")
            if force:
                expected_messages.append("rm -rf lms/static/certificates/css/*.css")
            expected_messages.append("libsass lms/static/certificates/sass")
        if "studio" in system:
            if force:
                expected_messages.append("rm -rf common/static/css/*.css")
            expected_messages.append("libsass common/static/sass")

            if force:
                expected_messages.append("rm -rf cms/static/css/*.css")
            expected_messages.append("libsass cms/static/sass")
        self.assertEquals(self.task_messages, expected_messages)


@ddt.ddt
class TestPaverThemeAssetTasks(PaverTestCase):
    """
    Test the Paver asset tasks.
    """

    @ddt.data(
        [""],
        ["--force"],
        ["--debug"],
        ["--system=lms"],
        ["--system=lms --force"],
        ["--system=studio"],
        ["--system=studio --force"],
        ["--system=lms,studio"],
        ["--system=lms,studio --force"],
    )
    @ddt.unpack
    def test_compile_theme_sass(self, options):
        """
        Test the "compile_sass" task.
        """
        parameters = options.split(" ")
        system = []

        if "--system=studio" not in parameters:
            system += ["lms"]
        if "--system=lms" not in parameters:
            system += ["studio"]
        debug = "--debug" in parameters
        force = "--force" in parameters

        self.reset_task_messages()
        call_task(
            'pavelib.assets.compile_sass',
            options={"system": system, "debug": debug, "force": force, "themes_dir": TEST_THEME.dirname(),
                     "themes": [TEST_THEME.basename()]},
        )
        expected_messages = []
        if "lms" in system:
            expected_messages.append("mkdir_p " + repr(TEST_THEME / "lms/static/css"))
            if force:
                expected_messages.append("rm -rf common/static/css/*.css")
            expected_messages.append("libsass common/static/sass")

            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/lms/static/css/*.css")
            expected_messages.append("libsass lms/static/sass")
            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/lms/static/css/*.css")
            expected_messages.append("libsass " + str(TEST_THEME) + "/lms/static/sass")
        if "studio" in system:
            expected_messages.append("mkdir_p " + repr(TEST_THEME / "cms/static/css"))
            if force:
                expected_messages.append("rm -rf common/static/css/*.css")
            expected_messages.append("libsass common/static/sass")

            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/cms/static/css/*.css")
            expected_messages.append("libsass cms/static/sass")
            if force:
                expected_messages.append("rm -rf " + str(TEST_THEME) + "/cms/static/css/*.css")
            expected_messages.append("libsass " + str(TEST_THEME) + "/cms/static/sass")

        self.assertEquals(self.task_messages, expected_messages)
