"""
General class for Test migrations.Based off an implementation provided at
https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""
# pylint: disable=redefined-outer-name

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
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
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        self.executor = MigrationExecutor(connection)

    def execute_migration(self, **args):
        """
        Execute migration from state to another.
        """
        # Reverse to the original migration
        self.executor.migrate(args['migrate_from'])

        self.setUpBeforeMigration()

        # Run the migration to test
        self.executor.migrate(args['migrate_to'])

    def setUpBeforeMigration(self):  # pylint: disable=invalid-name
        """
        Will run before migration using config field migrate_from.
        Implemented in derived class.
        """
        pass

    def migrate_forwards(self):
        """ Execute migration to forward state. """
        self.execute_migration(migrate_from=self.migrate_from, migrate_to=self.migrate_to)

    def migrate_backwards(self):
        """ Execute migration to backward state. """
        # self.executor.migrate(self.migrate_from)
        call_command("migrate", self.app, self.migrate_from[0][1])
        migration_state = MigrationRecorder.Migration.objects.filter(app=self.app).last()
        self.assertEqual(migration_state.name, self.migrate_from[0][1])
