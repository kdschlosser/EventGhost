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

from os import listdir
from os.path import join, basename, isdir, exists, splitext

# Local imports
import eg

def ImportAll():

    def Traverse(root, moduleRoot):
        for name in listdir(root):
            path = join(root, name)
            if isdir(path):
                name = basename(path)
                if name in [".svn", ".git", ".idea"]:
                    continue
                if not exists(join(path, "__init__.py")):
                    continue
                moduleName = moduleRoot + "." + name
                #print moduleName
                __import__(moduleName)
                Traverse(path, moduleName)
                continue
            base, ext = splitext(name)
            if ext != ".py":
                continue
            if base == "__init__":
                continue
            moduleName = moduleRoot + "." + base
            if moduleName in (
                "eg.StaticImports",
                "eg.CorePluginModule.EventGhost.OsdSkins.Default",
            ):
                continue
            #print moduleName
            __import__(moduleName)

    Traverse(join(eg.mainDir, "eg"), "eg")
    Traverse(eg.corePluginDir, "eg.CorePluginModule")



