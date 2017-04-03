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

import eg
import wx
import thread
import ctypes
from Notifier import BroadcastNotifier
from eg.cFunctions import (
    ResetIdleTimer as HookResetIdleTimer,
    SetIdleTime as HookSetIdleTime,
)
from eg.WinApi.Dynamic import (
    AdjustTokenPrivileges,
    byref,
    ExitWindowsEx,
    GetCurrentProcess,
    InitiateSystemShutdown,
    LookupPrivilegeValue,
    OpenProcessToken,
    SetThreadExecutionState,
    sizeof,
    HANDLE,
    LUID,
    TOKEN_PRIVILEGES,
    EWX_LOGOFF,
    SE_PRIVILEGE_ENABLED,
    SE_SHUTDOWN_NAME,
    TOKEN_ADJUST_PRIVILEGES,
    TOKEN_QUERY
)


ICON = None


def AddActions(plugin):
    group = plugin.AddGroup(
        Text.Group.name,
        Text.Group.description,
        ICON
    )
   
    group.AddAction(Reboot)
    group.AddAction(PowerDown)
    group.AddAction(Hibernate)
    group.AddAction(Standby)
    group.AddAction(LogOff)
    group.AddAction(LockWorkstation)
    group.AddAction(SetSystemIdleTimer)
    group.AddAction(SetIdleTime)
    group.AddAction(ResetIdleTimer)
    group.AddAction(GetBootTimestamp)
    group.AddAction(GetUpTime)


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Power'
        description = 'Power'
        
    text = "Choose option:"
    choices = [
        "Disable system idle timer",
        "Enable system idle timer"
    ]
    

class __ComputerPowerAction(eg.ActionBase):
    iconFile = "icons/Shutdown"

    def Configure(self, bForceClose=False):
        panel = eg.ConfigPanel()
        checkbox = panel.CheckBox(bForceClose, self.plugin.text.forcedCB)
        panel.sizer.Add(checkbox, 0, wx.ALL, 10)
        while panel.Affirmed():
            panel.SetResult(checkbox.GetValue())

    def GetLabel(self, bForceClose=False):
        s = eg.ActionBase.GetLabel(self)
        if bForceClose:
            return self.plugin.text.forced % s
        else:
            return s


class Hibernate(__ComputerPowerAction):
    name = "Hibernate"
    description = (
        "Suspends the system by shutting down and entering a hibernation "
        "(S4) state."
    )
    iconFile = "icons/Hibernate"

    def __call__(self, bForceClose=False):
        thread.start_new_thread(
            ctypes.windll.Powrprof.SetSuspendState,
            (True, bForceClose, False)
        )


class LockWorkstation(eg.ActionBase):
    name = "Lock Workstation"
    description = (
        "Submits a request to lock the workstation's display. Locking a "
        "workstation protects it from unauthorized use. This function has "
        "the same result as pressing Ctrl+Alt+Del and clicking Lock "
        "Workstation."
    )
    iconFile = "icons/LockWorkstation"

    def __call__(self):
        ctypes.windll.user32.LockWorkStation()


class LogOff(eg.ActionBase):
    name = "Sign Out"
    description = (
        "Shuts down all processes running in the current logon session, "
        "then signs the user out."
    )
    iconFile = "icons/LogOff"

    def __call__(self):
        #SHTDN_REASON_MAJOR_OPERATINGSYSTEM = 0x00020000
        #SHTDN_REASON_MINOR_UPGRADE         = 0x00000003
        #SHTDN_REASON_FLAG_PLANNED          = 0x80000000
        #                                     ----------
        #                                     0x80020003
        ExitWindowsEx(EWX_LOGOFF, 0x80020003)


class PowerDown(__ComputerPowerAction):
    name = "Shut Down"
    description = (
        "Shuts down the system and turns off the power. The system "
        "must support the power-off feature."
    )
    iconFile = "icons/PowerDown"

    def __call__(self, bForceClose=False):
        AdjustPrivileges()
        InitiateSystemShutdown(None, None, 0, bForceClose, False)


class Reboot(__ComputerPowerAction):
    name = "Reboot"
    description = "Reboots the system."
    iconFile = "icons/Reboot"

    def __call__(self, bForceClose=False):
        AdjustPrivileges()
        InitiateSystemShutdown(None, None, 0, bForceClose, True)

class SetSystemIdleTimer(eg.ActionBase):
    name = "Set System Idle Timer"
    description = "Enables or disables the system idle timer."

    def __call__(self, flag=False):
        # ES_CONTINUOUS       = 0x80000000
        # ES_DISPLAY_REQUIRED = 0x00000002
        # ES_SYSTEM_REQUIRED  = 0x00000001
        #      or-ed together = 0x80000003
        if flag:
            SetThreadExecutionState(0x80000000)
        else:
            SetThreadExecutionState(0x80000003)

    def Configure(self, flag=False):
        panel = eg.ConfigPanel()
        text = self.text
        radioBox = wx.RadioBox(
            panel,
            -1,
            text.text,
            choices=text.choices,
            majorDimension=1
        )
        radioBox.SetSelection(int(flag))
        panel.sizer.Add(radioBox, 0, wx.EXPAND)

        while panel.Affirmed():
            panel.SetResult(bool(radioBox.GetSelection()))

    def GetLabel(self, flag=0):
        return self.text.choices[flag]


class Standby(__ComputerPowerAction):
    name = "Sleep"
    description = (
        "Suspends the system by shutting down and entering a suspend "
        "(sleep) state."
    )
    iconFile = "icons/Standby"

    def __call__(self, bForceClose=False):
        thread.start_new_thread(
            ctypes.windll.Powrprof.SetSuspendState,
            (False, bForceClose, False)
        )


class SetIdleTime(eg.ActionBase):
    class text:
        name = "Set Idle Time"
        description = "Sets the idle timer."
        label1 = "Wait"
        label2 = "seconds before triggering idle event."

    def __call__(self, idleTime):
        HookSetIdleTime(int(idleTime * 1000))

    def Configure(self, waitTime=60.0):
        panel = eg.ConfigPanel()
        waitTimeCtrl = panel.SpinNumCtrl(waitTime, integerWidth=5)
        panel.AddLine(self.text.label1, waitTimeCtrl, self.text.label2)
        while panel.Affirmed():
            panel.SetResult(waitTimeCtrl.GetValue())


class ResetIdleTimer(eg.ActionBase):
    name = "Reset Idle Time"
    description = "Resets the idle timer."

    def __call__(self):
        HookResetIdleTimer()


class GetBootTimestamp(eg.ActionBase):
    class text:
        name = "Get Boot Timestamp"
        description = """
            Returns the time of the last system boot.
            If checkbox is checked, result is a UNIX timestamp;
            otherwise, it is in human-readable format.
        """
        timestamp = "Return result as an UNIX timestamp"

    def __call__(self, timestamp = True):
        return eg.Utils.GetBootTimestamp(unix_timestamp = timestamp)

    def Configure(self, timestamp = True):
        panel = eg.ConfigPanel()
        checkbox = panel.CheckBox(timestamp, self.text.timestamp)
        panel.sizer.Add(checkbox, 0, wx.ALL, 10)
        while panel.Affirmed():
            panel.SetResult(checkbox.GetValue())


class GetUpTime(eg.ActionBase):
    class text:
        name = "Get Uptime"
        description = """
            Returns the uptime of system in seconds.
            If checkbox is not checked, returns the number of days,
            hours, minutes, and seconds.
        """
        ticks = "Return result as the number of seconds (ticks)"

    def __call__(self, ticks = True):
        return eg.Utils.GetUpTime(seconds = ticks)

    def Configure(self, ticks = True):
        panel = eg.ConfigPanel()
        checkbox = panel.CheckBox(ticks, self.text.ticks)
        panel.sizer.Add(checkbox, 0, wx.ALL, 10)
        while panel.Affirmed():
            panel.SetResult(checkbox.GetValue())


def AdjustPrivileges():
    """
    Adjust privileges to allow power down and reboot.
    """
    hToken = HANDLE()
    luid = LUID()
    OpenProcessToken(
        GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        byref(hToken)
    )
    LookupPrivilegeValue(None, SE_SHUTDOWN_NAME, byref(luid))
    newState = TOKEN_PRIVILEGES()
    newState.PrivilegeCount = 1
    newState.Privileges[0].Luid = luid
    newState.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
    AdjustTokenPrivileges(
        hToken,            # TokenHandle
        0,                 # DisableAllPrivileges
        newState,          # NewState
        sizeof(newState),  # BufferLength
        None,              # PreviousState
        None               # ReturnLength
    )


