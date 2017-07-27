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
import wx
import string
from os.path import join

# Local imports
import eg

ID_SHOW = wx.NewId()
ID_HIDE = wx.NewId()
ID_EXIT = wx.NewId()


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, show):
        self.stateIcons = (
            wx.Icon(join(eg.imagesDir, "Tray1.png"), wx.BITMAP_TYPE_PNG),
            wx.Icon(join(eg.imagesDir, "Tray3.png"), wx.BITMAP_TYPE_PNG),
            wx.Icon(join(eg.imagesDir, "Tray2.png"), wx.BITMAP_TYPE_PNG),
        )

        self.tooltip = []
        wx.TaskBarIcon.__init__(self)

        self.IconBar = IconBar(
            (127, 127, 0),
            (255, 255, 0),
            (0, 127, 127),
        )
        self.SetIconBar(0, 0, (0, 255, 255))

        # SetIcon *must* be called immediately after creation, as otherwise
        # it won't appear on Vista restricted user accounts. (who knows why?)
        if show:
            self.Show()

        self.currentState = 0
        self.reentrantLock = threading.Lock()
        # eg.Bind("ProcessingChange", self.OnProcessingChange)
        menu = self.menu = wx.Menu()
        text = eg.text.MainFrame.TaskBarMenu
        menu.Append(ID_SHOW, text.Show)
        menu.Append(ID_HIDE, text.Hide)
        menu.AppendSeparator()
        menu.Append(ID_EXIT, text.Exit)
        self.Bind(wx.EVT_MENU, self.OnCmdShow, id=ID_SHOW)
        self.Bind(wx.EVT_MENU, self.OnCmdHide, id=ID_HIDE)
        self.Bind(wx.EVT_MENU, self.OnCmdExit, id=ID_EXIT)
        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.OnTaskBarMenu)
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnCmdShow)

    def SetIconBar(self, l, r, sr_on):
        icon = self.IconBar.Get(l, r, sr_on)

        event = eg.event

        if event is None:
            tooltip = eg.APP_NAME + " " + eg.Version.string

        elif not l and not r:
            if event.string in self.tooltip:
                self.tooltip.remove(event.string)
            else:
                self.tooltip += [event.string]
            tooltip = '\n'.join(sorted(self.tooltip))

        else:
            if event.string not in self.tooltip:
                self.tooltip += [event.string]
            tooltip = '\n'.join(sorted(self.tooltip))

        if not tooltip:
            tooltip = eg.APP_NAME + " " + eg.Version.string

        self.SetIcon(icon, tooltip)

    def Close(self):
        if eg.mainFrame is not None:
            eg.mainFrame.Iconize(False)
        self.Hide()

    def Hide(self):
        if eg.mainFrame is not None:
            eg.mainFrame.Iconize(False)
        self.RemoveIcon()

    def OnCmdExit(self, event):
        if eg.mainFrame is None or len(eg.mainFrame.openDialogs) == 0:
            eg.app.Exit(event)
        else:
            eg.mainFrame.Iconize(False)
            eg.mainFrame.RequestUserAttention()

    def OnCmdHide(self, dummyEvent):
        if eg.mainFrame is not None:
            eg.mainFrame.Iconize(True)

    def OnCmdShow(self, dummyEvent=None):
        if eg.mainFrame is not None:
            eg.mainFrame.Iconize(False)
        else:
            eg.document.ShowFrame()

    def OnProcessingChange(self, state, event=None):
        if self.IsIconInstalled():
            icon = self.stateIcons[state]
            if state == 2:
                bmp = wx.EmptyBitmap(16, 16)

                if event is None:
                    colour = wx.Colour(255, 0, 0)
                else:
                    colour = wx.Colour(*event.colour)

                dc = wx.MemoryDC()
                dc.SelectObject(bmp)
                dc.SetBackground(wx.Brush(wx.Colour(125, 125, 125)))

                points = [wx.Point(2, 1), wx.Point(2, 14), wx.Point(13, 8)]
                dc.SetBrush(wx.Brush(colour))
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
                dc.DrawPolygon(points)

                mask = wx.Mask(bmp, wx.Colour(125, 125, 125))
                bmp.SetMask(mask)

                # dc.DrawBitmap(bmp, 0, 0)
                dc.Destroy()
                del dc
                del points[:]

                icon = wx.EmptyIcon()
                icon.CopyFromBitmap(bmp)

            self.SetIcon(icon, self.tooltip)

    def OnTaskBarMenu(self, dummyEvent):
        self.menu.Enable(ID_HIDE, eg.document.frame is not None)
        self.PopupMenu(self.menu)

    def Open(self):
        self.Show()

    def SetProcessingState(self, l, r, sr_on):
        self.reentrantLock.acquire()
        try:
            if l == 0 and r == 0:
                state = 0
            else:
                state = 1

            # if state == 0:
            #     if event == self.processingEvent:
            #         state = 1
            #     elif event == self.currentEvent:
            #         state = 0
            #     else:
            #         return
            # elif state == 1:
            #     self.processingEvent = None
            #     if event.shouldEnd.isSet():
            #         self.currentEvent = None
            #         state = 0
            #     else:
            #         return
            # elif state == 2:
            #     self.currentEvent = event
            #     self.processingEvent = event
            # self.currentState = state
            self.SetIconBar(l, r, sr_on)
            wx.CallAfter(eg.Notify, "ProcessingChange", state)
        finally:
            self.reentrantLock.release()

    def SetToolTip(self, tooltip):
        self.tooltip = tooltip

        # wx.CallAfter(self.OnProcessingChange, self.currentState)

    def Show(self):
        self.SetIconBar(0, 0, (0, 255, 255))
        # self.SetIcon(self.stateIcons[0], self.tooltip)


class IconBar:

    def __init__(self, l_off, l_on, r_off):
        self.s_line = "\xff\xff\xff" + "\0" * 45
        self.s_border = "\xff\xff\xff\0\0\0"
        self.s_point = "\0" * 3
        self.sl_off = string.join(map(chr, l_off), '') * 6
        self.sl_on = string.join(map(chr, l_on), '') * 6
        self.sr_off = string.join(map(chr, r_off), '') * 6

    ##
    # \brief gets a new icon with 0 <= l,r <= 5
    #
    def Get(self, l, r, r_on):

        s = "" + self.s_line
        for i in range(5):
            if i < (5 - l):
                sl = self.sl_off
            else:
                sl = self.sl_on

            if i < (5 - r):
                sr = self.sr_off
            else:
                sr = r_on

            s += self.s_border + sl + self.s_point + sr + self.s_point
            s += self.s_border + sl + self.s_point + sr + self.s_point
            s += self.s_line

        image = wx.EmptyImage(16, 16)
        image.SetData(s)

        bmp = image.ConvertToBitmap()
        bmp.SetMask(
            wx.Mask(bmp, wx.WHITE)
        )
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)
        wx.CallAfter(eg.Notify, "ProcessingChange.Bitmap", bmp)
        return icon
