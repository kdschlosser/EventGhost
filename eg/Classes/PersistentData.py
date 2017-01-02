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

# Local imports

from types import ClassType, InstanceType

import eg


def FormatAttr(attrName, attr, indent):
    indent4 = ' ' * (indent + 1)
    indent = ' ' * indent
    attrField = '%s%s = ' % (indent, attrName)

    multiLine = len(attrField + repr(attr)) > 76

    if multiLine and type(attr) in (unicode, str, list, tuple):
        if type(attr) == list:
            attrField += '[\n'
            for item in attr:
                attrField += '%s%r,\n' % (indent4, item)
            attrField = '%s\n%s]' % (attrField[:-2], indent)

        else:
            if type(attr) in (unicode, str):
                stop = 76 - len(indent4)
                if stop > 25:
                    attrField += '(\n'
                    while len(repr(attr) + indent4) > 76:
                        attrField += '%s%r\n' % (indent4, attr[:stop])
                        attr = attr[stop:]
                    attrField += '%s%r\n%s)' % (indent4, attr, indent)
                else:
                    attrField += repr(attr)
            else:
                for item in attr:
                    attrField += '%s%r,\n' % (indent4, item)
                attrField = '%s\n%s)' % (attrField[:-2], indent)
    else:
        attrField += repr(attr)
    return attrField + '\n'


class PersistentDataBase(object):
    def __init__(self, parent, key):
        self._parent = parent
        self._key = key
        self._moduleName = repr(parent).split(' ')[0][1:]
        self._deleteFlag = False
        self._debugFlag = False
        if key:
            self._moduleName += '.' + key

    def SetDelete(self, flag=True):
        self._deleteFlag = flag

    def SetDebug(self, flag=True):
        self._debugFlag = flag

    def SaveData(self, fileWriter, indent):
        classKeys = []

        if self._debugFlag or self._deleteFlag:
            return

        for key, value in self:
            if type(value) in (PersistentDataMeta, PersistentDataBase):
                classKeys.append([key, value])
            else:
                line = FormatAttr(key, value, indent)
                fileWriter(line)

        for key, value in classKeys:

            formatString = '\n%sclass %s:\n'
            if not indent and key == 'eg':
                formatString = '\n' + formatString

            fileWriter(formatString % (' ' * indent, key))
            value.SaveData(fileWriter, indent + 1)

    def __repr__(self):
        objRepr = repr(self._parent).split(' ')
        objRepr[0] = '<' + self._moduleName
        return ' '.join(objRepr)

    def __delete__(self, instance):
        if self._key:
            delattr(self._parent, self._key)

    def __iter__(self):
        for key in sorted(self.__dict__.keys()):
            if key.startswith('_'):
                continue
            yield key, self.__dict__[key]

    def __getitem__(self, item):
        return getattr(self, item)

    def __getattr__(self, item):
        if item.startswith('_'):
            pass
        elif item in self.__dict__:
            return self.__dict__[item]

        raise AttributeError(
            '%s does not have attribute %s' % (self._moduleName, item)
        )

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            object.__setattr__(self, key, value)
        else:
            clsTypes = (
                PersistentDataBase, PersistentDataMeta, ClassType, InstanceType
            )
            if type(value) in clsTypes:
                if hasattr(self, key):
                    cls = getattr(self, key)
                else:
                    cls = PersistentDataBase(self, key)

                for attrName in value.__dict__.keys():
                    if not attrName.startswith('_'):
                        setattr(cls, attrName, value.__dict__[attrName])
                value = cls

            self.__dict__[key] = value

    def __delitem__(self, key):
        delattr(self, key)

    def __delattr__(self, item):
        if item in self.__dict__:
            del (self.__dict__[item])
        else:
            raise AttributeError(
                '%s does not have attribute %s' % (self._moduleName, item)
            )


class PersistentDataMeta(type):
    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)
        if len(bases):
            searchPath = dct["__module__"]
            config = eg.config
            parts = searchPath.split(".")
            for part in parts[:-1]:
                if hasattr(config, part):
                    config = getattr(config, part)
                else:
                    newConfig = PersistentDataBase(config, part)
                    setattr(config, part, newConfig)
                    config = newConfig
                    if eg.debugLevel:
                        config.SetDebug()

            setattr(config, parts[-1], cls)
            return getattr(config, parts[-1])

        return cls


class PersistentData:
    __metaclass__ = PersistentDataMeta
