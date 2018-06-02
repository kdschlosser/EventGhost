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

import threading
import time

# Local imports
import eg
from eg.WinApi.Dynamic import ExitProcess


class App(object):
    def __init__(self):
        self.onExitFuncs = []
        self.shouldVeto = False
        self.firstQuery = True
        self.endSession = False

    @eg.LogIt
    def Exit(self, dummyEvent=None):
        eg.document.Close()
        eg.PrintDebugNotice("Triggering OnClose")
        egEvent = eg.eventThread.TriggerEvent("OnClose")

        while not egEvent.isEnded:
            pass

        return True

    @eg.LogItWithReturn
    def OnEndSession(self, dummyEvent):
        if self.endSession:
            return
        self.endSession = True
        egEvent = eg.eventThread.TriggerEvent("OnEndSession")
        while not egEvent.isEnded:
            pass
        eg.document.Close()
        self.OnExit()

    @eg.LogIt
    def OnExit(self):

        eg.PrintDebugNotice("Calling exit functions")

        for func in self.onExitFuncs:
            eg.PrintDebugNotice(func)
            func()

        eg.PrintDebugNotice("Calling eg.DeInit()")
        eg.Init.DeInit()

        currentThread = threading.currentThread()
        startTime = time.clock()
        waitTime = 0
        while True:
            threads = [
                thread for thread in threading.enumerate()
                if (
                    thread is not currentThread and
                    thread is not eg.messageReceiver._ThreadWorker__thread and
                    not thread.isDaemon() and
                    thread.isAlive()
                )
            ]
            if len(threads) == 0:
                break
            waitTime = time.clock() - startTime
            if waitTime > 5.0:
                break
            time.sleep(0.01)
        eg.PrintDebugNotice(
            "Waited for threads shutdown: %f s" % (time.clock() - startTime)
        )
        if eg.debugLevel and len(threads):
            eg.PrintDebugNotice("The following threads did not terminate:")
            for thread in threads:
                eg.PrintDebugNotice(" ", thread, thread.getName())
        eg.PrintDebugNotice("Done!")
        ExitProcess(0)

    def Restart(self, asAdmin=False):
        pass
