# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2016 EventGhost Project <http://www.eventghost.net/>
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


import sys
import fnmatch

import eg


class EventError(Exception):
    err = ''
    NotFound = None
    Duplicate = None
    NotRunning = None

    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return self.err % self.msg


class NotFound(EventError):
    err = '%s event not found.'


class NotRunning(EventError):
    err = 'There are no events currently running this thread.%s'


class Duplicate(EventError):
    err = 'There is an event already named %s.'


EventError.NotFound = NotFound
EventError.Duplicate = Duplicate
EventError.NotRunning = NotRunning


class EventManager(object):
    EventError = EventError
    threads = {}
    events = {}
    indent = 0
    result = None
    payload = None
    programCounter = None
    stopExecutionFlag = False
    programReturnStack = []
    eventString = None
    currentItem = None
    lastFoundWindows = []

    wildcardEvents = {}

    def AddEvent(self, prefix, suffix='', description=None, plugin=None):
        if plugin is None:
            for plugin in eg.pluginList:
                if plugin.info.eventPrefix == prefix:
                    break
                plugin = None

        if prefix not in self.events:
            self.events[prefix] = eg.EventInfo(None, prefix)

        if suffix:
            event = self.events[prefix][suffix]
        else:
            event = self.events[prefix]

        return event

    def GetEvent(self, eventString):
        items = eventString.split('.')
        prefix = items.pop(0)

        try:
            event = self.events[prefix]
        except KeyError:
            raise EventManager.EventError.NotFound(prefix)

        if items:
            event = event['.'.join(items)]

        return event

    @eg.LogIt
    def UnregisterEvent(self, macro, eventString):
        event = self.GetEvent(eventString)
        event.UnregisterMacro(macro)

    @eg.LogIt
    def RegisterEvent(self, macro, eventString):
        try:
            event = self.GetEvent(eventString)
        except EventManager.EventError.NotFound:
            items = eventString.split('.')
            prefix = items.pop(0)
            if items:
                event = self.AddEvent(prefix, '.'.join(items))
            else:
                event = self.AddEvent(prefix)

        event.RegisterMacro(macro)

    @eg.LogIt
    def Stop(self):
        def IterEvents(events):
            for key in events.keys():
                event = events[key]
                log = getattr(event, '_log', None)
                if log is not None:
                    log.Hide()
                    log.Destroy()
                IterEvents(event.events)
        IterEvents(self.events)

EventManager = EventManager()
