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
        name = 'Hard/SSD Drive'
        description = 'Hard/SSD Drive'


class DriveBase(ActionBase.ActionBase):
    WMI_CLASS = 'Win32_LogicalDisk'
    DEVICE_TYPE = 'DriveType=3'
    DEVICE_NAME = 'Name'


class HardDriveFileSystem(DriveBase):
    """
    Get the type of file system used on a hard/SSD drive.
    """
    
    name = "Get File System"
    description = "Get the type of file system used on a hard/SSD drive."
    
    def _run(self, drive):
        return drive.FileSystem


class HardDriveSize(DriveBase):
    """
    Get a hard/SSD drives size.
    """
    
    name = "Get Size"
    description = "Get a hard/SSD drives size."
    
    def _run(self, drive):
        return drive.Size


class HardDriveFreeSpace(DriveBase):
    """
    Get a hard/SSD drives free space.
    """
    
    name = "Get Free Space"
    description = "Get a hard/SSD drives free space."
    
    def _run(self, drive):
        return drive.FreeSpace


class HardDrive(DriveBase):
    """
    Get an instance representing a hard/SSD drive.
    """
    
    name = "Get Drive"
    description = "Get a hard/SSD drive."
    
    def _run(self, drive):
        return drive


class HardDriveInvokeChkDsk(DriveBase):
    """
    Invokes check disk (chkdsk) on a hard/SSD drive.
    """
    
    name = "Invoke Check Disk"
    description = "Invokes check disk (chkdsk) on a hard/SSD drive."
    
    def _run(self, drive):
        return drive.Chkdsk


class HardDriveScheduleAutoChkDsk(DriveBase):
    """
    Schedules check disk (chkdsk) to be run at the next restart if the dirty
    bit has been set.
    """
    
    name = "Schedule Chkdsk"
    description = (
        "Schedules check disk (chkdsk) to be run at the next restart."
    )
    
    def _run(self, drive):
        return drive.ScheduleAutoChk
