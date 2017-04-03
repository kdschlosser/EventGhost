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
        name = 'Portable Battery'
        description = 'Portable Battery'
        

class BatteryBase(ActionBase.ActionBase):
    WMI_CLASS = 'Win32_PortableBattery'
    DEVICE_TYPE = None
    DEVICE_NAME = 'Caption'


class BatteryStatus(BatteryBase):
    """
    Get a portable batteries status.
    """
    
    name = "Get Status"
    description = "Get a portable batteries status."
    
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


class BatteryTimeToFullCharge(BatteryBase):
    """
    Get how long it will take for a portable battery to recharge.
    """
    
    name = "Get Recharge Time"
    description = (
        "Get how long it will take for a portable battery to recharge."
    )
    
    def _run(self, battery):
        return battery.TimeToFullCharge


class Battery(BatteryBase):
    """
    Get an instance representing a portable battery.
    """
    
    name = "Get Portable Battery"
    description = "Get a Portable Battery (laptop battery)."
    
    def _run(self, battery):
        return battery


class BatteryEstimatedRunTime(BatteryBase):
    """
    Estimates time remaining for a portable battery.
    """
    
    name = "Estimated Run Time"
    description = "Estimates time remaining for a portable battery."
    
    def _run(self, battery):
        return battery.EstimatedRunTime


class BatteryEstimatedChargeRemaining(BatteryBase):
    """
    Estimates portable batteries charge remaining (%).
    """
    
    name = "Estimated Charge Remaining"
    description = "Estimates portable batteries charge remaining (%)."
    
    def _run(self, battery):
        return battery.EstimatedChargeRemaining
