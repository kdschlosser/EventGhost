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

import wx
import eg
import Desktop
import Clipboard
import Device
import Power
import WinSys
import Session
from eg.WinApi import SoundMixer
from eg.cFunctions import StartHooks, StopHooks
from eg.WinApi import GetWindowThreadProcessId
from eg.WinApi.Dynamic import GetClipboardOwner, GetDriveType


eg.RegisterPlugin(
    name="System",
    author=(
        "Bitmonster",
        "blackwind",
        "K"
    ),
    version="1.2.0",
    description=(
        "Actions to control various aspects of your system, including "
        "audio, display, power, and registry."
    ),
    kind="core",
    guid="{A21F443B-221D-44E4-8596-E1ED7100E0A4}",
    icon=(
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/"
        "AAAACXBIWXMAAAsSAAALEgHS3X78AAAAB3RJTUUH1QsEFTMTHK3EDwAAAUhJREFUOMul"
        "k0FLAlEQx39vd/VLeJSV7hH0ASLqLBEU3u0UQUGHUBJvfYAkukWiKV2DvkHUNeiyxCai"
        "bAqlVHbYnQ6ur8Qktbm8mcf7/+bNezPwT1MAuXy2CiSn1BYyB4dbVhgkl5dWsO3ERMp2"
        "u0XpopgGNADbTrC6eTQR4Lq0r30NiEajACwuzCFjahXg5vZhaF8DfN8HwLBMkP5hpcIV"
        "QVB43ssIWAOCIOgDDBOU/MipAHh88njt9gAQkVHAwEzLDD2h+dzh/eOT7lsPUFgR62+A"
        "YRp47Q7NVgdEhdAIICjF+BIG1HunOST6fkCl419vMPgFz61P1U0aUKvVuDrfm0jUaDRG"
        "AIXqZTk9ZStnAFQun50H7na2d/F9H9d1icViQ3UCOI6jeyUej3NyegyQUrl8VtbXNmaa"
        "xHKliAWkypXi2YzTnPoC/MF4O/QjGPgAAAAASUVORK5CYII="
    ),
)

ACV = wx.ALIGN_CENTER_VERTICAL
oldGetDeviceId = SoundMixer.GetDeviceId


def GetDeviceId_(*args, **kwargs):
    id = oldGetDeviceId(*args, **kwargs)
    return id.encode(eg.systemEncoding) if not isinstance(id, int) else id


SoundMixer.GetDeviceId = GetDeviceId_

EVENT_LIST = (
    ("Idle", None),
    ("UnIdle", None),
    ("DriveMounted", None),
    ("DriveRemoved", None),
    ("DeviceAttached", None),
    ("DeviceRemoved", None),
)


class Text:
    forced = "Forced: %s"
    forcedCB = "Force close of all programs"
    primaryDevice = "Primary Sound Driver"
    device = "Device:"


class System(eg.PluginBase):
    text = Text
    hookStarted = False
    images = {}
    
    def __init__(self):
        text = self.text
        
        self.AddEvents(*EVENT_LIST)
        Device.AddActions(self)
        Desktop.AddActions(self)
        Power.AddActions(self)
        Clipboard.AddActions(self)
        WinSys.AddActions(self)
    
    def __start__(self):
        eg.Bind("ClipboardChange", self.OnClipboardChange)
        # Assign all available cd drives to self.drives. If CdRom.drive
        # is not already set, the first drive returned becomes the default.
        cdDrives = []
        letters = [l + ':' for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
        for drive in letters:
            if GetDriveType(drive) == 5:
                cdDrives.append(drive)
        self.cdDrives = cdDrives
        
        # start the drive changed notifications
        self.deviceChangeNotifier = Device.ChangeNotifier(self)
        
        # start the power broadcast notifications
        self.powerBroadcastNotifier = Power.BroadcastNotifier(self)
        
        # start the session change notifications (only on Win XP and above)
        if eg.WindowsVersion.IsXP():
            import Session
            
            self.sessionChangeNotifier = Session.ChangeNotifier(self)
        
        self.StartHookCode()
        eg.Bind("System.SessionLock", self.StopHookCode)
        eg.Bind("System.SessionUnlock", self.StartHookCode)
        
        # Use VistaVolume.dll from stridger for sound volume control on Vista
        if eg.WindowsVersion.IsVista():
            import VistaVolEvents as vistaVolumeDll
            
            vistaVolumeDll.RegisterVolumeHandler(self.VolumeEvent)
            vistaVolumeDll.RegisterMuteHandler(self.MuteEvent)
            
            def MuteOn2(self, deviceId=0):
                deviceId = SoundMixer.GetDeviceId(deviceId, True)
                try:
                    vistaVolumeDll.SetMute(1, deviceId)
                except:
                    return False
                    # pass
                return True
            
            def MuteOff2(self, deviceId=0):
                deviceId = SoundMixer.GetDeviceId(deviceId, True)
                try:
                    vistaVolumeDll.SetMute(0, deviceId)
                except:
                    return True
                    # pass
                return False
            
            def ToggleMute2(self, deviceId=0):
                deviceId = SoundMixer.GetDeviceId(deviceId, True)
                newvalue = None  # NOQA
                try:
                    newValue = not vistaVolumeDll.GetMute(deviceId)
                    vistaVolumeDll.SetMute(newValue, deviceId)
                    eg.Utils.time.sleep(0.1)  # workaround
                    newValue = vistaVolumeDll.GetMute(deviceId)  # workaround
                except:
                    pass
                return newValue
            
            def GetMute2(self, deviceId=0):
                try:
                    # deviceId = SoundMixer.GetDeviceId(deviceId, True).encode(eg.systemEncoding)
                    deviceId = SoundMixer.GetDeviceId(deviceId, True)
                    newvalue = None
                    try:
                        newvalue = vistaVolumeDll.GetMute(deviceId)
                    except:
                        pass
                    return newvalue
                except:
                    eg.PrintTraceback()
            
            def SetMasterVolume2(self, value=200, deviceId=0):
                deviceId = SoundMixer.GetDeviceId(deviceId, True)
                value = float(value) if isinstance(value,
                    (int, float)) else float(eg.ParseString(value))
                newvalue = None
                try:
                    if value >= 0 and value <= 100:
                        vistaVolumeDll.SetMasterVolume(value / 100.0, deviceId)
                    eg.Utils.time.sleep(0.1)  # workaround
                    newvalue = vistaVolumeDll.GetMasterVolume(deviceId) * 100.0
                except:
                    pass
                return newvalue
            
            def ChangeMasterVolumeBy2(self, value, deviceId=0):
                deviceId = SoundMixer.GetDeviceId(deviceId, True)
                value = float(value) if isinstance(value,
                    (int, float)) else float(eg.ParseString(value))
                newvalue = None
                try:
                    old = vistaVolumeDll.GetMasterVolume(deviceId) * 100
                    if old + value <= 0:
                        vistaVolumeDll.SetMasterVolume(0, deviceId)
                    elif old + value >= 100:
                        vistaVolumeDll.SetMasterVolume(1.0, deviceId)
                    else:
                        vistaVolumeDll.SetMasterVolume((old + value) / 100.0,
                            deviceId)
                    eg.Utils.time.sleep(0.1)  # workaround
                    newvalue = vistaVolumeDll.GetMasterVolume(deviceId) * 100.0
                except:
                    pass
                return newvalue
            
            actions = self.info.actions
            actions["MuteOn"].__call__ = MuteOn2
            actions["MuteOff"].__call__ = MuteOff2
            actions["ToggleMute"].__call__ = ToggleMute2
            actions["GetMute"].__call__ = GetMute2
            actions["SetMasterVolume"].__call__ = SetMasterVolume2
            actions["ChangeMasterVolumeBy"].__call__ = ChangeMasterVolumeBy2
    
    @eg.LogItWithReturn
    def __stop__(self):
        eg.Unbind("System.SessionLock", self.StopHookCode)
        eg.Unbind("System.SessionUnlock", self.StartHookCode)
        eg.Unbind("ClipboardChange", self.OnClipboardChange)
        self.deviceChangeNotifier.Close()
        self.powerBroadcastNotifier.Close()
        self.StopHookCode()
    
    def HideImage(self, title):
        if title in self.images:
            try:
                wx.CallAfter(self.images[title].OnExit)
            except:
                pass
    
    def IdleCallback(self):
        self.TriggerEvent("Idle")
    
    def MuteEvent(self, mute, volume):
        try:
            if mute:
                self.TriggerEvent("Mute", volume)
            else:
                self.TriggerEvent("UnMute", volume)
        except:
            pass
    
    def OnClipboardChange(self, value):
        ownerHwnd = GetClipboardOwner()
        if GetWindowThreadProcessId(ownerHwnd)[1] != eg.processId:
            self.TriggerEvent("ClipboardChanged")
    
    def OnComputerResume(self, dummySuspendType):
        self.StartHookCode()
    
    def OnComputerSuspend(self, dummySuspendType):
        self.StopHookCode()
    
    def StartHookCode(self, event=None):
        if self.hookStarted:
            return
        try:
            StartHooks(
                self.IdleCallback,
                self.UnIdleCallback,
            )
        except:
            eg.PrintTraceback()
        self.hookStarted = True
    
    def StopHookCode(self, event=None):
        if not self.hookStarted:
            return
        StopHooks()
        self.hookStarted = False
    
    def UnIdleCallback(self):
        self.TriggerEvent("UnIdle")
    
    def VolumeEvent(self, mute, volume):
        try:
            if mute:
                self.TriggerEvent("Mute", volume)
            else:
                self.TriggerEvent("Volume", volume)
        except:
            pass




