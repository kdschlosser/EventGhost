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
import ActionBase
from win32gui import SendMessage
from win32con import HWND_BROADCAST, WM_SYSCOMMAND
from eg.WinApi.Dynamic import SC_MONITORPOWER


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Monitor'
        description = 'Monitor'


class MonitorBase(ActionBase.ActionBase):
    WMI_CLASS = 'Win32_DesktopMonitor'
    DEVICE_TYPE = None
    DEVICE_NAME = 'Name'


class Monitor(MonitorBase):
    """
    Get a device instance representing a monitor.
    """
    
    name = "Get Monitor"
    description = "Get a device instance representing a monitor"
    
    def _run(self, monitor):
        return monitor


class MonitorSize(MonitorBase):
    """
    Get a monitors screen size.
    """
    
    name = "Get Screen Size"
    description = "Get a monitors screen size."
    
    def _run(self, monitor):
        return (
            monitor.ScreenWidth,
            monitor.ScreenHeight
        )


class MonitorHeight(MonitorBase):
    """
    Get a monitors screen height.
    """
    
    name = "Get Screen Height"
    description = "Get a monitors screen height."
    
    def _run(self, monitor):
        return monitor.ScreenHeight


class MonitorWidth(MonitorBase):
    """
    Get a monitors screen width.
    """
    
    name = "Get Screen Width"
    description = "Get a monitors screen width."
    
    def _run(self, monitor):
        return monitor.ScreenWidth


class MonitorPowerBase(eg.ActionBase):
    name = ''
    description = ''
    iconFile = None
    
    def __call__(self):
        raise NotImplementedError
    
    def _change_monitor_state(self, state):
        SendMessage(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, state)


class MonitorPowerOff(MonitorPowerBase):
    name = "Turn Off"
    description = (
        "Sets the state of the display to power-off mode. This will "
        "be the most power-saving mode the display supports."
    )
    iconFile = "icons/Display"
    
    def __call__(self):
        self._change_monitor_state(2)


class MonitorPowerOn(MonitorPowerBase):
    name = "Turn On"
    description = (
        "Turns on a display when it is in low-power or power-off "
        "mode. Will also stop a running screen saver."
    )
    iconFile = "icons/Display"
    
    def __call__(self):
        self._change_monitor_state(-1)


class MonitorStandby(MonitorPowerBase):
    name = "Standby"
    description = "Sets the state of the display to low-power mode."
    iconFile = "icons/Display"
    
    def __call__(self):
        self._change_monitor_state(1)
