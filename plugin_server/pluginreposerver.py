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

import threading
import socket
import json
import os
import ast
import traceback
import tempfile
import __builtin__
import shutil

from packaging import version as pv
from cStringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED


DEBUG = True


def _log(*args):
    if DEBUG:
        print ' '.join(list(repr(arg) for arg in args))


PLUGIN_DIRECTORY = os.path.join(
    '\\'.join(__file__.split('\\')[:-1]),
    'plugins'
)


def _open_eg_plugin(file_path):
    tmp_dir = tempfile.mkdtemp()
    zipfile = ZipFile(file_path, "r", ZIP_DEFLATED)
    zipfile.extractall(tmp_dir)
    zipfile.close()
    zipfile = open(os.path.join(tmp_dir, "info.py"), "r")
    plugin_info = SafeExecParser.Parse(zipfile.read())
    zipfile.close()

    try:
        return plugin_info
    finally:
        shutil.rmtree(tmp_dir, True)


class PluginManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._plugins = {}

        guids = os.listdir(PLUGIN_DIRECTORY)

        for guid in guids:

            if guid not in self._plugins:
                self._plugins[guid] = {}

            plugin = self._plugins[guid]
            plugin_path = os.path.join(PLUGIN_DIRECTORY, guid)

            versions = os.listdir(plugin_path)
            for version in versions:
                if version not in plugin:
                    version_path = os.path.join(plugin_path, version)
                    eg_plugin = os.path.join(version_path, 'plugin.egplugin')
                    plugin[version] = dict(
                        info=dict(**_open_eg_plugin(eg_plugin)),
                        file=eg_plugin
                    )
                    _log('__init__', plugin[version])

    def _add_plugin(self, plugin_data):
        plugin = StringIO()
        plugin.write(plugin_data)
        plugin.seek(0)
        plugin_info = _open_eg_plugin(plugin)

        guid = plugin['guid']
        version = plugin['version']

        self._lock.acquire()
        if guid not in self._plugins:
            self._plugins[guid] = {}

        if version not in self._plugins[guid]:
            self._plugins[guid][version] = dict(
                info=dict(**plugin_info),
                file=os.path.join(PLUGIN_DIRECTORY, guid, version)
            )

        file_path = self._plugins[guid][version]['file']
        with open(file_path, 'wb') as f:
            f.write(plugin_data)

        _log('_add_plugin', self._plugins[guid][version])

        self._lock.release()

    def _get_plugin_list(self):

        res = []
        for guid in self._plugins:
            version = self._get_newest_version(guid)
            self._lock.acquire()
            res += [dict(
                name=self._plugins[guid][version]['info']['name'],
                icon=self._plugins[guid][version]['info']['icon'],
                kind=self._plugins[guid][version]['info']['kind'],
                valid=True,
                guid=guid,
                path=guid
            )]
            self._lock.release()

        _log('_get_plugin_list', res)

        return res

    def _get_plugin_version_list(self, guid):
        self._lock.acquire()

        res = []
        try:
            for v1 in self._plugins[guid].keys():
                for i, v2 in enumerate(res[:]):
                    if pv.parse(v1) > pv.parse(v2):
                        res.insert(i, v1)
                        break
                if v1 not in res:
                    res.append(v1)
        except KeyError:
            res = []
        finally:
            self._lock.release()

        _log('_get_plugin_version_list', res)
        return res

    def _get_newest_version(self, guid):
        try:
            res = self._get_plugin_version_list(guid)[0]
        except (KeyError, IndexError):
            res = None

        _log('_get_newest_version', res)
        return res

    def _get_plugin_info(self, guid, version):
        self._lock.acquire()
        try:
            res = self._plugins[guid][version]['info']
        except KeyError:
            res = None
        finally:
            self._lock.release()

        _log('_get_plugin_info', res)
        return res

    def _get_plugin(self, guid, version):
        self._lock.acquire()

        if version is None:
            version = self._get_newest_version(guid)

        def close():
            pass

        try:
            f = open(self._plugins[guid][version]['file'], 'rb')
            close = f.close
            res = f.read()

        except KeyError:
            res = None

        finally:
            close()
            self._lock.release()

        _log('_get_plugin', guid, version, res is not None)

        return res

    def query(self, in_data):
        data = json.loads(in_data)

        _log('query', data)

        if 'get_newest_version' in data:
            return self._get_newest_version(
                **data['get_newest_version']
            )

        elif 'get_plugin_info' in data:
            return self._get_plugin_info(**data['get_plugin_info'])

        elif 'add_plugin' in data:
            return self._add_plugin(
                **data['add_plugin']
            )

        elif 'get_plugin_list' in data:
            return self._get_plugin_list()

        elif 'get_plugin_version_list' in data:
            return self._get_plugin_version_list(
                **data['get_plugin_version_list']
            )

        elif 'get_plugin' in data:
            return self._get_plugin(
                **data['get_plugin']
            )


class ClientThread(threading.Thread):
    def __init__(self, handler, timeout, ip, sock):
        _log('ClientThread', ip)

        self._handler = handler
        self._timeout = timeout
        self._ip = ip
        self._sock = sock
        self._event = threading.Event()

        threading.Thread.__init__(
            self,
            name='Plugin Repo Client %s' % ip
        )

    def run(self):
        self._sock.settimeout(self._timeout)
        data = self._sock.recv(4096)

        while True:
            new_data = self._sock.recv(4096)
            if new_data:
                data += new_data
            else:
                break

        data = PluginManager.query(data.strip())

        try:
            data = json.dumps(dict(response=data))
        except UnicodeDecodeError:
            pass

        print data

        self._sock.sendall(data)
        self._sock.close()
        self._handler.remove_thread(self)


class Server(threading.Thread):

    def __init__(self, timeout):
        self._timeout = timeout
        self._sock = None
        self._threads = []
        self._event = threading.Event()
        threading.Thread.__init__(self, name='Plugin Repo Server')

    def run(self):
        try:
            self._sock = sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self._timeout)
            sock.bind(('localhost', 56420))
        except socket.error:
            traceback.print_exc()
        else:
            while not self._event.isSet():
                sock.listen(4)
                try:
                    conn, addr = sock.accept()
                    t = ClientThread(
                        self,
                        self._timeout,
                        addr[0],
                        conn
                    )
                    t.start()
                    self._threads.append(t)
                except socket.error as e:
                    if str(e) != 'timed out':
                        if not self._event.isSet():
                            traceback.print_exc()
                        self._event.set()
            self._sock = None

    def remove_thread(self, t):
        try:
            self._threads.remove(t)
        except:
            pass

    def stop(self):
        self._threads = list(t for t in self._threads if t)

        for t in self._threads[:]:
            t.stop()
        self._event.set()
        try:
            self._sock.close()
        except AttributeError:
            pass
        self.join(self._timeout + 1)


class SafeExecParser(object):
    @classmethod
    def Parse(cls, source):
        return cls().Visit(ast.parse(source))

    def Visit(self, node, *args):
        meth = getattr(self, 'Visit' + node.__class__.__name__)
        return meth(node, *args)

    def VisitAssign(self, node, parent):
        value = self.Visit(node.value)
        for target in node.targets:
            parent[self.Visit(target)] = value

    def VisitModule(self, node):
        mod = {}
        for child in node.body:
            self.Visit(child, mod)
        return mod

    def VisitName(self, node):
        if isinstance(node.ctx, ast.Load):
            if node.id in ("True", "False", "None"):
                return getattr(__builtin__, node.id)
        return node.id

    def VisitStr(self, node):
        return node.s


PluginManager = PluginManager()

server = Server(5.0)

server.start()

while True:
    pass
