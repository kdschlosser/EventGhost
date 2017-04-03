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


ICON = "icons/SetClipboard"


class Text(eg.TranslatableStrings):
    class Group:
        name = ' Clipboard'
        description = 'Clipboard'
        
    class SetClipboard:
        error = "Can't open clipboard"


class SetClipboard(eg.ActionWithStringParameter):
    name = "Copy to Clipboard"
    description = "Copies the specified string to the system clipboard."
    iconFile = "icons/SetClipboard"
    text = Text.SetClipboard
    
    def __call__(self, text):
        self.clipboardString = eg.ParseString(text)
        
        def Do():
            if wx.TheClipboard.Open():
                tdata = wx.TextDataObject(self.clipboardString)
                wx.TheClipboard.Clear()
                wx.TheClipboard.AddData(tdata)
                wx.TheClipboard.Close()
                wx.TheClipboard.Flush()
            else:
                self.PrintError(self.text.error)
        
        # We call the hot stuff in the main thread. Otherwise we get
        # a "CoInitialize not called" error form wxPython (even though we
        # surely have called CoInitialize for this thread.
        eg.CallWait(Do)


def AddActions(plugin):
    group = plugin.AddGroup(
        Text.Group.name,
        Text.Group.description,
        ICON
    )
    
    group.AddAction(SetClipboard)
