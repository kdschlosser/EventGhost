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
import wx.lib.agw.supertooltip as STT
from wx._core import PyDeadObjectError

import eg


Text = eg.text.EventDialog


class Config(eg.PersistentData):
    lastSelected = None


class AddEventPanel(eg.Panel):
    def __init__(self, parent, editName=""):
        super(AddEventPanel, self).__init__(parent=parent)

        self.parent = parent

        self.splitterWindow = splitterWindow = wx.SplitterWindow(
            self,
            -1,
            style=(
                wx.SP_LIVE_UPDATE |
                wx.CLIP_CHILDREN |
                wx.NO_FULL_REPAINT_ON_RESIZE
            )
        )

        leftPanel = eg.Panel(splitterWindow)
        self.tree = tree = wx.TreeCtrl(
            leftPanel, -1,
            style=wx.TR_DEFAULT_STYLE |
            wx.TR_HIDE_ROOT |
            wx.TR_FULL_ROW_HIGHLIGHT
        )
        tree.SetMinSize((100, 100))
        tree.SetImageList(eg.Icons.gImageList)

        tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChanged)
        tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated)
        tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnStartDrag)
        tree.Bind(wx.EVT_SET_FOCUS, self.OnFocusTree)
        tree.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpanding)
        tree.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnCollapsing)

        userEventLabel = wx.StaticText(
            leftPanel,
            label="{0}:".format(Text.userEventLabel)
        )
        userEventLabel.SetToolTip(wx.ToolTip(Text.userEventTooltip))

        self.eventName = eventName =wx.TextCtrl(
            leftPanel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER
        )
        eventName.Bind(wx.EVT_TEXT_ENTER, self.OnTextEnter)
        eventName.Bind(wx.EVT_SET_FOCUS, self.OnFocusUserEvent)
        eventName.Bind(wx.EVT_TEXT, self.OnText)
        eventName.SetToolTip(wx.ToolTip(Text.userEventTooltip))

        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(tree, 1, wx.EXPAND)
        leftSizer.Add(userEventLabel, 0, wx.TOP, 5)
        leftSizer.Add(eventName, 0, wx.EXPAND)
        leftPanel.SetSizer(leftSizer)
        leftPanel.SetToolTip(wx.ToolTip(Text.userEventTooltip))

        rightPanel = self.rightPanel = eg.Panel(splitterWindow)
        rightSizer = self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightPanel.SetSizer(rightSizer)
        rightPanel.SetAutoLayout(True)

        self.nameText = nameText = wx.StaticText(rightPanel)
        nameText.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))

        rightSizer.Add(nameText, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 5)

        staticBoxSizer = wx.StaticBoxSizer(
            wx.StaticBox(rightPanel, label=Text.descriptionLabel),
            wx.VERTICAL
        )
        self.docText = eg.HtmlWindow(rightPanel)
        self.docText.SetBorders(2)

        staticBoxSizer.Add(self.docText, 1, wx.EXPAND)
        rightSizer.Add(staticBoxSizer, 1, wx.EXPAND, 5)

        splitterWindow.SplitVertically(leftPanel, rightPanel)
        splitterWindow.SetMinimumPaneSize(120)
        splitterWindow.UpdateSize()

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(splitterWindow, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizerAndFit(mainSizer)
        self.SetSizer(mainSizer)
        splitterWindow.SetSashPosition(220)

        self.resultData = ""
        self.FillTree()

        if editName:
            eventName.ChangeValue(editName)
            item = self.FindEventItem(editName)
            if item.IsOk():
                tree.EnsureVisible(item)
                tree.SelectItem(item)
        else:
            self.ReselectLastSelected()
        eventName.SetInsertionPointEnd()
        wx.CallAfter(eventName.SetFocus)

    def FillTree(self):
        tree = self.tree
        tree.DeleteAllItems()
        self.root = tree.AddRoot("Functions")

        for node in eg.EventInfo.Nodes():
            parent = tree.AppendItem(
                parent=self.root,
                text=node.name,
                image=node.folderIndex,
            )
            tree.SetPyData(parent, node)
            tree.SetItemHasChildren(parent, True)

    def Collapse(self, treeItem):
        self.tree.Unbind(
            wx.EVT_TREE_ITEM_COLLAPSING,
            handler=self.OnCollapsing
        )
        self.tree.CollapseAllChildren(treeItem)
        self.tree.Bind(
            wx.EVT_TREE_ITEM_COLLAPSING,
            self.OnCollapsing
        )
        self.tree.DeleteChildren(treeItem)
        self.tree.SetItemHasChildren(treeItem)

    def Expand(self, treeItem, node):
        self.tree.Unbind(
            wx.EVT_TREE_ITEM_EXPANDING,
            handler=self.OnExpanding
        )
        for eventInfo in node:
            print eventInfo
            child = self.tree.AppendItem(
                parent=treeItem,
                text=eventInfo.event,
                image=eventInfo.iconIndex,
            )
            self.tree.SetPyData(child, eventInfo)

        self.tree.Expand(treeItem)

        self.tree.Bind(
            wx.EVT_TREE_ITEM_EXPANDING,
            self.OnExpanding
        )

    def OnExpanding(self, event):
        treeItem = event.GetItem()
        if treeItem.IsOk():
            node = self.tree.GetPyData(treeItem)
            self.Expand(treeItem, node)

    def OnCollapsing(self, event):
        treeItem = event.GetItem()
        if treeItem.IsOk():
            self.Collapse(treeItem)

    def OnActivated(self, event):
        treeItem = self.tree.GetSelection()
        if treeItem.IsOk():
            node = self.tree.GetPyData(treeItem)
            if isinstance(node, eg.EventInfo.Node):
                if self.tree.IsExpanded(treeItem):
                    self.Collapse(treeItem)
                else:
                    self.Expand(treeItem, node)
            else:
                Config.lastSelected = node.event
                self.resultData = Config.lastSelected
                self.parent.OnOK(event)

    def OnFocusTree(self, event):
        item = self.tree.GetSelection()
        if not item.IsOk():
            return
        self.DoSelectionChanged(item)

    def OnFocusUserEvent(self, event):
        value = self.resultData
        self.eventName.ChangeValue(value)
        self.resultData = value
        event.Skip()

    def OnStartDrag(self, event):
        treeItem = event.GetItem()
        if treeItem.IsOk():
            node = self.tree.GetPyData(treeItem)
            if isinstance(node, eg.EventInfo):
                text = node.event
            else:
                text = node.name
            # create our own data format and use it in a
            # custom data object
            customData = wx.CustomDataObject(wx.CustomDataFormat("DragItem"))
            customData.SetData(text.encode("utf-8"))

            # And finally, create the drop source and begin the drag
            # and drop opperation
            dropSource = wx.DropSource(self)
            dropSource.SetData(customData)
            result = dropSource.DoDragDrop(wx.Drag_DefaultMove)
            if result == wx.DragMove:
                self.Refresh()

    def OnSelectionChanged(self, event):
        item = event.GetItem()
        self.DoSelectionChanged(item)
        event.Skip()

    def DoSelectionChanged(self, treeItem):
        if treeItem.IsOk():
            node = self.tree.GetPyData(treeItem)
            if isinstance(node, eg.EventInfo):
                self.resultData = node.event
                Config.lastSelected = node.event

            self.eventName.ChangeValue(self.resultData)
            self.eventName.SetInsertionPointEnd()
            wx.CallAfter(self.SetFocusToTextCtrl)
            self.nameText.SetLabel(node.name)
            self.docText.SetBasePath(node.path)
            self.docText.SetPage(node.description)

    def SetFocusToTextCtrl(self):
        try:
            # It could happen that an event arrives after the dialog
            # has been closed. To avoid an error we use try/except here.
            self.eventName.SetFocus()
        except PyDeadObjectError:
            pass

    def OnText(self, evt):
        if not evt.GetEventObject().HasFocus():
            return
        self.resultData = value = evt.GetString()
        if not value:
            wx.CallAfter(self.FillTree)
            return

        values = [value.lower()]
        if "." in value:
            for v in value.split(".", 1):
                if v:
                    values.append(v.lower())

        allevts = self._allEventsData
        filtered = {}
        match = False
        label = Text.userEventLabel
        path = ""
        desc = Text.userEventTooltip

        for plugin in allevts:
            if len(values) < 3:
                if any(v in allevts[plugin][1].evalName.lower() for v in values):
                    filtered.update({plugin: allevts[plugin]})
                    continue

            events = allevts[plugin][2]
            for event in events:
                if any(v in event.lower() for v in values):
                    if any(v == event.lower() for v in values):
                        match = True
                        data = events[event][1]
                        if data.info.eventPrefix:
                            evt = data.info.eventPrefix + "." + data.name
                        else:
                            evt = data.name
                        self.resultData = evt
                        Config.lastSelected = evt
                        path = data.info.path
                        label = data.name
                        desc = data.description

                    if plugin not in filtered:
                        filtered.update(
                            {plugin: (
                                allevts[plugin][0],
                                allevts[plugin][1],
                                {event: (
                                    allevts[plugin][2][event][0],
                                    allevts[plugin][2][event][1]
                                )}
                            )}
                        )
                    else:
                        filtered[plugin][2].update(
                            {event: (
                                allevts[plugin][2][event][0],
                                allevts[plugin][2][event][1]
                            )}
                        )

        if not filtered:
            dummy_info = eg.PluginInstanceInfo()
            dummy_info.name = ""
            dummy_info.eventPrefix = ""
            dummy_info.description = Text.noMatch

            filtered = {Text.noMatch: (
                -1,
                dummy_info,
                {}  # events
            )}

        self.nameText.SetLabel(label if match else Text.userEventLabel)
        self.docText.SetBasePath(path if match else "")
        self.docText.SetPage(desc if match else Text.userEventTooltip)
        self.FillTree(filtered)
        self.tree.ExpandAllChildren(self.root)

    def OnTextEnter(self, event):
        value = event.GetString()
        if value:
            self.resultData = value
            Config.lastSelected = value
            #event.Skip()
            self.parent.OnOK(event)
        else:
            self.resultData = ""

    def ReselectLastSelected(self):
        if Config.lastSelected:
            treeItem = self.FindEventItem(Config.lastSelected)
            if treeItem.IsOk():
                self.tree.EnsureVisible(treeItem)
                self.tree.SelectItem(treeItem)

    def FindEventItem(self, searchText):
        if not searchText or "." not in searchText:
            return wx.TreeItemId()

        tree = self.tree
        parts = searchText.split(".", 1)
        eventPrefix, event = parts[0], parts[1].lower()

        treeItem = self.FindPluginItem(eventPrefix)

        while treeItem.IsOk():
            treeItem, cookie = tree.GetFirstChild(treeItem)
            if tree.GetItemText(treeItem).lower() == event:
                return treeItem
        return wx.TreeItemId()

    def FindPluginItem(self, pluginName):
        pluginName = pluginName.lower()
        tree = self.tree
        root = tree.GetRootItem()
        treeItem, cookie = tree.GetFirstChild(root)
        while treeItem.IsOk():
            node = tree.GetItemPyData(treeItem)
            if node.evalName and node.evalName.lower() == pluginName:
                return treeItem
            treeItem, cookie = tree.GetNextChild(root, cookie)

        return wx.TreeItemId()

