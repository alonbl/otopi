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


"Config plugin."""


import os
import configparser
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import common
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """Configuration file provider.

    Environment:
        CoreEnv.CONFIG_FILE_NAME -- configuration file name.

    OS Environment:
        SystemEnvironment.CONFIG -- config file name.

    Configuration file has two sections:
        Const.CONFIG_SECTION_DEFAULTS -- loaded at init high+ priority.
        Const.CONFIG_SECTION_OVERRIDES -- loaded at customization high
            priority.

    Configuration files read:
        CoreEnv.CONFIG_FILE_NAME
        CoreEnv.CONFIG_FILE_NAME.d/*.conf - sorted

    Keys are the environment key names, values are at type:value notation.

    """
    def _readEnvironment(self, section, override):
        if self._config.has_section(section):
            for name, value in self._config.items(section):
                try:
                    value = common.parseTypedValue(value)
                except Exception as e:
                    raise RuntimeError(
                        _(
                            "Cannot parse configuration file key "
                            "{key} at section {section}: {exception}"
                        ).format(
                            key=name,
                            section=section,
                            exception=e,
                        )
                    )
                if True or override:
                    self.environment[name] = value
                else:
                    self.environment.setdefault(name, value)

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._config = configparser.ConfigParser()
        self._config.optionxform = str

    @plugin.event(
        name=constants.Stages.CORE_CONFIG_INIT,
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_HIGH - 10,
    )
    def _init(self):
        self.environment.setdefault(
            constants.CoreEnv.CONFIG_FILE_NAME,
            self.resolveFile(
                os.environ.get(
                    constants.SystemEnvironment.CONFIG,
                    self.resolveFile(constants.Defaults.CONFIG_FILE),
                )
            )
        )
        self.environment.setdefault(
            constants.CoreEnv.CONFIG_FILE_APPEND,
            None
        )

        configs = []
        for f in (
            self.environment[constants.CoreEnv.CONFIG_FILE_NAME],
            self.environment[constants.CoreEnv.CONFIG_FILE_APPEND],
        ):
            if f:
                for c in f.split(':'):
                    configFile = self.resolveFile(c)
                    configDir = '%s.d' % configFile
                    if os.path.exists(configFile):
                        configs.append(configFile)
                    if os.path.isdir(configDir):
                        configs += [
                            os.path.join(configDir, f)
                            for f in sorted(os.listdir(configDir))
                            if f.endswith('.conf')
                        ]

        self._configFiles = self._config.read(configs)

        self._readEnvironment(
            section=constants.Const.CONFIG_SECTION_DEFAULT,
            override=False
        )
        self._readEnvironment(
            section=constants.Const.CONFIG_SECTION_INIT,
            override=True
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _post_init(self):
        self.dialog.note(
            _('Configuration files: {files}').format(
                files=self._configFiles,
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _customize1(self):
        self._readEnvironment(
            section=constants.Const.CONFIG_SECTION_OVERRIDE,
            override=True,
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        priority=plugin.Stages.PRIORITY_LOW,
    )
    def _customize2(self):
        self._readEnvironment(
            section=constants.Const.CONFIG_SECTION_ENFORCE,
            override=True,
        )


# vim: expandtab tabstop=4 shiftwidth=4
