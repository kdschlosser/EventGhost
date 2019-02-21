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

import os
from shutil import copy2


from distutils.core import Command


# Local imports

class ReleaseToWeb(Command):

    def initialize_options(self):
        self.options = {"url": ""}
        self.build_setup = None

    def finalize_options(self):
        self.build_setup = self.distribution.get_command_obj('build')

    def run(self):
        if not self.options["url"]:
            return

        import Upload

        build_setup = self.build_setup

        filename = (
            build_setup.app_name + "_" + build_setup.app_version + "_Setup.exe"
        )
        src = os.path.join(build_setup.output_dir, filename)
        dst = os.path.join(build_setup.website_dir, "downloads", filename)
        Upload.Upload(src, self.options["url"])
        copy2(src, dst)
