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


import wx
import time
import threading
import random
import string
from fnmatch import fnmatchcase

import eg


class Text(eg.TranslatableStrings):
    noDescription = "<i>No description available</i>"


def iter_events(child, instances=()):
    for eventName in child:
        instances += (child[eventName],)
        instances = iter_events(child[eventName], instances)
    return instances


class EventThread(object):

    def __init__(
        self,
        event_name,
        payload=None,
    ):
        self._thread = None
        self.queue_time = time.time()
        self._running_macro = ''
        self._running_action = ''
        self._payload = payload
        self._result = None
        self._start_time = 0
        self.run_time = 0
        self.stop_time = 0
        self.stop_event = threading.Event()
        self.event_name = event_name
        self.indent = 0
        self.isEnded = False
        self.programCounter = None
        self.skipEvent = False
        self.stopExecutionFlag = False
        self.programReturnStack = []
        self.currentItem = None
        self.shouldEnd = threading.Event()
        self.lastFoundWindows = []
        self._percent_actions = 0
        self._percent_macros = 0
        self.macro_len = 0
        self.event_len = 0
        self.count = 0
        self.l = 0
        self.r = 0
        eg.Bind('Events.Shutdown', self.OnShutdown)

    def Update(self):
        if eg.eventRunningDialog is not None:
            eg.eventRunningDialog.EventUpdate(update_object=self)

    @property
    def thread(self):
        return self._thread

    @thread.setter
    def thread(self, thread):
        self._thread = thread
        if eg.eventRunningDialog is not None:
            eg.eventRunningDialog.EventUpdate(add_object=self)

    @property
    def running_macro(self):
        return self._running_macro

    @running_macro.setter
    def running_macro(self, running_macro):
        self._running_macro = running_macro
        self.Update()

    @property
    def running_action(self):
        return self._running_action

    @running_action.setter
    def running_action(self, running_action):
        self._running_action = running_action
        self.Update()

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, payload):
        self._payload = payload
        self.Update()

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, result):
        self._result = result
        self.Update()

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, start_time):
        self._start_time = start_time
        self.Update()

    @property
    def percent_actions(self):
        return self._percent_actions

    @property
    def percent_macros(self):
        return self._percent_macros

    @property
    def id(self):
        return self.thread.ident

    @property
    def stop(self):
        return self.stop_event.isSet()

    @stop.setter
    def stop(self, flag=True):
        if flag:
            self.stop_event.set()

    def Wait(self, timeout=None):
        self.stop_event.wait(timeout)

    def SetProcessingState(self, l, r, colour):
        if self.macro_len and l:
            self._percent_actions = float(l * 100) / float(self.macro_len)
            self.l = int(float(l * 5) / float(self.macro_len))
        else:
            self._percent_actions = 0.0
            self.l = 1

        if self.event_len and r:
            self._percent_macros = float(r * 100) / float(self.event_len)

            self.r = int(float(r * 5) / float(self.event_len))
        else:
            self._percent_macros = 0.0
            self.r = 1

        self.Update()
        eg.taskBarIcon.ChangeIcon(self.l, self.r, colour)

    def OnShutdown(self, evt):
        self.stop = True
        try:
            self.thread.join()
        except threading.ThreadError:
            pass

    def Close(self):
        if eg.eventRunningDialog is not None:
            eg.eventRunningDialog.EventUpdate(remove_object=self)
        eg.Unbind('Events.Shutdown', self.OnShutdown)


class EventInfo(object):

    def __init__(self, parent, name):
        self.name = name
        self.description = Text.noDescription
        self.payloads = ()
        self.macros = []
        self.upFuncList = []
        self.children = dict()
        self.source = eg
        self._log = None
        self._lock = threading.Lock()
        self._threads = {}
        self._colour = None
        self._icon_colour = None

        colour = (
            random.randint(170, 255),
            random.randint(170, 255),
            random.randint(170, 255)
        )
        self.colour = colour

        if parent is None:
            self.string = name
            self.prefix = name
            self.suffix = None
        else:
            self.string = parent.string + '.' + name
            self.prefix = parent.prefix
            if parent.suffix is not None:
                self.suffix = parent.suffix + '.' + name
            else:
                self.suffix = name

        self.eventString = self.string

    @property
    def queue(self):
        res = list(
            [event.queue_time, event] for event in self._threads.values()
        )
        return list(event[1] for event in sorted(res))

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]

        thread = threading.currentThread()
        if thread in self._threads:
            if hasattr(self._threads[thread], item):
                return getattr(self._threads[thread], item)

        raise AttributeError

    def __setattr__(self, key, value):
        event_thread_attribs = (
            'thread',
            'id',
            'shouldEnd',
            'indent',
            'isEnded',
            'programCounter',
            'skipEvent',
            'stopExecutionFlag',
            'programReturnStack',
            'currentItem',
            'lastFoundWindows',
            'payload',
            'result',
            'stop'
        )

        if key in event_thread_attribs:
            thread = threading.currentThread()
            if thread in self._threads:
                setattr(self._threads[thread], key, value)
            else:
                raise AttributeError
        else:
            object.__setattr__(self, key, value)

    @property
    def log(self):
        if self._log is None:
            self._log = eg.EventLog()
        return self._log

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, colour):
        if isinstance(colour, wx.Colour):
            colour = (colour.Red, colour.Green, colour.Blue)
        self._colour = colour
        self._icon_colour = string.join(map(chr, colour), '') * 6

    def __iter__(self):
        return iter(self.children.keys())

    def __contains__(self, item):
        return item in self.children.keys()

    def __delitem__(self, key):
        if key not in self:
            raise eg.EventManager.EventError.NotFound(key)
        del(self.children[key])

    def __getitem__(self, item):
        sections = item.split('.')
        section = sections.pop(0)

        try:
            event = self.children[section]
            while sections:
                event = event[sections.pop(0)]
            return event
        except (KeyError, eg.EventManager.EventError.NotFound):
            raise eg.EventManager.EventError.NotFound(item)

    def __setitem__(self, key, value):
        if key in self:
            raise eg.EventManager.EventError.Duplicate(key)
        self.children[key] = value

    def RegisterMacro(self, macro):
        eg.PrintDebugNotice(
            "EventManager['%s'].RegisterMacro('%s')" %
            (self.string, macro.parent.GetLabel())
        )
        self.macros.append(macro)

    def UnregisterMacro(self, macro):
        eg.PrintDebugNotice(
            "EventManager['%s'].UnregisterMacro('%s')" %
            (self.string, macro.parent.GetLabel())
        )
        self.macros.remove(macro)

    @eg.LogIt
    def _Execute(self, et):
        self._lock.acquire()
        eg.EventManager.threads[et.thread] = self
        et.start_time = time.time()
        eg.Notify('Event.Dialog.Update', False)

        try:
            if not et.stop:
                if self.string in eg.notificationHandlers:
                    nHandlers = eg.notificationHandlers[self.string]
                    for listener in nHandlers.listeners:
                        if listener(self) is True:
                            return

                activeHandlers = set()
                for macro in self.macros:
                    obj = macro
                    while obj:
                        if not obj.isEnabled:
                            break
                        obj = obj.parent
                    else:
                        activeHandlers.add(macro)

                for listener in eg.log.eventListeners:
                    listener.LogEvent(self)

                if eg.config.onlyLogAssigned and len(activeHandlers) == 0:
                    self.SetStarted()
                    return

                eg.log.LogEvent(self)

                activeHandlers = sorted(
                    activeHandlers,
                    key=eg.EventItem.GetPath
                )

                et.event_len = len(activeHandlers)
                et.SetProcessingState(0, 0, self._icon_colour)

                for i, eventHandler in enumerate(activeHandlers):
                    try:
                        if isinstance(eventHandler.parent, eg.MacroItem):
                            et.macro_len = len(
                                list(
                                    child for child in eventHandler.parent.childs
                                    if isinstance(child, eg.document.ActionItem)
                                )
                            )
                            et.running_macro = eventHandler.parent.GetLabel()
                            macro_adjust = (
                                len(eventHandler.parent.childs) - et.macro_len
                            )

                            def update_icon(idx):
                                if idx is None:
                                    idx = macro_adjust

                                et.running_action = (
                                    eventHandler.parent.childs[idx].GetLabel()
                                )
                                et.SetProcessingState(
                                    idx - macro_adjust - 1,
                                    i,
                                    self._icon_colour
                                )
                                et.count += 1
                        else:
                            def update_icon(idx=None):
                                pass

                        et.programCounter = (eventHandler.parent, None)
                        et.indent = 1
                        if et.stop:
                            break
                        eg.RunProgram(update_icon)

                    except:
                        eg.PrintTraceback()
                    if et.skipEvent:
                        break

                self.SetStarted()
        except:
            pass

        finally:
            et.stop = True
            del eg.EventManager.threads[et.thread]
            del self._threads[et.thread]

            et.stop_time = time.time()
            et.run_time = (et.stop_time - et.start_time) * 1000
            et.SetProcessingState(0, 0, self._icon_colour)
            self._lock.release()

    @eg.LogIt
    def Execute(self):
        et = EventThread(self.string, self.payloads[0])
        self.payloads = self.payloads[1:]

        thread = threading.Thread(
            name=self.string,
            target=self._Execute,
            args=(et,)
        )
        thread.setDaemon(True)
        et.thread = thread
        self._threads[thread] = et
        thread.start()

        return

    def SetPayload(self, payload):
        self.payloads += (payload,)

    def AddUpFunc(self, func, *args, **kwargs):
        if self.isEnded:
            func(*args, **kwargs)
        else:
            self.upFuncList.append((func, args, kwargs))

    def DoUpFuncs(self):
        for func, args, kwargs in self.upFuncList:
            func(*args, **kwargs)
        self.isEnded = True

    def SetShouldEnd(self):
        try:
            if not self.shouldEnd.isSet():
                self.shouldEnd.set()
                eg.actionThread.Call(self.DoUpFuncs)
        except AttributeError:
            pass

    def SetStarted(self):
        if self.shouldEnd.isSet():
            self.DoUpFuncs()

    def __str__(self):
        return self.string

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return "<eventghost-event '%s'>" % self.string
