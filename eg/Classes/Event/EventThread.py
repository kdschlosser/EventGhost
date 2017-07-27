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

from ..ThreadWorker import ThreadWorker

# Local imports
import eg
from eg.WinApi.Dynamic import OpenProcess, PROCESS_SET_QUOTA


class EventThread(ThreadWorker):
    def __init__(self):
        ThreadWorker.__init__(self)
        self.startupEvent = None
        self.hHandle = OpenProcess(PROCESS_SET_QUOTA, 0, eg.processId)
        self.filters = {}

    def AddFilter(self, source, filterFunc):
        if source in self.filters:
            self.filters[source].append(filterFunc)
        else:
            self.filters[source] = [filterFunc]

    def Poll(self):
        pass

    def RemoveFilter(self, source, filterFunc):
        self.filters[source].remove(filterFunc)
        if len(self.filters[source]) == 0:
            del self.filters[source]

    @eg.LogIt
    def StartSession(self, filename):
        eg.actionThread.Func(eg.actionThread.StartSession, 120)(filename)
        eg.TriggerEvent("OnInit")
        if self.startupEvent is not None:
            eg.TriggerEvent(*self.startupEvent)
            self.startupEvent = None

    @eg.LogIt
    def StopSession(self):
        eg.actionThread.Func(eg.actionThread.StopSession, 120)()
        eg.PrintDebugNotice("StopSession done")
