"""
Test migrations instructor_task table.
"""
# pylint: disable=attribute-defined-outside-init
import json

from common.test.test_migrations.utils import TestMigrations
from django.contrib.auth.models import User
from instructor_task.models import InstructorTask
from opaque_keys.edx.keys import CourseKey


class TestTextFields(TestMigrations):
    """
    Test migration no. 0002_auto_20160208_0810 for InstructorTask model.
    Fields changes from CharField to TextField.
    """
    migrate_from = '0001_initial'
    migrate_to = '0002_auto_20160208_0810'
    app = 'instructor_task'
    test_course_key = CourseKey.from_string('course-v1:edX+1.23x+test_course')

    def setUpBeforeMigration(self):
        """
        Setup before migration create InstructorTask model entry to verify after migration.
        """
        self.task_input = 'x' * 250
        self.task_output = 'x' * 999
        self.instructor = User.objects.create(username="instructor", email="instructor@edx.org")
        self.task = InstructorTask.create(
            self.test_course_key,
            "dummy type",
            "dummy key",
            self.task_input,
            self.instructor
        )
        self.task.task_output = self.task_output
        self.task.save_now()

    def test_text_fields_migrated(self):
        """
        Verify that data does not loss after migration when model field changes
        from CharField to TextField.
        """
        self.migrate_forwards()
        task_after_migration = InstructorTask.objects.get(id=self.task.id)
        self.assertEqual(task_after_migration.task_input, json.dumps(self.task_input))
        self.assertEqual(task_after_migration.task_output, self.task_output)

    def test_migrated_backward(self):
        """
        Verify that migrate to backwards does not loose any data.
        """
        self.migrate_forwards()
        self.migrate_backwards()
        task_after_backward_migration = InstructorTask.objects.get(id=self.task.id)
        self.assertEqual(task_after_backward_migration.task_input, json.dumps(self.task_input))
