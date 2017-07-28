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


from threading import Lock
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
    _wildcardEvents = {}

    _lock = Lock()

    def __iter__(self):
        return iter(self.events.keys())

    def __contains__(self, item):
        if '*' in item or '?' in item:
            return False

        items = item.split('.')
        if items[0] in self.events:
            event = self.events[items.pop(0)]
        else:
            return False

        while items:
            try:
                event = event[items.pop(0)]
            except EventManager.EventError.NotFound:
                return False
        return True

    def __getitem__(self, item):
        sections = item.split('.')
        prefix = sections.pop(0)

        try:
            event = self.events[prefix]
            while sections:
                event = event[sections.pop(0)]
            return event
        except (KeyError, EventManager.EventError.NotFound):
            raise EventManager.EventError.NotFound(item)

    def AddEvent(self, prefix, suffix='', description=None, plugin=None):
        self._lock.acquire()
        try:

            if suffix:
                eventString = prefix + '.' + suffix
            else:
                eventString = prefix

            if plugin is None:
                for plugin in eg.pluginList:
                    if plugin.info.eventPrefix == prefix:
                        break
                    plugin = None

            if prefix in self.events:
                event = self.events[prefix]
                possible_wildcard = False
            else:
                self.events[prefix] = event = eg.EventInfo(None, prefix)
                possible_wildcard = True

            if suffix:
                suffix = suffix.split('.')
                while suffix:
                    suf = suffix.pop(0)
                    try:
                        event = event[suf]
                    except EventManager.EventError.NotFound:
                        evt = eg.EventInfo(event, suf)
                        event[suf] = evt
                        event = evt
                        possible_wildcard = True

            if possible_wildcard:
                for pattern, macros in self._wildcardEvents.items():
                    if fnmatch.fnmatchcase(eventString, pattern):
                        for macro in macros:
                            event.RegisterMacro(macro)
            return event
        finally:
            self._lock.release()

    def GetEvent(self, eventString):
        self._lock.acquire()
        try:
            if eventString not in self:
                raise EventManager.EventError.NotFound(eventString)

            items = eventString.split('.')
            prefix = items.pop(0)

            event = self.events[prefix]
            while items:
                event = event[items.pop(0)]

            return event
        finally:
            self._lock.release()

    @eg.LogIt
    def UnregisterEvent(self, macro, event):
        if isinstance(event, tuple):
            for e in event:
                e.UnregisterMacro(macro)
        else:
            event = self.GetEvent(event)
            event.UnregisterMacro(macro)

    @eg.LogIt
    def RegisterEvent(self, macro, eventString):

        items = eventString.split('.')
        prefix = items.pop(0)
        events = ()

        if '*' in eventString or '?' in eventString:
            if eventString in self._wildcardEvents:
                self._wildcardEvents[eventString] += [macro]
            else:
                self._wildcardEvents[eventString] = [macro]

            def iter_events(evt, sections, evts=()):
                section = sections.pop(0)

                for name in evt:
                    e = evt[name]
                    if '*' in section and fnmatch.fnmatchcase(name, section):
                        evts += (e,)
                        evts += iter_events(e, ['*'], evts)
                    elif '?' in section and fnmatch.fnmatchcase(name, section):
                        if sections:
                            evts += iter_events(e, sections, evts)
                        else:
                            evts += (e,)
                    elif name == section and not sections:
                        evts += (e,)
                        break
                return evts

            if '*' in prefix:
                for evt_name in self:
                    if fnmatch.fnmatchcase(evt_name, prefix):
                        event = self.events[evt_name]
                        events += (event,)
                        events += iter_events(event, ['*'])
            elif '?' in prefix:
                for evt_name in self:
                    if fnmatch.fnmatchcase(evt_name, prefix):
                        event = self.events[evt_name]
                        if items:
                            events += iter_events(event, items)
                        else:
                            events += (event,)
            else:
                event = self.events[prefix]
                if items:
                    events += iter_events(event, items)
                else:
                    events += (event,)
        else:
            if eventString in self:
                event = self.GetEvent(eventString)
            else:
                event = self.AddEvent(prefix, '.'.join(items))

            events += (event,)

        for event in events:
            event.RegisterMacro(macro)

        return events

EventManager = EventManager()
