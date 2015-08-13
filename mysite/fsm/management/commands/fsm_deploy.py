import re
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from fsm.fsmspec import deploy, deploy_all


class Command(BaseCommand):
    """Command for convenient way to deploy FSM.

    Whenever an FSM specification changes (e.g. adding a new FSM or modifying an existing FSM),
    that specification must be loaded to the database. Whenever the database table is flushed,
    the set of FSM specifications must be loaded.
    This command provides a convenient way to deploy|re-deploy FSM(s)
    """
    help = 'Deploy all not ignored FSM(s)'
    args = 'APP.fsm_plugin.MODULENAME'

    def handle(self, *args, **options):
        os.chdir(settings.BASE_DIR)
        deployed = []

        if len(args) == 0:
            deployed += deploy_all('admin')
        elif len(args) == 1:
            if re.match(r'^.+\.fsm_plugin\..+$', args[0]):
                try:
                    deployed += deploy(args[0], 'admin')
                except ImportError as err:
                    self.stdout.write('FSM on path `%s` can\'t be imported.' % args[0])
                    self.stderr.write('%s: %s' % (err.__class__.__name__, err))
                    sys.exit(1)
            else:
                self.stdout.write('Please specify FSM path in form of `%s`.' % self.args)
                self.stderr.write('Error: Specified path `%s` is incorrect.' % args[0])
                sys.exit(1)
        elif len(args) > 1:
            raise CommandError('Command doesn\'t accept more then one argument.')

        for fsm in deployed:
            self.stdout.write('FSM `%s` is deployed.' % fsm.name)
