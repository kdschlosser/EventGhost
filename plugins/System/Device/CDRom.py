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
import wx
import thread
import time
from eg.WinApi.Dynamic import (
    byref,
    CloseHandle,
    CreateFile,
    DeviceIoControl,
    GetDriveType,
    DWORD,
    FILE_SHARE_READ,
    GENERIC_READ,
    OPEN_EXISTING,
)


ICON = 'icons/cdrom'


class Text(eg.TranslatableStrings):
    class Group:
        name = 'CD-ROM Drive'
        description = 'CD-ROM Drive'
        
    labels = [
        "Toggle drive tray: %s",
        "Open drive tray: %s",
        "Close drive tray: %s"
    ]
    options = [
        "Toggle between open and close drive tray",
        "Only open drive tray",
        "Only close drive tray"
    ]
    optionsLabel = "Choose action"
    driveLabel = "Drive:"


class OpenDriveTray(eg.ActionBase):
    name = "Open/Close Drive Tray"
    description = "Controls the tray of an optical drive."
    iconFile = "icons/cdrom"
    
    def __call__(self, drive=None, action=0):
        drive = drive or self.plugin.cdDrives[0]
        
        def SendCodeToDrive(code):
            device = getDeviceHandle(drive)
            try:
                hDevice = CreateFile(
                    device,
                    GENERIC_READ,
                    FILE_SHARE_READ,
                    None,
                    OPEN_EXISTING,
                    0,
                    0
                )
            except Exception:
                self.PrintError(
                    "Couldn't find drive %s:" % drive[:1].upper()
                )
                return
            bytesReturned = DWORD()
            DeviceIoControl(
                hDevice, # handle to the device
                code, # control code for the operation
                None, # pointer to the input buffer
                0, # size of the input buffer
                None, # pointer to the output buffer
                0, # size of the output buffer
                byref(bytesReturned),
                None      # pointer to an OVERLAPPED structure
            )
            CloseHandle(hDevice)
        
        def ToggleMedia():
            start = time.clock()
            SendCodeToDrive(2967560)
            end = time.clock()
            if end - start < 0.1:
                SendCodeToDrive(2967564)
        
        if action is 0:
            thread.start_new_thread(ToggleMedia, ())
        elif action is 1:
            thread.start_new_thread(SendCodeToDrive, (2967560,))
        elif action is 2:
            thread.start_new_thread(SendCodeToDrive, (2967564,))
    
    def Configure(self, drive=None, action=0):
        panel = eg.ConfigPanel()
        text = Text
        radiobox = wx.RadioBox(
            panel,
            -1,
            text.optionsLabel,
            choices=text.options,
            majorDimension=1
        )
        radiobox.SetSelection(action)
        # Assign all available cd drives to self.drives. If CdRom.drive
        # is not already set the first drive returned becomes the default.
        cdDrives = []
        letters = [letter + ':' for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
        for driveLetter in letters:
            if GetDriveType(driveLetter) == 5:
                cdDrives.append(driveLetter)
        
        choice = wx.Choice(panel, -1, choices=cdDrives)
        if drive is None:
            drive = ''
        if not choice.SetStringSelection(drive):
            choice.SetSelection(0)
        mySizer = eg.HBoxSizer(
            (panel.StaticText(text.driveLabel), 0, wx.ALIGN_CENTER_VERTICAL),
            ((5, 5)),
            (choice),
        )
        panel.sizer.AddMany(
            (
                (radiobox, 0, wx.EXPAND),
                ((5, 5)),
                (mySizer, 0, wx.EXPAND | wx.ALL, 5),
            )
        )
        while panel.Affirmed():
            panel.SetResult(
                str(choice.GetStringSelection()),
                radiobox.GetSelection()
            )
    
    def GetLabel(self, drive, action):
        return self.text.labels[action] % drive


def getDeviceHandle(drive):
    """
    Returns a properly formatted device handle for DeviceIOControl call.
    """
    return "\\\\.\\%s:" % drive[:1].upper()


class DriveBase(ActionBase.ActionBase):
    WMI_CLASS = 'Win32_CDROMDrive'
    DEVICE_TYPE = None
    DEVICE_NAME = 'Drive'


class CDRomSize(DriveBase):
    """
    Get a ROM drives size.
    """
    
    name = "Get Size"
    description = "Get a ROM drives size."
    
    def _run(self, drive):
        return drive.MaxMediaSize


class CDRomMediaType(DriveBase):
    """
    Get a ROM drives media type.
    """
    
    name = "Get Media Type"
    description = "Get a ROM drives media type."
    
    def _run(self, drive):
        return drive.MediaType


class CDRomTransferRate(DriveBase):
    """
    Get a ROM drives transfer rate.
    """
    
    name = "Get Transfer Rate"
    description = "Get a ROM drives transfer rate."
    
    def _run(self, drive):
        return drive.TransferRate


class CDRom(DriveBase):
    """
    Get an instance representing a ROM drive.
    """
    
    name = "Get ROM Drive"
    description = "Get a ROM drive"
    
    def _run(self, drive):
        return drive

