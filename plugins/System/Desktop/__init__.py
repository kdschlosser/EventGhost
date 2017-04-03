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
import os
import _winreg
import ctypes
from eg.WinApi.Utils import BringHwndToFront, GetMonitorDimensions
from base64 import b64decode, b64encode
from PIL import Image
from qrcode import QRCode, constants as QRconstants
from StringIO import StringIO
from threading import Timer
from eg.WinApi.Dynamic import (
    create_unicode_buffer,
    GetForegroundWindow,
    SendMessage,
    SystemParametersInfo,
    SC_SCREENSAVE,
    SPI_SETDESKWALLPAPER,
    SPIF_SENDCHANGE,
    SPIF_UPDATEINIFILE,
    WM_SYSCOMMAND
)


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = ' Desktop'
        description = 'Desktop'
        
    class SetWallpaper:
        text1 = "Path to image file:"
        text2 = "Alignment:"
        choices = (
            "Centered",
            "Tiled",
            "Stretched"
        )
        fileMask = (
            "All Image Files|*.jpg;*.bmp;*.gif;*.png|All Files (*.*)|*.*"
        )


def AddActions(plugin):
    group = plugin.AddGroup(
        Text.Group.name,
        Text.Group.description,
        ICON
    )
    
    group.AddAction(SetWallpaper)
    group.AddAction(StartScreenSaver)
    group.AddAction(DisplayImage)
    group.AddAction(HideImage)
    group.AddAction(ShowPicture)
    group.AddAction(ShowQRcode)

    
class SetWallpaper(eg.ActionWithStringParameter):
    name = "Change Wallpaper"
    description = "Changes your desktop wallpaper."
    iconFile = "icons/SetWallpaper"
    
    text = Text.SetWallpaper
    
    def __call__(self, imageFileName='', style=1):
        if imageFileName:
            image = wx.Image(imageFileName)
            imageFileName = os.path.join(
                eg.folderPath.RoamingAppData, "Microsoft", "Wallpaper1.bmp"
            )
            image.SaveFile(imageFileName, wx.BITMAP_TYPE_BMP)
        tile, wstyle = (("0", "0"), ("1", "0"), ("0", "2"))[style]
        hKey = _winreg.CreateKey(
            _winreg.HKEY_CURRENT_USER,
            "Control Panel\\Desktop"
        )
        _winreg.SetValueEx(
            hKey,
            "TileWallpaper",
            0,
            _winreg.REG_SZ,
            tile
        )
        _winreg.SetValueEx(
            hKey,
            "WallpaperStyle",
            0,
            _winreg.REG_SZ,
            wstyle
        )
        _winreg.CloseKey(hKey)
        res = SystemParametersInfo(
            SPI_SETDESKWALLPAPER,
            0,
            create_unicode_buffer(imageFileName),
            SPIF_SENDCHANGE | SPIF_UPDATEINIFILE
        )
        if res == 0:
            self.PrintError(ctypes.FormatError())
    
    def Configure(self, imageFileName='', style=1):
        panel = eg.ConfigPanel()
        text = self.text
        filepathCtrl = eg.FileBrowseButton(
            panel,
            size=(340, -1),
            initialValue=imageFileName,
            labelText="",
            fileMask=text.fileMask,
            buttonText=eg.text.General.browse,
        )
        choice = wx.Choice(panel, -1, choices=text.choices)
        choice.SetSelection(style)
        sizer = panel.sizer
        sizer.Add(panel.StaticText(text.text1), 0, wx.EXPAND)
        sizer.Add(filepathCtrl, 0, wx.EXPAND)
        sizer.Add(panel.StaticText(text.text2), 0, wx.EXPAND | wx.TOP, 10)
        sizer.Add(choice, 0, wx.BOTTOM, 10)
        
        while panel.Affirmed():
            panel.SetResult(filepathCtrl.GetValue(), choice.GetSelection())


class StartScreenSaver(eg.ActionBase):
    name = "Start Screensaver"
    description = "Starts the default screen saver."
    iconFile = "icons/StartScreenSaver"
    
    def __call__(self):
        SendMessage(GetForegroundWindow(), WM_SYSCOMMAND, SC_SCREENSAVE, 0)


class ShapedFrame(wx.Frame):
    timer = None
    
    def __init__(
        self,
        error,
        imageFile,
        sizeMode,
        fitMode,
        fit,
        stretch,
        resample,
        onTop,
        border,
        timeout,
        display,
        x,
        y,
        width_,
        height_,
        back,
        shaped,
        center,
        noFocus,
        name,
        plugin,
        data=None
    ):
        if data is None:
            try:
                pil = Image.open(imageFile)
            except:
                try:
                    pil = Image.open(StringIO(b64decode(imageFile)))
                except:
                    eg.PrintError(error % imageFile[:256])
                    return
        else:
            try:
                pil = Image.open(StringIO(b64decode(imageFile)))
            except:
                eg.PrintError(error % data)
                return
        self.name = name
        self.plugin = plugin
        self.imageFile = imageFile
        style = wx.FRAME_NO_TASKBAR
        self.hasAlpha = (pil.mode in ('RGBA', 'LA') or (
            pil.mode == 'P' and 'transparency' in pil.info))
        if self.hasAlpha:
            style |= wx.FRAME_SHAPED
        if onTop:
            style |= wx.STAY_ON_TOP
        style |= (
            wx.NO_BORDER,
            wx.BORDER_SIMPLE,
            wx.BORDER_DOUBLE,
            wx.BORDER_SUNKEN,
            wx.BORDER_RAISED)[border] if sizeMode != 3 else wx.NO_BORDER
        wx.Frame.__init__(self, None, -1, u"EG.System.DisplayImage.%s" % name,
            style=style)
        self.SetBackgroundColour(back)
        
        self.hasShape = False
        self.shaped = shaped
        self.delta = (0, 0)
        
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_TIMER, self.OnExit)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        if timeout:
            self.timer = wx.Timer(self)
            self.timer.Start(1000 * timeout)
        else:
            self.timer = None
        
        back = list(back)
        back.append((255, 0)[int(self.hasAlpha)])
        w, h = pil.size
        res = False
        monDim = GetMonitorDimensions()
        try:
            dummy = monDim[display]  # NOQA
        except IndexError:
            display = 0
        if sizeMode == 0:
            width_ = w
            height_ = h
        elif sizeMode == 3:  # FULLSCREEN
            width_ = monDim[display][2]
            height_ = monDim[display][3]
            x = 0
            y = 0
        if sizeMode > 0:  # SEMI/FIX SIZE or FULLSCREEN
            if (width_, height_) == (w, h):
                pass
            elif stretch and fit:
                res = True
            else:
                if stretch and w <= width_ and h <= height_:
                    res = True
                
                # elif fit and w >= width_ and h >= height_:
                elif fit and w >= width_ or h >= height_:
                    res = True
        if res:  # resize !
            if fitMode == 0:  # ignore aspect
                w = width_
                h = height_
            elif fitMode == 1:  # width AND height AND aspect
                w, h = Resize(w, h, width_, height_, force=True)
            elif fitMode == 2:  # width
                wpercent = (width_ / float(w))
                w = width_
                h = int((float(h) * wpercent))
            else:  # height
                wpercent = (height_ / float(h))
                h = height_
                w = int((float(w) * wpercent))
            if sizeMode == 1:
                width_ = w
                height_ = h
            meth = (
                Image.ANTIALIAS,
                Image.BILINEAR,
                Image.BICUBIC,
                Image.NEAREST)[resample]
            pil = pil.resize((w, h), meth)
        if (w, h) != (width_, height_) and width_ >= w and height_ >= h:
            im = Image.new("RGBA", (width_, height_), tuple(back))
            im.paste(pil, ((width_ - w) / 2, (height_ - h) / 2),
                pil.convert("RGBA"))
        else:
            im = pil
        
        im = piltoimage(im, self.hasAlpha)
        
        cliSize = (width_, height_)
        self.SetClientSize(cliSize)
        self.bmp = wx.BitmapFromImage(im)
        if self.hasAlpha:
            im.ConvertAlphaToMask()  # Here we can set threshold of alpha channel
            self.region = wx.RegionFromBitmap(wx.BitmapFromImage(im))
            if self.shaped:
                self.SetWindowShape()
        
        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0, 0, True)
        
        if center:
            w, h = self.GetSize()
            x = (monDim[display][2] - w) / 2
            y = (monDim[display][3] - h) / 2
        
        self.SetPosition((monDim[display][0] + x, monDim[display][1] + y))
        if name:
            self.plugin.images[name] = self
            self.plugin.TriggerEvent("ImageDisplayed", payload=name)
        if noFocus:
            eg.WinApi.Dynamic.ShowWindow(self.GetHandle(), 4)
        else:
            self.Show(True)
    
    def OnDoubleClick(self, evt):
        eg.TriggerEvent(
            "DoubleClick",
            prefix="System.DisplayImage",
            payload=self.imageFile
        )
        if self.hasAlpha:
            if self.hasShape:
                self.SetShape(wx.Region())
                self.hasShape = False
            else:
                self.SetWindowShape()
    
    def OnExit(self, evt=None):
        if self.timer:
            self.timer.Stop()
        del self.timer
        if self.name in self.plugin.images:
            del self.plugin.images[self.name]
        self.Close()
    
    def OnLeftDown(self, evt):
        self.CaptureMouse()
        x, y = self.ClientToScreen(evt.GetPosition())
        originx, originy = self.GetPosition()
        dx = x - originx
        dy = y - originy
        self.delta = ((dx, dy))
    
    def OnLeftUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
    
    def OnMouseMove(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            x, y = self.ClientToScreen(evt.GetPosition())
            fp = (x - self.delta[0], y - self.delta[1])
            self.Move(fp)
    
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 0, 0, True)
    
    def OnRightUp(self, evt):
        eg.TriggerEvent(
            "RightClick",
            prefix="System.DisplayImage",
            payload=self.imageFile
        )
        wx.CallAfter(self.OnExit)
    
    def SetWindowShape(self, *evt):
        self.hasShape = self.SetShape(self.region)


class ShowPictureFrame(wx.Frame):
    def __init__(self, size=(-1, -1), pic_path=None, display=0):
        wx.Frame.__init__(
            self,
            None,
            -1,
            "ShowPictureFrame",
            style=wx.NO_BORDER | wx.FRAME_NO_TASKBAR  # | wx.STAY_ON_TOP
        )
        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.Bind(wx.EVT_LEFT_DCLICK, self.LeftDblClick)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        bitmap = wx.EmptyBitmap(1, 1)
        self.staticBitmap = wx.StaticBitmap(self, -1, bitmap)
        self.staticBitmap.Bind(wx.EVT_LEFT_DCLICK, self.LeftDblClick)
        self.staticBitmap.Bind(wx.EVT_MOTION, self.ShowCursor)
        self.timer = Timer(2.0, self.HideCursor)
    
    def HideCursor(self):
        wx.CallAfter(
            self.staticBitmap.SetCursor,
            wx.StockCursor(wx.CURSOR_BLANK)
        )
    
    def LeftDblClick(self, dummyEvent):
        self.Show(False)
    
    def OnClose(self, dummyEvent):
        self.Hide()
    
    def OnShowMe(self):
        self.Show()
        BringHwndToFront(self.GetHandle())
        self.Raise()
        self.Update()
        self.staticBitmap.SetCursor(wx.StockCursor(wx.CURSOR_BLANK))
    
    def SetPicture(self, picturePath=None, display=0):
        if not picturePath:
            return
        width_ = GetMonitorDimensions()[display][2]
        height_ = GetMonitorDimensions()[display][3]
        pil = Image.open(picturePath)
        w, h = pil.size
        w, h = Resize(w, h, width_, height_)
        if pil.size != (w, h):
            pil = pil.resize((w, h), Image.NEAREST)
        
        bitmap = wx.BitmapFromBuffer(
            w, h, pil.convert('RGB').tobytes()
        )
        self.staticBitmap.SetBitmap(bitmap)
        x = GetMonitorDimensions()[display][0] + (width_ - w) / 2
        y = GetMonitorDimensions()[display][1] + (height_ - h) / 2
        self.SetDimensions(x, y, w, h)
    
    def ShowCursor(self, event):
        self.staticBitmap.SetCursor(wx.NullCursor)
        self.timer.cancel()
        self.timer = Timer(2.0, self.HideCursor)
        self.timer.start()
        event.Skip()


class DisplayImage(eg.ActionBase):
    name = "Display Image"
    description = "Displays an image on the screen."
    iconFile = "icons/ShowPicture"
    
    
    class text:
        path = "Path to image or base64 string:"
        titleLbl = "Name of image (required only if you want to close the image window programmatically):"
        display = "Monitor:"
        allImageFiles = 'All Image Files'
        allFiles = "All files"
        winSizeLabel = "Window size mode"
        winSizes = (
            "Adapt window size to image size",
            "Use a semi-fixed window size (no margins)",
            "Use a fixed window size",
            "Fullscreen"
        )
        posAndSize = "Monitor, position and size of window"
        xCoord = "X coordinate:"
        yCoord = "Y coordinate:"
        width = "Width:"
        high = "Height:"
        fitModeLabel = "Fit mode"
        fitModes = (
            "Fit image to window (ignore the aspect ratio)",
            "Fit image to window (keep the aspect ratio)",
            "Fit to window width (keep the aspect ratio)",
            "Fit to window height (keep the aspect ratio)",
        )
        fit = "Fit big images"
        stretch = "Stretch small images"
        resample = "Resample method:"
        resampleMethods = (
            "Antialias",
            "Bilinear",
            "Bicubic",
            "Nearest",
        )
        bckgrnd = "Background and alpha channel"
        bckgrndColour = "Background colour"
        shaped = "Shaped window (if alpha channel exists)"
        timeout1 = "The window automatically disappears after"
        timeout2 = "seconds (0 = feature disabled)"
        topFocus = "On top and focus options"
        onTop = "Stay on top"
        noFocus = "Show a image without stealing focus"
        borderLabel = "Window border:"
        borders = (
            "No border",
            "Simple",
            "Double",
            "Sunken",
            "Raised",
        )
        other = "Other options"
        Error = 'Exception in action "%s": Failed to open file "%%s" !'
        center = "Center on screen"
        toolTipFile = (
            "Enter a filename of image or insert the image as a base64 string"
        )
    
    
    def __call__(
        self,
        imageFile='',
        winSize=0,
        fitMode=1,
        fit=True,
        stretch=False,
        resample=0,
        onTop=True,
        border=4,
        timeout=10,
        display=0,
        x=0,
        y=0,
        width_=640,
        height_=360,
        back=(0, 0, 0),
        shaped=True,
        center=False,
        noFocus=True,
        title=""
    ):
        def parseArgument(arg):
            if not arg:
                return 0
            if isinstance(arg, int):
                return arg
            else:
                from locale import localeconv
                
                
                decimal_point = localeconv()['decimal_point']
                arg = eg.ParseString(arg).replace(decimal_point, ".")
                return int(float(arg))
        
        imageFile = eg.ParseString(imageFile)
        x = parseArgument(x)
        y = parseArgument(y)
        width_ = parseArgument(width_)
        height_ = parseArgument(height_)
        timeout = parseArgument(timeout)
        
        if title in self.plugin.images:
            self.plugin.HideImage(title)
        if imageFile:
            wx.CallAfter(
                ShapedFrame,
                self.text.Error % (self.name),
                imageFile,
                winSize,
                fitMode,
                fit,
                stretch,
                resample,
                onTop,
                border,
                timeout,
                display,
                x,
                y,
                width_,
                height_,
                back,
                shaped,
                center,
                noFocus,
                title,
                self.plugin,
            )
    
    def Configure(
        self,
        imageFile='',
        winSize=0,
        fitMode=1,
        fit=True,
        stretch=False,
        resample=0,
        onTop=True,
        border=4,
        timeout=10,
        display=0,
        x=0,
        y=0,
        width_=640,
        height_=360,
        back=(0, 0, 0),
        shaped=True,
        center=False,
        noFocus=True,
        title=""
    ):
        panel = eg.ConfigPanel()
        text = self.text
        
        displayLbl = wx.StaticText(panel, -1, text.display)
        pathLbl = wx.StaticText(panel, -1, text.path)
        titleLbl = wx.StaticText(panel, -1, text.titleLbl)
        titleCtrl = wx.TextCtrl(panel, -1, title)
        resampleLbl = wx.StaticText(panel, -1, text.resample)
        bckgrndLbl = wx.StaticText(panel, -1, text.bckgrndColour + ":")
        borderLbl = wx.StaticText(panel, -1, text.borderLabel)
        timeoutLbl_1 = wx.StaticText(panel, -1, text.timeout1)
        timeoutLbl_2 = wx.StaticText(panel, -1, text.timeout2)
        radioBoxWinSizes = wx.RadioBox(
            panel,
            -1,
            text.winSizeLabel,
            choices=self.text.winSizes,
            style=wx.RA_SPECIFY_ROWS
        )
        radioBoxWinSizes.SetSelection(winSize)
        filepathCtrl = eg.FileBrowseButton(
            panel,
            size=(340, -1),
            initialValue=imageFile,
            labelText="",
            fileMask='%s|*.jpg;*.bmp;*.gif;*.png|%s (*.*)|*.*' % (
                text.allImageFiles,
                text.allFiles
            ),
            buttonText=eg.text.General.browse,
        )
        filepathCtrl.textControl.SetToolTipString(text.toolTipFile)
        displayChoice = eg.DisplayChoice(panel, display)
        xCoordLbl = wx.StaticText(panel, -1, text.xCoord)
        yCoordLbl = wx.StaticText(panel, -1, text.yCoord)
        widthLbl = wx.StaticText(panel, -1, text.width)
        heightLbl = wx.StaticText(panel, -1, text.high)
        fitCtrl = wx.CheckBox(panel, -1, text.fit)
        fitCtrl.SetValue(fit)
        stretchCtrl = wx.CheckBox(panel, -1, text.stretch)
        stretchCtrl.SetValue(stretch)
        
        rb0 = wx.RadioButton(panel, -1, text.fitModes[0], style=wx.RB_GROUP)
        rb0.SetValue(fitMode == 0)
        rb1 = wx.RadioButton(panel, -1, text.fitModes[1])
        rb1.SetValue(fitMode == 1)
        rb2 = wx.RadioButton(panel, -1, text.fitModes[2])
        rb2.SetValue(fitMode == 2)
        rb3 = wx.RadioButton(panel, -1, text.fitModes[3])
        rb3.SetValue(fitMode == 3)
        resampleCtrl = wx.Choice(panel, -1, choices=text.resampleMethods)
        resampleCtrl.SetSelection(resample)
        backColourButton = eg.ColourSelectButton(panel, back,
            name=text.bckgrndColour)
        shapedCtrl = wx.CheckBox(panel, -1, text.shaped)
        shapedCtrl.SetValue(shaped)
        onTopCtrl = wx.CheckBox(panel, -1, text.onTop)
        onTopCtrl.SetValue(onTop)
        noFocusCtrl = wx.CheckBox(panel, -1, text.noFocus)
        noFocusCtrl.SetValue(noFocus)
        borderCtrl = wx.Choice(panel, -1, choices=text.borders)
        borderCtrl.SetSelection(border)
        centerCtrl = wx.CheckBox(panel, -1, text.center)
        centerCtrl.SetValue(center)
        
        xCoordCtrl = eg.SmartSpinIntCtrl(panel, -1, x, size=wx.Size(88, -1),
            textWidth=105)
        yCoordCtrl = eg.SmartSpinIntCtrl(panel, -1, y, size=((88, -1)),
            textWidth=105)
        widthCtrl = eg.SmartSpinIntCtrl(panel, -1, width_, textWidth=105)
        heightCtrl = eg.SmartSpinIntCtrl(panel, -1, height_, textWidth=105)
        timeoutCtrl = eg.SmartSpinIntCtrl(panel, -1, timeout, textWidth=105)
        
        def onCenter(evt=None):
            flag = radioBoxWinSizes.GetSelection() != 3 and not centerCtrl.GetValue()
            xCoordCtrl.Enable(flag)
            xCoordLbl.Enable(flag)
            yCoordCtrl.Enable(flag)
            yCoordLbl.Enable(flag)
            if evt:
                evt.Skip()
        
        centerCtrl.Bind(wx.EVT_CHECKBOX, onCenter)
        
        def enableCtrls_B(evt=None):
            mode = radioBoxWinSizes.GetSelection()
            wFlag = mode == 2 or (
                mode == 1 and (rb1.GetValue() or rb2.GetValue()))
            hFlag = mode == 2 or (
                mode == 1 and (rb1.GetValue() or rb3.GetValue()))
            widthCtrl.Enable(wFlag)
            widthLbl.Enable(wFlag)
            heightCtrl.Enable(hFlag)
            heightLbl.Enable(hFlag)
            if evt:
                evt.Skip()
        
        rb0.Bind(wx.EVT_RADIOBUTTON, enableCtrls_B)
        rb1.Bind(wx.EVT_RADIOBUTTON, enableCtrls_B)
        rb2.Bind(wx.EVT_RADIOBUTTON, enableCtrls_B)
        rb3.Bind(wx.EVT_RADIOBUTTON, enableCtrls_B)
        
        def enableCtrls_A(evt=None):
            mode = radioBoxWinSizes.GetSelection()
            flag = mode != 3
            centerCtrl.Enable(flag)
            if not flag:
                centerCtrl.SetValue(True)
            borderCtrl.Enable(flag)
            borderLbl.Enable(flag)
            if mode == 0:
                fitCtrl.SetValue(False)
                stretchCtrl.SetValue(False)
            elif mode == 1:
                if rb0.GetValue():
                    rb1.SetValue(True)
                fitCtrl.SetValue(True)
                stretchCtrl.SetValue(True)
            flag = mode != 0 and (fitCtrl.GetValue() or stretchCtrl.GetValue())
            rb1.Enable(flag)
            rb2.Enable(flag)
            rb3.Enable(flag)
            resampleCtrl.Enable(flag)
            resampleLbl.Enable(flag)
            flag = mode > 1
            fitCtrl.Enable(flag)
            stretchCtrl.Enable(flag)
            flag = flag and (fitCtrl.GetValue() or stretchCtrl.GetValue())
            rb0.Enable(flag)
            if evt:
                evt.Skip()
            enableCtrls_B()
            onCenter()
        
        radioBoxWinSizes.Bind(wx.EVT_RADIOBOX, enableCtrls_A)
        fitCtrl.Bind(wx.EVT_CHECKBOX, enableCtrls_A)
        stretchCtrl.Bind(wx.EVT_CHECKBOX, enableCtrls_A)
        enableCtrls_A()
        
        # Sizers
        borderSizer = wx.BoxSizer(wx.HORIZONTAL)
        borderSizer.Add(borderLbl, 0, wx.TOP, 3)
        borderSizer.Add(borderCtrl, 0, wx.LEFT, 5)
        timeoutSizer = wx.BoxSizer(wx.HORIZONTAL)
        timeoutSizer.Add(timeoutLbl_1, 0, wx.TOP, 3)
        timeoutSizer.Add(timeoutCtrl, 0, wx.LEFT | wx.RIGHT, 5)
        timeoutSizer.Add(timeoutLbl_2, 0, wx.TOP, 3)
        box1 = wx.StaticBox(panel, -1, text.other)
        otherSizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
        otherSizer.Add(borderSizer, 0, wx.TOP, 0)
        otherSizer.Add(timeoutSizer, 0, wx.TOP, 4)
        posAndSizeSizer = wx.FlexGridSizer(6, 2, hgap=20, vgap=1)
        posAndSizeSizer.Add(displayLbl, 0, wx.TOP, 0)
        posAndSizeSizer.Add((1, 1), 0, wx.TOP, 0)
        posAndSizeSizer.Add(displayChoice, 0, wx.TOP, 0)
        posAndSizeSizer.Add(centerCtrl, 0, wx.TOP, 3)
        posAndSizeSizer.Add(xCoordLbl, 0, wx.TOP, 5)
        posAndSizeSizer.Add(yCoordLbl, 0, wx.TOP, 5)
        posAndSizeSizer.Add(xCoordCtrl, 0, wx.TOP, 0)
        posAndSizeSizer.Add(yCoordCtrl, 0, wx.TOP, 0)
        posAndSizeSizer.Add(widthLbl, 0, wx.TOP, 5)
        posAndSizeSizer.Add(heightLbl, 0, wx.TOP, 5)
        posAndSizeSizer.Add(widthCtrl, 0, wx.TOP, 0)
        posAndSizeSizer.Add(heightCtrl, 0, wx.TOP, 0)
        box4 = wx.StaticBox(panel, -1, text.posAndSize)
        boxSizer4 = wx.StaticBoxSizer(box4, wx.HORIZONTAL)
        boxSizer4.Add(posAndSizeSizer, 0, wx.EXPAND)
        
        box3 = wx.StaticBox(panel, -1, text.fitModeLabel)
        fitSizer = wx.StaticBoxSizer(box3, wx.VERTICAL)
        fitSizer.Add(fitCtrl)
        fitSizer.Add(stretchCtrl, 0, wx.TOP, 7)
        fitSizer.Add(rb0, 0, wx.TOP, 7)
        fitSizer.Add(rb1, 0, wx.TOP, 7)
        fitSizer.Add(rb2, 0, wx.TOP, 7)
        fitSizer.Add(rb3, 0, wx.TOP, 7)
        resampleSizer = wx.BoxSizer(wx.HORIZONTAL)
        resampleSizer.Add(resampleLbl, 0, wx.TOP, 3)
        resampleSizer.Add(resampleCtrl, 0, wx.LEFT, 25)
        fitSizer.Add(resampleSizer, 0, wx.TOP, 4)
        
        box2 = wx.StaticBox(panel, -1, text.bckgrnd)
        bckgrndSizer = wx.StaticBoxSizer(box2, wx.VERTICAL)
        colourSizer = wx.BoxSizer(wx.HORIZONTAL)
        colourSizer.Add(bckgrndLbl, 0, wx.TOP, 3)
        colourSizer.Add(backColourButton, 0, wx.LEFT, 20)
        bckgrndSizer.Add(colourSizer, 0, wx.BOTTOM, 5)
        bckgrndSizer.Add(shapedCtrl, 0)
        
        box5 = wx.StaticBox(panel, -1, text.topFocus)
        topFocusSizer = wx.StaticBoxSizer(box5, wx.VERTICAL)
        topFocusSizer.Add(onTopCtrl, 0, wx.BOTTOM, 4)
        topFocusSizer.Add(noFocusCtrl, 0)
        
        leftSizer = wx.BoxSizer(wx.VERTICAL)
        leftSizer.Add(radioBoxWinSizes, 0, wx.EXPAND)
        leftSizer.Add(fitSizer, 0, wx.TOP | wx.EXPAND, 7)
        
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightSizer.Add(boxSizer4, 0, wx.EXPAND)
        rightSizer.Add(bckgrndSizer, 0, wx.TOP | wx.EXPAND, 6)
        rightSizer.Add(topFocusSizer, 0, wx.TOP | wx.EXPAND, 6)
        
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(leftSizer, 1, wx.EXPAND)
        mainSizer.Add(rightSizer, 1, wx.EXPAND | wx.LEFT, 5)
        panel.sizer.Add(mainSizer, 1, wx.EXPAND)
        panel.sizer.Add(otherSizer, 0, wx.EXPAND | wx.TOP, 10)
        panel.sizer.Add(pathLbl, 0, wx.TOP, 10)
        panel.sizer.Add(filepathCtrl, 0, wx.EXPAND | wx.TOP, 1)
        panel.sizer.Add(titleLbl, 0, wx.TOP, 10)
        panel.sizer.Add(titleCtrl, 0, wx.EXPAND | wx.TOP, 1)
        
        while panel.Affirmed():
            i = 0
            for rb in (rb0, rb1, rb2, rb3):
                if rb.GetValue():
                    break
                i += 1
            panel.SetResult(
                filepathCtrl.GetValue(),
                radioBoxWinSizes.GetSelection(),
                i,
                fitCtrl.GetValue(),
                stretchCtrl.GetValue(),
                resampleCtrl.GetSelection(),
                onTopCtrl.GetValue(),
                borderCtrl.GetSelection(),
                timeoutCtrl.GetValue(),
                displayChoice.GetValue(),
                xCoordCtrl.GetValue(),
                yCoordCtrl.GetValue(),
                widthCtrl.GetValue(),
                heightCtrl.GetValue(),
                backColourButton.GetValue(),
                shapedCtrl.GetValue(),
                centerCtrl.GetValue(),
                noFocusCtrl.GetValue(),
                titleCtrl.GetValue(),
            )


class HideImage(eg.ActionBase):
    name = "Hide Image"
    description = 'Hides an image displayed with "Display Image".'
    
    
    class text:
        title = "Name of image:"
    
    
    def __call__(self, title=""):
        if title:
            self.plugin.HideImage(title)
    
    def Configure(self, title=""):
        panel = eg.ConfigPanel(self)
        titleLbl = wx.StaticText(panel, -1, self.text.title)
        titleCtrl = wx.TextCtrl(panel, -1, title)
        panel.sizer.Add(titleLbl, 0, wx.TOP, 20)
        panel.sizer.Add(titleCtrl, 0, wx.TOP, 1)
        
        while panel.Affirmed():
            panel.SetResult(titleCtrl.GetValue())


class ShowPicture(eg.ActionBase):
    name = "Show Picture"
    description = "Shows a picture on the screen."
    iconFile = "icons/ShowPicture"
    
    
    class text:
        path = "Path to picture (use an empty path to clear):"
        display = "Monitor"
        allImageFiles = 'All Image Files'
        allFiles = "All files"
    
    
    def __call__(self, imageFile='', display=0):
        imageFile = eg.ParseString(imageFile)
        if imageFile:
            self.pictureFrame.SetPicture(imageFile, display)
            wx.CallAfter(self.pictureFrame.OnShowMe)
        else:
            self.pictureFrame.Show(False)
    
    def Configure(self, imageFile='', display=0):
        panel = eg.ConfigPanel()
        text = self.text
        filepathCtrl = eg.FileBrowseButton(
            panel,
            size=(340, -1),
            initialValue=imageFile,
            labelText="",
            fileMask='%s|*.jpg;*.bmp;*.gif;*.png|%s (*.*)|*.*' % (
                text.allImageFiles,
                text.allFiles
            ),
            buttonText=eg.text.General.browse,
        )
        displayChoice = eg.DisplayChoice(panel, display)
        
        panel.AddLabel(text.path)
        panel.AddCtrl(filepathCtrl)
        panel.AddLabel(text.display)
        panel.AddCtrl(displayChoice)
        
        while panel.Affirmed():
            panel.SetResult(filepathCtrl.GetValue(), displayChoice.GetValue())


class ShowQRcode(eg.ActionBase):
    name = "Show QR Code"
    description = "Shows a QR code on the screen."
    iconFile = "icons/QRcode"
    
    
    class text:
        data = "Data:"
        display = "Monitor:"
        Error = 'Exception in action "%s": Failed to show data "%%s" !'
        timeout1 = "The QR code automatically disappears after"
        timeout2 = "seconds (0 = feature disabled)"
        main = "Mandatory parameters"
        other = "Options"
        box = "Box size [px]:"
        border = "Border width [box]:"
        title = "Name of image:"
        sizeMode = "Fullscreen:"
        titleTool = (
            "Required only if you want to close the image window "
            "programmatically\nUse the action: Hide image"
        )
    
    
    def __call__(
        self,
        data='',
        display=0,
        timeout=0,
        box=12,
        border=4,
        title='QRcode',
        sizeMode=0
    ):
        data = eg.ParseString(data)
        title = eg.ParseString(title)
        
        def parseArgument(arg):
            if not arg:
                return 0
            if isinstance(arg, int):
                return arg
            else:
                from locale import localeconv
                
                
                decimal_point = localeconv()['decimal_point']
                arg = eg.ParseString(arg).replace(decimal_point, ".")
                return int(float(arg))
        
        timeout = parseArgument(timeout)
        box = parseArgument(box)
        border = parseArgument(border)
        
        if data:
            qr = QRCode(
                version=None,
                border=border,
                error_correction=QRconstants.ERROR_CORRECT_M,
                box_size=box,
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image()
            buff = StringIO()
            img.save(buff)
            b64 = b64encode(buff.getvalue())
            if title in self.plugin.images:
                self.plugin.HideImage(title)
            wx.CallAfter(
                ShapedFrame,
                self.text.Error % (self.name),
                b64,
                (0, 3)[int(sizeMode)],
                1,
                False,
                False,
                0,
                True,
                1,
                timeout,
                display,
                0,
                0,
                640,
                360,
                (0, 0, 0),
                True,
                True,
                True,
                title if title else 'QRcode',
                self.plugin,
                data
            )
    
    def Configure(
        self,
        data='',
        display=0,
        timeout=0,
        box=12,
        border=4,
        title='QRcode',
        sizeMode=0
    ):
        panel = eg.ConfigPanel()
        text = self.text
        dataCtrl = wx.TextCtrl(panel, -1, data)
        displayChoice = eg.DisplayChoice(panel, display)
        timeoutLbl_1 = wx.StaticText(panel, -1, text.timeout1)
        timeoutLbl_2 = wx.StaticText(panel, -1, text.timeout2)
        timeoutCtrl = eg.SmartSpinIntCtrl(panel, -1, timeout, textWidth=105)
        boxLbl = wx.StaticText(panel, -1, text.box)
        borderLbl = wx.StaticText(panel, -1, text.border)
        titleLbl = wx.StaticText(panel, -1, text.title)
        boxCtrl = eg.SmartSpinIntCtrl(
            panel,
            -1,
            box,
            min=5,
            max=50,
            textWidth=105
        )
        borderCtrl = eg.SmartSpinIntCtrl(
            panel,
            -1,
            border,
            min=1,
            max=20,
            textWidth=105
        )
        titleCtrl = wx.TextCtrl(panel, -1, title)
        titleLbl.SetToolTipString(self.text.titleTool)
        titleCtrl.SetToolTipString(self.text.titleTool)
        sizeModeLbl = wx.StaticText(panel, -1, self.text.sizeMode)
        sizeModeCtrl = wx.CheckBox(panel, -1, "")
        sizeModeCtrl.SetValue(sizeMode)
        box0 = wx.StaticBox(panel, -1, text.main)
        box1 = wx.StaticBox(panel, -1, text.other)
        inTopSizer = wx.FlexGridSizer(1, 2, 5, 5)
        inTopSizer.Add(wx.StaticText(panel, -1, text.data), 0, ACV)
        inTopSizer.Add(dataCtrl, 0, wx.EXPAND)
        inTopSizer.AddGrowableCol(1)
        topSizer = wx.StaticBoxSizer(box0, wx.VERTICAL)
        topSizer.Add(inTopSizer, 0, wx.EXPAND)
        
        inOtherSizer = wx.FlexGridSizer(5, 2, 5, 5)
        inOtherSizer.AddGrowableCol(1)
        inOtherSizer.Add(wx.StaticText(panel, -1, text.display), 0, ACV)
        inOtherSizer.Add(displayChoice)
        inOtherSizer.Add(sizeModeLbl, 0, ACV)
        inOtherSizer.Add(sizeModeCtrl, 0, wx.EXPAND)
        inOtherSizer.Add(boxLbl, 0, ACV)
        inOtherSizer.Add(boxCtrl, 0, wx.EXPAND)
        inOtherSizer.Add(borderLbl, 0, ACV)
        inOtherSizer.Add(borderCtrl, 0, wx.EXPAND)
        inOtherSizer.Add(titleLbl, 0, ACV)
        inOtherSizer.Add(titleCtrl, 0, wx.EXPAND)
        timeoutSizer = wx.BoxSizer(wx.HORIZONTAL)
        timeoutSizer.Add(timeoutLbl_1, 0, ACV)
        timeoutSizer.Add(timeoutCtrl, 0, wx.LEFT | wx.RIGHT, 5)
        timeoutSizer.Add(timeoutLbl_2, 0, ACV)
        otherSizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
        otherSizer.Add(inOtherSizer, 0, wx.EXPAND)
        otherSizer.Add(timeoutSizer, 0, wx.TOP, 5)
        
        panel.sizer.Add(topSizer, 0, wx.EXPAND)
        panel.sizer.Add(otherSizer, 0, wx.EXPAND | wx.TOP, 5)
        
        while panel.Affirmed():
            panel.SetResult(
                dataCtrl.GetValue(),
                displayChoice.GetValue(),
                timeoutCtrl.GetValue(),
                boxCtrl.GetValue(),
                borderCtrl.GetValue(),
                titleCtrl.GetValue(),
                sizeModeCtrl.GetValue()
            )


def _CreateShowPictureFrame():
    ShowPicture.pictureFrame = ShowPictureFrame()


wx.CallAfter(_CreateShowPictureFrame)


def piltoimage(pil, hasAlpha):
    """
    Convert PIL Image to wx.Image.
    """
    image = wx.EmptyImage(*pil.size)
    rgbPil = pil.convert('RGB')
    if hasAlpha:
        image.SetData(rgbPil.tobytes())
        image.SetAlphaData(pil.convert("RGBA").tobytes()[3::4])
    else:
        new_image = rgbPil
        data = new_image.tobytes()
        image.SetData(data)
    return image


def Resize(w, h, width_, height_, force=False):
    if force or (w > width_) or (h > height_):
        xfactor = (w * 1.0 / width_)
        yfactor = (h * 1.0 / height_)
        if xfactor > yfactor:
            w = width_
            h = int(round(h / xfactor))
        else:
            w = int(round(w / yfactor))
            h = height_
    return (w, h)

