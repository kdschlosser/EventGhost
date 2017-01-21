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

import eg


class EventInfo(object):
    iconIndex = eg.Icons.EVENT_ICON.index
    pluginEventPath = os.path.join(eg.configDir, 'events.py')
    eventInfoList = []
    undoInfoList = []
    name = None
    description = ''
    info = None
    pluginName = None
    event = ''
    path = ''
    plugins = {}

    def __init__(self, pluginInfo, eventString, eventDescription):
        if isinstance(pluginInfo, basestring):
            plugin = getattr(eg.plugins, pluginInfo, None)
            if plugin is not None:
                eventInfo = EventInfo.Create(
                    plugin.plugin.info,
                    eventString,
                    eventDescription
                )

                if eventInfo:
                    self.__dict__ = eventInfo.__dict__
        else:
            self.info = pluginInfo
            self.name = eventString
            self.description = eventDescription
            self.path = pluginInfo.path
            if self.info.eventPrefix:
                self.event = self.info.eventPrefix + '.' + self.name
            else:
                self.event = self.name
            self.pluginName = self.info.pluginName

    def __del__(self):
        if self not in EventInfo.undoInfoList:
            eventInfo = EventInfo(self.info, self.name, self.description)
            EventInfo.undoInfoList.append(eventInfo)

    def __repr__(self):
        if self.name is not None:
            return "eg.PluginInfo('%s', '%s', '%s')" % (
                self.info.pluginName,
                self.name,
                self.description
            )
        else:
            return ''

    @classmethod
    def Create(cls, pluginInfo, eventString, eventDescription):

        if not eventDescription:
            eventDescription = eg.text.EventDialog.noDescription

        eventList = pluginInfo.eventList

        for eventInfo in eventList:
            if eventInfo.name == eventString:
                return

        eventInfo = cls.__new__(cls, pluginInfo, eventString, eventDescription)

        return eventInfo

    @classmethod
    def Load(cls):
        if os.path.exists(cls.pluginEventPath):
            eventDict = {}
            eg.ExecFile(
                cls.pluginEventPath,
                {},
                eventDict
            )
            cls.eventInfoList = list(eventDict.get('eventInfoList', ()))

    @classmethod
    def Add(cls, eventString, plugin=None):

        def AddEventInfo(evt, plug):
            eventInfo = cls.Create(plug.info, evt)
            if eventInfo:
                cls.eventInfoList.append(eventInfo)
                plugin.info.eventList += (eventInfo,)

        if plugin is None and '.' in eventString:
            for plugin in eg.pluginList:
                eventPrefix = plugin.info.eventPrefix
                if not eventPrefix:
                    continue

                if eventPrefix in cls.plugins:
                    plugins = cls.plugins[eventPrefix]
                else:
                    plugins = []

                if plugin not in plugins:
                    plugins.append(plugin)
                cls.plugins[eventPrefix] = plugins[:]

                if eventString.startswith(eventPrefix):
                    eventString = '.'.join(eventString.split('.')[1:])
                    for plugin in plugins:
                        AddEventInfo(eventString, plugin)

        elif plugin is not None:
            AddEventInfo(eventString, plugin)

    @classmethod
    def Save(cls):
        for eventInfo in cls.undoInfoList[:]:
            plugin = getattr(eg.plugins, eventInfo.pluginName, None)
            if plugin or eg.document.isDirty:
                cls.eventInfoList.append(eventInfo)
            else:
                del(eventInfo)

        f = open(cls.pluginEventPath, 'w')
        if cls.eventInfoList:
            events = tuple(
                repr(event) for event in cls.eventInfoList if repr(event)
            )

            f.write('eventInfoList = (\n')
            for eventInfo in sorted(events):
                f.write('    %s,\n' % eventInfo)
            f.write(')\n')
        f.close()

    @classmethod
    def Nodes(cls):
        for plugin in eg.pluginList:
            info = plugin.info
            if info.eventList:
                yield cls.Node(plugin, info.eventList)

    class Node(object):

        def __init__(self, plugin, events):
            self.name = plugin.name
            self.description = plugin.description
            self.folderIndex = plugin.info.icon.folderIndex
            self.events = events
            self.path = plugin.info.path
            self.evalName = plugin.info.evalName

        def __iter__(self):
            for eventInfo in self.events:
                yield eventInfo
