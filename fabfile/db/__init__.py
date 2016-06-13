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

    fab db.init[:dbport=5432][:dbhost=localhost][,user=username][,password=password][,name=DBname]

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
If you want to use Database Name not the same as in settings you can type it
in command line.
These custom parameters (port, host, etc.) are not permanent and won't be saved in
settings file.

Backup DB task
--------------
Usage::

    fab db.backup[:custom_branch_name][,dbport=5432][,dbhost=localhost][,backup_path=backup_path][,user=username][,password=password][,name=DBname]

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
If you want to use User and Password not the same as in settings you can type them
in command line.
If you want to use Database Name not the same as in settings you can type it
in command line.
These custom parameters (port, host, etc.) are not permanent and won't be saved in
settings file.

Restore DB task
---------------
Usage::

    fab db.restore[:custom_branch_name][,dbport=5432][,dbhost=localhost][,backup_path=path][,user=username][,password=password][,name=DBname]

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
If you want to use User and Password not the same as in settings you can type them
in command line.
If you want to use Database Name not the same as in settings you can type it
in command line.
These custom parameters (port, host, etc.) are not permanent and won't be saved in
settings file.

If task can not find backup file it will list for you all backup files
available with specific DB engine given from Django settings.
"""
import re
import os
import sys

from django.core.management import call_command


from fab_settings import env
from fabric.contrib import django
from fabric.api import local, settings, hide, lcd
from fabric.tasks import Task
from tempfile import NamedTemporaryFile


sys.path.append(os.path.dirname(__file__) + '/../../mysite/')

django.settings_module('mysite.settings')
from django.conf import settings as dj_settings
import django
django.setup()


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
    name = None
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
        if self.name:
            self.db_cfg['NAME'] = self.name
        if self.user:
            self.db_cfg['USER'] = self.user
        if self.password:
            self.db_cfg['PASSWORD'] = self.password

        self.db_cfg['HOST'] = self.host or self.db_cfg['HOST'] or 'localhost'
        self.db_cfg['PORT'] = self.port or self.db_cfg['PORT'] or '5432'

        try:
            handlers[self.engine].__call__(self, suffix)
        except KeyError:
            print('Error: Unknown engine `%s`' % self.engine)

    def postgres(fn):
        """
        Decorator that adds PostgreSQL specific actions to task.
        """
        def wrapped(self, *args, **kwargs):
            with NamedTemporaryFile(suffix=".pgpass", delete=False) as f:
                f.write('%s:%s:*:%s:%s' % (self.db_cfg['HOST'],
                                           self.db_cfg['PORT'],
                                           self.db_cfg['USER'],
                                           self.db_cfg['PASSWORD']))
            os.environ["PGPASSFILE"] = f.name
            fn(self, *args, **kwargs)
            local('rm %s ' % f.name)
        return wrapped

    @postgres
    def init_db_postgres(self, *args, **kwargs):
        """
        Init db to original state for postgres.
        """
        path = os.path.dirname(os.path.dirname(
               os.path.dirname(os.path.dirname(self.base_path))))
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            local('dropdb %s --username=%s --host=%s --port=%s -w' % (self.db_cfg['NAME'],
                                                                      self.db_cfg['USER'],
                                                                      self.db_cfg['HOST'],
                                                                      self.db_cfg['PORT']))
            local('createdb %s encoding="UTF8" --username=%s --host=%s --port=%s -w ' %
                                                                      (self.db_cfg['NAME'],
                                                                       self.db_cfg['USER'],
                                                                       self.db_cfg['HOST'],
                                                                       self.db_cfg['PORT']))
            call_command('migrate')
            call_command('loaddata', os.path.join(path, 'mysite/dumpdata/debug-wo-fsm.json'))
            call_command('fsm_deploy')

    def init_db_sqlite(self, *args, **kwargs):
        """
        Init db to original state for sqlite.
        """
        path = os.path.dirname(os.path.dirname(
               os.path.dirname(os.path.dirname(self.base_path))))
        with lcd(os.path.join(path, 'mysite/')), settings(hide('warnings'), warn_only=True):
            local('pwd')
            if not self.db_cfg['NAME'].startswith('/'):
                self.db_cfg['NAME'] = os.path.join(path, 'mysite/', self.db_cfg['NAME'])
            local('rm %s' % (self.db_cfg['NAME']))
            call_command('migrate')
            call_command('loaddata', os.path.join(path, 'mysite/dumpdata/debug-wo-fsm.json'))
            call_command('fsm_deploy')

    @postgres
    def backup_db_postgres(self, suffix, *args, **kwargs):
        """
        Backup Postgres DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            log = local(
                'pg_dump %s --no-owner --no-acl -U %s --host=%s --port=%s -w > %s/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'], self.db_cfg['HOST'], self.db_cfg['PORT'],
                   self.backup_path, suffix), capture=True
            )
            if not log.stderr or 'FATAL' not in log.stderr:
                local('dropdb %s_temp --username=%s --host=%s --port=%s -w ' % (self.db_cfg['NAME'],
                                                                                self.db_cfg['USER'],
                                                                                self.db_cfg['HOST'],
                                                                                self.db_cfg['PORT']))
                local(
                    'createdb %s_temp encoding="UTF8" --username=%s --host=%s --port=%s -w'
                    % (self.db_cfg['NAME'], self.db_cfg['USER'], self.db_cfg['HOST'], self.db_cfg['PORT'])
                )
                x = local(
                    'psql %s_temp -U %s --host=%s --port=%s -w < %s/backup.postgres.%s'
                    % (self.db_cfg['NAME'], self.db_cfg['USER'], self.db_cfg['HOST'], self.db_cfg['PORT'],
                       self.backup_path, suffix),
                    capture=True)
                if not x.stderr or 'FATAL' not in x.stderr:
                    print 'Bakup is ok'
                else:
                    print(x.stderr)
                    print 'An error has occurred while backup'
                local('dropdb %s_temp --username=%s --host=%s --port=%s -w ' % (self.db_cfg['NAME'],
                                                                                self.db_cfg['USER'],
                                                                                self.db_cfg['HOST'],
                                                                                self.db_cfg['PORT']))
            else:
                print(log.stderr)
                print('An error has occurred while backup')

    def backup_db_sqlite(self, suffix, *args, **kwargs):
        """
        Backup Sqlite DB.
        """
        path = os.path.dirname(os.path.dirname(
               os.path.dirname(os.path.dirname(self.base_path))))
        with lcd(os.path.join(path, 'mysite/')), settings(hide('warnings'), warn_only=True):
            if not self.db_cfg['NAME'].startswith('/'):
                self.db_cfg['NAME'] = os.path.join(path, 'mysite/', self.db_cfg['NAME'])
            local(
                'cp %s %s/backup.sqlite.%s'
                % (self.db_cfg['NAME'],
                   self.backup_path, suffix)
            )

    @postgres
    def restore_db_postgres(self, suffix, *args, **kwargs):
        """
        Restore Postgres DB.
        """
        with lcd(self.base_path), settings(hide('warnings'), warn_only=True):
            if not local('ls %s/backup.postgres.%s' % (self.backup_path, suffix)).succeeded:
                return self.list_backups('postgres')
            local('dropdb %s_temp --username=%s --host=%s --port=%s -w ' % (self.db_cfg['NAME'],
                                                                            self.db_cfg['USER'],
                                                                            self.db_cfg['HOST'],
                                                                            self.db_cfg['PORT']))
            local(
                'createdb %s_temp encoding="UTF8" --username=%s --host=%s --port=%s -w'
                % (self.db_cfg['NAME'], self.db_cfg['USER'], self.db_cfg['HOST'], self.db_cfg['PORT'])
            )
            x = local(
                'psql %s_temp -U %s --host=%s --port=%s -w < %s/backup.postgres.%s'
                % (self.db_cfg['NAME'], self.db_cfg['USER'], self.db_cfg['HOST'], self.db_cfg['PORT'],
                   self.backup_path, suffix),
                capture=True)
            if not x.stderr or ('FATAL' not in x.stderr and 'no password supplied' not in x.stderr):
                log = local('psql --username %s --host=%s --port=%s -w -c "ALTER DATABASE %s RENAME TO %s_old"' %
                            (self.db_cfg['USER'],
                             self.db_cfg['HOST'],
                             self.db_cfg['PORT'],
                             self.db_cfg['NAME'],
                             self.db_cfg['NAME']), capture=True)
                if not log.stderr or (
                    'FATAL' not in log.stderr and
                    'no password supplied' not in log.stderr and
                    'ERROR:  database "%s" is being accessed by other' % self.db_cfg['NAME'] not in log.stderr
                ):
                    local('psql --username %s --host=%s --port=%s -w -c "ALTER DATABASE %s_temp RENAME TO %s"' %
                          (self.db_cfg['USER'],
                           self.db_cfg['HOST'],
                           self.db_cfg['PORT'],
                           self.db_cfg['NAME'],
                           self.db_cfg['NAME']))
                    local('dropdb %s_old --username=%s --host=%s --port=%s -w ' % (self.db_cfg['NAME'],
                                                                                   self.db_cfg['USER'],
                                                                                   self.db_cfg['HOST'],
                                                                                   self.db_cfg['PORT']))
                    print 'Restore is ok'
                else:
                    print(log.stderr)
                    print('An error has occured.')
                    local('dropdb %s_temp --username=%s --host=%s --port=%s -w ' % (self.db_cfg['NAME'],
                                                                                    self.db_cfg['USER'],
                                                                                    self.db_cfg['HOST'],
                                                                                    self.db_cfg['PORT']))
            else:
                print(x.stderr)
                print 'An error has occurred'

    def restore_db_sqlite(self, suffix, *args, **kwargs):
        """
        Restore Sqlite DB.
        """
        path = os.path.dirname(os.path.dirname(
               os.path.dirname(os.path.dirname(self.base_path))))
        with lcd(path), settings(hide('warnings'), warn_only=True):
            if not self.db_cfg['NAME'].startswith('/'):
                self.db_cfg['NAME'] = os.path.join(path, 'mysite/', self.db_cfg['NAME'])
            result = local(
                'cp %s/backup.sqlite.%s %s'
                % (self.backup_path, suffix, self.db_cfg['NAME'])
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

    def run(self, suffix=None, backup_path=None, dbport=None, dbhost=None,
            user=None, password=None, name=None):
        self.backup_path = backup_path or (self.base_path + '/backups/')
        self.port = dbport
        self.host = dbhost
        self.user = user
        self.name = name
        self.password = password
        super(RestoreDBTask, self).run(self.action, suffix)


class BackupDBTask(BaseTask):
    """
    Backup db task.
    """
    name = 'backup'
    action = 'backup'

    def run(self, suffix=None, backup_path=None, dbport=None, dbhost=None,
            user=None, password=None, name=None):
        self.backup_path = backup_path or (self.base_path + '/backups')
        self.port = dbport
        self.host = dbhost
        self.user = user
        self.name = name
        self.password = password
        super(BackupDBTask, self).run(self.action, suffix)


class InitDBTask(BaseTask):
    """
    Init db task.
    """
    name = 'init'
    action = 'init'

    def run(self, dbport=None, dbhost=None, user=None, password=None, name=None):
        self.port = dbport
        self.host = dbhost
        self.user = user
        self.name = name
        self.password = password
        super(InitDBTask, self).run(self.action)


restore = RestoreDBTask()
backup = BackupDBTask()
init = InitDBTask()
