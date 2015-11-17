Fabric deployment tool
======================

Introduction
------------

It provides a basic suite of operations for executing
local or remote shell commands (normally or via sudo)
and uploading/downloading files, as well as auxiliary
functionality such as prompting the running user for
input, or aborting execution.

Typical use involves creating a Python module containing
one or more functions, then executing them via the fab
command-line tool.


Configuration
-------------

To configure Fabric for Socraticqs2 project you need to 
copy ``fab_settings.py.example`` file to ``fab_settings.py``::

    cp fab_settings.py.example fab_settings.py

Then you need to specify virtualenv name by setting
``env.venv_name`` variable. By default it is setted to
``_ve_socraticqs2``.


Example fab_settings.py file::

    """Settings for Fabric.

    Params:

    - env.venv_name: name of the current virtualenv
    """
    from fabric.api import env


    env.venv_name = '_ve_socraticqs2'



Fabric database tasks
---------------------

Database tasks are tasks that help to automate typical database actions.

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
available with specific DB engine given from Django settings, e.g.::


    $ fab db.restore:custom_branch_name
    ...................................
    [localhost] local: ls /path/to/proj/backups/backup.postgres.custom_branch_name
    ls: cannot access /path/to/proj/backups/backup.postgres.custom_branch_name: No such file or directory
    ================================
    There is no requested backup file.
    [localhost] local: ls backups
    Below you can find available backup files:
    backup.postgres.branch_1
    backup.postgres.branch_2
    backup.postgres.branch_3
    ...................................

    Done.


Deploy task
-----------

These tasks used to deploy the project on the servers. There
relatively flexible adjustment of behavior. Deployment can
carried out both locally and on a remote server. Main tasks:

Production deploy task
----------------------

This task should is used to deploy Productions (In this
moment don't used because of security)

Staging deploy task
-------------------

This task is used to update Staging environment

Dev deploy task
---------------

This task is used to update developer server



Usage::
    fab deploy.[environment]:running='[server]',branch='[branch name]'

All task have common interface and have next parameters:

Running[local/remote] -  run deploying command locally or remote
Branch - name of branch to deploying.

Example::
    fab deploy.dev:running='local',branch='dev'