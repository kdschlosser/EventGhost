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


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Network Drive'
        description = 'Network Drive'


class NetworkDriveBase(ActionBase.ActionBase):
    WMI_CLASS = 'Win32_LogicalDisk'
    DEVICE_TYPE = 'DriveType=4'
    DEVICE_NAME = 'ProviderName'


class NetworkDriveFileSystem(NetworkDriveBase):
    """
    Get the type of file system used on a network drive.
    """
    
    name = "Get File System"
    description = "Get the type of file system used on a network drive."
    
    def _run(self, drive):
        return drive.FileSystem


class NetworkDriveSize(NetworkDriveBase):
    """
    Get a network drives size.
    """
    
    name = "Get Size"
    description = "Get a network drives size."
    
    def _run(self, drive):
        return drive.Size


class NetworkDriveFreeSpace(NetworkDriveBase):
    """
    Get a network drives free space.
    """
    
    name = "Get Free Space"
    description = "Get a network drives free space."
    
    def _run(self, drive):
        return drive.FreeSpace


class NetworkDrive(NetworkDriveBase):
    """
    Get an instance representing a network drive.
    """
    
    name = "Get Drive"
    description = "Get a network drive"
    
    def _run(self, drive):
        return drive


class NetworkDriveInvokeChkDsk(NetworkDriveBase):
    """
    Invokes check disk (chkdsk) on a network drive.
    """
    
    name = "Invoke Check Disk"
    description = "Invokes check disk (chkdsk) on a network drive."
    
    def _run(self, drive):
        return drive.Chkdsk

