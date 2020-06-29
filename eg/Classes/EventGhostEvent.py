# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2020 EventGhost Project <http://www.eventghost.net/>
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

from fnmatch import fnmatchcase
from time import clock, localtime
from collections import deque
from copy import deepcopy as copy
import threading
import six

# Local imports
import eg

# some shortcuts to speed things up
#pylint: disable-msg=C0103
actionThread = eg.actionThread
LogEvent = eg.log.LogEvent
RunProgram = eg.RunProgram
GetItemPath = eg.EventItem.GetPath
config = eg.config
#pylint: enable-msg=C0103


class InstanceSingleton(type):

    def __init__(cls, name, bases, dct):
        super(InstanceSingleton, cls).__init__(name, bases, dct)
        cls._instances = {}

    def __call__(cls, suffix="", payload=None, prefix="Main", source=eg, new_thread=False, new_event=False):
        if new_thread:
            return super(InstanceSingleton, cls).__call__(new_thread=True)

        key = prefix
        if suffix:
            key += '.' + suffix

        if new_event:
            instance = super(InstanceSingleton, cls).__call__(suffix, payload, prefix, source, new_event=new_event)
            cls._instances[key] = instance
            return instance

        if '.' in key:
            key = key.rsplit('.', 1)[0]

        if key not in cls._instances:
            suf = key.replace(prefix, '')

            instance = super(InstanceSingleton, cls).__call__(suf, None, prefix, source, new_event=True)
            cls._instances[key] = instance

        instance = cls._instances[key]
        return instance(suffix, payload, prefix, source)


@six.add_metaclass(InstanceSingleton)
class EventGhostEvent(threading.Thread):
    """
    .. attribute:: string

        This is the full qualified event string as you see it inside the
        logger, with the exception that if the payload field
        (that is explained below) is not None the logger will also show it
        behind the event string, but this is not a part of the event string
        we are talking about here.

    .. attribute:: payload

        A plugin might publish additional data related to this event.
        Through payload you can access this data. For example the 'Network
        Event Receiver' plugin returns also the IP of the client that has
        generated the event. If there is no data, this field is ``None``.

    .. attribute:: prefix

        This is the first part of the event string till the first dot. This
        normally identifies the source of the event as a short string.

    .. attribute:: suffix

        This is the part of the event string behind the first dot. So you
        could say:

        event.string = event.prefix + '.' + event.suffix

    .. attribute:: time

        The time the event was generated as a floating point number in
        seconds (as returned by the clock() function of Python's time module).
        Since most events are processed very quickly, this is most likely
        nearly the current time. But in some situations it might be more
        clever to use this time, instead of the current time, since even
        small differences might matter (for example if you want to determine
        a double-press).

    .. attribute:: isEnded

        This boolean value indicates if the event is an enduring event and is
        still active. Some plugins (e.g. most of the remote receiver plugins)
        indicate if a button is pressed longer. As long as the button is
        pressed, this flag is ``False`` and in the moment the user releases the
        button the flag turns to ``True``. So you can poll this flag to see, if
        the button is still pressed.

    """
    skipEvent = False

    _instances = {}

    @classmethod
    def ClearCachedEvents(cls):
        cls._instances.clear()

    @classmethod
    def RemoveCachedEvent(cls, eventItem):
        if '*' in eventItem.name or '?' in eventItem.name:
            for key in cls._instances.keys():
                if fnmatchcase(key, eventItem.name):
                    pattern = key
                    break
            else:
                pattern = []
                for item in eventItem.name.split('.'):
                    if '*' in item or '?' in item:
                        break

                    pattern += [item]

                pattern = '.'.join(pattern)

        else:
            pattern = eventItem.name.split('.')[-1]
            pattern = '.'.join(pattern)

        if pattern in cls._instances:
            instance = cls._instances[pattern]
            if eventItem in instance.eventHandlerList:
                instance.eventHandlerList.remove(eventItem)


    @classmethod
    def AddCachedEvent(cls, eventItem):
        if '*' in eventItem.name or '?' in eventItem.name:
            for key, instance in cls._instances.items():
                if fnmatchcase(key, eventItem.name):
                    instance.eventHandlerList.add(eventItem)
                    return

            pattern = []
            for item in eventItem.name.split('.'):
                if '*' in item or '?' in item:
                    break

                pattern += [item]

        else:
            pattern = eventItem.name.split('.')[-1]

        pattern = '.'.join(pattern)

        if pattern in cls._instances:
            instance = cls._instances[pattern]
            instance.eventHandlerList.add(eventItem)
            return


        if '.' in pattern:
            prefix, suffix = pattern.split('.', 1)
        else:
            prefix = pattern
            suffix = ''

        for plugin in eg.pluginList:
            if plugin.info.eventPrefix == prefix:
                source = plugin.info.plugin
                break
        else:
            source = eg

        cls(suffix=suffix, prefix=prefix, source=source, new_event=True)

    def __init__(
        self,
        suffix="",
        payload=None,
        prefix="Main",
        source=eg,
        new_thread=False,
        new_event=False
    ):
        eventString = prefix
        if suffix:
            eventString += '.' + suffix

        threading.Thread.__init__(self, name=eventString)

        if new_thread:
            return

        self.cached_string = eventString
        self.cached_prefix = prefix
        self.cached_suffix = suffix
        self.cached_source = source

        self.time = clock()

        self.eventHandlerList = set()
        self.last_event_time = 0
        self.event_count = 0

        self._queue = deque()
        self._queue_event = threading.Event()
        self._exit_event = threading.Event()
        self.__event = None


    @property
    def string(self):
        if self.__event is not None:
            return self.__event.string

        return self.cached_string

    @property
    def prefix(self):
        if self.__event is not None:
            return self.__event.prefix

        return self.cached_prefix

    @property
    def prefix(self):
        if self.__event is not None:
            return self.__event.suffix

        return self.cached_suffix

    @property
    def payload(self):
        if self.__event is not None:
            return self.__event.payload

    @property
    def source(self):
        if self.__event is not None:
            return self.__event.source

        return self.cached_source

    def __call__(self, suffix, payload, prefix, source):
        return Event(self, prefix, suffix, payload, source)

    def AddEvent(self, eventHolder):
        self._queue.append(eventHolder)
        self.start()

    @property
    def result(self):
        if self.__event is not None:
            return self.__event.result

    @result.setter
    def result(self, value):
        if self.__event is not None:
            self.__event.result = value

    @property
    def eventString(self):
        if self.__event is not None:
            return self.__event.string

    @eventString.setter
    def eventString(self, value):
        pass

    @property
    def programCounter(self):
        if self.__event is not None:
            return self.__event.programCounter

    @programCounter.setter
    def programCounter(self, value):
        if self.__event is not None:
            self.__event.programCounter = value

    @property
    def programReturnStack(self):
        if self.__event is not None:
            return self.__event.programReturnStack

        return []

    @programReturnStack.setter
    def programReturnStack(self, value):
        if self.__event is not None:
            self.__event.programReturnStack = value

    @property
    def indent(self):
        if self.__event is not None:
            return self.__event.index

        return 0

    @indent.setter
    def indent(self, value):
        if self.__event is not None:
            self.__event.indent = value

    @property
    def stopExecutionFlag(self):
        if self.__event is not None:
            return self.__event.stopEcevutionFlag

        return False

    @stopExecutionFlag.setter
    def stopExecutionFlag(self, value):
        if self.__event is not None:
            self.__event.stopExecutionFlag = value

    @property
    def lastFoundWindows(self):
        if self.__event is not None:
            return  self.__event.lastFoundWindows

        return []

    @lastFoundWindows.setter
    def lastFoundWindows(self, value):
        if self.__event is not None:
            self.__event.lastFoundWindows = value

    @property
    def currentItem(self):
        if self.__event is not None:
            return self.__event.currentItem

    @currentItem.setter
    def currentItem(self, value):
        if self.__event is not None:
            self.__event.currentItem = value

    def __execute(self):
        self.event_count += 1
        self.last_event_time = localtime()

        eventString = self.__event.string

        if eventString in eg.notificationHandlers:
            for listener in eg.notificationHandlers[eventString].listeners:
                if listener(self.__event) is True:
                    return

        activeHandlers = set()
        for eventHandler in self.eventHandlerList:
            obj = eventHandler
            if '*' in obj.name or '?' in obj.name:
                if not fnmatchcase(eventString, obj.name):
                    continue
            elif obj.name != eventString:
                continue

            while obj:
                if not obj.isEnabled:
                    break
                obj = obj.parent
            else:
                activeHandlers.add(eventHandler)

        for listener in eg.log.eventListeners:
            listener.LogEvent(self.__event)

        if config.onlyLogAssigned and len(activeHandlers) == 0:
            self.__event.SetStarted()
            return

        # show the event in the logger
        LogEvent(self.__event)

        activeHandlers = sorted(activeHandlers, key=GetItemPath)

        eg.SetProcessingState(2, self.__event)
        for eventHandler in activeHandlers:
            try:
                eg.programCounter = (eventHandler.parent, None)
                eg.indent = 1
                RunProgram()
            except:
                eg.PrintTraceback()
            if self.__event.skipEvent:
                break
        self.__event.SetStarted()
        eg.SetProcessingState(1, self.__event)

    def run(self):
        while not self._exit_event.is_set():
            while len(self._queue):
                self.__event = self._queue.popleft()
                self.__execute()
                self.__event = None

            self._queue_event.clear()
            self._queue_event.wait(3)

            if self._queue_event.is_set():
                self._queue_event.clear()
                continue
            else:
                self._exit_event.set()

        self._exit_event.clear()
        self._queue_event.clear()

    def start(self):
        if self.is_alive():
            self._queue_event.set()
        else:
            try:
                threading.Thread.start(self)
            except RuntimeError:
                instance = self.__class__(new_thread=True)
                self.__dict__.update(instance.__dict__)
                threading.Thread.start(self)

    def stop(self):
        if self.is_alive():
            self._exit_event.set()
            self._queue_event.set()
            self._queue.clear()
            self.join(3)

    def AddUpFunc(self, func, *args, **kwargs):
        if self.__event is not None:
            self.__event.AddUpFunc(func, *args, **kwargs)

    def DoUpFuncs(self):
        if self.__event is not None:
            self.__event.DoUpFuncs()

    def SetShouldEnd(self):
        if self.__event is not None:
            self.__event.SetShouldEnd()

    def SetStarted(self):
        if self.__event is not None:
            self.__event.SetStarted()


class Event(object):
    def __init__(self, parent, prefix, suffix, payload, source):
        self._parent = parent
        self.string = prefix
        if suffix:
            self.string += '.' + suffix

        self.prefix = prefix
        self.suffix = suffix
        if isinstance(payload, (dict, list)):
            try:
                self.payload = copy(payload)
            except:
                self.payload = payload
        else:
            self.payload = payload

        self.source = source
        self.skipEvent = False

        self.upFuncList = []
        self.isEnded = False
        self.shouldEnd = threading.Event()
        self.time = clock()

        self.result = None
        self.eventString = self.string
        self.programCounter = None
        self.programReturnStack = []
        self.indent = 0
        self.stopExecutionFlag = False
        self.lastFoundWindows = []
        self.currentItem = None

    def AddUpFunc(self, func, *args, **kwargs):
        if self.isEnded:
            func(*args, **kwargs)
        else:
            self.upFuncList.append((func, args, kwargs))

    def DoUpFuncs(self):
        for func, args, kwargs in self.upFuncList:
            func(*args, **kwargs)
        del self.upFuncList[:]
        self.isEnded = True

    def SetShouldEnd(self):
        if not self.shouldEnd.isSet():
            self.shouldEnd.set()
            eg.SetProcessingState(0, self)
            self.DoUpFuncs()

    def SetStarted(self):
        if self.shouldEnd.isSet():
            self.DoUpFuncs()

    def Execute(self):
        self._parent.AddEvent(self)
