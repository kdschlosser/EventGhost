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
import os
import sys
import pip
import subprocess

base_path = os.path.dirname(sys.executable)

for p in pip.get_installed_distributions():
    if p.project_name == 'pywin32':
        site_packages = p.location
        sys32_path = os.path.join(site_packages, 'pywin32_system32')
        win32_path = os.path.join(site_packages, 'win32')

        command = 'setx /M PATH "%PATH%'
        if base_path not in os.environ['PATH']:
            command += ';' + base_path
        if sys32_path not in os.environ['PATH']:
            command += ';' + sys32_path
        if win32_path not in os.environ['PATH']:
            command += ';' + win32_path

        proc = subprocess.Popen(command)
        proc.communicate()
        break

import win32serviceutil # NOQA
import win32service # NOQA
import servicemanager # NOQA
import time # NOQA

_module_snapshot = sys.modules.keys()[:]
_path_snapshot = sys.path[:]

import threading # NOQA
import __builtin__ # NOQA

eg = None


# noinspection PyPep8Naming
class EventGhostSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = 'EventGhost'
    _svc_display_name_ = 'EventGhost'

    # noinspection PyUnusedLocal
    def __init__(self, args):
        self.__was_running = False
        win32serviceutil.ServiceFramework.__init__(self, args)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPING,
            (self._svc_name_, '')
        )

        eg.mainThread.Continue()
        evt = threading.Event()

        def do():
            eg.document.Close()
            eg.PrintDebugNotice("Triggering OnClose")
            egEvent = eg.eventThread.TriggerEvent("OnClose")

            while not egEvent.isEnded:
                pass

            eg.PrintDebugNotice("Calling exit functions")
            eg.PrintDebugNotice("Calling eg.DeInit()")
            eg.PrintDebugNotice("stopping threads")
            eg.actionThread.Func(eg.actionThread.StopSession)()
            eg.scheduler.Stop()
            eg.actionThread.Stop()
            eg.eventThread.Stop()

            eg.PrintDebugNotice("shutting down")
            eg.config.Save()
            eg.messageReceiver.Stop()

            if eg.dummyAsyncoreDispatcher:
                eg.dummyAsyncoreDispatcher.close()

            currentThread = threading.currentThread()
            startTime = time.clock()
            # noinspection PyUnusedLocal
            waitTime = 0
            # noinspection PyProtectedMember
            msg_rcv_thread = eg.messageReceiver._ThreadWorker__thread

            while True:
                threads = [
                    thread for thread in threading.enumerate()
                    if (
                        thread not in (currentThread, msg_rcv_thread) and
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

            stopTime = time.clock() - startTime
            eg.PrintDebugNotice("Waited for threads shutdown: %f s" % stopTime)

            if eg.debugLevel and len(threads):
                eg.PrintDebugNotice("The following threads did not terminate:")
                for thread in threads:
                    eg.PrintDebugNotice(" ", thread, thread.getName())

            eg.PrintDebugNotice("Done!")
            eg.mainThread.Stop()

            evt.set()

        eg.mainThread.Call(do)
        evt.wait()

        for mod_name in sys.modules.keys():
            if mod_name not in _module_snapshot:
                try:
                    del sys.modules[mod_name]
                except KeyError:
                    continue

        delattr(__builtin__, 'eg')
        __builtin__.__import__ = eg._import
        sys.excepthook = eg._excepthook
        sys.path = _path_snapshot
        self.__was_running = True

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )

    def SvcPause(self):
        self.ReportServiceStatus(win32service.SERVICE_PAUSED)
        eg.mainThread.Pause()

    def SvcContinue(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        eg.mainThread.Continue()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTING,
            (self._svc_name_, '')
        )

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        import eg as _eg

        global eg
        eg = _eg

        eg.scheduler.start()
        eg.messageReceiver.Start()
        eg.actionThread.Start()
        eg.eventThread.startupEvent = eg.startupArguments.startupEvent

        startupFile = eg.startupArguments.startupFile
        if startupFile is None:
            startupFile = eg.config.autoloadFilePath
        if startupFile and not os.path.exists(startupFile):
            eg.PrintError(eg.text.Error.FileNotFound % startupFile)
            startupFile = None

        eg.eventThread.Start()
        eg.eventThread.Call(eg.eventThread.StartSession, startupFile)

        if eg.config.checkUpdate:
            # avoid more than one check per day
            today = time.gmtime()[:3]
            if eg.config.lastUpdateCheckDate != today:
                eg.config.lastUpdateCheckDate = today
                # eg.mainThread.Call(eg.CheckUpdate.Start)

        # Register restart handler for easy crash recovery.
        # if eg.WindowsVersion >= 'Vista':
        #     args = " ".join(eg.app.GetArguments())
        #     windll.kernel32.RegisterApplicationRestart(args, 8)

        eg.Print(eg.text.MainFrame.Logger.welcomeText)
        eg.mainThread.Start()


if __name__ == '__main__':
    # service = EventGhostSvc()
    # service.SvcDoRun()

    import pywintypes
    hSCManager = win32service.OpenSCManager(
        None,
        None,
        win32service.SC_MANAGER_CONNECT
    )
    try:
        status = win32serviceutil.QueryServiceStatus('EventGhost')[1]

    except pywintypes.error:
        print 'Cannot locate Service'
        args = sys.argv + ['--startup', 'auto', 'install']
        win32serviceutil.HandleCommandLine(EventGhostSvc, argv=args)
        status = win32serviceutil.QueryServiceStatus('EventGhost')[1]

    if status == win32service.SERVICE_STOPPED:
        win32serviceutil.StartService('EventGhost')
        win32serviceutil.WaitForServiceStatus(
            'EventGhost',
            win32service.SERVICE_RUNNING,
            10
        )
