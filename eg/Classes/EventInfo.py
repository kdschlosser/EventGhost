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


def GetPluginName(eventInfo):
    try:
        return eventInfo.info.pluginName
    except AttributeError:
        return eventInfo.info


class EventInfo(object):
    pluginEventPath = os.path.join(eg.configDir, 'events.py')
    eventInfoList = []
    undoInfoList = []
    plugins = {}

    @classmethod
    def Create(cls, pluginInfo, eventString, eventDescription):
        if eventDescription is None:
            eventDescription = ''

        if not pluginInfo.eventList:
            pluginInfo.eventList = ()

        eventList = pluginInfo.eventList
        for eventInfo in eventList:
            if eventInfo.name == eventString:
                return

        return EventInfo.Event(pluginInfo, eventString, eventDescription)

    @classmethod
    def Add(cls, eventString, plugin=None):

        def AddEventInfo(evt, plug):
            eventInfo = cls.Create(plug.info, evt, '')
            if eventInfo:
                eventInfo.added = True
                plug.info.eventList += (eventInfo,)
                for evtInfo in cls.eventInfoList:
                    if evtInfo.event == eventInfo.event:
                        return
                cls.eventInfoList.append(eventInfo)

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
    def Load(cls):
        if os.path.exists(cls.pluginEventPath):
            eventDict = {}
            eg.ExecFile(cls.pluginEventPath, {}, eventDict)
            events = list(
                event for events in eventDict.values()
                for event in events if event.name
            )
            cls.eventInfoList.extend(events)
            print cls.eventInfoList

    @classmethod
    def Save(cls):
        events = {}

        def AddEvent(evtInfo):
            plgName = GetPluginName(evtInfo)
            if plgName not in events:
                events[plgName] = []
            events[plgName].append(repr(evtInfo))

        for eventInfo in cls.undoInfoList[:]:
            plugin = getattr(eg.plugins, eventInfo.pluginName, None)
            if plugin or eg.document.isDirty or not eventInfo.added:
                AddEvent(eventInfo)
            else:
                del(eventInfo)

        for eventInfo in cls.eventInfoList:
            AddEvent(eventInfo)

        lines = ''
        for pluginName in sorted(events.keys()):
            line = '%s = [\n' % pluginName
            for eventInfo in sorted(events[pluginName]):
                line += '    %s,\n' % eventInfo
            lines += line[:-2] + '\n]\n\n'

        if lines:
            lines = lines[:-1]

        with open(cls.pluginEventPath, 'w') as f:
            f.write(lines)

    @classmethod
    def Nodes(cls):
        for plugin in eg.pluginList:
            if plugin.info.eventList:
                yield cls.Node(plugin.info)

    class Node(object):
        pluginInfo = None

        def __init__(self, pluginInfo):
            self.pluginInfo = pluginInfo

        def __getattr__(self, item):
            if hasattr(self.pluginInfo, item):
                return getattr(self.pluginInfo, item)

            raise AttributeError(
                '%r does not have attribute %s' % (self, item)
            )

        def __iter__(self):
            for eventInfo in self.pluginInfo.eventList:
                yield eventInfo


    class Event(object):
        icon = eg.Icons.EVENT_ICON
        name = None
        description = None
        info = None
        event = None
        path = ''
        added = False

        def __init__(self, pluginInfo, eventString, eventDescription=None):
            if eventDescription is None:
                for plugin in eg.pluginList:
                    if plugin.info.pluginName == pluginInfo:
                        EventInfo.Add(eventString, plugin)
                        del(self)
                        return
            else:
                self.path = pluginInfo.path
                if pluginInfo.eventPrefix:
                    self.event = pluginInfo.eventPrefix + '.' + eventString

                if not eventDescription:
                    eventDescription = eg.text.EventDialog.noDescription

            if self.event is None:
                self.event = eventString

            self.name = eventString
            self.description = eventDescription
            self.info = pluginInfo

        def __del__(self):
            if self.name:
                eventInfo = EventInfo.Event(
                    self.info,
                    self.name,
                    self.description
                )
                if not self.added:
                    eventInfo.added = False
                    eventInfo.info = eventInfo.info.pluginName
                EventInfo.undoInfoList.append(eventInfo)

        def __repr__(self):
            if self.name is None:
                return ''

            return (
                "eg.EventInfo.Event('%s', '%s')" %
                (GetPluginName(self), self.name)
            )
