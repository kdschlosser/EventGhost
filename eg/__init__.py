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

# the following three import are needed if we are running from source and the
# Python distribution was not installed by the installer. See the following
# link for details:
# http://www.voidspace.org.uk/python/movpy/reference/win32ext.html#id10
import pywintypes  # NOQA
import pythoncom  # NOQA
import win32api  # NOQA
import __builtin__
import locale
import wx
import threading
import asyncore
import socket
import time
import sys
import inspect
from types import ModuleType
from os import makedirs, chdir, listdir
from os.path import exists, join, isdir, splitext

__builtin__.wx = wx
__builtin__.eg = sys.modules[__name__]
sys.modules['eg'] = sys.modules[__name__]

_eg_imports = []


def _import_wrapper(name, *args, **kwargs):
    global _eg_imports

    def caller_name(start=3):
        stack = inspect.stack()
        parent_frame = stack[start][0]
        n = []
        m = inspect.getmodule(parent_frame)

        if m:
            n.append(m.__name__)
        if 'self' in parent_frame.f_locals:
            n.append(parent_frame.f_locals['self'].__class__.__name__)
        codename = parent_frame.f_code.co_name
        if codename != '<module>':
            n.append(codename)
        del parent_frame

        if n[-1] == 'LogItWrapper':
            return caller_name(5)
        else:
            return name[0]

    if name == 'eg':
        _eg_imports += [caller_name()]
        return sys.modules[__name__]

    return _import(name, *args, **kwargs)


def _update_eg_imports():
    for imp_mod in _eg_imports:
        if imp_mod in sys.modules:
            sys.modules[imp_mod] = sys.modules[__name__]

_import = __builtin__.__import__
__builtin__.__import__ = _import_wrapper


# Local imports
import Cli # NOQA
import Version # NOQA
from FolderPath import FolderPath # NOQA
from Utils import * # NOQA
import Init # NOQA
import Icons # NOQA
import NamedPipe # NOQA
import Config # NOQA
import Text # NOQA
import cFunctions
from WinApi.Dynamic import GetCurrentProcessId # NOQA

_update_eg_imports()


class Exception(Exception):
    def __unicode__(self):
        try:
            return "\n".join([unicode(arg) for arg in self.args])
        except UnicodeDecodeError:
            return "\n".join([str(arg).decode('mbcs') for arg in self.args])


class StopException(Exception):
    pass


class HiddenAction:
    pass


def TracebackHook(tType, tValue, traceback):
    log.PrintTraceback(excInfo=(tType, tValue, traceback))


def Bind(notification, listener):
    if notification not in notificationHandlers:
        notificationHandler = NotificationHandler()
        notificationHandlers[notification] = notificationHandler
    else:
        notificationHandler = notificationHandlers[notification]
    notificationHandler.listeners.append(listener)


def CallWait(func, *args, **kwargs):
    res = [None]
    evt = threading.Event()

    def CallWaitWrapper():
        try:
            res[0] = func(*args, **kwargs)
        finally:
            evt.set()

    wx.CallAfter(CallWaitWrapper)
    evt.wait()
    return res[0]


def DummyFunc(*dummyArgs, **dummyKwargs):
    """
    Just a do-nothing-function, that accepts arbitrary arguments.
    """
    pass


def Exit():
    """
    Sometimes you want to quickly exit a PythonScript, because you don't
    want to build deeply nested if-structures for example. eg.Exit() will
    exit your PythonScript immediately.
    (Note: This is actually a sys.exit() but will not exit EventGhost,
    because the SystemExit exception is catched for a PythonScript.)
    """
    sys.exit()


def HasActiveHandler(eventstring):
    for eventHandler in eventTable.get(eventstring, []):
        obj = eventHandler
        while obj:
            if not obj.isEnabled:
                break
            obj = obj.parent
        else:
            return True
    return False


def MessageBox(message, caption=None, style=wx.OK, parent=None):
    if caption is None:
        caption = APP_NAME
    if parent is None:
        style |= wx.STAY_ON_TOP
    dialog = MessageDialog(parent, message, caption, style)
    res = dialog.ShowModal()
    dialog.Destroy()
    return res


def Notify(notification, value=None):
    if notification in eg.notificationHandlers:
        for listener in eg.notificationHandlers[notification].listeners:
            listener(value)


# pylint: disable-msg=W0613
def RegisterPlugin(
    name = None,
    description = None,
    kind = "other",
    author = "[unknown author]",
    version = "[unknown version]",
    icon = None,
    canMultiLoad = False,
    createMacrosOnAdd = False,
    url = None,
    help = None,
    guid = None,
    **kwargs
):
    """
    Registers information about a plugin to EventGhost.

    :param name: should be a short descriptive string with the name of the
       plugin.
    :param description: a short description of the plugin.
    :param kind: gives a hint about the category the plugin belongs to. It
        should be a string with a value out of ``"remote"`` (for remote
        receiver plugins), ``"program"`` (for program control plugins),
        ``"external"`` (for plugins that control external hardware) or
        ``"other"`` (if none of the other categories match).
    :param author: can be set to the name or a list of names of the
        developer(s) of the plugin.
    :param version: can be set to a version string.
    :param icon: can be a base64 encoded image for the plugin. If
        ``icon == None``, an "icon.png" will be used if it exists
        in the plugin folder.
    :param canMultiLoad: set this to ``True``, if a configuration can have
       more than one instance of this plugin.
    :param createMacrosOnAdd: if set to ``True``, when adding the plugin,
        EventGhost will ask the user, if he/she wants to add a folder with all
        actions of this plugin to his/her configuration.
    :param url: displays a clickable link in the plugin info dialog.
    :param help: a longer description and/or additional information for the
        plugin. Will be added to
        'description'.
    :param guid: will help EG to identify your plugin, so there are no name
        clashes with other plugins that accidentally might have the same
        name and will later ease the update of plugins.
    :param \*\*kwargs: just to consume unknown parameters, to make the call
       backward compatible.
    """
    pass
# pylint: enable-msg=W0613


def RestartAsyncore():
    """
    Informs the asyncore loop of a new socket to handle.
    """
    global dummyAsyncoreDispatcher

    oldDispatcher = dummyAsyncoreDispatcher
    dispatcher = asyncore.dispatcher()
    dispatcher.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    dummyAsyncoreDispatcher = dispatcher
    if oldDispatcher:
        oldDispatcher.close()
    if oldDispatcher is None:
        # create a global asyncore loop thread
        threading.Thread(target=asyncore.loop, name="AsyncoreThread").start()


def RunProgram():
    global stopExecutionFlag
    global programCounter
    global indent

    stopExecutionFlag = False
    del programReturnStack[:]
    while programCounter is not None:
        programCounter_ = programCounter
        item, idx = programCounter_
        item.Execute()
        if programCounter == programCounter_:
            # program counter has not changed. Ask the parent for the next
            # item.
            if isinstance(item.parent, MacroItem):
                programCounter = item.parent.GetNextChild(idx)
            else:
                programCounter = None

        while programCounter is None and programReturnStack:
            # we have no next item in this level. So look in the return
            # stack if any return has to be executed
            indent -= 2
            item, idx = programReturnStack.pop()
            programCounter = item.parent.GetNextChild(idx)
    indent = 0


def StopMacro(ignoreReturn=False):
    """
    Instructs EventGhost to stop executing the current macro after the
    current action (thus the PythonScript or PythonCommand) has finished.
    """
    global programCounter
    programCounter = None
    if ignoreReturn:
        del programReturnStack[:]


def Unbind(notification, listener):
    notificationHandlers[notification].listeners.remove(listener)


def Wait(secs, raiseException=True):
    while secs > 0.0:
        if stopExecutionFlag:
            if raiseException:
                raise StopException("Execution interrupted by the user.")
            else:
                return False
        if secs > 0.1:
            time.sleep(0.1)
        else:
            time.sleep(secs)
        secs -= 0.1
    return True


def CommandEvent():
    """Generate new (CmdEvent, Binder) tuple
        e.g. MooCmdEvent, EVT_MOO = EgCommandEvent()
    """
    evttype = wx.NewEventType()

    class _Event(wx.PyCommandEvent):
        def __init__(self, id, **kw):
            wx.PyCommandEvent.__init__(self, evttype, id)
            self.__dict__.update(kw)
            if not hasattr(self, "value"):
                self.value = None

        def GetValue(self):
            return self.value

        def SetValue(self, value):
            self.value = value

    return _Event, wx.PyEventBinder(evttype, 1)


def Main():
    if Cli.args.install:
        return
    if Cli.args.translate:
        LanguageEditor()
    elif Cli.args.pluginFile:
        PluginInstall.Import(Cli.args.pluginFile)
        return
    else:
        Init.InitGui()
    if debugLevel:
        try:
            Init.ImportAll()
        except:
            PrintDebugNotice(sys.exc_info()[1])
    Tasklet(app.MainLoop)().run()
    stackless.run()


_update_eg_imports()

APP_NAME = "EventGhost"
CORE_PLUGIN_GUIDS = (
    "{9D499A2C-72B6-40B0-8C8C-995831B10BB4}",  # "EventGhost"
    "{A21F443B-221D-44E4-8596-E1ED7100E0A4}",  # "System"
    "{E974D074-B0A3-4D0C-BBD1-992475DDD69D}",  # "Window"
    "{6B1751BF-F94E-4260-AB7E-64C0693FD959}",  # "Mouse"
)
ID_TEST = wx.NewId()
ValueChangedEvent, EVT_VALUE_CHANGED = CommandEvent()

folderPath = FolderPath()
mainDir = folderPath.mainDir
configDir = folderPath.configDir
corePluginDir = folderPath.corePluginDir
localPluginDir = folderPath.localPluginDir
imagesDir = folderPath.imagesDir
languagesDir = folderPath.languagesDir
sitePackagesDir = folderPath.sitePackagesDir

if not exists(configDir):
    try:
        makedirs(configDir)
    except:
        pass

if not exists(localPluginDir):
    try:
        makedirs(localPluginDir)
    except:
        localPluginDir = corePluginDir

classesDir = join(mainDir, 'eg', 'Classes')

if not exists(join(classesDir, '__init__.py')):
    with open(join(classesDir, '__init__.py'), 'w') as f:
        for class_file in listdir(classesDir):
            file_name, file_ext = splitext(class_file)
            if file_name.startswith('_'):
                continue
            if isdir(join(classesDir, class_file)) or file_ext == '.py':
                f.write('from {0} import {0}\n'.format(file_name))

        f.write("\n__import__('pkg_resources').declare_namespace('eg')\n")

del classesDir

if Cli.args.isMain:
    if exists(configDir):
        chdir(configDir)
    else:
        chdir(mainDir)

pluginDirs = [corePluginDir, localPluginDir]

corePluginPackage = ModuleType("eg.CorePluginModule")
corePluginPackage.__path__ = [corePluginDir]
userPluginPackage = ModuleType("eg.UserPluginModule")
userPluginPackage.__path__ = [localPluginDir]
sys.modules["eg.CorePluginModule"] = corePluginPackage
sys.modules["eg.UserPluginModule"] = userPluginPackage
sys.modules['eg.cFunctions'] = cFunctions

revision = 2000  # Deprecated
startupArguments = Cli.args
sys.excepthook = TracebackHook
systemEncoding = locale.getdefaultlocale()[1]
config = Config.Config()
mainThread = threading.currentThread()
processId = GetCurrentProcessId()
namedPipe = NamedPipe.Server()
plugins = Bunch()
globals = Bunch()
actionGroup = Bunch()
actionGroup.items = []
programReturnStack = []
pluginList = []
lastFoundWindows = []

eventTable = {}
notificationHandlers = {}
eventString = ""
indent = 0
stopExecutionFlag = False
useTreeItemGUID = False
wit = None
currentItem = None
pyCrustFrame = None
dummyAsyncoreDispatcher = None
document = None
mainFrame = None
result = None
event = None
programCounter = None
debugLevel = int(config.logDebug) or startupArguments.debugLevel

if startupArguments.isMain and not startupArguments.translate:
    text = Text.Text(config.language)
else:
    text = Text.Text('en_EN')

_update_eg_imports()

from App import App

app = App()
Init.InitPil()
Icons.start()

from Classes import * # NOQA

messageReceiver = MainMessageReceiver()
log = Log()
colour = Colour()

Print = log.Print
PrintError = log.PrintError
PrintNotice = log.PrintNotice
PrintTraceback = log.PrintTraceback
PrintDebugNotice = log.PrintDebugNotice
PrintStack = log.PrintStack

actionThread = ActionThread()
eventThread = EventThread()
pluginManager = PluginManager()
scheduler = Scheduler()

TriggerEvent = eventThread.TriggerEvent
TriggerEnduringEvent = eventThread.TriggerEnduringEvent

from.WinApi.SendKeys import SendKeysParser # NOQA

SendKeys = SendKeysParser()

PluginClass = PluginBase
ActionClass = ActionBase

taskBarIcon = TaskBarIcon(
    startupArguments.isMain and
    config.showTrayIcon and
    not startupArguments.translate and
    not startupArguments.install and
    not startupArguments.pluginFile
)
SetProcessingState = taskBarIcon.SetProcessingState

_update_eg_imports()
__builtin__.__import__ = _import

if Cli.args.isMain:
    namedPipe.start()

Init.Init()



# # This is only here to make pylint happy. It is never really imported
# if "pylint" in sys.modules:
#     Init.ImportAll()
#     from StaticImports import *  # NOQA
