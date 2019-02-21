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

"""
Build py.exe and pyw.exe for EventGhost
"""

import shutil
import sys
import tempfile
import warnings
from os.path import join


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import py2exe # NOQA
    from py2exe import build_exe # NOQA


class BuildInterpreters(build_exe.py2exe):

    def initialize_options(self):
        self.build_setup = None
        build_exe.py2exe.initialize_options(self)

    def finalize_options(self):
        self.build_setup = (
            self.distribution.get_command_obj('build')
        )
        
        build_exe.py2exe.finalize_options(self)

    def run(self):
        build_exe.py2exe.run(self)
        
        build_setup = self.build_setup
        
        shutil.copy(
            os.path.join(
                self.dist_dir,
                self.distribution.console[0]['dest_base'] + '.exe'
            ),
            build_setup.source_dir
        )
        shutil.copy(
            os.path.join(
                self.dist_dir,
                self.distribution.windows[0]['dest_base'] + '.exe'
            ),
            build_setup.source_dir
        )
        shutil.rmtree(self.tmp_dir)
