# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2016 EventGhost Project <http://www.eventghost.org/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
from Utils import IsCIBuild


class Config(object):
    def __init__(self, build_setup, config_file_path):
        self.build_setup = build_setup
        self._config_file_path = config_file_path
        self.load_settings()

    def load_settings(self):
        """
        Load the ini file and set all options.
        """
        config_parser = ConfigParser.ConfigParser()
        if not IsCIBuild():
            config_parser.read(self._config_file_path)
        for task in self.build_setup.tasks:
            section = task.GetId()
            if not config_parser.has_section(section):
                continue
            options = config_parser.options(section)
            for option in options:
                if option == "enabled":
                    if task.visible:
                        task.activated = eval(
                            config_parser.get(section, "enabled")
                        )
                else:
                    task.options[option] = config_parser.get(section, option)
                    # print section, option, config_parser.get(section, option)

        if config_parser.has_option("GitHub", "Repository"):
            repository = config_parser.get('GitHub', "Repository")
            try:
                user, repo = repository.split('/')
            except ValueError:
                user = repo = ""
            self.build_setup.git_config.update({
                "user": user,
                "repo": repo,
                "branch": config_parser.get('GitHub', "Branch")
            })

        if config_parser.has_option("Website", "url"):
            self.build_setup.args.website_url = (
                config_parser.get('Website', "url")
            )

    def save_settings(self):
        """
        Save all options to the ini file.
        """
        config = ConfigParser.ConfigParser()
        # make ConfigParser case-sensitive
        config.optionxform = str
        config.read(self._config_file_path)
        for task in self.build_setup.tasks:
            section = task.GetId()
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, "enabled", task.activated)

        if not config.has_section('GitHub'):
                config.add_section('GitHub')
        repo = "{user}/{repo}".format(**self.build_setup.git_config)
        config.set('GitHub', "Repository", repo)
        config.set('GitHub', "Branch", self.build_setup.git_config["branch"])

        if not config.has_section('Website'):
                config.add_section('Website')
        config.set('Website', "url", self.build_setup.args.website_url)

        with open(self._config_file_path, "w") as f:
            config.write(f)
