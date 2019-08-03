# coding: utf-8
"""
Fabric task for deploying project on servers(production, staging, development)


"""

import os
import sys
from contextlib import contextmanager

from fabric.contrib import django
from fabric.api import local, run, lcd, cd
from fabric.tasks import Task

from fab_settings import env

sys.path.append(os.path.dirname(__file__) + '/../../mysite/')

django.settings_module('mysite.settings')

STAGING_BRANCH = 'master'
BASE_PATH = os.path.dirname(__file__)
STAGING_HOST = 'staging.courselets.org'


def debug(*args, **kwargs):
    output = ""
    for x in args:
        print(x)
        output += str(x)
    return output


@contextmanager
def debug_cd(path):
    print("run on path:{0}".format(path))
    yield


class Deploying(Task):
    """
    Deploy project on Production
    """

    func = local
    func_cd = lcd
    code_branch = STAGING_BRANCH

    @property
    def project_path(self):
        return os.path.join(BASE_PATH, 'socraticqs2')

    @property
    def local_settings_path(self):
        return os.path.join(self.project_path, '../settings')

    def __virtualenv(self):
        with self.func_cd(os.path.join(self.project_path, '../')):
            self.func('source {}/bin/activate'.format(env.venv_name))

    def update_requirements(self):
        with self.func_cd(self.project_path):
            self.func("sudo pip install -r requirements.txt")

    def _get_settings(self, branch='master'):
        with self.func_cd(self.local_settings_path):
            self.func('git pull origin {0}'.format(branch))
            self.func('cp production_conf.py ../socraticqs2/mysite/mysite/settings/production_conf.py')

    def __restart_service(self):
        self.func('sudo supervisorctl restart gunicorn')
        self.func('sudo supervisorctl restart celery')
        self.func('sudo service nginx restart')

    @property
    def __is_new_branch(self):
        if self.func == run:
            return self.code_branch in self.func('git branch')
        else:
            return self.code_branch in self.func('git branch', capture=True)

    def __update(self):

        if self.__is_new_branch:
            self.func('git checkout {0} --force'.format(self.code_branch))
            self.func('git pull origin {0} --force'.format(self.code_branch))
        else:
            self.func('git fetch origin')
            self.func('git checkout -b {0} origin/{0}'.format(self.code_branch))
        self._get_settings()
        self.func('find . -name "*.pyc" -print -delete')
        self.__virtualenv()
        self.update_requirements()
        with self.func_cd("mysite"):
            self.func('python manage.py collectstatic --noinput')
            self.func('python manage.py syncdb --noinput')
            self.func('python manage.py fsm_deploy --noinput')

        self.__restart_service()

    def run(self, running='local', branch='master', suffix=None):
        self.code_branch = branch
        if running == 'local':
            self.func = local
            self.func_cd = lcd
            self.__update()
        elif running == 'remote':
            self.func = run
            self.func_cd = cd
            env.hosts = [STAGING_HOST, ]
            global BASE_PATH
            BASE_PATH = env.project_root
            with self.func_cd(self.project_path):
                self.__update()
        elif running == 'debug':
            print("DEBUG:\n")
            self.func = debug
            self.func_cd = debug_cd
            self.__update()


class Staging(Deploying):
    """Deploy on Staging"""

    def _get_settings(self, branch='master'):
        """On dev/staging we don't use production settings"""
        with self.func_cd(self.local_settings_path):
            self.func('git pull origin {0} --force'.format(branch))
            self.func('cp local_conf.py ../dev/socraticqs2/mysite/mysite/settings/local_conf.py')


class Development(Staging):
    """Deploy on Development server
    Args:
        running - deploy code local or in server(local/run)
        branch - git branch name
    Example:
        fab deploy.dev:running='local', branch='dev'
    """

    @property
    def project_path(self):
        if self.func == local:
            return os.path.join(BASE_PATH, '../../../../dev')
        else:
            return os.path.join(BASE_PATH, 'dev/socraticqs2')

    @property
    def local_settings_path(self):
        if self.func == local:
            return os.path.join(self.project_path, '../settings')
        else:
            return os.path.join(self.project_path, '../../settings')

    code_branch = 'dev'


prod = Deploying()
staging = Staging()
dev = Development()
