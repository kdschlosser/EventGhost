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

import os
from distutils.core import Command
import sys
from subprocess import Popen, PIPE


BASE_PATH = os.path.abspath(os.path.dirname(__file__))

EXTENSIONS_PATH = os.path.join(BASE_PATH, '..', 'extensions')

RAW_INPUT_HOOK_SRC = os.path.join(EXTENSIONS_PATH, 'RawInputHook.dll')
RAW_INPUT_HOOK_DST = 'build\plugins\RawInput'

MCE_IR_SRC = os.path.join(EXTENSIONS_PATH, 'MceIr.dll')
MCE_IR_DST = 'build\plugins\MceRemote'

TASK_HOOK_SRC = os.path.join(EXTENSIONS_PATH, 'TaskHook.dll')
TASK_HOOK_DST = 'build\plugins\Task'

C_FUNCTIONS_SRC = os.path.join(EXTENSIONS_PATH, 'cFunctions')
C_FUNCTIONS_DST = 'pyd_imports'

DX_JOYSTICK_SRC = os.path.join(EXTENSIONS_PATH, '_dxJoystick')
DX_JOYSTICK_DST = 'pyd_imports'

VISTA_VOL_EVENTS_SRC = os.path.join(EXTENSIONS_PATH, 'VistaVolEvents')
VISTA_VOL_EVENTS_DST = 'pyd_imports'

WIN_USB_SRC = os.path.join(EXTENSIONS_PATH, 'WinUsbWrapper')
WIN_USB_DST = 'build\lib27\site-packages'

import msvc

sys.path.append(PYD_IMPORTS_PATH)


class Extension(object):
    def __init__(self, name, solution_path, destination_path):
        self.name = name
        self.solution_path = solution_path
        self.destination_path = destination_path


class BuildEXT(Command):

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import msvc

        build_base = self.distribution.get_command_obj("build").build_base
        tmp_folder = os.path.split(build_base)[0]

        extensions_build_path = os.path.join(tmp_folder,  'extensions')

        if not os.path.exists(extensions_build_path):
            os.mkdir(extensions_build_path)


        extensions = self.distribution.ext_modules
        environment = msvc.Environment()

        print environment

        for variable, setting in environment:
            os.environ[variable] = setting

        for ext in extensions:
            name = ext.name
            solution_path = ext.solution_path
            destination_path =  os.path.join(tmp_folder, ext.destination_path)
            if not os.path.exists(destination_path):
                os.mkdir(destination_path)

            if (
                'pyd_imports' in destination_path and
                destination_path not in sys.path
            ):
                sys.path.insert(0, destination_path)

            build_path = os.path.join(extensions_build_path, name)

            print(
                '\n\n-- updating solution {0} {1}\n\n'.format(
                    name,
                    '-' * (59 - len(ext.name))
                )
            )

            solution, output_path = environment.update_solution(
                os.path.abspath(solution_path),
                os.path.abspath(build_path)
            )

            build_command = environment.get_build_command(solution)

            print(
                '\n\n-- building {0} {1}\n\n'.format(
                    name,
                    '-' * (68 - len(name))
                )
            )

            proc = Popen(build_command, stdout=PIPE, stderr=PIPE)

            if sys.version_info[0] >= 3:
                empty_return = b''
            else:
                empty_return = ''

            while proc.poll() is None:
                for line in iter(proc.stdout.readline, empty_return):
                    if line:
                        print line.rstrip()

            self.copy_file(os.path.join(output_path, name), destination_path)



RawInputHook = eventghost_build_ext.Extension(
    'RawInputHook.dll',
    RAW_INPUT_HOOK_SRC,
    RAW_INPUT_HOOK_DST
)

MceIr = eventghost_build_ext.Extension(
    'MceIr.dll',
    MCE_IR_SRC,
    MCE_IR_DST
)

TaskHook = eventghost_build_ext.Extension(
    'TaskHook.dll',
    TASK_HOOK_SRC,
    TASK_HOOK_DST
)

cFunctions = eventghost_build_ext.Extension(
    'cFunctions.pyd',
    C_FUNCTIONS_SRC,
    C_FUNCTIONS_DST
)

dxJoystick = eventghost_build_ext.Extension(
    '_dxJoystick.pyd',
    DX_JOYSTICK_SRC,
    DX_JOYSTICK_DST
)

VistaVolEvents = eventghost_build_ext.Extension(
    'VistaVolEvents.pyd',
    VISTA_VOL_EVENTS_SRC,
    VISTA_VOL_EVENTS_DST
)

WinUsbWrapper = eventghost_build_ext.Extension(
    'WinUsbWrapper.dll',
    WIN_USB_SRC,
    WIN_USB_DST
)
