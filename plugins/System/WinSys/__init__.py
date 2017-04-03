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
import Command
import Execute
import Registry


ICON = None


class Text(eg.TranslatableStrings):
    class Group:
        name = 'Windows Commands'
        description = 'Windows Commands'


def AddActions(plugin):
    group = plugin.AddGroup(
        Text.Group.name,
        Text.Group.description,
        ICON
    )
    
    group.AddAction(Command.Command)
    group.AddAction(Execute.Execute)
    group.AddAction(RefreshEnvironment)
    group = group.AddGroup(
        Registry.Text.Group.name,
        Registry.Text.Group.description,
        Registry.ICON
    )
    group.AddAction(Registry.RegistryChange)
    group.AddAction(Registry.RegistryQuery)


class RefreshEnvironment(eg.ActionBase):
    name = "Refresh Environment"
    description = """<rst>
            Refreshes environment variables by reading their current
            values from the registry.

            When a program launches, it inherits the current environment
            from the program that launched it, and EventGhost is no
            different. By default, if you modify an environment variable,
            EventGhost won't pass your changes along to the programs it
            launches because it doesn't know those changes took place. If
            you update your %PATH%, for example, then open a Command
            Prompt from EventGhost, you'll find you're unable to run
            commands from the new folders you've added.

            In the past, the only solution to this problem was to restart
            EventGhost. Now, with the aid of this action (or "Refresh
            environment before executing Run actions" in Options), EventGhost
            can read the latest environment variables from the registry,
            apply them to its own environment, and thereby pass them along
            to anything it launches going forward.
        """
    
    __call__ = eg.Environment.Refresh

