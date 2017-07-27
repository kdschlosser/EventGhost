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

import stackless
import sys

# the following three import are needed if we are running from source and the
# Python distribution was not installed by the installer. See the following
# link for details:
# http://www.voidspace.org.uk/python/movpy/reference/win32ext.html#id10
import pywintypes  # NOQA
import pythoncom  # NOQA
import win32api  # NOQA
import threading  # NOQA

# Local imports
import Cli
from Utils import *  # NOQA
from Classes.WindowsVersion import WindowsVersion  # NOQA


class DynamicModule(object):
    def __init__(self):
        mod = sys.modules[__name__]
        self.__dict__ = mod.__dict__
        self.__orignal_module__ = mod
        sys.modules[__name__] = self

        import __builtin__
        __builtin__.eg = self

    def __getattr__(self, name):
        if name.startswith('Event'):
            mod = __import__("eg.Classes.Event." + name, None, None, [name], 0)
        else:
            mod = __import__("eg.Classes." + name, None, None, [name], 0)
        self.__dict__[name] = attr = getattr(mod, name)
        return attr

    def __repr__(self):
        return "<dynamic-module '%s'>" % self.__name__

    def RaiseAssignments(self):
        """
        After this method is called, creation of new attributes will raise
        AttributeError.

        This is meanly used to find unintended assignments while debugging.
        """
        def __setattr__(self, name, value):
            attrs = (
                'programReturnStack',
                'programCounter',
                'eventString',
                'result',
                'indent',
                'stopExecutionFlag',
                'currentItem'
            )
            if name not in self.__dict__ and name not in attrs:
                raise AttributeError("Assignment to new attribute %s" % name)
            object.__setattr__(self, name, value)
        self.__class__.__setattr__ = __setattr__

    def Main(self):
        if Cli.args.install:
            return
        if Cli.args.translate:
            eg.LanguageEditor()
        elif Cli.args.pluginFile:
            eg.PluginInstall.Import(Cli.args.pluginFile)
            return
        else:
            eg.Init.InitGui()
        if eg.debugLevel:
            try:
                eg.Init.ImportAll()
            except:
                eg.PrintDebugNotice(sys.exc_info()[1])
        eg.Tasklet(eg.app.MainLoop)().run()
        stackless.run()

    @property
    def programReturnStack(self):
        event = self.event
        if event is None:
            return self.EventManager.programReturnStack
        else:
            return event.programReturnStack

    @programReturnStack.setter
    def programReturnStack(self, value):
        event = self.event
        if event is None:
            self.EventManager.programReturnStack = value
        else:
            event.programReturnStack = value

    @property
    def programCounter(self):
        event = self.event
        if event is None:
            return self.EventManager.programCounter
        else:
            return event.programCounter

    @programCounter.setter
    def programCounter(self, value):
        event = self.event
        if event is None:
            self.EventManager.programCounter = value
        else:
            event.programCounter = value

    @property
    def eventString(self):
        event = self.event
        if event is None:
            return self.EventManager.eventString
        else:
            return event.eventString

    @eventString.setter
    def eventString(self, value):
        event = self.event
        if event is None:
            self.EventManager.eventString = value
        else:
            event.eventString = value

    @property
    def result(self):
        event = self.event
        if event is None:
            return self.EventManager.result
        else:
            return event.result

    @result.setter
    def result(self, value):
        event = self.event
        if event is None:
            self.EventManager.result = value
        else:
            event.result = value

    @property
    def indent(self):
        event = self.event
        if event is None:
            return self.EventManager.indent
        else:
            return event.indent

    @indent.setter
    def indent(self, value):
        event = self.event
        if event is None:
            self.EventManager.indent = value
        else:
            event.indent = value

    @property
    def event(self):
        t = threading.currentThread()
        if t in self.EventManager.threads:
            return self.EventManager.threads[t]
        else:
            return None

    @property
    def stopExecutionFlag(self):
        event = self.event
        if event is None:
            return self.EventManager.stopExecutionFlag
        else:
            return event.stopExecutionFlag

    @stopExecutionFlag.setter
    def stopExecutionFlag(self, value):
        event = self.event
        if event is None:
            self.EventManager.stopExecutionFlag = value
        else:
            event.stopExecutionFlag = value

    @property
    def currentItem(self):
        event = self.event
        if event is None:
            return self.EventManager.currentItem
        else:
            return event.currentItem

    @currentItem.setter
    def currentItem(self, value):
        event = self.event
        if event is None:
            self.EventManager.currentItem = value
        else:
            event.currentItem = value

    @property
    def lastFoundWindows(self):
        event = self.event
        if event is None:
            return self.EventManager.lastFoundWindows
        else:
            return event.lastFoundWindows

    @lastFoundWindows.setter
    def lastFoundWindows(self, value):
        event = self.event
        if event is None:
            self.EventManager.lastFoundWindows[:] = value
        else:
            event.lastFoundWindows[:] = value



eg = DynamicModule()

# This is only here to make pylint happy. It is never really imported
if "pylint" in sys.modules:
    from Init import ImportAll
    ImportAll()
    from StaticImports import *  # NOQA
    from Core import *  # NOQA

import Core  # NOQA
if eg.debugLevel:
    eg.RaiseAssignments()
