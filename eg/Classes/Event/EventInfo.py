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
import time
import threading
from fnmatch import fnmatchcase

import eg


class Text(eg.TranslatableStrings):
    noDescription = "<i>No description available</i>"


def iter_events(child, instances=()):
    for eventName in child:
        instances += (child[eventName],)
        instances = iter_events(child[eventName], instances)
    return instances


class EventInfo(object):

    def __init__(self, parent, name):
        self.name = name
        self.description = Text.noDescription
        self.indent = 0
        self.time = None
        self.stop = None
        self.result = None
        self.payload = None
        self.isEnded = None
        self.programCounter = None
        self.skipEvent = False
        self.stopExecutionFlag = False
        self.macros = []
        self.upFuncList = []
        self.programReturnStack = []
        self.children = dict()
        self.source = eg
        self.shouldEnd = threading.Event()
        self.lock = threading.Lock()
        self.log = eg.EventLog()

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

    def __iter__(self):
        return iter(self.children.keys())

    def __contains__(self, item):
        return item in self.children.keys()

    def __delitem__(self, key):
        if key not in self:
            raise eg.EventManager.EventError.NotFound(key)
        del(self.children[key])

    def __getitem__(self, item):
        items = item.split('.')
        item = items.pop(0)

        if item not in self:
            event = EventInfo(self, item)
            self[item] = event

        if items:
            return self.children[item]['.'.join(items)]
        else:
            return self.children[item]

    def __setitem__(self, key, value):
        if key in self:
            raise eg.EventManager.EventError.Duplicate(key)
        self.children[key] = value

    def RegisterMacro(self, macro):
        self.macros.append(macro)

    def UnregisterMacro(self, macro):
        self.macros.remove(macro)

    @eg.LogIt
    def _Execute(self, payload):
        self.lock.acquire()
        self.payload = payload
        self.isEnded = False
        self.time = time.clock()

        try:
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
            eg.SetProcessingState(2, self)

            for eventHandler in activeHandlers:
                try:
                    self.programCounter = (eventHandler.parent, None)
                    self.indent = 1
                    eg.RunProgram()
                except:
                    eg.PrintTraceback()
                if self.skipEvent:
                    break
            self.SetStarted()
        except:
            pass

        finally:
            self.stop = time.clock()
            self.lock.release()
            eg.SetProcessingState(1, self)
            del(eg.EventManager.threads[threading.currentThread()])

    @eg.LogIt
    def Execute(self, payload):
        t = threading.Thread(
            name=self.string,
            target=self._Execute,
            args=(payload,)
        )
        t.setDaemon(True)
        eg.EventManager.threads[t] = self
        t.start()

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
        if not self.shouldEnd.isSet():
            self.shouldEnd.set()
            eg.SetProcessingState(0, self)
            eg.actionThread.Call(self.DoUpFuncs)

    def SetStarted(self):
        if self.shouldEnd.isSet():
            self.DoUpFuncs()

