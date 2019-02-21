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
This script creates the EventGhost setup installer.
"""

import os
import sys
import tempfile

from setuptools import setup

setup(
    setup_requires=[
        'pywin32>=223',
        'py2exe_py2==0.6.9',
        'CommonMark==0.7.0',
        'comtypes>=1.1.2',
        'future>=0.15.2',
        'Pillow>=3.1.1',
        'py2exe_py2>=0.6.9',
        'PyCrypto==2.6.1',
        'Sphinx>=1.7.5',
        'ctypeslib==0.5.6 https://eventghost.github.io/dist/dependencies/ctypeslib-0.5.6-cp27-none-any.whl',
        'wxPython==3.0.2.0 https://eventghost.github.io/dist/dependencies/wxPython-3.0.2.0-cp27-none-win32.whl',
    ]
)

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



# Local imports
import build

if not build.VirtualEnv.Running() and build.VirtualEnv.Exists():
    build.VirtualEnv.Activate()


BASE_PATH = os.path.dirname(__file__)

if BASE_PATH is None:
    BASE_PATH = os.path.dirname(sys.argv[0])
if BASE_PATH is None:
    BASE_PATH = os.getcwd()

BASE_PATH = os.path.abspath(BASE_PATH)


NAME = 'EventGhost',
AUTHOR = 'Lars-Peter Voss,Torsten P., Kevin Schlosser',
URL = 'http://www.eventghost.net',
DESCRIPTION = 'EventGhost Automation Tool',
COPYRIGHT = u'Copyright © 2005-2019 EventGhost Project',
COMPANY = 'EventGhost Project',

DLL_EXCLUDES = [
    "DINPUT8.dll",
    "w9xpopen.exe",
]


if Is64bitInterpreter():
    print(
        "ERROR: Sorry, EventGhost can't be built with the 64-bit "
        "version of Python!"
    )
    sys.exit(1)

PY_VERSION_STRING = "%d%d" % sys.version_info[:2]
BUILD_DIR = BASE_PATH
DATA_DIR = os.path.join(BUILD_DIR, "data")
PY_VERSION_DIR = os.path.join(
    DATA_DIR,
    "Python%s" % PY_VERSION_STRING
)

if not os.path.exists(PY_VERSION_DIR):
    print(
        "ERROR: Sorry, EventGhost can't be built with Python %d.%d!"
        % sys.version_info[:2]
    )
    sys.exit(1)

SOURCE_DIR = os.path.abspath(os.path.join(BUILD_DIR, ".."))
LIBRARY_NAME = "lib%s" % PY_VERSION_STRING
LIBRARY_DIR = os.path.join(SOURCE_DIR, LIBRARY_NAME)
DOCS_DIR = os.path.join(DATA_DIR, "docs")
OUTPUT_DIR = os.path.join(BUILD_DIR, "output")
WEBSITE_DIR = os.path.join(OUTPUT_DIR, "website")
PACKAGES_DIR = os.path.join(LIBRARY_DIR, "site-packages")
APP_VERSION = None
APP_VERSION_INFO = None
TMP_DIR = tempfile.mkdtemp()
APP_NAME = NAME
BUILD_BASE = os.path.join(TMP_DIR, "build")

commit_message = os.environ.get("APPVEYOR_REPO_COMMIT_MESSAGE", "")

if commit_message.upper().startswith("VERBOSE:"):
    VERBOSE = True
else:
    VERBOSE = False


PYVERSION = "%d%d" % sys.version_info[:2]
PY_BASE_NAME = "py%s" % PYVERSION
PYW_BASE_NAME = "pyw%s" % PYVERSION
INTERPRETER_BUILD_TMP = tempfile.mkdtemp()
INTERPRETER_DIST_DIR = os.path.join(INTERPRETER_BUILD_TMP, "dist")

ZIP_FILE = "lib{0}/python{1}.zip".format(PYVERSION, PYVERSION)
MANIFEST = file(os.path.join(PY_VERSION_DIR, "Manifest.xml")).read()


CONSOLE = [
    dict(
        script=os.path.join(DATA_DIR, "py.py"),
        dest_base=PY_BASE_NAME,
        other_resources=[(24, 1, MANIFEST)],
    )
]
WINDOWS = [
    dict(
        script=os.path.join(DATA_DIR, "py.py"),
        dest_base=PYW_BASE_NAME,
        other_resources=[(24, 1, MANIFEST)],
    )
]

INCLUDES = [
    "CommonMark",
    "comtypes",
    "Crypto",
    "docutils",
    "isapi",
    "jinja2",
    "PIL",
    "pkg_resources",
    "pythoncom",
    "pywin32",
    "six",
    "win32com",
    "wx",
],
MAIN_SCRIPT = "EventGhost.pyw"

EXCLUDES = [
    "eg",
    "_imagingtk",
    "_tkinter",
    "cffi",  # bundled for no reason
    "comtypes.gen",
    # "ctypes.macholib",  # seems to be for Apple
    "curses",
    "distutils.command.bdist_packager",
    "distutils.mwerkscompiler",
    "FixTk",
    "FixTk",
    "gopherlib",
    "idlelib",
    "ImageGL",
    "ImageQt",
    "ImageTk",  # py2exe seems to hang if not removed
    "ipaddr",  # bundled for no reason
    "ipaddress",  # bundled for no reason
    "lib2to3",
    "PIL._imagingtk",
    "PIL.ImageTk",
    "pyasn1",  # bundles a broken version if not removed
    "pycparser",  # bundled for no reason
    "pywin",
    "simplejson",  # bundled for no reason
    "tcl",
    "test",
    "Tix",
    "Tkconstants",
    "tkinter",  # from `future`
    "Tkinter",
    "turtle",  # another Tkinter module
    "WalImageFile",  # odd syntax error in file
    "win32com.axdebug",
    "win32com.axscript",
    "win32com.demos",
    "win32com.gen_py",
    "wx.lib.floatcanvas",  # needs NumPy
    "wx.lib.plot",  # needs NumPy
    "wx.lib.vtk",
    "wx.tools.Editra",
    "wx.tools.XRCed",
    "wx.lib.pdfwin_old",
    "wx.lib.pdfviewer",
    "wx.lib.pubsub"
    "wx.lib.iewin",
    "wx.lib.iewin_old"
],

LIBRARY_DIST_DIR = EncodePath(SOURCE_DIR)
CUSTOM_BOOT_SCRIPT = os.path.join(DATA_DIR, "Py2ExeBootScript.py")
py2exe=dict(
                    compressed=0,
                    includes=["encodings", "encodings.*", "Imports"],
                    excludes=EXCLUDES,
                    dll_excludes=DLL_EXCLUDES,
                    dist_dir=LIBRARY_DIST_DIR,
                    custom_boot_script=CUSTOM_BOOT_SCRIPT
                    ),
                )
setup(
    name=NAME,
    author=AUTHOR,
    url=URL,
    description=DESCRIPTION,
    copyright=COPYRIGHT,
    company=COMPANY,
    verbose=int(VERBOSE),
    zipfile=ZIP_FILE,
    console=CONSOLE,
    windows=WINDOWS,
    cmdclass = dict(
        build_ext=current_template.build_ext,
        build=build.Build,
        build_changelog=build.ChangeLog,
        build_chmdocs=build.ChmDocs,
        build_htmldocs=build.HtmlDocs,
        build_installer=build.Installer,
        build_imports=build.Imports,
        build_interpreters=build.Interpreters,
        build_library=build.Library,
        build_static=build.StaticImports,
        build_version=build.VersionFile,
        build_website=build.Website,
        check_sourcecode=build.CheckSourceCode,
        release_github=build.ReleaseToGitHub,
        release_website=build.ReleaseToWeb
    ),
    options=dict(
        build=dict(
            build_base=BUILD_BASE,
            source_dir=SOURCE_DIR,
            library_name=LIBRARY_NAME,
            library_dir=LIBRARY_DIR,
            docs_dir=DOCS_DIR,
            output_dir=OUTPUT_DIR,
            website_dir=WEBSITE_DIR,
            packages_dir=PACKAGES_DIR,
            app_version=APP_VERSION,
            app_version_info=APP_VERSION_INFO,
            tmp_dir=TMP_DIR,
            app_name=APP_NAME,
            verbose=VERBOSE,
        ),
    build_interpreters=dict(
        compressed=0,
        dist_dir=INTERPRETER_DIST_DIR
    ),


build_imports
build_library

    ),
    #~ scripts=['src-lib/scripts/pyozw_check', 'src-manager/scripts/pyozw_shell'],
    ext_modules = [
        Extension(**current_template.ctx)
    ],
    data_files=data_files,
    install_requires = install_requires(),



)



class MyBuilder(builder.Builder):
    name =
    description =








MyBuilder().Start()
