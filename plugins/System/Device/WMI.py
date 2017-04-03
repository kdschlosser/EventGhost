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
import win32com.client
import pythoncom


class Text(eg.TranslatableStrings):
    deviceErrors = [
        'Device is working properly.',
        'Device is not configured correctly.',
        'Windows cannot load the driver for this device.',
        (
            'The driver for this device might be corrupted, or your '
            'system may be running low on memory or other resources.'
        ),
        (
            'Device is not working properly. One of its drivers or the '
            'registry might be corrupted.'
        ),
        (
            'Driver for the device requires a resource that Windows '
            'cannot manage.'
        ),
        'Boot configuration for the device conflicts with other devices.',
        'Cannot filter.',
        'The driver loader for the device is missing.',
        (
            'Device is not working properly. The controlling firmware is '
            'incorrectly reporting the resources for the device.'
        ),
        'Device cannot start.',
        'Device failed.',
        'Device cannot find enough free resources to use.',
        'Windows cannot verify the device\'s resources.',
        'Device cannot work properly until the computer is restarted.',
        (
            'Device is not working properly due to a possible '
            're-enumeration problem.'
        ),
        (
            'Windows cannot identify all of the resources that the '
            'device uses.'
        ),
        'Device is requesting an unknown resource type.',
        'Device drivers must be reinstalled.',
        'Failure using the VxD loader.',
        'Registry might be corrupted.',
        (
            'System failure. If changing the device driver is '
            'ineffective, see the hardware documentation. Windows is '
            'removing the device.'
        ),
        'Device is disabled.',
        (
            'System failure. If changing the device driver is '
            'ineffective, see the hardware documentation.'
        ),
        (
            'Device is not present, not working properly, or does not '
            'have all of its drivers installed.'
        ),
        'Windows is still setting up the device.',
        'Windows is still setting up this device.',
        'Device does not have valid log configuration.',
        'Device drivers are not installed.',
        (
            'Device is disabled. The device firmware did not provide '
            'the required resources.',
        ),
        'Device is using an IRQ resource that another device is using.',
        (
            'Device is not working properly. Windows cannot load the '
            'required device drivers.'
        )
    ]


class DeviceError(Exception):
    """
    Exception class for errors when enabling or disabling network adapters
    """
    
    def __init__(self, msg, device_state=None):
        
        if device_state is None:
            self.msg = str(msg) + ' device(s) not found'
        else:
            self.msg = '{0}, {1}'.format(
                str(msg),
                Text.deviceErrors[device_state]
            )
    
    def __str__(self):
        return self.msg


def GetDevices(query, addl_query=None):
    pythoncom.CoInitialize()
    wmi = win32com.client.GetObject("winmgmts:\\root\\cimv2")
    query = 'SELECT * FROM ' + query
    if addl_query is not None:
        query += ' WHERE ' + addl_query

    try:
        return wmi.ExecQuery(query)
    
    except pythoncom.com_error:
        raise DeviceError(
            '' if addl_query is None else addl_query.split('=')[-1]
        )
    
    finally:
        del wmi
        pythoncom.CoUninitialize()
