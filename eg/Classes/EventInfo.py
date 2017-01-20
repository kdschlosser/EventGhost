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


class EventInfo:
    icon = eg.Icons.EVENT_ICON
    pluginEventPath = None
    undoPlugins = None
    pluginEvents = None

    def __init__(self, name, description, info):
        self.name = name
        if description:
            self.description = description
        else:
            self.description = ""
        self.info = info

    @classmethod
    def Load(cls):
        cls.pluginEventPath = os.path.join(eg.configDir, 'events.py')
        cls.undoPlugins = {}
        cls.pluginEvents = {}

        if os.path.exists(cls.pluginEventPath):
            eg.ExecFile(
                cls.pluginEventPath,
                {},
                cls.pluginEvents
            )
        for plugin in eg.pluginList:
            pluginName = cls._GetPluginName(plugin)
            if pluginName in cls.pluginEvents:
                if plugin.info.eventList:
                    savedEvents = list(cls.pluginEvents[pluginName])
                    pluginEvents = tuple(
                        event[0] for event in plugin.info.eventList
                    )

                    for event in savedEvents[:]:
                        if event in pluginEvents:
                            savedEvents.remove(event)
                        else:
                            plugin.info.eventList += ((event, u''),)

                    cls.pluginEvents[pluginName] = tuple(savedEvents)

                else:
                    plugin.info.eventList = tuple(
                        (event, u'') for event in cls.pluginEvents[pluginName]
                    )

    @classmethod
    def Add(cls, plugin, event):
        event = unicode(event)
        if plugin.info.eventList is None:
            plugin.info.eventList = ((event, u''),)
        else:
            eventList = tuple(item[0] for item in plugin.info.eventList)
            if event in eventList:
                event = None

        if event is not None:
            eventList = cls.GetEvents(plugin)

            if event not in eventList:
                eventList += (event,)
                cls.pluginEvents[cls._GetPluginName(plugin)] = eventList

    @classmethod
    def _GetPluginName(cls, plugin):
        return plugin.__module__.split('.')[2]

    @classmethod
    def RemovePlugin(cls, plugin):
        pluginName = cls._GetPluginName(plugin)
        if pluginName in cls.pluginEvents:
            cls.undoPlugins[pluginName] = cls.pluginEvents[pluginName][:]
            del (cls.pluginEvents[pluginName])

    @classmethod
    def GetEvents(cls, plugin):
        pluginName = cls._GetPluginName(plugin)

        if pluginName in cls.pluginEvents:
            return cls.pluginEvents[pluginName]
        else:
            return ()

    @classmethod
    def Undo(cls):
        for pluginName in cls.undoPlugins.keys():
            cls.pluginEvents[pluginName] = cls.undoPlugins[pluginName]

    @classmethod
    def Save(cls):
        if eg.document.isDirty:
            cls.Undo()

        with open(cls.pluginEventPath, 'w') as f:
            for pluginName in sorted(cls.pluginEvents.keys()):
                if not pluginName.startswith('_'):
                    line = '%s = (\n' % pluginName
                    for event in cls.pluginEvents[pluginName]:
                        line += '    %r,\n' % event
                    line += '\n)\n\n'

                    f.write(line)
