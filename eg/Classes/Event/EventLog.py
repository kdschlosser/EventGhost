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
import wx
from time import localtime, strftime


class EventLog(object):

    def __init__(self):
        self.itemId = None
        self.maxlength = 2000
        self.data = []
        self.log = None
        eg.Bind('Clear.Event.Logs', self.ClearLog)

    def SetItemId(self, itemId):
        self.itemId = itemId

        if self.log is not None:
            self.log.SetItemId(itemId)

    def ClearLog(self, dummyEvent=None):
        del self.data[:]
        if self.log is not None:
            self.log.logCtrl.OnCmdClearLog()

    def IsShown(self):
        return self.log is not None

    def CloseLog(self, dummyEvent=None):
        eg.Notify('Remove.Event.Logs', self.itemId)

    def Show(self, flag=True):
        if flag:
            if self.log is None:
                self.log = EventFrame(
                    self.itemId,
                    self.data[:]
                )
                eg.Bind('Close.Event.Logs', self.CloseLog)
                eg.Bind('Update.Event.Logs', self.log.CalculateSize)
                eg.Bind('SetIndent.Event.Logs', self.log.logCtrl.SetIndent)
                eg.Bind('SetTime.Event.Logs', self.log.logCtrl.SetTimeLogging)


                self.log.Show()
        else:
            if self.log is not None:
                eg.Unbind('Close.Event.Logs', self.CloseLog)
                eg.Unbind('Update.Event.Logs', self.log.CalculateSize)
                eg.Unbind('SetIndent.Event.Logs', self.log.logCtrl.SetIndent)
                eg.Unbind('SetTime.Event.Logs', self.log.logCtrl.SetTimeLogging)

                self.log.Show(False)
                self.log.Destroy()
                self.log = None

    def WriteLine(self, line, icon, wRef, when, indent):
        if len(self.data) >= self.maxlength:
            self.data.pop(0)
        self.data.append((line, icon, wRef, when, indent))
        if self.log is not None:
            self.log.logCtrl.WriteLine(line, icon, wRef, when, indent)
            self.log.logCtrl.Update()


EVENT_ICON = eg.EventItem.icon
ERROR_ICON = eg.Icons.ERROR_ICON


class EventFrame(wx.Frame):

    def __init__(self, itemId, data):
        self.itemId = itemId
        wx.Frame.__init__(
            self,
            eg.document.frame.logCtrl,
            style=(
                wx.FRAME_NO_TASKBAR |
                wx.FRAME_FLOAT_ON_PARENT |
                wx.BORDER_NONE |
                wx.CLIP_CHILDREN
            )
        )

        self.data = data
        self.logCtrl = LogCtrl(self, data)

        eg.document.frame.Bind(wx.EVT_SCROLL, self.CalculateSize)
        eg.document.frame.Bind(wx.EVT_SIZE, self.CalculateSize)
        eg.document.frame.Bind(wx.EVT_MOVE, self.CalculateSize)
        self.Bind(wx.EVT_SIZE, self.CalculateSize)
        self.CalculateSize()

    def SetItemId(self, itemId):
        self.itemId = itemId
        self.CalculateSize()

    def CalculateSize(self, evt=None):
        try:
            rect = eg.document.frame.logCtrl.GetItemRect(self.itemId)
        except wx.PyDeadObjectError:
            return

        l_x, l_y = eg.document.frame.ClientToScreen(
            eg.document.frame.logCtrl.GetPositionTuple()
        )
        l_w, l_h = eg.document.frame.logCtrl.GetClientSize()
        topItem = eg.document.frame.logCtrl.GetTopItem()
        bottomItem = eg.document.frame.logCtrl.GetCountPerPage() + topItem

        x_Pos = rect.x + l_x
        y_Pos = rect.y + l_y + rect.height
        w_Ctrl = l_w + 2
        h_Ctrl = (rect.height * 6) + 3

        item_count = self.logCtrl.GetItemCount()
        if item_count <= 6:
            col_width = w_Ctrl - 17
        else:
            col_width = w_Ctrl - 17

        if self.itemId + 7 >= bottomItem:
            h_Ctrl -= ((self.itemId + 7) - bottomItem) * rect.height

        elif topItem > self.itemId + 1:
            h_Ctrl -= (topItem - self.itemId) * rect.height
            mult = [5, 4, 3, 2, 1, 1]
            try:
                y_Pos += rect.height * mult[int(h_Ctrl / rect.height)]
            except IndexError:
                h_Ctrl = 0

        if h_Ctrl > 0:
            if not self.IsShown():
                self.Show()
                eg.document.frame.logCtrl.SetFocus()

            if self.GetPositionTuple() != (x_Pos, y_Pos):
                self.SetPosition((x_Pos, y_Pos))
            if self.GetSizeTuple() != (w_Ctrl, h_Ctrl):
                self.SetSize((w_Ctrl, h_Ctrl))

            self.logCtrl.SetColumnWidth(0, col_width)
        else:
            if self.IsShown():
                self.Hide()

        if evt is not None:
            try:
                evt.Skip()
            except AttributeError:
                pass


class LogCtrl(wx.ListCtrl):
    """
    Implementation of a ListCtrl with a circular buffer.
    """
    def __init__(self, parent, data):
        self.data = data
        self.parent = parent
        self.indent = eg.document.frame.logCtrl.indent
        self.logTimes = eg.document.frame.logCtrl.logTimes
        if self.logTimes:
            self.OnGetItemText = self.OnGetItemTextWithTime
        else:
            self.OnGetItemText = self.OnGetItemTextNormal
        self.__inSelection = False
        self.isOdd = False

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
            font = wx.Font(
                df.GetPointSize(),
                wx.DEFAULT,
                wx.NORMAL,
                wx.NORMAL,
                False,
                "Courier New"
            )
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
        menu.Append(menuId, eg.text.MainFrame.Menu.ClearLog)
        self.Bind(wx.EVT_MENU, self.OnCmdClearLog, id=menuId)
        self.contextMenu = menu

        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightUp)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnStartDrag)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

        accel_entries = [
            wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('A'), wx.ID_SELECTALL)
        ]
        accel = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel)

        self.SetItemCount(len(data))

        if eg.document.visibleLogItem:
            self.EnsureVisible(eg.document.visibleLogItem)
        else:
            self.EnsureVisible(len(self.data) - 1)

    if eg.debugLevel:
        @eg.LogIt
        def __del__(self):
            pass

    def CanCut(self):
        return False

    def CanCopy(self):
        return self.GetSelectedItemCount() > 0

    def CanPaste(self):
        return False

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

    def OnCmdSelectAll(self, dummyEvent=None):
        for idx in range(self.GetItemCount()):
            self.Select(idx)

    def OnDoubleClick(self, event):
        item, flags = self.HitTest(event.GetPosition())
        if flags & wx.LIST_HITTEST_ONITEM:
            icon, wref = self.GetItemData(item)[1:3]
            if icon != eg.EventItem.icon and wref is not None:
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
        customData.SetData(text.encode("utf-8"))

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

    def SetIndent(self, shouldIndent):
        if shouldIndent:
            self.indent = "    "
        else:
            self.indent = ""
        self.Refresh()

    def SetTimeLogging(self, flag):
        self.logTimes = flag
        if flag:
            self.OnGetItemText = self.OnGetItemTextWithTime
        else:
            self.OnGetItemText = self.OnGetItemTextNormal
        self.Refresh()

    @eg.AssertInMainThread
    def WriteLine(self, *args):
        self.data += [args]
        self.Freeze()
        while self.GetItemCount() >= len(self.data):
            self.DeleteItem(0)
            self.data.pop(0)

        self.Thaw()
        self.SetItemCount(len(self.data))
        self.Scroll()
        self.Update()
