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


#
#
# ' and DeviceID like "%&001653%"'

import eg
import ActionBase
import WMI


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Bluetooth Device'
        description = 'Bluetooth Device'


class BlueteethBase(ActionBase.ActionBase):
    WMI_CLASS = 'Win32_PnPEntity'
    DEVICE_TYPE = None
    DEVICE_NAME = 'Name'

    def _get_devices(self, deviceId=None):
        query = (
            ' WHERE ConfigManagerErrorCode=0'
            ' AND Caption LIKE "Standard Serial over Bluetooth link (COM%"'
        )
        
        if deviceId is None:
            result = WMI.getdevices(self.WMI_CLASS + query, self.DEVICE_TYPE)
        else:
            result = WMI.getdevices(
                self.WMI_CLASS + query + ' AND DeviceID="%s"' % deviceId
            )
            
        return result[0] if len(result) == 1 else result


class CurrentVideoMode(BlueteethBase):
    """
    Get a video cards current video mode
    (width, height, color depth, refresh rate).
    """
    
    name = "Get Video Mode"
    description = (
        "Get a video cards current video mode "
        "(width, height, color depth, refresh rate)."
    )
    
    def _run(self, video):
        return (
            video.CurrentHorizontalResolution,
            video.CurrentVerticalResolution,
            video.CurrentNumberOfColors,
            video.CurrentRefreshRate
        )


class MinRefreshRate(VideoBase):
    """
    Get a video cards min refresh rate.
    """
    
    name = "Get Video Cards Min Refresh Rate"
    description = "Get a video cards min refresh rate."
    
    def _run(self, video):
        return video.MinRefreshRate


class MaxRefreshRate(VideoBase):
    """
    Get a video cards max refresh rate.
    """
    
    name = "Get Video Cards Max Refresh Rate"
    description = "Get a video cards max refresh rate."
    
    def _run(self, video):
        return video.MaxRefreshRate


class GetVideoCard(VideoBase):
    """
    Get an instance representing a video card.
    """
    
    name = "Get Video Card"
    description = "Get a video card."
    
    def _run(self, video):
        return video


class CurrentRefreshRate(VideoBase):
    """
    Video cards current refresh rate.
    """
    
    name = "Video Cards Current Refresh Rate"
    description = "Get a video cards current refresh rate."
    
    def _run(self, video):
        return video.CurrentRefreshRate


class CurrentResolution(VideoBase):
    """
    Video cards current resolution.
    """
    
    name = "Video Cards Current Resolution"
    description = "Get a video cards current resolution."
    
    def _run(self, video):
        return (
            video.CurrentHorizontalResolution,
            video.CurrentVerticalResolution
        )


class CurrentVerticalResolution(VideoBase):
    """
    Video cards current vertical resolution.
    """
    
    name = "Video Cards Current Vertical Resolution"
    description = "Get a video cards current vertical resolution."
    
    def _run(self, video):
        return video.CurrentVerticalResolution


class CurrentHorizontalResolution(VideoBase):
    """
    Video cards current horizontal resolution.
    """
    
    name = "Video Cards Current Horizontal Resolution"
    description = "Get a video cards current horizontal resolution."
    
    def _run(self, video):
        return video.CurrentHorizontalResolution
