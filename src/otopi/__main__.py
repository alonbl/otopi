#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""otopi entry point."""


import gettext
import os
import shlex
import sys
import traceback


from otopi import common
from otopi import constants
from otopi import main


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


class Installer(object):
    """otopi bootstrap.

    Parameters are in name=type:value format, to be added into
    environment.

    """
    def _setupEnvironment(self, environment):
        """Setup environment based on command-line parameters."""

        environment[constants.BaseEnv.EXECUTION_DIRECTORY] = os.environ[
            constants.SystemEnvironment.EXEC_DIR
        ]

        for arg in sys.argv[1:]:
            for statement in shlex.split(arg):
                entry = statement.split('=', 1)
                if len(entry) == 2:
                    key, value = entry[0], common.parseTypedValue(entry[1])
                    if key.startswith(
                        constants.Const.ENVIRONMENT_APPEND_PREFIX
                    ):
                        key = key.replace(
                            constants.Const.ENVIRONMENT_APPEND_PREFIX,
                            ''
                        )
                        environment.setdefault(key, '')
                        environment[key] += ':%s' % value
                    elif key.startswith(
                        constants.Const.ENVIRONMENT_PREPEND_PREFIX
                    ):
                        key = key.replace(
                            constants.Const.ENVIRONMENT_PREPEND_PREFIX,
                            ''
                        )
                        environment.setdefault(key, '')
                        environment[key] = '%s:%s' % (value, environment[key])
                    else:
                        environment[key] = value

    def _getExitCode(self, environment):
        return sorted(
            environment[constants.BaseEnv.EXIT_CODE],
            key=lambda x: x['priority'],
        )[0]['code']

    def __init__(self):
        self._debug = int(
            os.environ.get(
                constants.SystemEnvironment.DEBUG,
                0
            )
        )

    def main(self):
        try:
            installer = main.Otopi()
            os.environ.setdefault(
                constants.SystemEnvironment.EXEC_DIR,
                os.getcwd()
            )
            os.chdir('/')
            self._setupEnvironment(installer.environment)
            installer.execute()
            os.chdir(
                installer.environment[
                    constants.BaseEnv.EXECUTION_DIRECTORY
                ]
            )
            return self._getExitCode(installer.environment)
        except main.PluginLoadException as e:
            print(
                '***L:ERROR %s: %s' % (
                    _('Internal error'),
                    e,
                )
            )
            if self._debug > 0:
                traceback.print_exc()
            return constants.Const.EXIT_CODE_INITIALIZATION_ERROR
        except Exception as e:
            if self._debug > 0:
                print(
                    _('FATAL Internal error (main): {error}').format(
                        error=e
                    ),
                )
                traceback.print_exc()

            # return failure if someone set, never success
            return max(
                self._getExitCode(installer.environment),
                constants.Const.EXIT_CODE_GENERAL_ERROR,
            )

if __name__ == '__main__':
    installer = Installer()
    sys.exit(installer.main())


# vim: expandtab tabstop=4 shiftwidth=4
