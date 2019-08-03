# coding: utf-8
"""
Fabric task for management service on servers(production, staging, development)


"""

import os
import sys
from contextlib import contextmanager
from datetime import datetime
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


class NginxTask(Task):
    """
    Task for management Nginx serive
    """

    func = local
    func_cd = lcd
    config_branch = STAGING_BRANCH
    service_bin = '/etc/nginx/'
    service_path = '/etc/nginx/'
    project_name = 'courselets'
    config_path = os.path.join(BASE_PATH, '../config')

    def restart_service(self):
        self.func('sudo service nginx restart')

    @property
    def __is_new_branch(self):
        if self.func == run:
            return self.config_branch in self.func('git branch')
        else:
            return self.config_branch in self.func('git branch', capture=True)

    @property
    def is_config_valid(self):
        if self.func == run:
            return 'OK' in self.func('sudo service nginx testconfig')
        else:
            return 'OK' in self.func('sudo service nginx testconfig', capture=True)

    def __update(self):

        if self.__is_new_branch:
            self.func('git checkout {0} --force'.format(self.config_branch))
            self.func('git pull origin {0} --force'.format(self.config_branch))
        else:
            self.func('git fetch origin')
            self.func('git checkout -b {0} origin/{0}'.format(self.config_branch))

        self.func('sudo cp {0} {1}site-available/{0}'.format(self.project_name, self.service_path))

        backup_name = "{0}.backup_{1}".format(
            self.project_name, str(datetime.now()).replace(" ", "-").replace(":", "-"))

        self.func('sudo cp {1}site-available/{0} {1}site-available/{2}'.format(
            self.project_name, self.service_path, backup_name))

        self.func('sudo ln -S {1}site-available/{0} {1}site-enabled/{0}'.format(
            self.project_name, self.service_path))
        if self.is_config_valid:
            self.restart_service()
        else:
            self.func('sudo cp {1}site-available/{2} {1}site-available/{0}'.format(
                self.project_name, self.service_path, backup_name))

            s = "*" * 80
            print("{0}\n{0}\n\t\t\tNEW CONFIG ON BRANCH `{1}` FAILED!!!\n"\
                  "\n \t\t\t OLD CONFIG RESTORED\n{0}\n{0}".format(s, self.config_branch))

    def run(self, running='local', branch='master', suffix=None):
        self.config_branch = branch
        if running == 'local':
            self.func = local
            self.func_cd = lcd
        elif running == 'remote':
            self.func = run
            self.func_cd = cd
            env.hosts = [STAGING_HOST, ]
            global BASE_PATH
            BASE_PATH = env.project_root
        elif running == 'debug':
            print("DEBUG:\n")
            self.func = debug
            self.func_cd = debug_cd

        with self.func_cd(self.config_path):
                self.__update()

nginx = NginxTask()
