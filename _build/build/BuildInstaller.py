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
import _winreg
from distutils.core import Command
from Utils import EncodePath, StartProcess, CaseInsensitiveList, ListDir


SKIP_IF_UNCHANGED = CaseInsensitiveList(
    r"plugins\Task\TaskHook.dll",
)


class InnoSetupError(Exception):
    pass


class BuildInstaller(Command):
    """
    Create and compile the Inno Setup installer script.
    """

    def initialize_options(self):
        self.build_setup = None
        self.changelog_path = None
        self.py_path = None
        self.pyw_path = None
        self.version_path = None
        self.template_path = None
        self.inno_sections = {}

    def finalize_options(self):
        self.build_setup = build_setup = (
            self.distribution.get_command_obj('build')
        )
        self.changelog_path = os.path.join(
            build_setup.source_dir,
            "CHANGELOG.md"
        )
        self.py_path = os.path.join(
            build_setup.source_dir,
            "py%s.exe" % build_setup.py_version_str
        )
        self.pyw_path = os.path.join(
            build_setup.source_dir,
            "pyw%s.exe" % build_setup.py_version_str
        )
        self.version_path = os.path.join(
            build_setup.tmp_dir,
            "VersionInfo.py"
        )
        self.template_path = os.path.join(
            build_setup.data_dir,
            "InnoSetup.template"
        )
        self.script_path = os.path.join(
            build_setup.tmp_dir,
            "Setup.iss"
        )
        self.includes_path = os.path.join(
            build_setup.py_version_dir,
            "Root Includes.txt"
        )

    @property
    def files(self):
        """
        Return all files needed by the installer.

        The code scans for all files in the working copy and adds
        them to the list, except if a "noinstall" property is set for the file
        or a parent directory of the file.

        Plugins with a "noinclude" file are also skipped.
        """
        files = set(ListDir(self.build_setup.source_dir, [], fullpath=False))

        with open(self.includes_path, "r") as f:
            root_includes = CaseInsensitiveList(*f.read().strip().split("\n"))

        no_includes = [".", "_"]
        core_plugins = []
        for f in files.copy():
            if f.endswith("noinclude"):
                no_includes.append(f.replace("noinclude", ""))
            elif f.endswith("core-plugin"):
                core_plugins.append(f.replace("core-plugin", ""))
                files.remove(f)

        install_files = []
        for f in files:
            if not f.startswith(tuple(no_includes)):
                if f.count("\\") == 0 and f not in root_includes:
                    pass
                else:
                    #if f.startswith(tuple(coreplugins)):
                    install_files.append([f, "{app}"])
                    #else:
                    #    # Install to ProgramData\EventGhost\plugins
                    #    installFiles.append([f,
                    #        "{commonappdata}\\%s" % self.appName])

        return install_files

    def run(self):
        build_setup = self.build_setup

        for filename, prefix in self.files:
            self.add_file(
                os.path.join(build_setup.source_dir, filename),
                os.path.dirname(filename),
                ignore_version=(filename not in SKIP_IF_UNCHANGED),
                prefix=prefix
            )

        changelog_path = os.path.join(
            self.build_setup.output_dir,
            "CHANGELOG.md"
        )

        if os.path.exists(changelog_path):
            self.changelog_path = changelog_path

        self.add_file(self.changelog_path)
        self.add_file(self.py_path, dest_name="py.exe")
        self.add_file(self.pyw_path, dest_name="pyw.exe")
        self.add_file(self.version_path, dest_dir="eg\\Classes")
        self.run_inno_setup()

    @property
    def inno_compiler_path(self):
        try:
            key = _winreg.OpenKey(
                _winreg.HKEY_LOCAL_MACHINE,
                (
                    "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\"
                    "Uninstall\\Inno Setup 5_is1"
                )
            )
            install_path = _winreg.QueryValueEx(key, "InstallLocation")[0]
            _winreg.CloseKey(key)
        except WindowsError:
            return None
        install_path = os.path.join(install_path, "ISCC.exe")
        if not os.path.exists(install_path):
            raise RuntimeError('Unable to locate InnoSetup compiler')

        return install_path

    def add_line(self, section, line):
        """
        Adds a line to the INI section.
        """
        if section not in self.inno_sections:
            self.inno_sections[section] = []
        self.inno_sections[section].append(EncodePath(line))

    def add_file(
        self,
        source,
        dest_dir="",
        dest_name=None,
        ignore_version=True,
        prefix="{app}"
    ):
        """
        Adds a file to the [Files] section.
        """
        line = 'Source: "%s"; DestDir: "%s\\%s"' % (
            os.path.abspath(source), prefix, dest_dir
        )
        if dest_name is not None:
            line += '; DestName: "%s"' % dest_name
        if ignore_version:
            line += '; Flags: ignoreversion'

        self.add_line("Files", line)

    def run_inno_setup(self):
        """
        Finishes the setup, writes the Inno Setup script and calls the
        Inno Setup compiler.
        """

        with open(self.template_path, "rt") as f:
            inno_script_template = f.read()

        iss_file = open(self.script_path, "w")
        template_dict = {}

        for key, value in self.build_setup.__dict__.items():
            if isinstance(value, unicode):
                value = EncodePath(value)
            template_dict[key] = value

        iss_file.write(inno_script_template % template_dict)

        for section, lines in self.innoSections.iteritems():
            iss_file.write("[%s]\n" % section)
            for line in lines:
                iss_file.write("%s\n" % line)
        iss_file.close()

        res = StartProcess(self.inno_compiler_path, self.script_path, "/Q")
        if res != 0:
            raise InnoSetupError




