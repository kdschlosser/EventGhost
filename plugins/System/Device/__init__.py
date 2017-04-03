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
import Battery
# import BlueTooth
import CDRom
import HardDrive
import Monitor
import Network
import NetworkDrive
import RemovableDrive
import SoundCard
import UPS
import VideoCard
import Devices
from Notifier import ChangeNotifier


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Devices'
        description = 'Devices'


def AddActions(plugin):
    deviceGroup = plugin.AddGroup(
        Text.Group.name,
        Text.Group.description,
        ICON
    )
    deviceGroup.AddAction(Devices.GetDevices)
    
    group = deviceGroup.AddGroup(
        Battery.Text.Group.name,
        Battery.Text.Group.description,
        Battery.ICON
    )
    group.AddAction(Battery.BatteryStatus)
    group.AddAction(Battery.BatteryTimeToFullCharge)
    group.AddAction(Battery.Battery)
    group.AddAction(Battery.BatteryEstimatedRunTime)
    group.AddAction(Battery.BatteryEstimatedChargeRemaining)
    
    #     group = deviceGroup.AddGroup(
    #         BlueTooth.Text.Group.name,
    #         BlueTooth.Text.Group.description,
    #         BlueTooth.ICON
    #     )
    group = deviceGroup.AddGroup(
        CDRom.Text.Group.name,
        CDRom.Text.Group.description,
        CDRom.ICON
    )
    group.AddAction(CDRom.OpenDriveTray)
    group.AddAction(CDRom.CDRomSize)
    group.AddAction(CDRom.CDRomMediaType)
    group.AddAction(CDRom.CDRomTransferRate)
    group.AddAction(CDRom.CDRom)
    
    group = deviceGroup.AddGroup(
        HardDrive.Text.Group.name,
        HardDrive.Text.Group.description,
        HardDrive.ICON
    )
    group.AddAction(HardDrive.HardDriveFileSystem)
    group.AddAction(HardDrive.HardDriveSize)
    group.AddAction(HardDrive.HardDriveFreeSpace)
    group.AddAction(HardDrive.HardDrive)
    group.AddAction(HardDrive.HardDriveInvokeChkDsk)
    group.AddAction(HardDrive.HardDriveScheduleAutoChkDsk)
    
    group = deviceGroup.AddGroup(
        Monitor.Text.Group.name,
        Monitor.Text.Group.description,
        Monitor.ICON
    )
    group.AddAction(Monitor.MonitorPowerOn)
    group.AddAction(Monitor.MonitorPowerOff)
    group.AddAction(Monitor.MonitorStandby)
    group.AddAction(Monitor.Monitor)
    group.AddAction(Monitor.MonitorSize)
    group.AddAction(Monitor.MonitorHeight)
    group.AddAction(Monitor.MonitorWidth)
    
    group = deviceGroup.AddGroup(
        Network.Text.Group.name,
        Network.Text.Group.description,
        Network.ICON
    )
    
    group.AddAction(Network.NetworkEnable)
    group.AddAction(Network.NetworkDisable)
    group.AddAction(Network.WakeOnLan)
    group.AddAction(Network.NetworkIPAddresses)
    group.AddAction(Network.Network)
    
    group = deviceGroup.AddGroup(
        NetworkDrive.Text.Group.name,
        NetworkDrive.Text.Group.description,
        NetworkDrive.ICON
    )
    group.AddAction(NetworkDrive.NetworkDriveFileSystem)
    group.AddAction(NetworkDrive.NetworkDriveSize)
    group.AddAction(NetworkDrive.NetworkDriveFreeSpace)
    group.AddAction(NetworkDrive.NetworkDrive)
    group.AddAction(NetworkDrive.NetworkDriveInvokeChkDsk)
    
    group = deviceGroup.AddGroup(
        RemovableDrive.Text.Group.name,
        RemovableDrive.Text.Group.description,
        RemovableDrive.ICON
    )
    group.AddAction(RemovableDrive.RemovableDriveFileSystem)
    group.AddAction(RemovableDrive.RemovableDriveSize)
    group.AddAction(RemovableDrive.RemovableDriveFreeSpace)
    group.AddAction(RemovableDrive.RemovableDrive)
    group.AddAction(RemovableDrive.RemovableDriveInvokeChkDsk)
    
    group = deviceGroup.AddGroup(
        SoundCard.Text.Group.name,
        SoundCard.Text.Group.description,
        SoundCard.ICON
    )
    group.AddAction(SoundCard.ChangeMasterVolumeBy)
    group.AddAction(SoundCard.GetMute)
    group.AddAction(SoundCard.PlaySound)
    group.AddAction(SoundCard.SetMasterVolume)
    group.AddAction(SoundCard.ToggleMute)
    group.AddAction(SoundCard.MuteOn)
    group.AddAction(SoundCard.MuteOff)
    
    group = deviceGroup.AddGroup(
        UPS.Text.Group.name,
        UPS.Text.Group.description,
        UPS.ICON
    )
    group.AddAction(UPS.UPSStatus)
    group.AddAction(UPS.UPSTimeToFullCharge)
    group.AddAction(UPS.UPS)
    group.AddAction(UPS.UPSEstimatedRunTime)
    group.AddAction(UPS.UPSEstimatedChargeRemaining)
    
    group = deviceGroup.AddGroup(
        VideoCard.Text.Group.name,
        VideoCard.Text.Group.description,
        VideoCard.ICON
    )
    group.AddAction(VideoCard.ChangeSettings)
    group.AddAction(VideoCard.SetDisplayPreset)
    group.AddAction(VideoCard.VideoCardCurrentMode)
    group.AddAction(VideoCard.VideoCardMinRefreshRate)
    group.AddAction(VideoCard.VideoCardMaxRefreshRate)
    group.AddAction(VideoCard.VideoCard)
    group.AddAction(VideoCard.VideoCardCurrentRefreshRate)
    group.AddAction(VideoCard.VideoCardCurrentResolution)
    group.AddAction(VideoCard.VideoCardCurrentVerticalResolution)
    group.AddAction(VideoCard.VideoCardCurrentHorizontalResolution)
