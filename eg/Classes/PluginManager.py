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
from os.path import exists, isdir, join
from cStringIO import StringIO
from types import ClassType
from threading import Event

# Local imports
import eg
import PluginRepository


class PluginData:
    name = None
    description = None
    kind = ""
    author = ""
    version = ""
    icon = None
    canMultiLoad = False
    createMacrosOnAdd = False
    url = None
    help = None
    guid = None


class PluginManager:
    def __init__(self):
        self.database = {}
        self.ScanAllPlugins()

    def GetPlugin(self, guid, version):
        if guid in self.database:
            plugin_info = self.database[guid]
            if guid in eg.CORE_PLUGIN_GUIDS:
                return plugin_info
            if version == plugin_info.version:
                return plugin_info

        if version is None:
            version = PluginRepository.send(
                get_newest_version=dict(guid=guid)
            )

        plugin_data = PluginRepository.send(
            get_plugin=dict(guid=guid, version=version)
        )

        eg_plugin = StringIO()
        eg_plugin.write(plugin_data)
        event = Event()

        def Do():
            eg.PluginInstall.Import(eg_plugin)
            eg_plugin.close()
            self.ScanAllPlugins()
            event.set()

        eg.AsTasklet(Do)()

        while not event.isSet():
            event.wait(0.01)

        return self.database[guid]

    def GetPluginInfo(self, guid, version):
        if guid in self.database:
            plugin_info = self.database[guid]
            if version == plugin_info.version:
                return plugin_info

        plugin_info = PluginRepository.send(
                get_plugin_info=dict(guid=guid, version=version)
            )

        return ClassType('PluginInfo', (PluginData,), plugin_info)

    def GetPluginList(self):
        """
        Get a list of all PluginInfo for all plugins in the plugin directory
        """
        plugin_list = PluginRepository.send(get_plugin_list=None)
        plugin_list.sort(key=lambda pluginInfo: pluginInfo['name'].lower())

        for i, plugin_info in enumerate(plugin_list[:]):
            class PluginInfo:
                name = plugin_info['name']
                icon = plugin_info['icon']
                kind = plugin_info['kind']
                guid = plugin_info['guid']
                valid = True
                path = plugin_info['guid']
                url = ''


            plugin_list[i] = ClassType(
                'PluginInfo',
                (PluginInfo,),
                {}
            )

        return plugin_list

    def GetPluginVersionList(self, guid):
        version_list = PluginRepository.send(
            get_plugin_version_list=dict(guid=guid)
        )
        return version_list

    def OpenPlugin(self, guid, version, evalName, args, treeItem=None):
        moduleInfo = self.GetPlugin(guid, version)
        if moduleInfo is None:
            # we don't have such plugin
            clsInfo = NonexistentPluginInfo(ident, evalName)
        else:
            try:
                clsInfo = eg.PluginInstanceInfo.FromModuleInfo(moduleInfo)
            except eg.Exceptions.PluginLoadError:
                if evalName:
                    clsInfo = NonexistentPluginInfo(ident, evalName)
                else:
                    raise
        info = clsInfo.CreateInstance(args, evalName, treeItem)
        if moduleInfo is None:
            info.actions = ActionsMapping(info)
        return info

    @eg.TimeIt
    def ScanAllPlugins(self):
        """
        Scans the plugin directories to get all needed information for all
        plugins.
        """
        self.database.clear()

        # scan through all directories in the plugin directory
        for root in eg.pluginDirs:
            for dirname in os.listdir(root):
                # filter out non-plugin names
                if dirname.startswith(".") or dirname.startswith("_"):
                    continue
                pluginDir = join(root, dirname)
                if not isdir(pluginDir):
                    continue
                if not exists(join(pluginDir, "__init__.py")):
                    continue
                info = eg.PluginModuleInfo(pluginDir)
                self.database[info.guid] = info


class ActionsMapping(object):
    def __init__(self, info):
        self.info = info
        self.actions = {}

    def __getitem__(self, name):
        if name in self.actions:
            return self.actions[name]

        class Action(eg.ActionBase):
            pass
        Action.__name__ = name
        action = self.info.actionGroup.AddAction(Action, hidden=True)
        self.actions[name] = action
        return action

    def __setitem__(self, name, value):
        self.actions[name] = value


class LoadErrorPlugin(eg.PluginBase):
    def __init__(self):
        raise self.Exceptions.PluginLoadError

    def __start__(self, *dummyArgs):
        raise self.Exceptions.PluginLoadError


class NonexistentPlugin(eg.PluginBase):
    class text:
        pass

    def __init__(self):
        raise self.Exceptions.PluginNotFound

    def __start__(self, *dummyArgs):
        raise self.Exceptions.PluginNotFound

    def GetLabel(self, *dummyArgs):
        return '<Unknown Plugin "%s">' % self.name


class NonexistentPluginInfo(eg.PluginInstanceInfo):
    def __init__(self, guid, name):
        self.guid = guid
        self.name = name
        self.pluginName = name

        class Plugin(NonexistentPlugin):
            pass

        Plugin.__name__ = name
        self.pluginCls = Plugin
