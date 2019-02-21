# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2018 EventGhost Project <http://eventghost.net/>
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

import time
from os.path import join
from distutils.core import Command


class BuildVersionFile(Command):
    """
    Write version information to eg/Classes/VersionInfo.py
    """

    def initialize_options(self):
        self.build_setup = None

    def finalize_options(self):
        self.build_setup = build_setup = (
            self.distribution.get_command_obj('build')
        )
        build_setup.build_time = time.time()
        self.file_path = join(
            build_setup.tmp_dir,
            "VersionInfo.py"
        )

    def run(self):
        build_setup = self.build_setup
        output = TEMPLATE.format(
            build_setup.app_version,
            build_setup.app_version.split("-")[0],
            *build_setup.app_version_info
        )
        with open(self.file_path, "wt") as f:
            f.write(output)


TEMPLATE = '''\
buildTime = {0}
string = '{1}'
base = '{2}'
major = {3}
minor = {4}
patch = {5}
alpha = {6}
beta = {7}
rc = {8}
'''
