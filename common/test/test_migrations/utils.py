"""
General class for test migrations.Based off an implementation provided at
https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""
# pylint: disable=redefined-outer-name

from django.db.migrations.recorder import MigrationRecorder
from django.test import TransactionTestCase
from django.core.management import call_command


class TestMigrations(TransactionTestCase):
    """ Base class for testing migrations. """
    migrate_from = None
    migrate_to = None
    app = None

    def setUp(self):
        super(TestMigrations, self).setUp()
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_from properties".format(type(self).__name__)
        assert self.app, "app must be define in the TestCase"
        self.most_recent_migration = MigrationRecorder.Migration.objects.filter(app=self.app).last().name

    def tearDown(self):
        """ Back to initial migration """
        super(TestMigrations, self).tearDown()
        call_command("migrate", self.app, self.most_recent_migration)
        self._check_migration_state(self.most_recent_migration)

    def _check_migration_state(self, migration_name):
        """ Veirfy the migration from djano migration table"""
        migration_state = MigrationRecorder.Migration.objects.filter(app=self.app).last()
        self.assertEqual(migration_state.name, migration_name)

    def execute_migration(self, migrate_from, migrate_to):
        """
        Execute migration from state to another.
        """
        # Reverse to the original migration
        call_command("migrate", self.app, migrate_from)

        self.setUpBeforeMigration()

        # Run the migration to test
        call_command("migrate", self.app, migrate_to)

    def setUpBeforeMigration(self):  # pylint: disable=invalid-name
        """
        Will run before migration using config field migrate_from.
        Implemented in derived class.
        """
        pass

    def migrate_forwards(self):
        """ Execute migration to forward state. """
        self.execute_migration(self.migrate_from, self.migrate_to)

    def migrate_backwards(self):
        """ Execute migration to backward state. """
        call_command("migrate", self.app, self.migrate_from)
        self._check_migration_state(self.migrate_from)
