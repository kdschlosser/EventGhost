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


# the following three import are needed if we are running from source and the
# Python distribution was not installed by the installer. See the following
# link for details:
# http://www.voidspace.org.uk/python/movpy/reference/win32ext.html#id10

import sys
import __builtin__

_excepthook = sys.excepthook
_import = __builtin__.__import__

import pywintypes # NOQA
import pythoncom # NOQA
import win32api # NOQA
import socket # NOQA
import time # NOQA
import locale # NOQA
import asyncore # NOQA
import os # NOQA
import threading # NOQA
import json # NOQA
from types import ModuleType # NOQA

APP_NAME = "EventGhost"


# noinspection PyShadowingBuiltins,PyShadowingNames
def import_wrapper(name, globals={}, locals={}, fromlist=[], level=-1):
    if name.startswith('eg'):
        sys.modules['eg'] = sys.modules[__name__]
        split_name = name.split('.', 1)
        if len(split_name) == 2:
            try:
                mod = _import(split_name[1], globals, locals, fromlist, level)
                return mod
            except ImportError:
                pass

    return _import(name, globals, locals, fromlist, level)


__builtin__.__import__ = import_wrapper
__builtin__.eg = sys.modules[__name__]


# noinspection PyPep8Naming
def TracebackHook(tType, tValue, traceback):
    PrintTraceback(excInfo=(tType, tValue, traceback))


# noinspection PyShadowingBuiltins
class Exception(Exception):
    def __unicode__(self):
        try:
            return "\n".join([unicode(arg) for arg in self.args])
        except UnicodeDecodeError:
            return "\n".join([str(arg).decode('mbcs') for arg in self.args])


class StopException(Exception):
    pass


# noinspection PyClassHasNoInit
class HiddenAction:
    pass


def Bind(notification, listener):
    global notificationHandler

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

    mainThread.Call(CallWaitWrapper)
    evt.wait()
    return res[0]


# noinspection PyPep8Naming,PyUnusedLocal
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


def Notify(notification, value=None):
    if notification in notificationHandlers:
        def do(val):
            for listener in notificationHandlers[notification].listeners:
                listener(val)

        mainThread.Call(do, value)


# pylint: disable-msg=W0613
# noinspection PyPep8Naming,PyUnusedLocal
def RegisterPlugin(
    name=None,
    description=None,
    kind="other",
    author="[unknown author]",
    version="[unknown version]",
    icon=None,
    canMultiLoad=False,
    createMacrosOnAdd=False,
    url=None,
    help=None,
    guid=None,
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
    :param kwargs: just to consume unknown parameters, to make the call
       backward compatible.
    """
    pass


# pylint: enable-msg=W0613
# noinspection PyPep8Naming
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
        threading.Thread(
            target=asyncore.loop,
            name="AsyncoreThread"
        ).start()


def RunProgram():
    global stopExecutionFlag
    global programCounter
    global indent

    stopExecutionFlag = False
    del programReturnStack[:]
    while programCounter is not None:
        program_counter = programCounter
        item, idx = program_counter
        item.Execute()
        if programCounter == program_counter:
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


# noinspection PyPep8Naming
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


# noinspection PyPep8Naming
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


def SetProcessingState(*_):
    pass


from Classes.Version import Version # NOQA
import PythonPaths # NOQA
import WinApi.pywin32_patches  # NOQA
import Cli  # NOQA
from Classes.WindowsVersion import WindowsVersion  # NOQA


from Classes.FolderPath import FolderPath  # NOQA
folderPath = FolderPath()
mainDir = folderPath.mainDir
configDir = folderPath.configDir
corePluginDir = folderPath.corePluginDir
localPluginDir = folderPath.localPluginDir
sitePackagesDir = folderPath.sitePackagesDir
imagesDir = folderPath.imagesDir
languagesDir = folderPath.languagesDir


if not os.path.exists(configDir):
    # noinspection PyPep8,PyBroadException
    try:
        os.makedirs(configDir)
    except:
        pass

if not os.path.exists(localPluginDir):
    # noinspection PyPep8,PyBroadException
    try:
        os.makedirs(localPluginDir)
    except:
        localPluginDir = corePluginDir


startupArguments = Cli.args
debugLevel = startupArguments.debugLevel

import Utils # NOQA

from Classes.Config import Config  # NOQA
config = Config()
debugLevel = int(config.logDebug) or debugLevel

import Utils  # NOQA
from Utils import (
    Bunch,
    NotificationHandler,
    LogIt,
    LogItWithReturn,
    TimeIt,
    AssertInMainThread,
    AssertInActionThread,
    ParseString,
    SetDefault,
    EnsureVisible,
    AsTasklet,
    ExecFile,
    GetTopLevelWindow,
    GetClosestLanguage,
    LogService
) # NOQA


import PIL # NOQA
from PIL import Image # NOQA

# noinspection PyProtectedMember
for plg in PIL._plugins:
    try:
        __import__('PIL.' + plg)
    except ImportError:
        pass

Image._initialized = 2

del PIL
del Image

import Icons  # NOQA

from Classes.Log import Log # NOQA
log = Log()
Print = log.Print
PrintError = log.PrintError
PrintNotice = log.PrintNotice
PrintTraceback = log.PrintTraceback
PrintDebugNotice = log.PrintDebugNotice
PrintServiceNotice = log.PrintServiceNotice
PrintWarningNotice = log.PrintWarningNotice
PrintStack = log.PrintStack


import websocket_server # NOQA


# noinspection PyShadowingBuiltins
class WebsocketServer(object):
    icons = {}
    clients = {}

    def __init__(self, host, port):
        self._server = websocket_server.WebsocketServer(port, host)

        self._server.set_fn_new_client(self._client_connected)
        self._server.set_fn_client_left(self._client_disconnected)
        self._server.set_fn_message_received(self._incoming_message)

    def open(self):
        def do():
            self._server.run_forever()

        t = threading.Thread(target=do)
        t.daemon = True
        t.start()

    def send_message(self, client, message):
        self._server.send_message(client, message)

    def _client_connected(self, client, server):
        pass

    def _client_disconnected(self, client, _):
        for id in self.clients.keys():
            if client == self.clients[id]:
                del self.clients[id]

    def _incoming_message(self, client, server, message):
        data = json.loads(message)
        if data['Type'] == 'Auth':
            auth = data['Data']
            self.clients[auth['Id']] = client

        elif data['Type'] == 'TriggerEvent':
            data = data['Data']
            args = data['Args']
            kwargs = data['Kwargs']

            TriggerEvent(*args, **kwargs)

        elif data['Type'] == 'GetLog':
            data = log.GetData()

            out_data = []

            for line, icon, _, when, idnt in data:
                if icon not in self.icons:
                    pil = icon.pil

                    value = ((pil.size[0], pil.size[1]), str(pil.tobytes()))
                    self.icons[icon] = value

                out_data += [
                    dict(
                        line=line,
                        icon=str(self.icons[icon]),
                        when=when,
                        indent=idnt
                    )
                ]

            out_data = dict(Type="GetLog", Data=out_data)
            server.send_message(client, json.dumps(out_data))

    def WriteLine(self, line, icon, _, when, idnt):
        if icon not in self.icons:
            pil = icon.pil

            value = ((pil.size[0], pil.size[1]), str(pil.tobytes()))
            self.icons[icon] = value

        data = dict(
            Type="Log",
            Data=dict(
                Args=(),
                Kwargs=dict(
                    line=line,
                    icon=str(self.icons[icon]),
                    when=when,
                    indent=idnt
                )
            )
        )

        self._server.send_message_to_all(json.dumps(data))


websocketServer = WebsocketServer(
    socket.gethostbyname(socket.gethostname()),
    6584
)

websocketServer.open()
log.SetCtrl(websocketServer)


# noinspection PyPep8Naming
class MainThread(object):

    def __init__(self):
        self._event = threading.Event()
        self._call_event = threading.Event()
        self._queue = []
        self.is_running = False
        self._pause_event = threading.Event()
        self._pause_event.set()

    def Pause(self):
        eventThread.Pause()
        actionThread.Pause()
        messageReceiver.Pause()
        self._pause_event.clear()

    def Continue(self):
        eventThread.Continue()
        actionThread.Continue()
        messageReceiver.Continue()
        self._pause_event.set()

    @LogService
    def Stop(self):
        self._event.set()
        self._call_event.set()

    @LogService
    def Start(self):
        self._MainLoop()

    @LogService
    def _MainLoop(self):
        self.is_running = True
        while not self._event.isSet():
            self._pause_event.wait()
            self._call_event.wait()
            self._call_event.clear()
            while self._queue:
                func, args, kwargs = self._queue.pop(0)
                func(*args, **kwargs)
        self.is_running = False
        self._event = threading.Event()
        self._call_event = threading.Event()
        self._queue = []

    def Call(self, func, *args, **kwargs):
        self._queue += [(func, args, kwargs)]
        self._call_event.set()


mainThread = MainThread()

CORE_PLUGIN_GUIDS = (
    "{9D499A2C-72B6-40B0-8C8C-995831B10BB4}",  # "EventGhost"
    "{A21F443B-221D-44E4-8596-E1ED7100E0A4}",  # "System"
    "{E974D074-B0A3-4D0C-BBD1-992475DDD69D}",  # "Window"
    "{6B1751BF-F94E-4260-AB7E-64C0693FD959}",  # "Mouse"
)


if os.path.exists(configDir):
    os.chdir(configDir)
else:
    os.chdir(mainDir)

useTreeItemGUID = False
revision = 2000  # Deprecated
mainFrame = None
result = None
event = None
eventTable = {}
eventString = ""
notificationHandlers = {}
programCounter = None
programReturnStack = []
indent = 0
pluginList = []
stopExecutionFlag = False
lastFoundWindows = []
currentItem = None
pyCrustFrame = None
dummyAsyncoreDispatcher = None
systemEncoding = locale.getdefaultlocale()[1]
wit = None

sys.excepthook = TracebackHook

pluginDirs = [corePluginDir, localPluginDir]
cFunctions = __import__('cFunctions')
sys.modules['eg.cFunctions'] = cFunctions

_corePluginPackage = ModuleType("eg.CorePluginModule")
_corePluginPackage.__path__ = [corePluginDir]
CorePluginModule = _corePluginPackage
sys.modules['eg.CorePluginModule'] = CorePluginModule

_userPluginPackage = ModuleType("eg.UserPluginModule")
_userPluginPackage.__path__ = [localPluginDir]
UserPluginModule = _userPluginPackage
sys.modules['eg.UserPluginModule'] = UserPluginModule

# noinspection PyShadowingBuiltins
globals = Bunch()
plugins = Bunch()
actionGroup = Bunch()
actionGroup.items = []

from WinApi.Dynamic import GetCurrentProcessId  # NOQA
processId = GetCurrentProcessId()

from Classes.GUID import GUID  # NOQA
GUID = GUID()

import NamedPipe  # NOQA
namedPipe = NamedPipe.Server()

from Classes.ThreadWorker import ThreadWorker  # NOQA
from Classes.UndoHandler import UndoHandler  # NOQA
from Classes.MessageReceiver import MessageReceiver  # NOQA

from Classes.MainMessageReceiver import MainMessageReceiver  # NOQA
messageReceiver = MainMessageReceiver()

from Classes.Text import Text  # NOQA
if startupArguments.isMain and not startupArguments.translate:
    text = Text(config.language)
else:
    text = Text('en_EN')

from Classes.TranslatableStrings import TranslatableStrings  # NOQA
from Classes.TreeLink import TreeLink  # NOQA
from Classes.TreePosition import TreePosition  # NOQA
from Classes.ContainerItem import ContainerItem  # NOQA
from Classes.MacroItem import MacroItem  # NOQA
from Classes.AutostartItem import AutostartItem  # NOQA
from Classes.PluginItem import PluginItem  # NOQA
from Classes.RootItem import RootItem  # NOQA
from Classes.TreeItem import TreeItem  # NOQA
from Classes.ActionItem import ActionItem  # NOQA
from Classes.EventItem import EventItem  # NOQA
from Classes.FolderItem import FolderItem  # NOQA
from Classes.PersistentData import PersistentData  # NOQA

from Classes.Document import Document  # NOQA
document = Document()

from Classes.ActionThread import ActionThread  # NOQA
actionThread = ActionThread()

from Classes.EventGhostEvent import EventGhostEvent  # NOQA
from Classes.EventThread import EventThread  # NOQA
eventThread = EventThread()

from Classes.Tasklet import Tasklet  # NOQA
from Classes.PluginMetaClass import PluginMetaClass  # NOQA
from Classes.PluginModuleInfo import PluginModuleInfo  # NOQA
from Classes.PluginBase import PluginBase  # NOQA
PluginClass = PluginBase

from Classes.ActionBase import ActionBase  # NOQA
ActionClass = ActionBase

from Classes.PluginInstanceInfo import PluginInstanceInfo  # NOQA
from Classes.Scheduler import Scheduler  # NOQA
scheduler = Scheduler()

TriggerEvent = eventThread.TriggerEvent
TriggerEnduringEvent = eventThread.TriggerEnduringEvent

from WinApi.SendKeys import SendKeysParser  # NOQA
SendKeys = SendKeysParser()

from Classes.ActionGroup import ActionGroup  # NOQA
from Classes.ActionWithStringParameter import ActionWithStringParameter  # NOQA
from Classes.App import App  # NOQA
from Classes.CheckUpdate import CheckUpdate  # NOQA
from Classes.Environment import Environment  # NOQA
from Classes.Exceptions import Exceptions  # NOQA
from Classes.ExceptionsProvider import ExceptionsProvider  # NOQA
from Classes.IrDecoder import IrDecoder  # NOQA
from Classes.IrDecoderPlugin import IrDecoderPlugin  # NOQA
from Classes.License import License  # NOQA
from Classes.NetworkSend import NetworkSend  # NOQA
from Classes.Password import Password  # NOQA
from Classes.RawReceiverPlugin import RawReceiverPlugin  # NOQA
from Classes.ResettableTimer import ResettableTimer  # NOQA
from Classes.SerialPort import SerialPort  # NOQA
from Classes.SerialThread import SerialThread  # NOQA
from Classes.Shortcut import Shortcut  # NOQA
from Classes.StdLib import StdLib  # NOQA
from Classes.Translation import Translation  # NOQA
from Classes.Version import Version  # NOQA
from Classes.WindowMatcher import WindowMatcher  # NOQA
from Classes.WinUsb import WinUsb  # NOQA
from Classes.WinUsbRemote import WinUsbRemote  # NOQA

from Classes.PluginManager import PluginManager  # NOQA
pluginManager = PluginManager()

STANDARD_RIGHTS_READ = 0x00020000
