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

import __builtin__
import os
import sys
from glob import glob
from os.path import basename, exists, join


def InstallPy2exePatch():
    """
    Tricks py2exe to include the win32com module.

    ModuleFinder can't handle runtime changes to __path__, but win32com
    uses them, particularly for people who build from sources.
    """
    try:
        import modulefinder
        import win32com
        for path in win32com.__path__[1:]:
            modulefinder.AddPackagePath("win32com", path)
        for extra in ["win32com.shell"]:
            __import__(extra)
            module = sys.modules[extra]
            for path in module.__path__[1:]:
                modulefinder.AddPackagePath(extra, path)
    except ImportError:  # IGNORE:W0704
        # no build path setup, no worries.
        pass


InstallPy2exePatch()


from py2exe import build_exe # NOQA

# Local imports
from Utils import EncodePath # NOQA


_compile = __builtin__.compile


# noinspection PyShadowingBuiltins
def compile(source, filename, *args):
    try:
        return _compile(source, filename, *args)
    except SyntaxError:
        ver = sys.version_info

        if ver[0] > 2 and ver[1] > 4:
            raise
        if 'import asyncio' in source or 'from asyncio' in source:
            return _compile('', filename, *args)
        raise


__builtin__.compile = compile

DLL_EXCLUDES = [
    "DINPUT8.dll",
    "w9xpopen.exe",
]

RT_MANIFEST = 24


class BuildInterpreters(build_exe.py2exe):

    def initialize_options(self):        
        self.build_setup = build_setup = (
            self.distribution.get_command_obj('build')
        )
        self.zip_name = "python%s.zip" % self.build_setup.py_version_str

        sys.path.append(EncodePath(build_setup.py_version_dir))
        
        orig_is_system_dll = build_exe.isSystemDLL

        def isSystemDLL(path):
            if basename(path).lower().startswith("api-ms-win-"):
                return 1
            else:
                return orig_is_system_dll(path)
            
        build_exe.isSystemDLL = isSystemDLL

        self.distribution.script_args = ["py2exe"]
        self.distribution.windows = [Target(build_setup)]
        self.distribution.verbose = 0
        self.distribution.zipfile = EncodePath(
            join(build_setup.library_name, self.zip_name)
        )
        self.distribution.options.update(
            dict(
                build=dict(build_base=join(build_setup.tmp_dir, "build")),
                py2exe=dict(
                    compressed=0,
                    includes=["encodings", "encodings.*", "Imports"],
                    excludes=build_setup.exclude_modules,
                    dll_excludes=DLL_EXCLUDES,
                    dist_dir=EncodePath(build_setup.source_dir),
                    custom_boot_script=join(
                        build_setup.data_dir, "Py2ExeBootScript.py"
                    ),
                )
            )
        )

        build_exe.py2exe.initialize_options(self)

    def finalize_options(self):
        build_exe.py2exe.finalize_options(self)

    def run(self):
        build_setup = self.build_setup

        library_dir = build_setup.library_dir
        if exists(library_dir):
            for filename in os.listdir(library_dir):
                path = join(library_dir, filename)
                if not os.path.isdir(path):
                    os.remove(path)
        
        wip_version = None
        if build_setup.app_version.startswith("WIP-"):
            # this is to avoid a py2exe warning when building a WIP version
            wip_version = build_setup.app_version
            build_setup.app_version = ".".join(
                build_setup.app_version.split("-")[1].split(".")
            )
            
        build_exe.py2exe.run(self)

        if wip_version:
            build_setup.app_version = wip_version

        dll_names = list(
            basename(name) for name in glob(join(library_dir, "*.dll"))
        )
        needed_dlls = []

        paths = [sys.prefix]
        if hasattr(sys, "real_prefix"):
            paths.append(sys.real_prefix)

        for path in paths:
            for _, _, files in os.walk(path):
                for filename in files:
                    if filename in dll_names:
                        needed_dlls.append(filename)

        for dll_name in dll_names:
            if dll_name not in needed_dlls:
                os.remove(join(library_dir, dll_name))


class Target:
    def __init__(self, build_setup):
        self.icon_resources = []
        
        icon_path = join(build_setup.docs_dir, "_static", "arrow.ico")
        if exists(icon_path):
            self.icon_resources.append((0, icon_path))
            
        icon_path = join(build_setup.docsDir, "_static", "ghost.ico")
        if exists(icon_path):
            self.icon_resources.append((6, icon_path))

        manifest = file(
            join(build_setup.pyVersionDir, "Manifest.xml")
        ).read() % build_setup.__dict__
        
        self.other_resources = [(RT_MANIFEST, 1, manifest)]
        self.name = build_setup.name
        self.description = build_setup.description
        self.company_name = build_setup.company_name
        self.copyright = build_setup.copyright
        self.dest_base = build_setup.name
        self.version = build_setup.app_version
        self.script = join(build_setup.source_dir, build_setup.main_script)


def RemoveAllManifests(scanDir):
    """
    Remove embedded manifest resource for all DLLs and PYDs in the supplied
    directory.

    This seems to be the only way how the setup can run with Python 2.6
    on Vista and above.
    """
    import ctypes
    BeginUpdateResource = ctypes.windll.kernel32.BeginUpdateResourceW
    UpdateResource = ctypes.windll.kernel32.UpdateResourceW
    EndUpdateResource = ctypes.windll.kernel32.EndUpdateResourceW

    for name in os.listdir(scanDir):
        path = os.path.join(scanDir, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in (".pyd", ".dll"):
            continue
        handle = BeginUpdateResource(path, 0)
        if not handle:
            raise ctypes.WinError()
        res = UpdateResource(handle, RT_MANIFEST, 2, 1033, None, 0)
        if not res:
            continue
        if not EndUpdateResource(handle, 0):
            raise ctypes.WinError()
