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
import WMI

import pythoncom
import win32com.client


class ActionBase(eg.ActionBase):
    """
    Base action class for device actions.
    """
    
    name = ''
    description = ''
    
    WMI_CLASS = ''
    DEVICE_TYPE = None
    DEVICE_NAME = ''
    
    def _get_devices(self, deviceId=None, deviceName=None):
        """
        Calls WMI to retrieve the devices.

        Makes the call to Windows WMI to retrieve device instances. If the
        deviceId parameter is not None it will return a device where
        the name matches. Otherwise it will return all devices.

        :type deviceId: str
        :rtype: tuple(instances)
        """
        
        try:
            if deviceId is None and deviceName is None:
                return WMI.GetDevices(self.WMI_CLASS, self.DEVICE_TYPE)
            elif deviceId is not None:
                return WMI.GetDevices(
                    self.WMI_CLASS,
                    'DeviceID="{0}"'.format(deviceId)
                )[0]
            else:
                return WMI.GetDevices(
                    self.WMI_CLASS,
                    '{0}="{1}"'.format(self.DEVICE_NAME, deviceId)
                )[0]
        
        except pythoncom.com_error:
            if deviceName is None:
                raise WMI.DeviceError('')
            else:
                raise WMI.DeviceError(deviceName)
    
    def GetLabel(self, deviceId='', deviceName=''):
        return "{0}: {1}".format(self.text.name, deviceName)
    
    def _run(self, device):
        raise NotImplementedError
    
    def __call__(self, deviceId=None, deviceName=None):
        device = self._get_devices(deviceId, deviceName)
        if device.ConfigManagerErrorCode not in (0, 22, None):
            raise WMI.DeviceError(deviceName, device.ConfigManagerErrorCode)
        
        return self._run(device)
    
    def Configure(self, deviceId='', deviceName=''):
        panel = eg.ConfigPanel()
        devices = self._get_devices()
        for device in devices:
            print device.Name, device.ConfigManagerErrorCode
        selection = 0
        choices = [
            getattr(d, self.DEVICE_NAME) for d in devices
            if d.ConfigManagerErrorCode in (0, 22, None)
        ]
        if not choices:
            choices = ['']
            ids = [None]
        
        else:
            ids = [
                d.DeviceID for d in devices
                if d.ConfigManagerErrorCode in (0, 22, None)
            ]
        
        if deviceName in choices:
            selection = choices.index(deviceName)
        
        driveCtrl = panel.Choice(selection, choices=choices)
        panel.AddLine(self.plugin.text.device, driveCtrl)
        
        while panel.Affirmed():
            panel.SetResult(
                ids[driveCtrl.GetSelection()],
                driveCtrl.GetStringSelection()
            )
