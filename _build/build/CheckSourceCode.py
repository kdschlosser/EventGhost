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

import os
from os.path import join, splitext
from distutils.core import Command

PLUGINS = [
    "EventGhost",
    "System",
    "Window",
    "Mouse",
    "AtiRemoteWonder2",
    "Barco",
    "Conceptronic",
    "DBox2",
    "DesktopRemote",
    "DirectoryWatcher",
    "Fhz100Pc",
    "Conceptronic",
    "LogitechUltraX",
    "TechniSatUsb",
    "IgorPlugUSB",
    "Joystick",
    "Keyboard",
    "MediaPortal",
    "NetworkReceiver",
    "NetworkSender",
    "PowerDVD",
    "Serial",
    "Streamzap",
    "SysTrayMenu",
    "Task",
    "TechnoTrendIr",
    "TestPatterns",
    "Tira",
    "TVcentral",
    "UIR",
    "UIRT2",
    "USB-UIRT",
    "Webserver",
    "X10",
    "YARD",
    "ZoomPlayer",
]

HEADER = """# -*- coding: utf-8 -*-
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


class CheckSourceCode(Command):

    def initialize_options(self):
        self.build_setup = None

    def finalize_options(self):
        self.build_setup = self.distribution.get_command_obj('build')

    def run(self):
        source_dir = self.build_setup.source_dir
        search_dirs = [
            join(source_dir, "eg"),
            join(self.build_setup.build_dir),
        ]
        
        for plugin in PLUGINS:
            search_dirs.append(join(source_dir, "plugins", plugin))
        serial_dir = join(source_dir, "eg", "WinApi", "serial")

        for searchDir in search_dirs:
            for root, dirs, files in os.walk(searchDir):
                for filename in files:
                    if splitext(filename)[1].lower() in (".py", ".pyw"):
                        path = join(root, filename)
                        if path.startswith(serial_dir):
                            continue
                        self.check_header(path)
                        self.check_line_length(path)
                        # don't fix files that are versioned but haven't 
                        # changed
                        # TODO: something equivalent in git? repo.status
                        # itemStatus = status[paths.index(path)]
                        # if itemStatus.text_status == pysvn.wc_status_
                        # kind.normal:
                        #     continue
                        self.fix_trailing_whitespace(path)

    @staticmethod
    def check_header(path):
        """
        Checks if the source file has the right GPLv2 header.
        """
        source_file = open(path, "rt")
        header = source_file.read(len(HEADER))
        if header != HEADER:
            print "wrong file header:", path

    @staticmethod
    def check_line_length(path):
        """
        Checks if the source file doesn't exceed the line length.
        """
        source_file = open(path, "rt")
        for line in source_file.readlines():
            if len(line.rstrip()) > 79:
                print "line too long", path, line.rstrip()
                return

    @staticmethod
    def fix_trailing_whitespace(path):
        """
        Removes trailing whitespace from the source file.
        """
        with open(path, "rt") as f:
            old_content = f.read()
        
        lines = [line.rstrip() for line in old_content.splitlines()]
        while len(lines) and lines[-1].strip() == "":
            del lines[-1]
            
        lines.append("")
        lines.append("")
        
        new_content = "\n".join(lines)
        if old_content != new_content:
            with open(path, "wt") as f:
                f.write(new_content)
