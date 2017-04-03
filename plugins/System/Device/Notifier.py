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

# ____Changes By K                            2/21/2017 21:07 -7
# Added support for more device types         2/21/2017 21:07 -7
# Added support for device metrics in payload 2/21/2017 21:07 -7
# Added support for device names in the event 2/21/2017 21:07 -7

import eg
import win32com.client
import threading
import pythoncom
from types import ClassType
from eg.WinApi.Dynamic import (
    DBT_DEVICEARRIVAL,
    DBT_DEVICEREMOVECOMPLETE,
    DBT_DEVTYP_DEVICEINTERFACE,
    DBT_DEVTYP_VOLUME,
    DEV_BROADCAST_DEVICEINTERFACE as _DEV_BROADCAST_DEVICEINTERFACE,
    DEV_BROADCAST_HDR,
    DEV_BROADCAST_VOLUME,
    pointer,
    RegisterDeviceNotification,
    sizeof,
    UnregisterDeviceNotification,
    WM_DEVICECHANGE,
    wstring_at,
    byref,
    oledll,
    c_wchar_p,
    windll
)


DEVICE_NOTIFY_ALL_INTERFACE_CLASSES = 0x00000004
# XP and later
BUS1394_CLASS_GUID = '{6BDD1FC1-810F-11D0-BEC7-08002BE2092F}'
KSCATEGORY_AUDIO = '{6994AD04-93EF-11D0-A3CC-00A0C9223196}'
KSCATEGORY_BDA_NETWORK_EPG = '{71985F49-1CA1-11D3-9CC8-00C04F7971E0}'
KSCATEGORY_BDA_NETWORK_TUNER = '{71985F48-1CA1-11D3-9CC8-00C04F7971E0}'
KSCATEGORY_TVTUNER = '{A799A800-A46D-11D0-A18C-00A02401DCD4}'
GUID_61883_CLASS = '{7EBEFBC0-3200-11D2-B4C2-00A0C9697D07}'
GUID_DEVICE_BATTERY = '{72631E54-78A4-11D0-BCF7-00AA00B7B32A}'
GUID_BTHPORT_DEVICE_INTERFACE = '{0850302A-B344-4FDA-9BE9-90576B8D46F0}'
GUID_DEVINTERFACE_WPD = '{6AC27878-A6FA-4155-BA85-F98F491D4F33}'
GUID_DEVINTERFACE_USB_HUB = '{F18A0E88-C30C-11D0-8815-00A0C906BED8}'
GUID_DEVINTERFACE_USB_DEVICE = '{A5DCBF10-6530-11D2-901F-00C04FB951ED}'
GUID_DEVINTERFACE_PARCLASS = '{811FC6A5-F728-11D0-A537-0000F8753ED1}'
GUID_DEVINTERFACE_PARALLEL = '{97F76EF0-F883-11D0-AF1F-0000F800845C}'
GUID_DEVINTERFACE_COMPORT = '{86E0D1E0-8089-11D0-9CE4-08003E301F73}'
GUID_DEVINTERFACE_MODEM = '{2C7089AA-2E0E-11D1-B114-00C04FC2AAE4}'
GUID_DEVINTERFACE_MOUSE = '{378DE44C-56EF-11D1-BC8C-00A0C91405DD}'
GUID_DEVINTERFACE_KEYBOARD = '{884B96C3-56EF-11D1-BC8C-00A0C91405DD}'
GUID_DEVINTERFACE_HID = '{4D1E55B2-F16F-11CF-88CB-001111000030}'
GUID_DEVINTERFACE_MONITOR = '{E6F07B5F-EE97-4A90-B076-33F57BF4EAA7}'
GUID_DEVINTERFACE_IMAGE = '{6BDD1FC6-810F-11D0-BEC7-08002BE2092F}'
GUID_DEVINTERFACE_DISPLAY_ADAPTER = '{5B45201D-F2F2-4F3B-85BB-30FF1F953599}'
GUID_DEVINTERFACE_CDROM = '{53F56308-B6BF-11D0-94F2-00A0C91EFB8B}'
GUID_DEVINTERFACE_DISK = '{53F56307-B6BF-11D0-94F2-00A0C91EFB8B}'
GUID_DEVINTERFACE_FLOPPY = '{53F56311-B6BF-11D0-94F2-00A0C91EFB8B}'
GUID_DEVINTERFACE_STORAGEPORT = '{2ACCFE60-C130-11D2-B082-00A0C91EFB8B}'
GUID_DEVINTERFACE_TAPE = '{53F5630B-B6BF-11D0-94F2-00A0C91EFB8B}'
GUID_DEVCLASS_IRDA = '{6BDD1fC5-810F-11D0-BEC7-08002BE2092F}'
GUID_DEVCLASS_SYSTEM = ' {4D36E97D-E325-11CE-BFC1-08002BE10318}'
GUID_DEVCLASS_PRINTERS = '{4D36E979-E325-11CE-BFC1-08002BE10318}'
GUID_DEVCLASS_PCMCIA = '{4D36E977-E325-11CE-BFC1-08002BE10318}'

KSCATEGORY_CAPTURE = '{65E8773D-8F56-11D0-A3B9-00A0C9223196}'
KSCATEGORY_VIDEO = '{6994AD05-93EF-11D0-A3CC-00A0C9223196}'
KSCATEGORY_STILL = '{FB6C428A-0353-11D1-905F-0000C0CC16BA}'
GUID_DEVINTERFACE_WRITEONCEDISK = (# Blank CD/DVD insertion
    '{53F5630C-B6BF-11D0-94F2-00A0C91EFB8B}'
)
GUID_DEVINTERFACE_USB_HOST_CONTROLLER = (
    '{3ABF6F2D-71C4-462A-8A92-1E6861E6AF27}'
)
GUID_DEVINTERFACE_SERENUM_BUS_ENUMERATOR = (# S Dev
    '{4D36E978-E325-11CE-BFC1-08002BE10318}'
)

MOUNTDEV_MOUNTED_DEVICE_GUID = '{53F5630D-B6BF-11D0-94F2-00A0C91EFB8B}'
# Vista and later

GUID_DEVINTERFACE_NET1 = '{CAC88484-7515-4C03-82E6-71A87ABAC361}'
GUID_DEVINTERFACE_NET2 = '{AD498944-762F-11D0-8DCB-00C04FC3358C}'
GUID_DEVINTERFACE_I2C = '{2564AA4F-DDDB-4495-B497-6AD4A84163D7}'
GUID_DEVINTERFACE_PHYSICALMEDIA = '{F33FDC04-D1AC-4E8E-9A30-19BBD4B108AE}'

GUID_DEVINTERFACE_NET = (
    GUID_DEVINTERFACE_NET1,
    GUID_DEVINTERFACE_NET2
)

DEVICES = {
    GUID_DEVINTERFACE_KEYBOARD           : (
        dict(
            cls_name='Keyboard',
            attr_names=(),
            action_search='Description',
            display_name='Keyboard'
        ),
    ),
    GUID_DEVICE_BATTERY                  : (
        dict(
            cls_name='Battery',
            attr_names=(
                'BatteryRechargeTime',
                'EstimatedChargeRemaining',
                'ExpectedBatteryLife',
                'FullChargeCapacity',
                'MaxRechargeTime'
            ),
            action_search='Caption',
            display_name='Battery'
        ),
        dict(
            cls_name='PortableBattery',
            attr_names=(
                'DesignVoltage',
                'DesignCapacity',
                'ExpectedBatteryLife',
                'EstimatedRunTime',
                'ExpectedLife',
                'Manufacturer',
                'ManufactureDate',
                'TimeOnBattery',
                'MaxRechargeTime'
            ),
            action_search='Caption',
            display_name='Portable Battery'
        ),
    ),
    GUID_DEVINTERFACE_CDROM              : (
        dict(
            cls_name='CDROMDrive',
            attr_names=(
                'CompressionMethod',
                'Drive',
                'Manufacturer',
                'MaxMediaSize',
                'MediaLoaded',
                'MediaType'
            ),
            action_search='Caption',
            display_name='CD-ROM Drive'
        ),
    ),
    GUID_DEVINTERFACE_MONITOR            : (
        dict(
            cls_name='DesktopMonitor',
            attr_names=(
                'DisplayType',
                'MonitorManufacturer',
                'MonitorType',
                'ScreenWidth',
                'ScreenHeight'
            ),
            action_search='Caption',
            display_name='Desktop Monitor'
        ),
    ),
    GUID_DEVINTERFACE_DISK               : (
        dict(
            cls_name='DiskDrive',
            attr_names=(
                'Model',
                'Manufacturer',
                'InterfaceType',
                'Partitions',
                'MediaLoaded',
                'MediaType',
                'Size'
            ),
            action_search='Caption',
            display_name='Disk Drive'
        ),
        dict(
            cls_name='IDEController',
            attr_names=(),
            action_search='Caption',
            display_name='IDE Controller'
        ),
        dict(
            cls_name='SCSIController',
            attr_names=('Manufacturer',),
            action_search='Caption',
            display_name='SCSI Controller'
        ),
    ),
    GUID_DEVINTERFACE_USB_HOST_CONTROLLER: (
        dict(
            cls_name='USBController',
            attr_names=('Manufacturer',),
            action_search='Caption',
            display_name='USB Controller'
        ),
    ),
    GUID_DEVINTERFACE_USB_HUB            : (
        dict(
            cls_name='USBHub',
            attr_names=('USBVersion',),
            action_search='Caption',
            display_name='USB Hub'
        ),
    ),
    GUID_DEVINTERFACE_DISPLAY_ADAPTER    : (
        dict(
            cls_name='VideoController',
            attr_names=(
                'VideoProcessor',
                'AdapterRAM',
                'CurrentHorizontalResolution',
                'CurrentVerticalResolution'
            ),
            action_search='Caption',
            display_name='Video Controller'
        ),
    ),
    GUID_DEVINTERFACE_TAPE               : (
        dict(
            cls_name='TapeDrive',
            attr_names=(
                'Manufacturer',
                'MediaType',
                'MaxMediaSize'
            ),
            action_search='Caption',
            display_name='Tape Drive'
        ),
    ),
    KSCATEGORY_AUDIO                     : (
        dict(
            cls_name='SoundDevice',
            attr_names=('Manufacturer', 'ProductName'),
            action_search='Caption',
            display_name='Sound Device'
        ),
    ),
    GUID_DEVINTERFACE_COMPORT            : (
        dict(
            cls_name='SerialPort',
            attr_names=(),
            action_search='Caption',
            display_name='Serial Port'
        ),
    ),
    GUID_DEVINTERFACE_MOUSE              : (
        dict(
            cls_name='PointingDevice',
            attr_names=(
                'Manufacturer',
                'NumberOfButtons',
                'Resolution',
                'SampleRate',
                'HardwareType'
            ),
            action_search='Caption',
            display_name='Pointing Device'
        ),
    ),
    GUID_DEVINTERFACE_MODEM              : (
        dict(
            cls_name='POTSModem',
            attr_names=(),
            action_search='Caption',
            display_name='POTS Modem'
        ),
    ),
    GUID_DEVINTERFACE_PARALLEL           : (
        dict(
            cls_name='ParallelPort',
            attr_names=(),
            action_search='Caption',
            display_name='Parallel Port'
        ),
    ),
    BUS1394_CLASS_GUID                   : (
        dict(
            cls_name='1394Controller',
            attr_names=(),
            action_search='Caption',
            display_name='1394 Controller'
        ),
    ),
    GUID_61883_CLASS                     : (
        dict(
            cls_name='1394ControllerDevice',
            attr_names=(),
            action_search='Caption',
            display_name='1394 Controller Device'
        ),
    ),
    GUID_DEVCLASS_IRDA                   : (
        dict(
            cls_name='InfraredDevice',
            attr_names=(),
            action_search='Caption',
            display_name='Infrared Device'
        ),
    ),
    GUID_DEVCLASS_SYSTEM                 : (
        dict(
            cls_name='MotherboardDevice',
            attr_names=(),
            action_search='Name',
            display_name='Motherboard Device'
        ),
        dict(
            cls_name='CacheMemory',
            attr_names=(),
            action_search='DeviceID',
            display_name='Cache Memory'
        ),
        dict(
            cls_name='Fan',
            attr_names=(),
            action_search='Caption',
            display_name='Fan'
        ),
        dict(
            cls_name='HeatPipe',
            attr_names=(),
            action_search='Caption',
            display_name='Heat Pipe'
        ),
        dict(
            cls_name='OnBoardDevice',
            attr_names=(),
            action_search='Caption',
            display_name='OnBoard Device'
        ),
        dict(
            cls_name='PhysicalMemory',
            attr_names=(),
            action_search='Tag',
            display_name='Physical Memory'
        ),
        dict(
            cls_name='Refrigeration',
            attr_names=(),
            action_search='Caption',
            display_name='Refrigeration'
        ),
        dict(
            cls_name='SystemSlot',
            attr_names=(),
            action_search='SlotDesignation',
            display_name='System Slot'
        ),
        dict(
            cls_name='TemperatureProbe',
            attr_names=(),
            action_search='Caption',
            display_name='Temperature Probe'
        ),
        dict(
            cls_name='VoltageProbe',
            attr_names=(),
            action_search='Caption',
            display_name='Voltage Probe'
        ),
        dict(
            cls_name='Processor',
            attr_names=(),
            action_search='Name',
            display_name='Processor'
        )
    ),
    GUID_DEVCLASS_PCMCIA                 : (
        dict(
            cls_name='PCMCIAController',
            attr_names=(),
            action_search='Caption',
            display_name='PCMCIA Controller'
        ),
    ),
    GUID_DEVCLASS_PRINTERS               : (
        dict(
            cls_name='Printer',
            attr_names=(),
            action_search='Caption',
            display_name='Printer'
        ),
        dict(
            cls_name='TCPIPPrinterPort',
            attr_names=(),
            action_search='Caption',
            display_name='TCPIP PrinterPort'
        ),
        dict(
            cls_name='PrinterController',
            attr_names=(),
            action_search='Caption',
            display_name='Printer Controller'
        )
    ),
    KSCATEGORY_BDA_NETWORK_EPG           : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='EPG'
        ),
    ),
    KSCATEGORY_BDA_NETWORK_TUNER         : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='Network Tuner'
        ),
    ),
    KSCATEGORY_TVTUNER                   : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='TV Tuner'
        ),
    ),
    GUID_BTHPORT_DEVICE_INTERFACE        : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='BlueTeeth Device'
        ),
    ),
    GUID_DEVINTERFACE_WPD                : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='Portable'
        ),
    ),
    GUID_DEVINTERFACE_USB_DEVICE         : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='USB Device'
        ),
    ),
    GUID_DEVINTERFACE_HID                : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='HID Device'
        ),
    ),
    GUID_DEVINTERFACE_IMAGE              : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='Imaging Device'
        ),
    ),
    KSCATEGORY_CAPTURE                   : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='Video Capture'
        ),
    ),
    KSCATEGORY_VIDEO                     : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='Video Device'
        ),
    ),
    KSCATEGORY_STILL                     : (
        dict(
            cls_name='PNPEntity',
            attr_names=('Caption', 'Description', 'Manufacturer'),
            action_search='Description',
            display_name='Still Capture'
        ),
    ),
}

NOEVENT = (
    MOUNTDEV_MOUNTED_DEVICE_GUID,
    GUID_DEVINTERFACE_PHYSICALMEDIA
)

SETUP_CLASS_GUIDS = {
    '{72631E54-78A4-11D0-BCF7-00AA00B7B32A}': 'Battery',
    '{53D29EF7-377C-4D14-864B-EB3A85769359}': 'BiometricDevice',
    '{E0CBF06C-CD8B-4647-BB8A-263B43F0F974}': 'BluetoothDevice',
    '{4D36E965-E325-11CE-BFC1-08002BE10318}': 'CDROMDrive',
    '{4D36E967-E325-11CE-BFC1-08002BE10318}': 'DiskDrive',
    '{4D36E968-E325-11CE-BFC1-08002BE10318}': 'DisplayAdapter',
    '{4D36E969-E325-11CE-BFC1-08002BE10318}': 'FloppyDiskController',
    '{4D36E980-E325-11CE-BFC1-08002BE10318}': 'FloppyDiskDrive',
    '{6BDD1FC3-810F-11D0-BEC7-08002BE2092F}': 'GlobalPositioningDevice',
    '{4D36E96A-E325-11CE-BFC1-08002BE10318}': 'HardDriveController',
    '{745A17A0-74D3-11D0-B6FE-00A0C90F57DA}': 'HIDDevice',
    '{48721B56-6795-11D2-B1A8-0080C72E74A2}': '1284.4Device',
    '{49CE6AC8-6F86-11D2-B1E5-0080C72E74A2}': '1284.4PrintFunction',
    '{7EBEFBC0-3200-11D2-B4C2-00A0C9697D07}': '1394-61883Device',
    '{C06FF265-AE09-48F0-812C-16753D7CBA83}': '1394-AVCDevice',
    '{D48179BE-EC20-11D1-B6B8-00C04FA372A7}': '1394-SBP2Device',
    '{6BDD1FC1-810F-11D0-BEC7-08002BE2092F}': '1394Controller',
    '{6BDD1FC6-810F-11D0-BEC7-08002BE2092F}': 'ImagingDevice',
    '{6BDD1FC5-810F-11D0-BEC7-08002BE2092F}': 'IrDADevice',
    '{4D36E96B-E325-11CE-BFC1-08002BE10318}': 'Keyboard',
    '{CE5939AE-EBDE-11D0-B181-0000F8753EC4}': 'MediaChanger',
    '{4D36E970-E325-11CE-BFC1-08002BE10318}': 'MemoryTechnology',
    '{4D36E96D-E325-11CE-BFC1-08002BE10318}': 'Modem',
    '{4D36E96E-E325-11CE-BFC1-08002BE10318}': 'Monitor',
    '{4D36E96F-E325-11CE-BFC1-08002BE10318}': 'Mouse',
    '{4D36E971-E325-11CE-BFC1-08002BE10318}': 'Multifunction',
    '{4D36E96C-E325-11CE-BFC1-08002BE10318}': 'Multimedia',
    '{50906CB8-BA12-11D1-BF5D-0000F805F530}': 'MultiportSerialAdapter',
    '{4D36E972-E325-11CE-BFC1-08002BE10318}': 'NetworkAdapter',
    '{4D36E973-E325-11CE-BFC1-08002BE10318}': 'NetworkClient',
    '{4D36E974-E325-11CE-BFC1-08002BE10318}': 'NetworkService',
    '{4D36E975-E325-11CE-BFC1-08002BE10318}': 'NetworkTransport',
    '{268C95A1-EDFE-11D3-95C3-0010DC4050A5}': 'SSLSecurityAccelerator',
    '{4D36E977-E325-11CE-BFC1-08002BE10318}': 'PCMCIA',
    '{4D36E978-E325-11CE-BFC1-08002BE10318}': 'Ports',
    '{4D36E979-E325-11CE-BFC1-08002BE10318}': 'Printer',
    '{4658EE7E-F050-11D1-B6BD-00C04FA372A7}': 'PNPPrinters',
    '{50127DC3-0F36-415E-A6CC-4CB3BE910B65}': 'Processor',
    '{4D36E97B-E325-11CE-BFC1-08002BE10318}': 'SCSIAdapter',
    '{5175D334-C371-4806-B3BA-71FD53C9258D}': 'Sensor',
    '{50DD5230-BA8A-11D1-BF5D-0000F805F530}': 'SmartCardReader',
    '{71A27CDD-812A-11D0-BEC7-08002BE2092F}': 'StorageVolume',
    '{4D36E97D-E325-11CE-BFC1-08002BE10318}': 'SystemDevice',
    '{6D807884-7D21-11CF-801C-08002BE10318}': 'TapeDrive',
    '{88BAE032-5A81-49F0-BC3D-A4FF138216D6}': 'USBDevice',
    '{25DBCE51-6C8F-4A72-8A6D-B54C2B4FC835}': 'CEUSBActiveSync',
    '{EEC5AD98-8080-425F-922A-DABF3DE3F69A}': 'Portable',
    '{997B5D8D-C442-4F2E-BAF3-9C8E671E9E21}': 'SideShow'
}

SEARCH = [
    GUID_DEVINTERFACE_KEYBOARD,
    GUID_DEVICE_BATTERY,
    GUID_DEVINTERFACE_CDROM,
    GUID_DEVINTERFACE_MONITOR,
    GUID_DEVINTERFACE_DISK,
    GUID_DEVINTERFACE_USB_HOST_CONTROLLER,
    GUID_DEVINTERFACE_USB_HUB,
    GUID_DEVINTERFACE_DISPLAY_ADAPTER,
    GUID_DEVINTERFACE_TAPE,
    KSCATEGORY_AUDIO,
    GUID_DEVINTERFACE_COMPORT,
    GUID_DEVINTERFACE_MOUSE,
    GUID_DEVINTERFACE_MODEM,
    GUID_DEVINTERFACE_PARALLEL,
    BUS1394_CLASS_GUID,
    GUID_61883_CLASS,
    GUID_DEVCLASS_IRDA,
    GUID_DEVCLASS_SYSTEM,
    GUID_DEVCLASS_PCMCIA,
    GUID_DEVCLASS_PRINTERS,
    GUID_DEVINTERFACE_USB_DEVICE,
]

if not eg.WindowsVersion.IsXP():
    DEVICES[GUID_DEVINTERFACE_DISK][0]['attr_names'] += (
        'FirmwareRevision',
    )
    DEVICES[GUID_DEVINTERFACE_I2C] = (
        dict(
            cls_name='PNPEntity',
            attr_names=(),
            action_search='Caption',
            display_name='I2C Device'
        ),
    )
    DEVICES[GUID_DEVINTERFACE_NET1] = (
        dict(
            cls_name='NetworkAdapter',
            attr_names=(
                'AdapterType',
                'MACAddress',
                'Manufacturer',
                'MaxSpeed',
                'NetworkAddresses'
            ),
            action_search='Description',
            display_name='Network Adapter'
        ),
    )
    DEVICES[GUID_DEVINTERFACE_NET2] = DEVICES[GUID_DEVINTERFACE_NET1]
    SEARCH.insert(0, GUID_DEVINTERFACE_NET1)
    SEARCH.insert(0, GUID_DEVINTERFACE_NET2)

if not eg.WindowsVersion.Is10():
    DEVICES[GUID_DEVINTERFACE_FLOPPY] = (
        dict(
            cls_name='FloppyDrive',
            attr_names=(
                'Manufacturer',
            ),
            action_search='Caption',
            display_name='Floppy Drive'
        ),
        dict(
            cls_name='FloppyController',
            attr_names=(),
            action_search='Caption',
            display_name='Floppy Controller'
        )
    )
    
    SEARCH.insert(0, GUID_DEVINTERFACE_FLOPPY)


class DEV_BROADCAST_DEVICEINTERFACE(_DEV_BROADCAST_DEVICEINTERFACE):
    def __init__(self):
        self.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        self.dbcc_size = sizeof(DEV_BROADCAST_DEVICEINTERFACE)


DBD_NAME_OFFSET = DEV_BROADCAST_DEVICEINTERFACE.dbcc_name.offset

ASSOCIATORS = (
    'ASSOCIATORS OF {Win32_%s.DeviceID="%s"}'
    ' WHERE AssocClass=Win32_%s'
)


def _parse_vendor_id(vendor_id):
    vendor_id = vendor_id.replace('\\\\?\\', '').split('#')
    vendor_id = vendor_id[:-1]
    
    if len(vendor_id) >= 3:
        vendor_id = '\\'.join(vendor_id[:3]).upper()
    else:
        vendor_id = '\\'.join(vendor_id[:2]).upper()
    
    return vendor_id


def _get_ids(device):
    res = ()
    
    if hasattr(device, 'PNPDeviceID') and device.PNPDeviceID is not None:
        res = (device.PNPDeviceID,)
    else:
        for attr_name in ('DeviceId', 'DeviceID', 'HardwareId'):
            device_id = getattr(device, attr_name, None)
            if device_id is not None:
                if not isinstance(device_id, tuple):
                    device_id = (device_id,)
                res += device_id
    return res


def _create_key(device_ids):
    return tuple(device_id.upper() for device_id in device_ids)


class DeviceBase(object):
    obj = None
    __name__ = ''
    
    def __getattr__(self, item):
        return getattr(self.obj, item)
    
    def __repr__(self):
        return "<dynamic-device '%s'>" % self.__name__


def _create_event(
    device,
    device_ids,
    current_devices,
    display_name,
    cls_name,
    **kwargs
):
    if hasattr(device, 'DeviceId'):
        devId = device.DeviceId
    elif hasattr(device, 'DeviceID'):
        devId = device.DeviceId
    else:
        devId = ''
    clsName = display_name.replace(' ', '')
    payload = ClassType(
        cls_name,
        (DeviceBase,),
        dict(obj=device, __name__=clsName)
    )()
    
    name = device.Name
    if name.endswith('.'):
        name = name[:-1]
    
    for device_id in device_ids:
        if device_id.startswith('WPDBUSENUMROOT'):
            name = device.Description.strip() + '.' + device.Name[0]
            device_ids += (devId,)
    
    if hasattr(device, 'ClassGuid') and device.ClassGuid in SETUP_CLASS_GUIDS:
        suffix = [SETUP_CLASS_GUIDS[device.ClassGuid], name]
    else:
        suffix = [display_name.replace(' ', ''), name]
    
    key = _create_key(device_ids)
    if not key:
        return False, False
    if key in current_devices:
        return None, None
    
    current_devices[key] = (suffix, payload)
    
    return suffix, payload


class WMI(threading.Thread):
    """
    Subclass of threading.Thread that handles the WMI lookup of devices as well
     as generating events.
    """
    
    def __init__(self, plugin):
        """
        Threading object that runs the WMI device lookup.

        :param plugin: System plugin instance
        :type plugin: instance
        """
        
        threading.Thread.__init__(self, name='WMI Thread')
        self.plugin = plugin
        self.wmi = None
        self.queueEvent = threading.Event()
        self.stopEvent = threading.Event()
        self.queue = []
        self.currentDevices = {}
        self.networkDrives = {}
        self.removableDrives = {}
        self.ramDrives = {}
        self.localDrives = {}
        self.cdromDrives = {}
        self.wmi = None
    
    def _get_drive_type(self, driveType):
        driveTypes = (
            ([], {}, None),
            ([], {}, None),
            (['RemovableDrive'], self.removableDrives, 'DiskDrive'),
            (['Drive'], self.localDrives, 'DiskDrive'),
            (['NetworkDrive'], self.networkDrives, 'MappedLogicalDisk'),
            (['CD-Rom'], self.cdromDrives, 'CDROMDrive'),
            (['RamDrive'], self.ramDrives, 'DiskDrive'),
        )
        return driveTypes[driveType]
    
    @eg.LogIt
    def UnmountDrive(self, letter):
        """
        Called by the internal queue mechanism for generating a drive unmounted
         event.

        :param letter: Drive letter.
        :type letter: str
        :return: None
        :rtype: None
        """
        
        eventTypes = (
            None,
            None,
            'Unplugged',
            'Unmounted',
            'Detached',
            'Ejected',
            'Destroyed'
        )
        
        for i in range(2, 7):
            suffix, storedDrives, _ = self._get_drive_type(i)
            
            if letter + ':' in storedDrives:
                suffix, payload = storedDrives[letter + ':']
                self.plugin.TriggerEvent(
                    '.'.join([eventTypes[i]] + suffix),
                    payload
                )
                del storedDrives[letter + ':']
                return
    
    @eg.LogIt
    def MountDrive(self, letter=None):
        """
        Called by the internal queue mechanism for generating a drive mounted
        event.

        :param letter: Drive letter.
        :type letter: str
        :return: None
        :rtype: None
        """
        
        if letter:
            TriggerEvent = self.plugin.TriggerEvent
            logicalDisks = self.wmi.ExecQuery(
                'Select * from Win32_LogicalDisk WHERE DeviceID="%s"' %
                (letter + ':',)
            )
        
        else:
            def TriggerEvent(*args):
                pass
            
            logicalDisks = self.wmi.ExecQuery(
                "Select * from Win32_LogicalDisk"
            )
        
        for disk in logicalDisks:
            suffix, storedDrives, clsName = (
                self._get_drive_type(disk.DriveType)
            )
            
            if clsName is not None:
                drives = self.wmi.ExecQuery(
                    'Select * from Win32_' + clsName
                )
                
                for drive in drives:
                    deviceId = drive.DeviceID
                    
                    if deviceId in storedDrives:
                        continue
                    
                    payload = ClassType(
                        clsName,
                        (DeviceBase,),
                        dict(obj=drive, __name__=clsName)
                    )()
                    
                    if clsName != 'DiskDrive':
                        if 'CD-Rom' in suffix:
                            if letter and drive.Drive[:-1] != letter:
                                continue
                            if not drive.MediaLoaded:
                                continue
                            
                            suffix += [
                                'Inserted',
                                drive.Caption
                            ]
                        
                        elif 'NetworkDrive' in suffix:
                            if letter and drive.Name[:-1] != letter:
                                continue
                            
                            suffix += [
                                'Attached',
                                drive.ProviderName.replace('\\', '\\\\')
                            ]
                        
                        suffix += [disk.DeviceID[:-1]]
                        storedDrives[disk.DeviceID] = (suffix[1:], payload)
                        TriggerEvent('.'.join(suffix), payload)
                    
                    else:
                        partitionQuery = ASSOCIATORS % (
                            'DiskDrive',
                            deviceId.replace('\\', '\\\\'),
                            'DiskDriveToDiskPartition'
                        )
                        for partition in self.wmi.ExecQuery(partitionQuery):
                            diskQuery = ASSOCIATORS % (
                                'DiskPartition',
                                partition.DeviceID,
                                'LogicalDiskToPartition'
                            )
                            for disk in self.wmi.ExecQuery(diskQuery):
                                if letter and disk.DeviceID[:-1] != letter:
                                    continue
                                
                                suffix += [
                                    'Mounted',
                                    drive.Caption,
                                    disk.DeviceID[:-1]
                                ]
                                
                                storedDrives[disk.DeviceID] = (
                                    suffix[1:],
                                    payload
                                )
                                TriggerEvent('.'.join(suffix), payload)
    
    @eg.LogIt
    def Removed(self, guid, data):
        """
        Called by the internal queue mechanism for generating a device removed
         event.

        :param guid: Guid of the notification.
        :type guid: str
        :param data: Vendor id from the notification.
        :type data: str
        :return: None
        :rtype: None
        """
        
        TriggerEvent = self.plugin.TriggerEvent
        
        if guid in NOEVENT or guid == GUID_DEVINTERFACE_NET2:
            return
        
        cDevices = self._current_devices(guid)
        vendor_id = _parse_vendor_id(data)
        
        for device_ids in cDevices.keys():
            for device_id in device_ids:
                if device_id.find(vendor_id) > -1:
                    suffix, payload = cDevices[device_ids]
                    TriggerEvent(
                        '.'.join(['Device.Removed'] + suffix),
                        payload
                    )
                    
                    del cDevices[device_ids]
                    return
        
        TriggerEvent('Device.Removed', [data])
    
    @eg.LogIt
    def Attached(self, guid, data):
        """
        Called by the internal queue mechanism for generating a device attached
         event.

        :param guid: Guid of the notification.
        :type guid: str
        :param data: Vendor id from the notification.
        :type data: str
        :return: None
        :rtype: None
        """
        
        if guid in NOEVENT:
            return
        
        if guid in GUID_DEVINTERFACE_NET:
            guid = GUID_DEVINTERFACE_NET1
        
        vendor_id = _parse_vendor_id(data)
        current_devices = self._current_devices(guid)
        TriggerEvent = self.plugin.TriggerEvent
        
        def FindId(device):
            device_ids = _get_ids(device)
            for device_id in device_ids:
                if device_id.upper().find(vendor_id) > -1:
                    return device_ids
            return ()
        
        def FindDevices(cls_name, **kwargs):
            
            def ProcessDevices(devc, devc_ids):
                suffix, payload = _create_event(
                    devc,
                    devc_ids,
                    current_devices,
                    cls_name=cls_name,
                    **kwargs
                )
                
                if not suffix:
                    return suffix
                
                TriggerEvent(
                    '.'.join(['Device.Attached'] + suffix),
                    payload
                )
                return True
            
            try:
                query = (
                    "SELECT * from Win32_{0} WHERE PNPDeviceID LIKE '%{1}%'"
                )
                devices = self.wmi.ExecQuery(
                    query.format(cls_name, vendor_id.split('\\')[-1].lower())
                )
                
                if not len(devices):
                    raise ValueError
                
                for device in devices:
                    result = ProcessDevices(device, (device.PNPDeviceID,))
                    if result is False:
                        continue
                return True
            
            except (win32com.client.pythoncom.com_error, ValueError):
                query = "SELECT * from Win32_{0}"
                devices = self.wmi.ExecQuery(
                    query.format(cls_name)
                )
                for device in devices:
                    result = ProcessDevices(device, FindId(device))
                    if result is False:
                        continue
                    return result
            return False
        
        if guid in DEVICES:
            res = FindDevices(**DEVICES[guid][0])
            if res is not False:
                return
        else:
            for guid in SEARCH:
                for dev in DEVICES[guid]:
                    res = FindDevices(**dev)
                    if res is not False:
                        return
        
        TriggerEvent('Device.Attached', [data])
    
    def DriveEvent(self, eventType, letter):
        """
        Puts the Windows notification data into the queue.

        :param eventType: Method name to use for processing the notification.
        :type eventType: str
        :param letter: Drive letter.
        :type letter: str
        :return: None
        :rtype: None
        """
        
        self.queue.append((getattr(self, eventType), (letter,)))
        self.queueEvent.set()
    
    def DeviceEvent(self, eventType, guid, data):
        """
        Puts the Windows notification data into the queue.

        :param eventType: Method name to use for processing the notification.
        :type eventType: str
        :param guid: Guid of the notification.
        :type guid: str
        :param data: Vendor id from the notification.
        :type data: str
        :return: None
        :rtype: None
        """
        
        self.queue.append((getattr(self, eventType), (guid, data)))
        self.queueEvent.set()
    
    def _current_devices(self, guid):
        guid = guid.upper()
        if guid not in self.currentDevices:
            self.currentDevices[guid] = {}
        return self.currentDevices[guid]
    
    def run(self):
        """
        Handles the population of devices when the thread starts. This also
        loops and pulls data from the queue and sends it where it needs to go
         for proper event generation.
        :return: None
        :rtype: None
        """
        pythoncom.CoInitialize()
        self.wmi = wmi = win32com.client.GetObject("winmgmts:\\root\\cimv2")
        
        self.MountDrive()
        
        for guid in DEVICES.keys():
            if guid == GUID_DEVINTERFACE_NET2:
                continue
            
            for dev in DEVICES[guid]:
                devices = wmi.ExecQuery(
                    "Select * from Win32_" + dev['cls_name']
                )
                
                for device in devices:
                    _create_event(
                        device,
                        _get_ids(device),
                        self._current_devices(guid),
                        **dev
                    )
        
        while not self.stopEvent.isSet():
            self.queueEvent.wait()
            if not self.stopEvent.isSet():
                while self.queue:
                    func, data = self.queue.pop(0)
                    func(*data)
                self.queueEvent.clear()
        
        del self.wmi
        self.wmi = None
        pythoncom.CoUninitialize()
    
    def stop(self):
        """
        Stops the thread.
        :return: None
        :rtype: None
        """
        self.stopEvent.set()
        self.queueEvent.set()
        self.join(1.0)


class ChangeNotifier:
    """
    This class receives the Windows notifications and grams any necessary data
    from the message and then passes it to the WMI thread so an event can be
     generated.
    """
    
    def __init__(self, plugin):
        """
        Registers for Windows notifications for Devices/Drives being attached
        or removed.

        :param plugin: System plugin instance.
        :type plugin: instance
        """
        self.plugin = plugin
        self.notifier = None
        self.WMI = WMI(plugin)
        
        eg.messageReceiver.AddHandler(
            WM_DEVICECHANGE,
            self.OnDeviceChange
        )
        
        self.WMI.start()
        wx.CallAfter(self.Register)
    
    def Register(self):
        """
        Registers for the notifications. This gets called via the use of
        wx.CallAfter. This is done because the actual registration seems to be
        much happier when done from the main thread.

        :return: None
        :rtype: None
        """
        self.notifier = RegisterDeviceNotification(
            eg.messageReceiver.hwnd,
            pointer(DEV_BROADCAST_DEVICEINTERFACE()),
            DEVICE_NOTIFY_ALL_INTERFACE_CLASSES
        )
    
    def Close(self):
        """
        Performs the shutdown of the WMI thread. Als unregisters for the
        Windows notifications.

        :return: None
        :rtype: None
        """
        self.WMI.stop()
        UnregisterDeviceNotification(self.notifier)
        
        eg.messageReceiver.RemoveHandler(
            WM_DEVICECHANGE,
            self.OnDeviceChange
        )
    
    def OnDeviceChange(self, hwnd, msg, wparam, lparam):
        """
        Callback method the Windows notification calls when a message needs to
        be delivered.

        :param hwnd: Window handle.
        :type hwnd: long
        :param msg: Message.
        :type msg: long
        :param wparam: Notification type.
        :type wparam: long
        :param lparam: Memory address of notification class.
        :type lparam: long
        :return: None
        :rtype: None
        """
        
        def DriveLettersFromMask(mask):
            return [
                chr(65 + driveNum) for driveNum in range(0, 26)
                if (mask & (2 ** driveNum))
            ]
        
        def IsDeviceInterface():
            dbch = DEV_BROADCAST_HDR.from_address(lparam)
            return dbch.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE
        
        def IsVolume():
            dbch = DEV_BROADCAST_HDR.from_address(lparam)
            return dbch.dbch_devicetype == DBT_DEVTYP_VOLUME
        
        def DeviceEvent(suffix):
            dbcc = DEV_BROADCAST_DEVICEINTERFACE.from_address(lparam)
            
            p = c_wchar_p()
            oledll.ole32.StringFromCLSID(
                byref(dbcc.dbcc_classguid),
                byref(p)
            )
            guid = p.value
            windll.ole32.CoTaskMemFree(p)
            
            self.WMI.DeviceEvent(
                suffix,
                guid,
                wstring_at(lparam + DBD_NAME_OFFSET)
            )
        
        def VolumeEvent(mountType):
            dbcv = DEV_BROADCAST_VOLUME.from_address(lparam)
            letters = DriveLettersFromMask(dbcv.dbcv_unitmask)
            for letter in letters:
                self.WMI.DriveEvent(mountType, letter)
        
        if wparam == DBT_DEVICEARRIVAL:
            if IsDeviceInterface():
                DeviceEvent('Attached')
            elif IsVolume():
                VolumeEvent("MountDrive")
        
        elif wparam == DBT_DEVICEREMOVECOMPLETE:
            if IsDeviceInterface():
                DeviceEvent('Removed')
            elif IsVolume():
                VolumeEvent("UnmountDrive")
        return 1
