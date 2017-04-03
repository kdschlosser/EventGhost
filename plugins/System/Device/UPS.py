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
        name = 'UPS Battery Backup'
        description = 'UPS Battery Backup'


class UPSBase(ActionBase.ActionBase):
    WMI_CLASS = ' Win32_Battery'
    DEVICE_TYPE = None
    DEVICE_NAME = 'VolumeName'


class UPSStatus(UPSBase):
    """
    Get a UPS status.
    """
    
    name = "Get Status"
    description = "Get a UPS status."
    
    def _run(self, battery):
        status = [
            None,
            'Other',
            'Unknown',
            'Fully Charged',
            'Low',
            'Critical',
            'Charging',
            'Charging and High',
            'Charging and Low',
            'Charging and Critical'
            'Undefined',
            'Partially Charged'
        ]
        
        return [status[battery.BatteryStatus], battery.BatteryStatus]


class UPSTimeToFullCharge(UPSBase):
    """
    Get how long it will take for a UPS to recharge.
    """
    
    name = "Get Recharge Time"
    description = (
        "Get how long it will take for a UPS to recharge."
    )
    
    def _run(self, battery):
        return battery.TimeToFullCharge


class UPS(UPSBase):
    """
    Get an instance representing a UPS.
    """
    
    name = "Get UPS"
    description = "Get a UPS (laptop battery)."
    
    def _run(self, battery):
        return battery


class UPSEstimatedRunTime(UPSBase):
    """
    Estimates time remaining for a UPS.
    """
    
    name = "Estimated Run Time"
    description = "Estimates time remaining for a UPS."
    
    def _run(self, battery):
        return battery.EstimatedRunTime


class UPSEstimatedChargeRemaining(UPSBase):
    """
    Estimates UPS charge remaining (%).
    """
    
    name = "Estimated Charge Remaining"
    description = "Estimates UPS charge remaining (%)."
    
    def _run(self, battery):
        return battery.EstimatedChargeRemaining
