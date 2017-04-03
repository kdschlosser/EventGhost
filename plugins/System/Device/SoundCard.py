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

import eg.WinApi.SoundMixer as SoundMixer
import threading
import os
import wx


ICON = 'icons/SoundCard'


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Sound Card'
        description = 'Sound Card'
        
    class SetMasterVolume:
        text1 = "Set master volume to"
        text2 = "percent."
    
    class PlaySound:
        text1 = "Path to soundfile:"
        text2 = "Wait for completion"
        text3 = "Trigger event after completion"
        fileMask = "Wav-Files (*.WAV)|*.wav|All-Files (*.*)|*.*"
        eventSuffix = "Completion"
        
    class ChangeMasterVolumeBy:
        text1 = "Change master volume by"
        text2 = "percent."
        


class ChangeMasterVolumeBy(eg.ActionBase):
    name = "Change Master Volume"
    description = "Changes the master volume relative to the current value."
    iconFile = "icons/SoundCard"

    text = Text.ChangeMasterVolumeBy
    

    def __call__(self, value, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        value = float(value) if isinstance(value, (int, float)) else float(eg.ParseString(value))
        SoundMixer.ChangeMasterVolumeBy(value, deviceId)
        return SoundMixer.GetMasterVolume(deviceId)

    def Configure(self, value=0, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        panel = eg.ConfigPanel()
        deviceCtrl = panel.Choice(
            deviceId + 1, choices=SoundMixer.GetMixerDevices(True)
        )
        #if eg.WindowsVersion.IsVista():
        #    deviceCtrl.SetValue(0)
        #    deviceCtrl.Enable(False)

        valueCtrl = panel.SmartSpinNumCtrl(value, min=-100, max=100)
        sizer = eg.HBoxSizer(
            (panel.StaticText(self.text.text1), 0, wx.ALIGN_CENTER_VERTICAL),
            (valueCtrl, 0, wx.LEFT | wx.RIGHT, 5),
            (panel.StaticText(self.text.text2), 0, wx.ALIGN_CENTER_VERTICAL),
        )

        #panel.AddLine("Device:", deviceCtrl)
        panel.AddLine(self.plugin.text.device, deviceCtrl)
        panel.AddLine(sizer)
        while panel.Affirmed():
            panel.SetResult(
                valueCtrl.GetValue(),
                deviceCtrl.GetStringSelection(),
            )

    def GetLabel(self, value, deviceId=0):
        primaryDevice = (deviceId == self.plugin.text.primaryDevice)
        deviceId = SoundMixer.GetDeviceId(deviceId)
        if isinstance(value, (int, float)):
            value = float(value)
            if not primaryDevice:
                return "%s #%i: %.2f %%" % (self.name, deviceId + 1, value)
            else:
                return "%s: %.2f %%" % (self.name, value)
        else:
            if not primaryDevice:
                return "%s #%i: %s %%" % (self.name, deviceId + 1, value)
            else:
                return "%s: %s %%" % (self.name, value)


class GetMute(eg.ActionBase):
    name = "Get Mute Status"
    description = "Gets mute status."
    iconFile = "icons/SoundCard"

    def __call__(self, deviceId=0):
        return SoundMixer.GetMute(deviceId)

    def Configure(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        panel = eg.ConfigPanel()
        deviceCtrl = panel.Choice(
            deviceId + 1, choices=SoundMixer.GetMixerDevices(True)
        )
        """if eg.WindowsVersion.IsVista():
            deviceCtrl.SetValue(0)
            deviceCtrl.Enable(False)"""
        #panel.AddLine("Device:", deviceCtrl)
        panel.AddLine(self.plugin.text.device, deviceCtrl)
        while panel.Affirmed():
            panel.SetResult(deviceCtrl.GetStringSelection())

    def GetLabel(self, *args):
        return self.text.name


class MuteOff(eg.ActionBase):
    name = "Turn Mute Off"
    description = "Turns mute off."
    iconFile = "icons/SoundCard"

    def __call__(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        SoundMixer.SetMute(False, deviceId)
        return False

    def Configure(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        panel = eg.ConfigPanel()
        deviceCtrl = panel.Choice(
            deviceId + 1, choices=SoundMixer.GetMixerDevices(True)
        )
        """if eg.WindowsVersion.IsVista():
            deviceCtrl.SetValue(0)
            deviceCtrl.Enable(False)"""
        #panel.AddLine("Device:", deviceCtrl)
        panel.AddLine(self.plugin.text.device, deviceCtrl)
        while panel.Affirmed():
            panel.SetResult(deviceCtrl.GetStringSelection())

    def GetLabel(self, *args):
        return self.text.name


class MuteOn(eg.ActionBase):
    name = "Turn Mute On"
    description = "Turns mute on."
    iconFile = "icons/SoundCard"

    def __call__(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        SoundMixer.SetMute(True, deviceId)
        return True

    def Configure(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        panel = eg.ConfigPanel()
        deviceCtrl = panel.Choice(
            deviceId + 1, choices=SoundMixer.GetMixerDevices(True)
        )
        """if eg.WindowsVersion.IsVista():
            deviceCtrl.SetValue(0)
            deviceCtrl.Enable(False)"""
        #panel.AddLine("Device:", deviceCtrl)
        panel.AddLine(self.plugin.text.device, deviceCtrl)
        while panel.Affirmed():
            panel.SetResult(deviceCtrl.GetStringSelection())

    def GetLabel(self, *args):
        return self.text.name
        

class PlaySound(eg.ActionWithStringParameter):
    name = "Play Sound"
    description = "Plays the specified sound."
    iconFile = "icons/SoundCard"
    text = Text.PlaySound
    

    class TriggerEvent(threading.Thread):
        def __init__(self, sound, suffix, prefix):
            threading.Thread.__init__(self)
            self.sound = sound
            self.suffix = suffix
            self.prefix = prefix

        def run(self):
            self.sound.Play(wx.SOUND_SYNC)
            eg.TriggerEvent(self.suffix, prefix = self.prefix)

    def __call__(self, wavfile, flags=wx.SOUND_ASYNC, evt = False):
        self.sound = wx.Sound(wavfile)
        suffix = "%s.%s" % (
            "%s.%s" % (self.name.replace(' ', ''), self.text.eventSuffix),
            os.path.splitext(os.path.split(wavfile)[1])[0].replace('.', '_')
        )
        prefix = self.plugin.name.replace(' ', '')
        if flags == wx.SOUND_SYNC:
            self.sound.Play(flags)
            if evt:
                eg.TriggerEvent(suffix, prefix = prefix)
        elif evt:
            te = self.TriggerEvent(self.sound, suffix, prefix)
            te.start()
        else:
            self.sound.Play(flags)

    def Configure(self, wavfile='', flags=wx.SOUND_ASYNC, evt = False):
        panel = eg.ConfigPanel()
        text = self.text
        filepathCtrl = panel.FileBrowseButton(wavfile, fileMask=text.fileMask)
        waitCheckbox = panel.CheckBox(flags == wx.SOUND_SYNC, text.text2)
        eventCheckbox = panel.CheckBox(evt, text.text3)

        panel.sizer.Add(panel.StaticText(text.text1), 0, wx.EXPAND)
        panel.sizer.Add(filepathCtrl, 0, wx.EXPAND)
        panel.sizer.Add(waitCheckbox, 0, wx.EXPAND | wx.TOP, 10)
        panel.sizer.Add(eventCheckbox, 0, wx.EXPAND | wx.TOP, 8)

        while panel.Affirmed():
            if waitCheckbox.IsChecked():
                flags = wx.SOUND_SYNC
            else:
                flags = wx.SOUND_ASYNC
            panel.SetResult(
                filepathCtrl.GetValue(),
                flags,
                eventCheckbox.IsChecked()
            )
    

class SetMasterVolume(eg.ActionBase):
    name = "Set Master Volume"
    description = "Sets the master volume to an absolute value."
    iconFile = "icons/SoundCard"
    text = Text.SetMasterVolume

    def __call__(self, value, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        value = float(value) if isinstance(value, (int, float)) else float(eg.ParseString(value))
        SoundMixer.SetMasterVolume(value, deviceId)
        return SoundMixer.GetMasterVolume(deviceId)

    def Configure(self, value=0, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        panel = eg.ConfigPanel()
        deviceCtrl = panel.Choice(
            deviceId + 1, choices=SoundMixer.GetMixerDevices(True)
        )
#        deviceCtrl = panel.Choice(deviceId, SoundMixer.GetMixerDevices())
        """if eg.WindowsVersion.IsVista():
            deviceCtrl.SetValue(0)
            deviceCtrl.Enable(False)"""
        valueCtrl = panel.SmartSpinNumCtrl(value, min=0, max=100)
        label1 = panel.StaticText(self.text.text1)
        label3 = panel.StaticText(self.plugin.text.device)
        eg.EqualizeWidths((label1, label3))
        sizer1 = eg.HBoxSizer(
            (label3, 0, wx.ALIGN_CENTER_VERTICAL),
            (deviceCtrl, 1, wx.LEFT | wx.RIGHT, 5),
        )
        style1 = wx.LEFT | wx.RIGHT
        style2 = wx.TOP
        if isinstance(valueCtrl.ctrl, wx._controls.TextCtrl):
            style1 |= wx.EXPAND
            style2 |= wx.EXPAND
        sizer2 = eg.HBoxSizer(
            (label1, 0, wx.ALIGN_CENTER_VERTICAL),
            (valueCtrl, 1, style1, 5),
            (panel.StaticText(self.text.text2), 0, wx.ALIGN_CENTER_VERTICAL),
        )
        panel.sizer.Add(sizer1, 0, wx.TOP, 10)
        panel.sizer.Add(sizer2, 0, style2, 10)
        while panel.Affirmed():
            panel.SetResult(
                valueCtrl.GetValue(),
                deviceCtrl.GetStringSelection(),
            )

    def GetLabel(self, value, deviceId=0):
        primaryDevice = (deviceId == self.plugin.text.primaryDevice)
        deviceId = SoundMixer.GetDeviceId(deviceId)
        if isinstance(value, (int, float)):
            value = float(value)
            if not primaryDevice:
                return "%s #%i: %.2f %%" % (self.name, deviceId + 1, value)
            else:
                return "%s: %.2f %%" % (self.name, value)
        else:
            if not primaryDevice:
                return "%s #%i: %s %%" % (self.name, deviceId + 1, value)
            else:
                return "%s: %s %%" % (self.name, value)


class ToggleMute(eg.ActionBase):
    name = "Toggle Mute"
    description = "Toggles mute."
    iconFile = "icons/SoundCard"

    def __call__(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        return SoundMixer.ToggleMute(deviceId)

    def Configure(self, deviceId=0):
        deviceId = SoundMixer.GetDeviceId(deviceId)
        panel = eg.ConfigPanel()
        deviceCtrl = panel.Choice(
            deviceId + 1, choices=SoundMixer.GetMixerDevices(True)
        )
        """if eg.WindowsVersion.IsVista():
            deviceCtrl.SetValue(0)
            deviceCtrl.Enable(False)"""
        #panel.AddLine("Device:", deviceCtrl)
        panel.AddLine(self.plugin.text.device, deviceCtrl)
        while panel.Affirmed():
            panel.SetResult(deviceCtrl.GetStringSelection())

    def GetLabel(self, *args):
        return self.text.name
