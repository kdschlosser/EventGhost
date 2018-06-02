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


class Tasklet(threading.Thread):
    countTasklets = 0

    def __init__(self, func):
        self.__func = func
        self.__args = ()
        self.__kwargs = {}
        threading.Thread.__init__(self, target=self.__run)
        self.daemon = True

        Tasklet.countTasklets += 1
        self.taskId = Tasklet.countTasklets

    def __call__(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs

    def run(self):
        self.start()

    def __run(self):
        self.__func(*self.__args, **self.__kwargs)

    @classmethod
    def GetCurrentId(cls):
        return 0
