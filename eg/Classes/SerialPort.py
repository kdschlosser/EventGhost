# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2016 EventGhost Project <http://www.eventghost.org/>
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

from serial import Serial


class SerialPort(Serial):
    def __init__(self, *args, **kwargs):
        # the following if's are for backward compatibility. From EG 0.5rc5 we
        # return a str instead of an int from SerialPortChoice, so we need
        # to take care if we load a config file that was saved with pre 0.5rc5
        if args and isinstance(args[0], int):
            device_str = 'COM%d' % (args[0] + 1)
            args = list(args)
            args[0] = device_str
        elif 'port' in kwargs and isinstance(kwargs['port'], int):
            device_str = 'COM%d' % (kwargs['port'] + 1)
            kwargs['port'] = device_str
        Serial.__init__(self, *args, **kwargs)
