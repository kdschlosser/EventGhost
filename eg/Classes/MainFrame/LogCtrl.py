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

import wx
from ast import literal_eval
from time import localtime, strftime

# Local imports
import eg

EVENT_ICON = eg.EventItem.icon
ERROR_ICON = eg.Icons.ERROR_ICON

class LogCtrl(wx.ListCtrl):
    """
    Implementation of a ListCtrl with a circular buffer.
    """
    def __init__(self, parent):
        self.maxlength = 2000
        self.removeOnMax = 200
        self.eventLogs = {}
        self.indent = ""
        self.OnGetItemText = self.OnGetItemTextWithTime
        wx.ListCtrl.__init__(
            self,
            parent,
            style=(
                wx.LC_REPORT |
                wx.LC_VIRTUAL |
                wx.NO_FULL_REPAINT_ON_RESIZE |
                wx.HSCROLL |
                wx.CLIP_CHILDREN |
                wx.LC_NO_HEADER
            )
        )
        if eg.config.useFixedFont:
            df = self.GetFont()
            font = wx.Font(df.GetPointSize(), wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, "Courier New")
            self.SetFont(font)

        self.SetImageList(eg.Icons.gImageList, wx.IMAGE_LIST_SMALL)

        sysColour = eg.colour.windowBackground
        sysTextColour = eg.colour.windowText
        oddColour = eg.colour.GetOddLogColour()

        self.attr1 = wx.ListItemAttr()
        self.attr1.BackgroundColour = oddColour
        self.attr1.TextColour = sysTextColour

        self.attr2 = wx.ListItemAttr()
        self.attr2.BackgroundColour = sysColour
        self.attr2.TextColour = sysTextColour

        self.attr3 = wx.ListItemAttr()
        self.attr3.BackgroundColour = oddColour
        self.attr3.TextColour = (255, 0, 0)

        self.attr4 = wx.ListItemAttr()
        self.attr4.BackgroundColour = sysColour
        self.attr4.TextColour = (255, 0, 0)

        self.InsertColumn(0, "")

        # logger popup menu
        menu = wx.Menu()
        menu.Append(wx.ID_SELECTALL, eg.text.MainFrame.Menu.SelectAll)
        self.Bind(wx.EVT_MENU, self.OnCmdSelectAll, id=wx.ID_SELECTALL)
        menu.Append(wx.ID_COPY, eg.text.MainFrame.Menu.Copy)
        self.Bind(wx.EVT_MENU, self.OnCmdCopy, id=wx.ID_COPY)
        menu.AppendSeparator()
        menuId = wx.NewId()
        menu.Append(menuId, eg.text.MainFrame.Menu.Replay)
        self.Bind(wx.EVT_MENU, self.OnCmdReplay, id=menuId)
        menu.AppendSeparator()
        menuId = wx.NewId()
        menu.Append(menuId, eg.text.MainFrame.Menu.ClearLog)
        self.Bind(wx.EVT_MENU, self.OnCmdClearLog, id=menuId)
        self.contextMenu = menu

        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightUp)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnStartDrag)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        parent.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        parent.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

        eg.Bind('Remove.Event.Logs', self.RemoveEventLog)

        accel_entries = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('A'), wx.ID_SELECTALL)
        ]
        accel = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel)

        self.logTimes = True
        self.__inSelection = False
        self.isOdd = False
        self.data = []
        eg.log.SetCtrl(self)
        wx.CallAfter(self.SetData, eg.log.GetData())

    if eg.debugLevel:
        @eg.LogIt
        def __del__(self):
            pass

    def OnMouseWheel(self, evt):
        wx.CallAfter(eg.Notify, 'Update.Event.Logs')
        evt.Skip()

    def OnLeftDown(self, evt):
        x, y = evt.GetPosition()
        l_x, l_y = eg.document.frame.ClientToScreen(self.GetPositionTuple())
        l_c_w, l_c_h = self.GetClientSize()
        l_w, l_h = self.GetSizeTuple()

        stop_x = l_x + l_w
        stop_y = l_y + l_c_h

        start_x = l_x + l_c_w
        stary_y = l_y

        print x, y, start_x, stary_y, stop_x, stop_y

        if stop_x > x > start_x and stop_y > y > stary_y:
            self.CaptureMouse()
        evt.Skip()

    def OnLeftUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
            wx.CallAfter(eg.Notify, 'Update.Event.Logs')
        evt.Skip()

    def CanCut(self):
        return False

    def CanCopy(self):
        return self.GetSelectedItemCount() > 0

    def CanPaste(self):
        return False

    @eg.LogIt
    def Destroy(self):
        eg.Unbind('Remove.Event.Logs', self.RemoveEventLog)
        eg.Notify('Close.Event.Logs')
        eg.log.SetCtrl(None)

    def FocusLastItem(self):
        if self.GetFocusedItem() == -1:
            item = len(self.data) - 1
            self.Focus(item)
            self.SetItemState(item, 0, wx.LIST_STATE_SELECTED)

    def GetItemData(self, item):
        return self.data[item]

    def OnCmdClearLog(self, dummyEvent=None):
        self.SetItemCount(0)
        self.DeleteAllItems()
        del self.data[:]
        eg.log.data.clear()
        eg.Print(eg.text.MainFrame.Logger.welcomeText)
        self.FocusLastItem()
        self.Scroll()
        self.Refresh()

    def OnCmdCopy(self, dummyEvent=None):
        text = ""
        lines = 1
        firstItem = item = self.GetNextItem(
            -1,
            wx.LIST_NEXT_ALL,
            wx.LIST_STATE_SELECTED
        )
        if item != -1:
            text = self.OnGetItemText(item, 0)[1:]
            item = self.GetNextItem(
                item,
                wx.LIST_NEXT_ALL,
                wx.LIST_STATE_SELECTED
            )
            while item != -1:
                lines += 1
                text += "\r\n" + self.OnGetItemText(item, 0)[1:]
                item = self.GetNextItem(
                    item,
                    wx.LIST_NEXT_ALL,
                    wx.LIST_STATE_SELECTED
                )
        if text != "" and wx.TheClipboard.Open():
            textDataObject = wx.TextDataObject(text)
            dataObjectComposite = wx.DataObjectComposite()
            dataObjectComposite.Add(textDataObject)
            if lines == 1:
                eventstring, icon = self.GetItemData(firstItem)[:2]
                if icon == EVENT_ICON:
                    customDataObject = wx.CustomDataObject("DragEventItem")
                    customDataObject.SetData(eventstring.encode("UTF-8"))
                    dataObjectComposite.Add(customDataObject)

            wx.TheClipboard.SetData(dataObjectComposite)
            wx.TheClipboard.Close()
            wx.TheClipboard.Flush()

    def OnCmdReplay(self, dummyEvent=None):
        item = self.GetFirstSelected()
        while item != -1:
            text, icon = self.GetItemData(item)[:2]
            if icon == eg.Icons.EVENT_ICON:
                parts = text.split(" ", 1)
                e = parts[0]
                prefix, suffix = e.split(".", 1) if "." in e else [e, ""]
                payload = literal_eval(parts[1]) if len(parts) == 2 else None
                eg.TriggerEvent(suffix, payload, prefix)
            item = self.GetNextSelected(item)

    def OnCmdSelectAll(self, dummyEvent=None):
        for idx in range(self.GetItemCount()):
            self.Select(idx)

    def RemoveEventLog(self, item):
        event = self.eventLogs.pop(item)
        item_height = self.GetItemRect(item).height
        log_height = event.log.GetSizeTuple()[1]
        remove_entries = log_height / item_height

        self.Freeze()
        for _ in range(remove_entries):
            self.DeleteItem(item + 1)
            self.data.pop(item + 1)
            for idx in self.eventLogs.keys():
                if idx > item:
                    self.UpdateEventLog(idx, idx - 1)
        self.Thaw()
        event.log.Show(False)
        event.log.SetItemId(None)
        self.Scroll()
        self.Update()
        wx.CallAfter(eg.Notify, 'Update.Event.Logs')

    def AddEventLog(self, item, event):
        self.eventLogs[item] = event
        item_height = self.GetItemRect(item).height
        event.log.SetItemId(item)
        event.log.Show(True)
        log_height = event.log.GetSizeTuple()[1]
        add_entries = log_height / item_height

        self.Freeze()
        for _ in range(add_entries):
            self.data.insert(item + 1, self.data[item])
            for idx in self.eventLogs.keys():
                if idx > item:
                    self.UpdateEventLog(idx, idx + 1)

        self.SetItemCount(len(self.data))
        self.Thaw()
        self.Scroll()
        self.Update()
        wx.CallAfter(eg.Notify, 'Update.Event.Logs')

    def UpdateEventLog(self, old_index, new_index):
        if old_index in self.eventLogs:
            event = self.eventLogs.pop(old_index)
            if old_index == 0:
                self.RemoveEventLog(0)
            else:
                event.log.SetItemId(new_index)
                self.eventLogs[new_index] = event

    def OnDoubleClick(self, event):
        item, flags = self.HitTest(event.GetPosition())
        if flags & wx.LIST_HITTEST_ONITEM:
            icon, wref = self.GetItemData(item)[1:3]
            if icon == eg.EventItem.icon:
                if wref.log.IsShown():
                    self.RemoveEventLog(item)
                else:
                    self.AddEventLog(item, wref)
            elif wref is not None:
                node = wref()
                if node is not None and not node.isDeleted:
                    node.Select()

    def OnGetItemAttr(self, item):
        if item % 2 == 0:
            if self.data[item][1] != ERROR_ICON:
                return self.attr1
            else:
                return self.attr3
        else:
            if self.data[item][1] != ERROR_ICON:
                return self.attr2
            else:
                return self.attr4

    def OnGetItemImage(self, item):
        return self.data[item][1].index

    def OnGetItemText(self, item, column):
        return ""

    def OnGetItemTextNormal(self, item, dummyColumn):
        line, _, _, _, indent = self.data[item]
        return " " + indent * self.indent + line

    def OnGetItemTextWithTime(self, item, dummyColumn):
        line, _, _, when, indent = self.data[item]
        return (
            #strftime(" %X   ", localtime(when))
            strftime(" %H:%M:%S   ", localtime(when)) +
            indent * self.indent +
            line
        )

    def OnKillFocus(self, event):
        eg.Notify("FocusChange", None)
        event.Skip()

    def OnRightUp(self, dummyEvent):
        self.PopupMenu(self.contextMenu)

    def OnSetFocus(self, event):
        self.FocusLastItem()
        eg.Notify("FocusChange", self)
        event.Skip()

    def OnStartDrag(self, event):
        idx = event.GetIndex()
        itemData = self.GetItemData(idx)
        if itemData[1] != EVENT_ICON:
            return
        text = itemData[2]
        # create our own data format and use it in a
        # custom data object
        customData = wx.CustomDataObject(wx.CustomDataFormat("DragItem"))
        customData.SetData(text.string.encode("utf-8"))

        # And finally, create the drop source and begin the drag
        # and drop operation
        dropSource = wx.DropSource(self)
        dropSource.SetData(customData)
        result = dropSource.DoDragDrop(wx.Drag_AllowMove)
        if result == wx.DragMove:
            self.Refresh()

    def Scroll(self):
        if self.IsAutoscroll():
            self.ScrollList(0, 1000000)

    def IsAutoscroll(self):
        val = self.GetTopItem() + self.GetCountPerPage() + 2
        return len(self.data) <= val

    @eg.AssertInMainThread
    def SetData(self, data):
        # self.Freeze()
        for item in data:
            self.data += [item]

        self.SetItemCount(len(self.data))

        if eg.document.visibleLogItem:
            self.EnsureVisible(eg.document.visibleLogItem)
        else:
            self.EnsureVisible(len(self.data) - 1)

        # self.Thaw()

    def SetIndent(self, shouldIndent):
        eg.Notify('SetIndent.Event.Logs', shouldIndent)
        if shouldIndent:
            self.indent = "   "
        else:
            self.indent = ""
        self.Refresh()

    def SetTimeLogging(self, flag):
        eg.Notify('SetTime.Event.Logs', flag)
        self.logTimes = flag
        if flag:
            self.OnGetItemText = self.OnGetItemTextWithTime
        else:
            self.OnGetItemText = self.OnGetItemTextNormal
        self.Refresh()

    @eg.AssertInMainThread
    def WriteLine(self, line, icon, wRef, when, indent):
        data = self.data
        if len(data) >= self.maxlength:
            self.Freeze()
            for _ in range(self.removeOnMax):
                self.DeleteItem(0)
                data.pop(0)
                for i in self.eventLogs.keys():
                    self.UpdateEventLog(i, i - 1)
            self.Thaw()

        data.append((line, icon, wRef, when, indent))
        self.SetItemCount(len(data))
        self.Scroll()
        wx.CallAfter(eg.Notify, 'Update.Event.Logs')
        self.Update()
