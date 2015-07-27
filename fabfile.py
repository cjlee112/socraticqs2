import os

from fabric.api import task, local, settings, hide, lcd

from fab_settings import env


@task(default=True)
def init_db():
    """
    Init db to original state.
    """
    with lcd(os.path.dirname(__file__)), settings(hide('warnings'), warn_only=True):
        local('echo localhost:5432:postgres:%s:%s > ~/.pgpass' % (env.db_cfg['user'], env.db_cfg['password']))
        local('chmod 600 ~/.pgpass')
        local('dropdb %s --username=%s -w ' % (env.db_cfg['db_name'], env.db_cfg['user']))
        local('createdb %s encoding="utf-8" --username=%s -w' % (env.db_cfg['db_name'], env.db_cfg['user']))
        local('%s/bin/python mysite/manage.py migrate' % env.venv_name)
        local('%s/bin/python mysite/manage.py loaddata mysite/dumpdata/debug-wo-fsm.json' % env.venv_name)
        local('%s/bin/python mysite/manage.py fsm_deploy' % env.venv_name)
        local('rm ~/.pgpass')
