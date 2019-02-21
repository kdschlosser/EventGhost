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

import logging
import os
import sys
import tempfile

import VirtualEnv



from BuildChangelog import BuildChangelog as ChangeLog
from BuildDocs import BuildChmDocs as ChmDocs
from BuildDocs import BuildHtmlDocs as HtmlDocs
from BuildImports import BuildImports as Imports
from BuildInstaller import BuildInstaller as Installer
from BuildInterpreters import BuildInterpreters as Interpreters
from BuildLibrary import BuildLibrary as Library
from BuildStaticImports import BuildStaticImports as StaticImports
from BuildVersionFile import BuildVersionFile as VersionFile
from BuildWebsite import BuildWebsite as Website
from CheckSourceCode import CheckSourceCode
from ReleaseToGitHub import ReleaseToGitHub
from ReleaseToWeb import ReleaseToWeb
from WebsiteSync import WebsiteSync

from distutils.core import Command

# Local imports
from Logging import LogToFile
from Utils import (
    GetGitHubConfig,
    GetVersion,
    Is64bitInterpreter,
    IsCIBuild
)


logger = logging.getLogger()

# Local imports
    

BASE_PATH = os.path.dirname(__file__)


class Build(Command):

    def initialize_options(self):
        if Is64bitInterpreter():
            print(
                "ERROR: Sorry, EventGhost can't be built with the 64-bit "
                "version of Python!"
            )
            sys.exit(1)

        self.py_version_str = "%d%d" % sys.version_info[:2]
        self.build_dir = os.path.abspath(os.path.join(BASE_PATH, ".."))
        self.data_dir = os.path.join(self.build_dir, "data")
        self.py_version_dir = os.path.join(
            self.data_dir,
            "Python%s" % self.py_version_str
        )

        if not os.path.exists(self.py_version_dir):
            print(
                "ERROR: Sorry, EventGhost can't be built with Python %d.%d!"
                % sys.version_info[:2]
            )
            sys.exit(1)

        self.source_dir = os.path.abspath(os.path.join(self.build_dir, ".."))
        self.library_name = "lib%s" % self.py_version_str
        self.library_dir = os.path.join(self.source_dir, self.library_name)
        self.docs_dir = os.path.join(self.data_dir, "docs")
        self.output_dir = os.path.join(self.build_dir, "output")
        self.website_dir = os.path.join(self.output_dir, "website")

        self.packages_dir = os.path.join(self.library_dir, "site-packages")
        self.app_version = None
        self.app_version_info = None
        self.tmp_dir = tempfile.mkdtemp()
        self.app_name = self.name

        commit_message = os.environ.get("APPVEYOR_REPO_COMMIT_MESSAGE", "")

        if commit_message.upper().startswith("VERBOSE:"):
            self.distribution.verbose = 1
            self.verbose = True

        else:
            self.distribution.verbose = 0
            self.verbose = False
            
        self.git_config = dict(
            all_repos={
                "EventGhost/EventGhost": dict(
                    all_branches=["master"],
                    def_branch="master",
                    name="EventGhost"
                ),
            },
            branch="master",
            repo="EventGhost",
            repo_full="EventGhost/EventGhost",
            token="",
            user="EventGhost"
        )

    def finalize_options(self):
        sys.path.append(self.source_dir)
        sys.path.append(self.packages_dir)
        
        try:
            self.git_config = GetGitHubConfig()
        except Exception as e:
            msg = (
                "WARNING: To change version or release to GitHub, you must:\n"
                "    $ git config --global github.user <your github username>\n"
                "    $ git config --global github.token <your github token>\n"
                "To create a token, go to: https://github.com/settings/tokens\n"
            )
            if type(e) is ValueError:
                msg = "WARNING: Specified `github.token` is invalid!\n" + msg
            if not IsCIBuild():
                print msg
            else:
                self.git_config['token'] = os.environ["GITHUB_TOKEN"]
                
    def run(self):
        os.chdir(self.build_dir)

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
            
        LogToFile(os.path.join(self.output_dir, "Build.log"), self.verbose)

        from CheckDependencies import CheckDependencies
        if not CheckDependencies(self):
            sys.exit(1)


from setuptools import setup


class (object):
    
    
    
    
    def __init__(self):
    def ParseArgs(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-b", "--build",
            action="store_true",
            help="build imports, lib%s, and interpreters" % self.pyVersionStr,
        )
        parser.add_argument(
            "-c", "--check",
            action="store_true",
            help="check source code for issues",
        )
        parser.add_argument(
            "-m", "--make-env",
            action="store_true",
            help="auto-install dependencies into a virtualenv",
        )
        parser.add_argument(
            "-p", "--package",
            action="store_true",
            help="build changelog, docs, and setup.exe",
        )
        parser.add_argument(
            "-r", "--release",
            action="store_true",
            help="release to github and web if credentials available",
        )
        parser.add_argument(
            "-s", "--sync",
            action="store_true",
            help="build and synchronize website",
        )
        parser.add_argument(
            "-d", "--docs",
            action="store_true",
            help="build and synchronize usr and dev docs",
        )
        parser.add_argument(
            "-u", "--url",
            dest="websiteUrl",
            default='',
            type=str,
            help="sftp url for doc synchronizing",
        )
        parser.add_argument(
            "-vv", "--verbose",
            action="store_true",
            help="give a more verbose output",
        )
        parser.add_argument(
            "-v", "--version",
            action="store",
            help="package as the specified version",
        )
        return parser.parse_args()
