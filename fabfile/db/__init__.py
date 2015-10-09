"""Fabric tasks to automate typical database actions.

There are three DB tasks:
* db.init
* db.backup
* db.restore

To list all available tasks::

  fab --list

All tasks makes decision about DB engine given from Django settings and
performs appropriate actions.

Init DB task
------------
Usage::

    fab db.init

This task performs following actions:

  1. DROP database given from Django settings
  2. CREATE new database with name given from Django settings
  3. Apply all migrations
  4. Load fixture data
  5. Deploy FSMs

Backup DB task
--------------
Usage::

    fab db.backup[:custom_branch_name]

This task performs following actions:

  1. DROP database given from Django settings
  2. CREATE new database with name given from Django settings
  3. ``psql pg_dump > backup.postgres.custom_branch_name`` action
     for PostgreSQL and ``cp mysite.db backup.sqlite.custom_branch_name``
     action for SQLite DB.

If ``custom_branch_name`` param is not presented task gets current
git branch name and using it as a custom suffix for backup files.

Restore DB task
---------------
Usage::

    fab db.restore[:custom_branch_name]

This task performs following actions:

  1. DROP database given from Django settings
  2. CREATE new database with name given from Django settings
  3. ``psql < backup.postgres.custom_branch_name`` action for
     PostgreSQL and ``cp backup.sqlite.custom_branch_name mysite.db``
     action for SQLite DB.

If ``custom_branch_name`` param is not presented task get current
git branch name and using it as a suffix for backup files.

If task can not find backup file it will list for you all backup files
available with specific DB engine given from Django settings.
"""
import re
import os
import sys

from fab_settings import env
from fabric.contrib import django
from fabric.api import local, settings, hide, lcd
from fabric.tasks import Task


sys.path.append(os.path.dirname(__file__) + '/../../mysite/')

django.settings_module('mysite.settings')
from django.conf import settings as dj_settings


class BaseTask(Task):
    """
    Base class for all DB tasks.
    """
    db_cfg = dj_settings.DATABASES['default']
    engine = db_cfg.get('ENGINE').split('.')[-1]
    base_path = os.path.dirname(__file__) + '/../..'

    def run(self, action, suffix=None):
        # VF: don't we support mysql?
        handlers = {
            'postgresql_psycopg2': getattr(BaseTask, '%s_db_postgres' % action),
            'sqlite3': getattr(BaseTask, '%s_db_sqlite' % action)
        }
        suffix = suffix or local('git rev-parse --abbrev-ref HEAD', capture=True)
        suffix = re.sub(r'/', r'\\\\', suffix)
        suffix = re.sub(r'!', r'\\!', suffix)
        suffix = re.sub(r'\$', r'U+0024', suffix)
        suffix = re.sub(r'`', r'\\`', suffix)
        try:
            handlers[self.engine].__call__(self, suffix)
        except KeyError:
            print('Error: Unknown engine `%s`' % self.engine)

    # VF: @staticmethod
    def postgres(fn):
        """
        Decorator that adds PostgreSQL specific actions to task.

        # VF: not good to use user's home dir for ~/.pgpass in such user-case
        # VF: same file is used by pgAdmin and maybe other GUIs
        # VF: and overwriting + removing of it can cause problems
        # VF: for some users
        # VF: Suggestion - generate random file and update environment
        # VF: variable PGPASSFILE.

        # VF: Also we should pass HOST and PORT, because they could be non-default

        # >>> from tempfile import NamedTemporaryFile
        # >>> with NamedTemporaryFile(suffix=".pgpass", delete=False) as f:
        # ...     f.write('{HOST}:{PORT}:postgres:{USER}:{PASSWORD}%(**self.db_cfg)
        # ... os.environ["PGPASSFILE"] = f.name
        # ... local('chmod 600 %s' % f.name)
        # ... fn(self, *args, **kwargs)
        # ... local('rm %s ' % f.name)
        """
        def wrapped(self, *args, **kwargs):
            local(
                'echo localhost:5432:postgres:%s:%s > ~/.pgpass'
                % (self.db_cfg['USER'], self.db_cfg['PASSWORD'])
            )
            local(
                'echo localhost:5432:%s:%s:%s >> ~/.pgpass'
                % (self.db_cfg['NAME'], self.db_cfg['USER'], self.db_cfg['PASSWORD'])
            )
            local('chmod 600 ~/.pgpass')
            fn(self, *args, **kwargs)
            local('rm ~/.pgpass')
        return wrapped

    @postgres
    def init_db_postgres(self, *args, **kwargs):
        """
        Init db to original state for postgres.

        # VF: We should pass also --host and --port arguments
        # VF: because user can have different values for them

        # VF: Also - we need arguments to pass user/password for restoration
        # VF: process, because database user from django config could have no
        # VF: permissions for database-level operations.

        # VF: Or there should be config to skip database drop/create
        # VF: Maybe add alternative - drop public schema inside database
        # VF: (fastest way to drop all tables) and create it again
        # VF: SQL: drop schema public cascade;
        # VF: SQL: create schema public;
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local('dropdb %s --username=%s -w ' % (self.db_cfg['NAME'], self.db_cfg['USER']))
            local('createdb %s encoding="UTF8" --username=%s -w' % (self.db_cfg['NAME'], self.db_cfg['USER']))
            local('%s/bin/python mysite/manage.py migrate' % env.venv_name)
            local('%s/bin/python mysite/manage.py loaddata mysite/dumpdata/debug-wo-fsm.json' % env.venv_name)
            local('%s/bin/python mysite/manage.py fsm_deploy' % env.venv_name)

    def init_db_sqlite(self, *args, **kwargs):
        """
        Init db to original state for sqlite.

        # VF: Here we should use NAME variable from config, because
        # VF: database path and file could be different.
        # VF: BTW - user can set absolute path to database file in config.

        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local('rm %s/mysite.db' % dj_settings.BASE_DIR)
            local('%s/bin/python mysite/manage.py migrate' % env.venv_name)
            local('%s/bin/python mysite/manage.py loaddata mysite/dumpdata/debug-wo-fsm.json' % env.venv_name)
            local('%s/bin/python mysite/manage.py fsm_deploy' % env.venv_name)

    @postgres
    def backup_db_postgres(self, suffix, *args, **kwargs):
        """
        Backup Postgres DB.

        # VF: path for saving backups should be overwritable by some
        # VF: input argument
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local(
                'pg_dump %s -U %s -w > %s/backups/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'], self.base_path, suffix)
            )

    def backup_db_sqlite(self, suffix, *args, **kwargs):
        """
        Backup Sqlite DB.

        # VF: path for saving backups should be overwritable by some
        # VF: input argument
        #
        # VF: We should pass also --host and --port arguments
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local(
                'cp %s/mysite.db %s/backups/backup.sqlite.%s'
                % (dj_settings.BASE_DIR, self.base_path, suffix)
            )

    @postgres
    def restore_db_postgres(self, suffix, *args, **kwargs):
        """
        Restore Postgres DB.

        # VF: We should pass also --host and --port arguments

        # VF: dropping current database before we are ensured, that restore
        # VF: was successful is dangerous. Better way - create new database
        # VF: with different name, restore dump there, ensure that there is no
        # VF: errors and only after that - drop current database and rename new
        # VF: SQL: ALTER DATABASE name RENAME TO new_name
        #
        # VF: Also - we need arguments to pass user/password for restoration
        # VF: process, because database user from django config could have no
        # VF: permissions for database-level operations.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            if not local('ls %s/backups/backup.postgres.%s' % (self.base_path, suffix)).succeeded:
                return self.list_backups('postgres')
            local('dropdb %s --username=%s -w ' % (self.db_cfg['NAME'], self.db_cfg['USER']))
            local(
                'createdb %s encoding="UTF8" --username=%s -w'
                % (self.db_cfg['NAME'], self.db_cfg['USER'])
            )
            local(
                'psql %s -U %s -w  < %s/backups/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'], self.base_path, suffix)
            )

    def restore_db_sqlite(self, suffix, *args, **kwargs):
        """
        Restore Sqlite DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            result = local(
                'cp %s/backups/backup.sqlite.%s %s/mysite.db'
                % (self.base_path, suffix, dj_settings.BASE_DIR)
            )
            if not result.succeeded:
                self.list_backups('sqlite')

    @staticmethod
    def list_backups(engine):
        print('='*32)
        print('There is no requested backup file.')
        backups = local('ls backups', capture=True).split()
        print('Below you can find available backup files:')
        for backup in backups:
            if re.match(r'^backup\.%s\.' % engine, backup):
                print(backup)


class RestoreDBTask(BaseTask):
    """
    Restore DB task.
    """
    name = 'restore'
    action = 'restore'

    def run(self, suffix=None):
        super(RestoreDBTask, self).run(self.action, suffix)


class BackupDBTask(BaseTask):
    """
    Backup db task.
    """
    name = 'backup'
    action = 'backup'

    def run(self, suffix=None):
        super(BackupDBTask, self).run(self.action, suffix)


class InitDBTask(BaseTask):
    """
    Backup db task.
    """
    name = 'init'
    action = 'init'

    def run(self):
        super(InitDBTask, self).run(self.action)


restore = RestoreDBTask()
backup = BackupDBTask()
init = InitDBTask()
