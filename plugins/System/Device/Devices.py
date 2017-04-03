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
import pythoncom
import win32com.client
import fnmatch
import sys
import os
from Notifier import DEVICES


class GetDevices(eg.ActionBase):
    """
    System.GetDevice action.

    Searches for a device that the user specifies the name/vendorId.
    Returns a WMI device instance for the device(s).

    Help is located in the configuration dialog for this action.
    """

    __docsort__ = ('__call__',)

    name = 'Get System Devices'
    description = (
        'Returns a device object that represents a physical device\n'
        'on your computer.'
    )

    def __init__(self):
        self.result = None

    def __call__(self, pattern=None, **kwargs):
        """
        Searches Windows WMI for devices matching a user supplied string.

        Calls Windows WMI for device instances and then searches the instances
         Caption, Name, HardwareId, DeviceId, DeviceID attributes to see if
         they match the string that has been supplied.

        Wildcards can be used :
            ? Matches a single character
            * Matches a  series of characters

        When using this action it is advisable to pass the search text via a
        keyword. the keyword you would use is the device type. it is very
        expensive to iterate through all of the devices on a computer. If you
        also use wildcards it could take a while to return the devices. The
        device types can be gotten from the configuration dialog for this
        action. They are container labels for the devices, all you need do is
        remove any spaces.

        The returned value is a tuple of device instances.. Each device comes
        from a device type and each device type may have different attributes.
        So you will need to read the Help for the different device types you
        want to access. These help files contain all of the attribute names
        and a description of them. The help is located in this actions
        configuration panel, you just need to click on the device type you
        want to know about and the help will load.

        GetDevices('SOME HDD NAME')
        GetDevices(DiskDrive='SOME HDD NAME')

        :param pattern: Text to search for.
        :type pattern: str
        :param kwargs: Keyword must be a valid device type. Value is the string
         to search for.
        :type kwargs: str
        :return: WMI instances that represent a device.
        :rtype: tuple of instances
        """

        if pattern is None and not kwargs:
            return

        if isinstance(pattern, dict):
            clsName = pattern.keys()[0]
            pattern = pattern.values()[0]

        elif pattern is None:
            if len(kwargs.keys()) > 1:
                eg.PrintNotice(
                    'You can only specify one device to search for.\n'
                    'If you want to broaden your search use ? or * as'
                    ' wildcards'
                )
                return
            clsName = kwargs.keys()[0]
            pattern = kwargs.values()[0]
        else:
            clsName = None

        searchableItems = []
        foundDevices = ()

        pythoncom.CoInitialize()
        wmi = win32com.client.GetObject("winmgmts:\\root\\cimv2")

        for devs in DEVICES.values():
            for dev in devs:
                if clsName == dev['cls_name']:
                    searchableItems.append(dev)
                    break

                if clsName is None:
                    displayName = dev['display_name'].replace(' ', '')
                    if displayName == dev['cls_name']:
                        searchableItems.append(dev)

            if clsName is not None and searchableItems:
                break

        for searchCls in searchableItems:
            primarySearch = searchCls['action_search']
            clsName = searchCls['cls_name']
            for device in wmi.ExecQuery("Select * from Win32_" + clsName):
                priSearch = [getattr(device, primarySearch)]

                for attr in ('Name', 'DeviceId', 'Description'):
                    priSearch.append(getattr(device, attr, None))

                hardId = getattr(device, 'HardwareId', None)
                if hardId and isinstance(hardId, tuple):
                    priSearch.extend(list(hardId))
                elif hardId:
                    priSearch.append(hardId)

                if '*' not in pattern and '?' not in pattern:
                    if pattern in priSearch:
                        foundDevices += (device,)
                else:
                    for search in priSearch:
                        if fnmatch.fnmatch(search, pattern):
                            foundDevices += (device,)
                            break
        del wmi
        win32com.client.pythoncom.CoUninitialize()
        eg.Print(str(len(foundDevices)) + ' Devices Found')
        return foundDevices

    def Configure(self, pattern=None):

        filePath = os.path.join(os.path.split(__file__)[0], 'Help.zip')
        sys.path.insert(0, filePath)

        Help = __import__('Help')

        win32com.client.pythoncom.CoInitialize()
        wmi = win32com.client.GetObject("winmgmts:\\root\\cimv2")

        panel = eg.ConfigPanel()
        panel.EnableButtons(False)

        self.result = pattern
        splitterWindow = wx.SplitterWindow(
            panel,
            -1,
            size=(850, 400),
            style=(
                wx.SP_LIVE_UPDATE |
                wx.CLIP_CHILDREN |
                wx.NO_FULL_REPAINT_ON_RESIZE
            )
        )

        htmlHelp = eg.HtmlWindow(splitterWindow)

        tree = wx.TreeCtrl(
            splitterWindow,
            -1,
            style=(
                wx.TR_HAS_BUTTONS |
                wx.TR_ROW_LINES |
                wx.CLIP_CHILDREN
            )
        )

        root = tree.AddRoot('Devices')
        tree.SetPyData(root, 'START')

        def SetHelp(cName):
            if cName.startswith('1394'):
                cName = cName[4:] + '1394'
            htmlHelp.SetPage(getattr(Help, cName.upper()).encode('ascii'))

        deviceDict = {}
        for guid in DEVICES.keys():
            devices = DEVICES[guid]
            for device in devices:
                clsName = device['display_name'].replace(' ', '')
                if device['cls_name'] == clsName:
                    deviceDict[clsName] = device

        for clsName in sorted(deviceDict.keys()):
            dvc = deviceDict[clsName]
            deviceTree = tree.AppendItem(root, dvc['display_name'])
            tree.SetPyData(deviceTree, clsName)

            for device in wmi.ExecQuery("Select * from Win32_" + clsName):
                deviceLabel = getattr(device, dvc['action_search'])
                deviceItem = tree.AppendItem(deviceTree, deviceLabel)
                tree.SetPyData(deviceItem, dvc)
                if self.result == {clsName: deviceLabel}:
                    tree.SelectItem(deviceItem)

        def SetResult(item, pyData):
            deviceName = tree.GetItemText(item)
            clsName = pyData['cls_name']
            self.result = {clsName: deviceName}
            panel.EnableButtons(True)
            return clsName

        def OnActivated(evt):
            item = evt.GetItem()
            if item.IsOk():
                pyData = tree.GetPyData(item)
                if isinstance(pyData, dict):
                    helpName = SetResult(item, pyData)
                else:
                    if tree.ItemHasChildren(item):
                        if tree.IsExpanded(item):
                            tree.Collapse(item)
                        else:
                            tree.Expand(item)
                    helpName = pyData
                    panel.EnableButtons(False)
                    self.result = None
                SetHelp(helpName)

        def OnSelectionChanged(evt):
            item = evt.GetItem()
            if item.IsOk():
                pyData = tree.GetPyData(item)
                if isinstance(pyData, dict):
                    helpName = SetResult(item, pyData)
                else:
                    panel.EnableButtons(False)
                    self.result = None
                    helpName = pyData
                SetHelp(helpName)

        def OnClose(evt):
            self.event.set()
            evt.Skip()
        panel.Bind(wx.EVT_CLOSE, OnClose)

        tree.Expand(root)
        tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, OnActivated)
        tree.Bind(wx.EVT_TREE_SEL_CHANGED, OnSelectionChanged)

        splitterWindow.SplitVertically(tree, htmlHelp)
        splitterWindow.SetMinimumPaneSize(120)
        splitterWindow.UpdateSize()

        panel.sizer.Add(splitterWindow, 1, wx.EXPAND | wx.ALL, 10)
        SetHelp('START')
        splitterWindow.SetSashPosition(200)

        while panel.Affirmed():
            panel.SetResult(self.result)

        del wmi
        win32com.client.pythoncom.CoUninitialize()
        sys.path.remove(filePath)
