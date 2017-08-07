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

from IrDecoder import IrDecoder
from UndoHandler import UndoHandler
from MainFrame import MainFrame
from AboutDialog import AboutDialog
from ActionBase import ActionBase
from ActionGroup import ActionGroup
from ActionItem import ActionItem
from ActionSelectButton import ActionSelectButton
from ActionThread import ActionThread
from ActionWithStringParameter import ActionWithStringParameter
from AddActionDialog import AddActionDialog
from AddActionGroupDialog import AddActionGroupDialog
from AddEventDialog import AddEventDialog
from AddPluginDialog import AddPluginDialog
from AnimatedWindow import AnimatedWindow
from AutostartItem import AutostartItem
from BoxedGroup import BoxedGroup
from ButtonRow import ButtonRow
from CheckBoxGrid import CheckBoxGrid
from CheckUpdate import CheckUpdate
from Choice import Choice
from Colour import Colour
from ColourSelectButton import ColourSelectButton
from ConfigDialog import ConfigDialog
from ConfigPanel import ConfigPanel
from ContainerItem import ContainerItem
from ControlProviderMixin import ControlProviderMixin
from Dialog import Dialog
from DigitOnlyValidator import DigitOnlyValidator
from DirBrowseButton import DirBrowseButton
from DisplayChoice import DisplayChoice
from Document import Document
from Environment import Environment
from EventGhostEvent import EventGhostEvent
from EventItem import EventItem
from EventRemapDialog import EventRemapDialog
from EventThread import EventThread
from Exceptions import Exceptions
from ExceptionsProvider import ExceptionsProvider
from ExportDialog import ExportDialog
from FileBrowseButton import FileBrowseButton
from FindDialog import FindDialog
from FolderItem import FolderItem
from FontSelectButton import FontSelectButton
from GUID import GUID
from HeaderBox import HeaderBox
from HtmlDialog import HtmlDialog
from HtmlWindow import HtmlWindow
from HyperLinkCtrl import HyperLinkCtrl
from ImagePicker import ImagePicker
from IrDecoderPlugin import IrDecoderPlugin
from LanguageEditor import LanguageEditor
from License import License
from Log import Log
from MacroItem import MacroItem
from MacroSelectButton import MacroSelectButton
from MainMessageReceiver import MainMessageReceiver
from MessageDialog import MessageDialog
from MessageReceiver import MessageReceiver
from MonitorsCtrl import MonitorsCtrl
from NamespaceTree import NamespaceTree
from NetworkSend import NetworkSend
from OptionsDialog import OptionsDialog
from Panel import Panel
from Password import Password
from PasswordCtrl import PasswordCtrl
from PersistentData import PersistentData
from PluginBase import PluginBase
from PluginInstall import PluginInstall
from PluginInstanceInfo import PluginInstanceInfo
from PluginItem import PluginItem
from PluginManager import PluginManager
from PluginMetaClass import PluginMetaClass
from PluginModuleInfo import PluginModuleInfo
from PythonEditorCtrl import PythonEditorCtrl
from RadioBox import RadioBox
from RadioButtonGrid import RadioButtonGrid
from RawReceiverPlugin import RawReceiverPlugin
from ResettableTimer import ResettableTimer
from RootItem import RootItem
from Scheduler import Scheduler
from SerialPort import SerialPort
from SerialPortChoice import SerialPortChoice
from SerialThread import SerialThread
from Shortcut import Shortcut
from SimpleInputDialog import SimpleInputDialog
from SizeGrip import SizeGrip
from Slider import Slider
from SmartSpinIntCtrl import SmartSpinIntCtrl
from SmartSpinNumCtrl import SmartSpinNumCtrl
from SoundMixerTree import SoundMixerTree
from SpinIntCtrl import SpinIntCtrl
from SpinNumCtrl import SpinNumCtrl
from StaticTextBox import StaticTextBox
from StdLib import StdLib
from TaskBarIcon import TaskBarIcon
from Tasklet import Tasklet
from TaskletDialog import TaskletDialog
from ThreadWorker import ThreadWorker
from TimeCtrl import TimeCtrl
from TimeCtrl_Duration import TimeCtrl_Duration
from TransferDialog import TransferDialog
from TranslatableStrings import TranslatableStrings
from Translation import Translation
from TreeItem import TreeItem
from TreeItemBrowseCtrl import TreeItemBrowseCtrl
from TreeItemBrowseDialog import TreeItemBrowseDialog
from TreeLink import TreeLink
from TreePosition import TreePosition
from WindowDragFinder import WindowDragFinder
from WindowList import WindowList
from WindowMatcher import WindowMatcher
from WindowsVersion import WindowsVersion
from WindowTree import WindowTree
from WinUsb import WinUsb
from WinUsbRemote import WinUsbRemote

__import__('pkg_resources').declare_namespace('eg')
