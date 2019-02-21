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



# Local imports
import builder



from builder.CheckSourceCode import CheckSourceCode  # NOQA
from builder.BuildStaticImports import BuildStaticImports  # NOQA
from builder.BuildImports import BuildImports  # NOQA
from builder.BuildInterpreters import BuildInterpreters  # NOQA
from builder.BuildLibrary import BuildLibrary  # NOQA
from builder.BuildDocs import BuildChmDocs, BuildHtmlDocs  # NOQA
from builder.ReleaseToGitHub import ReleaseToGitHub  # NOQA
from builder.BuildWebsite import BuildWebsite  # NOQA
from builder.BuildChangelog import BuildChangelog  # NOQA

TASKS = [
    BuildVersionFile,
    CheckSourceCode,
    BuildStaticImports,
    BuildImports,
    BuildInterpreters,
    BuildLibrary,
    BuildChangelog,
    BuildChmDocs,
    BuildInstaller,
    ReleaseToGitHub,
    ReleaseToWeb,
    BuildWebsite,
    BuildHtmlDocs,
    SynchronizeWebsite,
]

def Main(buildSetup):
    """
    Main task of the script.
    """
    for task in buildSetup.tasks:
        if task.activated:
            logger.log(22, "--- {0}".format(task.description))
            task.DoTask()
            logger.log(22, "")
    logger.log(22, "--- All done!")
