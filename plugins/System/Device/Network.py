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
import socket
import struct
import ActionBase


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Network Card'
        description = 'Network Card'
    
    
    class WakeOnLan:
        parameterDescription = "Ethernet adapter MAC address to wake up:"


class NetworkBase(ActionBase.ActionBase):
    WMI_CLASS = (
        'MSFT_NetAdapter' if eg.WindowsVersion >= 8 else 'Win32_NetworkAdapter'
    )
    DEVICE_TYPE = None
    DEVICE_NAME = 'Name'


class NetworkIPAddresses(NetworkBase):
    """
    Get a list of IP addresses for a network adapter.
    """
    
    name = "Get IP Addresses"
    description = "Get a network adapters IP addresses."
    
    def _run(self, adapter):
        return adapter.NetworkAddresses


class Network(NetworkBase):
    """
    Get an instance representing a network adapter.
    """
    
    name = "Get Network Adapter"
    description = "Get a network adapter"
    
    def _run(self, adapter):
        return adapter


class NetworkEnable(NetworkBase):
    """
    Enable network adapter action.
    """
    
    name = "Enable"
    description = "Enable a network adapter"
    
    def _run(self, adapter):
        return adapter.Enable


class NetworkDisable(NetworkBase):
    """
    Disable network adapter action.
    """
    
    name = "Disable"
    description = "Disable a network adapter"
    
    def _run(self, adapter):
        return adapter.Disable


class WakeOnLan(eg.ActionBase):
    name = "Wake on LAN"
    description = (
        "Wakes up another computer by sending a special "
        "network packet."
    )
    iconFile = "icons/WakeOnLan"
    text = Text.WakeOnLan
    
    def __call__(self, macAddress):
        # Check macaddress format and try to compensate.
        if len(macAddress) == 12:
            pass
        elif len(macAddress) == 12 + 5:
            sep = macAddress[2]
            macAddress = macAddress.replace(sep, '')
        else:
            raise ValueError('Incorrect MAC address format')
        
        # Pad the synchronization stream.
        data = ''.join(['FFFFFFFFFFFF', macAddress * 20])
        send_data = ''
        
        # Split up the hex values and pack.
        for i in range(0, len(data), 2):
            send_data = ''.join(
                [send_data, struct.pack('B', int(data[i: i + 2], 16))]
            )
        
        # Broadcast it to the LAN.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(send_data, ('<broadcast>', 7))
    
    def Configure(self, macAddress=""):
        from wx.lib.masked import TextCtrl
        
        
        panel = eg.ConfigPanel()
        macCtrl = TextCtrl(
            panel,
            mask="##-##-##-##-##-##",
            includeChars="ABCDEF",
            choiceRequired=True,
            defaultValue=macAddress.upper(),
            formatcodes="F!",
        )
        panel.AddLine(self.text.parameterDescription, macCtrl)
        while panel.Affirmed():
            panel.SetResult(macCtrl.GetValue())
