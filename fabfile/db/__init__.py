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

    fab db.init[:port][:host][:user][:password]

This task performs following actions:

  1. DROP database given from Django settings
  2. CREATE new database with name given from Django settings
  3. Apply all migrations
  4. Load fixture data
  5. Deploy FSMs

If ``port`` is not presented task gets it from settings or if it not presented in
settings too give it standart value.
If ``host`` is not presented task gets it from settings or if it not presented in
settings too gives it standart value.
If you want to use User and Password not the same as in settings you can type them
in command line.

Backup DB task
--------------
Usage::

    fab db.backup[:custom_branch_name][:port][:host][:backup_path]

This task performs following actions:

  1. DROP database given from Django settings
  2. CREATE new database with name given from Django settings
  3. ``psql pg_dump > backup.postgres.custom_branch_name`` action
     for PostgreSQL and ``cp mysite.db backup.sqlite.custom_branch_name``
     action for SQLite DB.
  4. In case of PostgreSQL tries to restore from that backup to check if
     there is any errors in backup file

If ``custom_branch_name`` param is not presented task gets current
git branch name and using it as a custom suffix for backup files.
If ``port`` is not presented task gets it from settings or if it not presented in
settings too give it standart value.
If ``host`` is not presented task gets it from settings or if it not presented in
settings too gives it standart value.
If ``backup_path`` param is not presented task get backup file from 'backups'
folder in root folder of project.

Restore DB task
---------------
Usage::

    fab db.restore[:custom_branch_name][:port][:host][:backup_path]

This task performs following actions:

  1. DROP database given from Django settings
  2. CREATE new database with name given from Django settings
  3. ``psql < backup.postgres.custom_branch_name`` action for
     PostgreSQL and ``cp backup.sqlite.custom_branch_name mysite.db``
     action for SQLite DB.

If ``custom_branch_name`` param is not presented task get current
git branch name and using it as a suffix for backup files.
If ``port`` is not presented task gets it from settings or if it not presented in
settings too give it standart value.
If ``host`` is not presented task gets it from settings or if it not presented in
settings too gives it standart value.
If ``backup_path`` param is not presented task get backup file from 'backups'
folder in root folder of project.

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
from tempfile import NamedTemporaryFile


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
    backup_path = None
    port = None
    host = None
    user = None
    password = None

    def run(self, action, suffix=None):
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

    def postgres(fn):
        """
        Decorator that adds PostgreSQL specific actions to task.
        """
        def wrapped(self, *args, **kwargs):
            self.host = self.host or (
                self.db_cfg['HOST'] if 'HOST' in self.db_cfg else 'localhost'
                )
            self.port = self.port or (
                self.db_cfg['PORT'] if 'PORT' in self.db_cfg else '5432'
                )
            self.user = self.user or self.db_cfg['USER']
            self.password = self.password or self.db_cfg['PASSWORD']
            with NamedTemporaryFile(suffix=".pgpass", delete=False) as f:
                f.write('%s:%s:*:%s:%s' % (self.host,
                                                  self.port,
                                                  self.user,
                                                  self.password))
            os.environ["PGPASSFILE"] = f.name
            fn(self, *args, **kwargs)
            local('rm %s ' % f.name)
        return wrapped


    @postgres
    def init_db_postgres(self, *args, **kwargs):
        """
        Init db to original state for postgres.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local('dropdb %s --username=%s -w' % (self.db_cfg['NAME'],
                                                  self.db_cfg['USER']))
            local('createdb %s encoding="UTF8" --username=%s -w ' %
                  (self.db_cfg['NAME'],
                   self.db_cfg['USER']))
            local('%s/bin/python mysite/manage.py migrate' % env.venv_name)
            local('%s/bin/python mysite/manage.py '
                  'loaddata mysite/dumpdata/debug-wo-fsm.json' % env.venv_name)
            local('%s/bin/python mysite/manage.py fsm_deploy' % env.venv_name)

    def init_db_sqlite(self, *args, **kwargs):
        """
        Init db to original state for sqlite.
        """
        path = os.path.dirname(os.path.dirname(
               os.path.dirname(os.path.dirname(self.base_path))))
        with lcd(os.path.join(path,'mysite/')), settings(hide('warnings'), warn_only=True):
            local('pwd')
            local('rm %s' % (self.db_cfg['NAME']))
            local('%s/bin/python manage.py migrate' % env.venv_name)
            local(
                '%s/bin/python manage.py loaddata dumpdata/debug-wo-fsm.json' %
                 env.venv_name
                )
            local('%s/bin/python manage.py fsm_deploy' % env.venv_name)

    @postgres
    def backup_db_postgres(self, suffix, *args, **kwargs):
        """
        Backup Postgres DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local(
                'pg_dump %s -U %s -w > %s/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'],
                   self.backup_path, suffix)
            )
            local(
                'createdb %s_temp encoding="UTF8" --username=%s -w'
                % (self.db_cfg['NAME'], self.db_cfg['USER'])
            )
            x = local(
                'psql %s_temp -U %s -w < %s/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'],
                   self.backup_path, suffix),
                capture=True)
            if not x.stderr:
                print 'Bakup is ok'
            else:
                print 'An error has occurred while backup'
            local('dropdb %s_temp --username=%s -w ' % (self.db_cfg['NAME'],
                                                        self.db_cfg['USER']))

    def backup_db_sqlite(self, suffix, *args, **kwargs):
        """
        Backup Sqlite DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local(
                'cp %s/%s %s/backup.sqlite.%s'
                % (dj_settings.BASE_DIR, self.db_cfg['NAME'],
                   self.backup_path, suffix)
            )

    @postgres
    def restore_db_postgres(self, suffix, *args, **kwargs):
        """
        Restore Postgres DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            if not local('ls %s/backup.postgres.%s' %
                        (self.backup_path, suffix)).succeeded:
                return self.list_backups('postgres')
            local('dropdb %s_temp --username=%s -w ' % (self.db_cfg['NAME'],
                                                        self.db_cfg['USER']))
            local(
                'createdb %s_temp encoding="UTF8" --username=%s -w'
                % (self.db_cfg['NAME'], self.db_cfg['USER'])
            )
            x = local(
                'psql %s_temp -U %s -w < %s/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'],
                   self.backup_path, suffix),
                capture=True)
            if not x.stderr:
                local('dropdb %s --username=%s -w ' % (self.db_cfg['NAME'],
                                                       self.db_cfg['USER']))
                local('psql -U %s -c "ALTER DATABASE %s_temp RENAME TO %s"' %
                      (self.db_cfg['USER'],
                       self.db_cfg['NAME'],
                       self.db_cfg['NAME']))
                print 'Restore is ok'
            else:
                print 'An error has occurred'

    def restore_db_sqlite(self, suffix, *args, **kwargs):
        """
        Restore Sqlite DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            result = local(
                'cp %s/backup.sqlite.%s %s/%s'
                % (self.backup_path, suffix, dj_settings.BASE_DIR,
                   self.db_cfg['NAME'])
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

    def run(self, suffix=None, backup_path=None, port=None, host=None):
        self.backup_path = backup_path or (self.base_path + '/backups/')
        self.port = port
        self.host = host
        super(RestoreDBTask, self).run(self.action, suffix)


class BackupDBTask(BaseTask):
    """
    Backup db task.
    """
    name = 'backup'
    action = 'backup'

    def run(self, suffix=None, backup_path=None, port=None, host=None):
        self.backup_path = backup_path or (self.base_path + '/backups')
        self.port = port
        self.host = host
        super(BackupDBTask, self).run(self.action, suffix)


class InitDBTask(BaseTask):
    """
    Init db task.
    """
    name = 'init'
    action = 'init'

    def run(self, port=None, host=None, user=None, password=None):
        self.port = port
        self.host = host
        self.user = user
        self.password = password
        super(InitDBTask, self).run(self.action)


restore = RestoreDBTask()
backup = BackupDBTask()
init = InitDBTask()
