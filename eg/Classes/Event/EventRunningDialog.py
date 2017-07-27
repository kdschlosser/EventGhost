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
#
import eg
import wx
from threading import Lock
from ObjectListView import GroupListView, ColumnDefn
from os.path import join
from time import localtime, strftime


class EventRunningDialog(eg.TaskletDialog):

    def Configure(self, parent):
        super(EventRunningDialog, self).__init__(
            parent=parent,
            id=wx.ID_ANY,
            title='Running Events',
            size=(1491, 800),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self._lock = Lock()
        self._lock.acquire()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        button_row = eg.ButtonRow(self, (wx.ID_APPLY, wx.ID_CANCEL))
        self.end_button = button_row.cancelButton
        self.close_button = button_row.applyButton

        self.end_button.SetLabel('End Thread')
        self.close_button.SetLabel('Close')

        icon = eg.Icons.PathIcon(join(eg.imagesDir, 'logo.png'))
        header_box = eg.HeaderBox(
            self,
            'Event Manager',
            'See what events are running',
            icon
        )

        def stop_time_getter(tme):
            if tme:
                return strftime("%H:%M:%S %d-%m-%Y", localtime(tme))
            else:
                return ''

        def start_time_getter(tme):
            if tme:
                return strftime("%H:%M:%S %d-%m-%Y", localtime(tme))
            else:
                return 'Not Started'

        def run_time_getter(ms):
            if ms:
                return '%.2fms' % ms
            else:
                return ''

        self.groupList = GroupListView(
            self,
            -1,
            style=wx.LC_REPORT | wx.SUNKEN_BORDER,
            showItemCounts=True
        )

        self.groupList.SetColumns([
            ColumnDefn(
                "Thread Id",
                "right",
                150,
                "id"
            ),
            ColumnDefn(
                "Queue Time",
                "right",
                125,
                "queue_time",
                stringConverter=start_time_getter
            ),
            ColumnDefn(
                "Start Time",
                "right",
                125,
                "start_time",
                stringConverter=start_time_getter
            ),
            ColumnDefn(
                "Stop Time",
                "right",
                125,
                "stop_time",
                stringConverter=stop_time_getter
            ),
            ColumnDefn(
                "Run Time",
                "right",
                125,
                "run_time",
                stringConverter=run_time_getter
            ),
            ColumnDefn(
                "Payload",
                "right",
                100,
                "payload",
                stringConverter="%s"
            ),
            ColumnDefn(
                "Result",
                "right",
                100,
                "result",
                stringConverter="%s"
            ),
            ColumnDefn(
                "Macro Complete",
                "right",
                110,
                "percent_actions",
                stringConverter="%.2f%%"
            ),
            ColumnDefn(
                "Event Complete",
                "right",
                100,
                "percent_macros",
                stringConverter="%.2f%%"
            ),
            ColumnDefn(
                "Running Action",
                "right",
                100,
                "running_action"
            ),
            ColumnDefn(
                "Running Macro",
                "right",
                100,
                "running_macro"
            ),
            ColumnDefn(
                "Event Name",
                "right",
                150,
                "event_name"
            ),

        ])

        self.groupList.SetSortColumn(self.groupList.columns[12])
        objects = []

        for event in eg.EventManager.threads.values():
            objects += event.queue

        if objects:
            self.groupList.SetObjects(objects)
        else:
            self.groupList.SetObjects(None)

        main_sizer.Add(header_box, 0, wx.EXPAND)
        main_sizer.Add(self.groupList, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(button_row.sizer, 0, wx.EXPAND)

        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        eg.eventRunningDialog = self
        self._lock.release()

        while self.Affirmed():
            self.SetResult(None)

    def EventUpdate(
        self,
        add_object=None,
        remove_object=None,
        update_object=None
    ):
        self._lock.acquire()
        if add_object is not None:
            self.groupList.AddObjects([add_object])
        elif remove_object is not None:
            self.groupList.RemoveObjects([remove_object])
            del remove_object
        elif update_object is not None:
            idx = self.groupList.GetIndexOf(update_object)
            self.groupList.RefreshIndex(idx, update_object)

        self._lock.release()

    def OnClose(self, evt=None):
        self.Hide()
        self.Destroy()
        eg.eventRunningDialog = None

    def OnCancel(self, evt):
        for obj in self.groupList.GetSelectedObjects():
            obj.stop = True

    def OnApply(self, evt):
        wx.CallAfter(self.OnClose)







