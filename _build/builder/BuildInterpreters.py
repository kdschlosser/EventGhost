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


PYVERSION = "%d%d" % sys.version_info[:2]
PY_BASE_NAME = "py%s" % PYVERSION
PYW_BASE_NAME = "pyw%s" % PYVERSION


class BuildInterpreters(build_exe.py2exe):

    def initialize_options(self):
        self.build_setup = build_setup = (
            self.distribution.get_command_obj('build')
        )
        self.tmp_dir = tmp_dir = tempfile.mkdtemp()
        
        manifest = file(
            join(build_setup.py_version_dir, "Manifest.xml")
        ).read()

        self.distribution.zipfile = "lib{0}/python{1}.zip".format(
            PYVERSION,
            PYVERSION
        )

        self.distribution.script_args = ["py2exe"]
        self.distribution.options.update(
            dict(
                build=dict(build_base=join(tmp_dir, "build")),
                py2exe=dict(compressed=0, dist_dir=join(tmp_dir, "dist"))
            )
        )

        self.distribution.windows = [
            dict(
                script=join(build_setup.data_dir, "py.py"),
                dest_base=PYW_BASE_NAME,
                other_resources=[(24, 1, manifest)],
            )
        ]
        self.distribution.console = [
            dict(
                script=join(build_setup.data_dir, "py.py"),
                dest_base=PY_BASE_NAME,
                other_resources=[(24, 1, manifest)],
            )
        ]
        self.distribution.verbose = 0
        
        build_exe.py2exe.initialize_options(self)

    def finalize_options(self):
        build_exe.py2exe.finalize_options(self)

    def run(self):
        build_exe.py2exe.run(self)
        
        build_setup = self.build_setup
        
        shutil.copy(
            join(self.tmp_dir, "dist", PY_BASE_NAME + ".exe"),
            build_setup.sourceDir
        )
        shutil.copy(
            join(self.tmp_dir, "dist", PYW_BASE_NAME + ".exe"),
            build_setup.sourceDir
        )
        shutil.rmtree(self.tmp_dir)
