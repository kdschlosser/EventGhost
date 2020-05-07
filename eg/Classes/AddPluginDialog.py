# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2019 EventGhost Project <http://www.eventghost.net/>
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
import requests
import shutil
import os
import tempfile
from io import BytesIO
# Local imports
import eg

KIND_TAGS = ["other", "remote", "program", "external"]
URL = 'http://:52423/'


class Config(eg.PersistentData):
    position = None
    size = (640, 450)
    splitPosition = 240
    lastSelection = None
    collapsed = set()


class Text(eg.TranslatableStrings):
    title = "Add Plugin..."
    noInfo = "No information available."
    noMultiloadTitle = "No multiload possible"
    noMultiload = (
        "This plugin doesn't support multiload and you already have one "
        "instance of this plugin in your configuration."
    )
    otherPlugins = "General Plugins"
    remotePlugins = "Input Devices"
    programPlugins = "Software Control"
    externalPlugins = "Hardware Control"
    author = "Author:"
    version = "Version:"
    descriptionBox = "Description"
    downgrade_caption = 'Downgrade Plugin'
    downgrade_message = (
        'The installed plugin is newer then the one you want to install.\n\n'
        'Do you want to downgrade the plugin?'
    )


PLUGIN_TYPE = 'plugin'
VERSION_TYPE = 'version'
GROUP_TYPE = 'group'


class AddPluginDialog(eg.TaskletDialog):
    instance = None

    def CheckMultiload(self):
        if not self.checkMultiLoad:
            return True
        info = self.resultData
        if not info:
            return True
        if info.canMultiLoad:
            return True
        if any((plugin.info.path == info.path) for plugin in eg.pluginList):
            eg.MessageBox(
                Text.noMultiload,
                Text.noMultiloadTitle,
                style=wx.ICON_EXCLAMATION
            )
            return False
        else:
            return True

    @eg.LogItWithReturn
    def Configure(self, parent, checkMultiLoad=True, title=None):
        if title is None:
            title = Text.title
        self.checkMultiLoad = checkMultiLoad
        if self.__class__.instance:
            self.__class__.instance.Raise()
            return
        self.__class__.instance = self

        self.resultData = None

        eg.TaskletDialog.__init__(
            self,
            parent,
            -1,
            title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        splitterWindow = wx.SplitterWindow(
            self,
            style=(
                wx.SP_LIVE_UPDATE |
                wx.CLIP_CHILDREN |
                wx.NO_FULL_REPAINT_ON_RESIZE
            )
        )

        eg.Bind('AddPluginSelectionChanged', self.add_plugin_selection_changed)
        eg.Bind('AddPluginActivated', self.add_plugin_activated)

        self.temp_path = tempfile.mkdtemp()
        self.treeCtrl = TreeCtrl(splitterWindow)

        rightPanel = wx.Panel(splitterWindow)
        rightSizer = wx.BoxSizer(wx.VERTICAL)
        rightPanel.SetSizer(rightSizer)

        self.nameText = nameText = wx.StaticText(rightPanel)
        nameText.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        rightSizer.Add(nameText, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 5)

        subSizer = wx.FlexGridSizer(2, 2)
        self.authorLabel = wx.StaticText(rightPanel, label=Text.author)
        subSizer.Add(self.authorLabel)
        self.authorText = wx.StaticText(rightPanel)
        subSizer.Add(self.authorText, 0, wx.EXPAND | wx.LEFT, 5)
        self.versionLabel = wx.StaticText(rightPanel, label=Text.version)
        subSizer.Add(self.versionLabel)
        self.versionText = wx.StaticText(rightPanel)
        subSizer.Add(self.versionText, 0, wx.EXPAND | wx.LEFT, 5)
        rightSizer.Add(subSizer, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 5)

        staticBoxSizer = wx.StaticBoxSizer(
            wx.StaticBox(rightPanel, label=Text.descriptionBox)
        )

        self.descrBox = eg.HtmlWindow(rightPanel)
        staticBoxSizer.Add(self.descrBox, 1, wx.EXPAND)

        rightSizer.Add(staticBoxSizer, 1, wx.EXPAND | wx.LEFT, 5)

        splitterWindow.SplitVertically(self.treeCtrl, rightPanel)
        splitterWindow.SetMinimumPaneSize(60)
        splitterWindow.SetSashGravity(0.0)
        splitterWindow.UpdateSize()

        self.buttonRow = eg.ButtonRow(self, (wx.ID_OK, wx.ID_CANCEL), True)
        self.okButton = self.buttonRow.okButton
        self.okButton.Enable(False)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(splitterWindow, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(self.buttonRow.sizer, 0, wx.EXPAND)

        self.SetSizerAndFit(mainSizer)
        #minSize = mainSizer.GetMinSize()
        #self.SetMinSize(minSize)
        self.SetSize(Config.size)
        splitterWindow.SetSashPosition(Config.splitPosition)
        if Config.position:
            self.SetPosition(Config.position)

        while self.Affirmed():
            if isinstance(self.resultData, dict):
                if self.check_plugin(self.resultData):
                    self.resultData = eg.pluginManager.GetPluginInfo(self.resultData['guid'])
                else:
                    self.resultData = None

            if self.CheckMultiload():
                self.SetResult(self.resultData)

        eg.Unbind('AddPluginSelectionChanged', self.add_plugin_selection_changed)
        eg.Unbind('AddPluginActivated', self.add_plugin_activated)

        Config.size = self.GetSizeTuple()
        Config.position = self.GetPositionTuple()
        Config.splitPosition = splitterWindow.GetSashPosition()

        shutil.rmtree(self.temp_path)

        self.__class__.instance = None

    def add_plugin_selection_changed(self, plugin_info):
        if plugin_info['guid']:
            self.resultData = plugin_info
        else:
            self.resultData = None

        name = plugin_info['name']
        description = plugin_info['description']

        version = plugin_info['version']

        if version is None:
            self.authorLabel.SetLabel("")
            self.authorText.SetLabel("")
            self.versionLabel.SetLabel("")
            self.versionText.SetLabel("")
            self.okButton.Enable(False)
        else:
            if isinstance(version, list):
                version = '\n'.join(version)
                self.authorLabel.SetLabel('')
                self.authorText.SetLabel('')
                self.versionLabel.SetLabel('')
                self.okButton.Enable(False)
            else:
                images = self.treeCtrl.get_plugin_images(plugin_info['name'], plugin_info['version'])
                import base64
                for file_name, image_data in images:
                    image_data = base64.decodestring(image_data)
                    file_name = os.path.join(self.temp_path, file_name)

                    file_path = os.path.split(file_name)[0]

                    if file_path != self.temp_path and not os.path.exists(file_path):
                        os.makedirs(file_path)

                    with open(file_name, 'wb') as f:
                        f.write(image_data)

                self.descrBox.SetBasePath(self.temp_path)
                self.authorLabel.SetLabel(Text.author)
                self.authorText.SetLabel(plugin_info['author'].replace("&", "&&"))
                self.versionLabel.SetLabel(Text.version)

                self.okButton.Enable(True)

            self.versionText.SetLabel(version)

        self.nameText.SetLabel(name)
        self.descrBox.SetPage(eg.Utils.AppUrl(description, plugin_info['url']))

    def check_plugin(self, plugin_info):
        if plugin_info is None:
            return False

        plugin_versions = self.treeCtrl.get_plugin_versions(plugin_info['name'])

        for info in eg.pluginManager.GetPluginInfoList():
            if info.guid != plugin_info['guid']:
                continue

            if info.version not in plugin_versions:
                raise RuntimeError('Plugin version that is installed is unknown')

            old = plugin_versions.index(info.version)
            new = plugin_versions.index(plugin_info['version'])

            if old == new:
                return True

            if old > new:
                dialog = eg.MessageDialog(
                    eg.mainFrame,
                    Text.downgrade_message,
                    Text.downgrade_caption,
                    style=wx.ICON_QUESTION | wx.YES_NO
                )

                answer = dialog.ShowModal()
                dialog.Destroy()
                if answer == wx.ID_NO:
                    return False

                try:
                    shutil.rmtree(info.path)
                except OSError:
                    import traceback
                    traceback.print_exc()
                    return False

        return True

    def add_plugin_activated(self, plugin):
        if not self.check_plugin(self.resultData):
            self.resultData = None

        plugin_info = self.resultData

        eg.PluginInstall.Import(plugin)
        eg.pluginManager.ScanAllPlugins()
        self.resultData = eg.pluginManager.GetPluginInfo(plugin_info['guid'])
        self.OnOK(wx.CommandEvent())


class TreeCtrl(wx.TreeCtrl):

    def __init__(self, parent):
        wx.TreeCtrl.__init__(
            self,
            parent,
            style=(
                wx.TR_SINGLE |
                wx.TR_HAS_BUTTONS |
                wx.TR_HIDE_ROOT |
                wx.TR_LINES_AT_ROOT
            )
        )

        self.SetMinSize((170, 200))

        self.image_list = image_list = wx.ImageList(16, 16)
        image_list.Add(eg.Icons.PLUGIN_ICON.GetBitmap())
        image_list.Add(eg.Icons.FOLDER_ICON.GetBitmap())
        self.SetImageList(image_list)

        groups = self.query_server('plugin_groups', language=eg.config.language)
        root = self.AddRoot("")
        type_ids = {}

        for group_type, group_label in groups:
            type_id = self.AppendItem(root, group_label, 1)
            self.SetPyData(type_id, group_type)
            self.SetItemHasChildren(type_id, True)
            type_ids[group_type] = type_id

        self.type_ids = type_ids

        menu = wx.Menu()
        self.export_menu_id = menuId = wx.NewId()
        menu.Append(menuId, eg.text.MainFrame.Menu.Export)
        self.contextMenu = menu
        self.Bind(wx.EVT_MENU, self.on_command_export, id=menuId)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_item_right_click)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_selection_changed)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.on_item_expanding)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.on_item_collapsing)

    def on_command_export(self, _=None):
        item_id = self.GetSelection()

        plugin_version = self.GetItemText(item_id)
        plugin_id = self.GetItemParent(item_id)
        plugin_name = self.GetItemText(plugin_id)
        for info in eg.pluginManager.GetPluginInfoList():
            if (
                info.name == plugin_name and
                info.version == plugin_version
            ):
                eg.PluginInstall.Export(info)
                break

    def is_plugin_installed(self, guid):
        for info in eg.pluginManager.GetPluginInfoList():
            if info.guid == guid:
                return True
        return False

    def is_plugin_version_installed(self, guid, version):
        for info in eg.pluginManager.GetPluginInfoList():
            if info.guid == guid:
                return info.version == version

        return False

    def on_item_expanding(self, evt):
        item_id = evt.GetItem()

        if not self.IsExpanded(item_id):
            item_type = self.GetPyData(item_id)

            if item_type in self.type_ids:
                plugins = self.get_plugin_list(item_type)
                for plugin in plugins:
                    icon = self.get_plugin_icon(plugin)

                    if icon is None:
                        icon_index = 0
                    else:
                        icon = eg.Icons.StringIcon(icon)
                        icon_index = self.image_list.Add(icon.GetBitmap())

                    plugin_id = self.AppendItem(
                        item_id,
                        plugin,
                        icon_index
                    )
                    self.SetPyData(plugin_id, PLUGIN_TYPE)
                    self.SetItemHasChildren(plugin_id, True)

            elif item_type == PLUGIN_TYPE:
                plugin_name = self.GetItemText(item_id)
                for plugin_version in self.get_plugin_versions(plugin_name):
                    version_id = self.AppendItem(item_id, plugin_version)
                    self.SetPyData(version_id, VERSION_TYPE)

    def on_item_collapsing(self, evt):
        item_id = evt.GetItem()
        if self.IsExpanded(item_id):
            item_type = self.GetPyData(item_id)

            self.Unbind(wx.EVT_TREE_ITEM_COLLAPSING, handler=self.on_item_collapsing)
            self.Collapse(item_id)
            self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.on_item_collapsing)

            if item_type == PLUGIN_TYPE or item_type in self.type_ids:
                self.DeleteChildren(item_id)
                self.SetItemHasChildren(item_id, True)

    def get_plugin_icon(self, plugin_name):
        return self.query_server('get_plugin_icon', plugin_name=plugin_name)[0]

    def get_plugin_list(self, kind):
        return self.query_server('get_plugin_list', kind=kind)

    def get_plugin_guid(self, plugin_name):
        return self.query_server('get_plugin_guid', plugin_name=plugin_name)

    def get_plugin_detail(self, plugin_name, plugin_version):
        return self.query_server('get_plugin_detail', plugin_name=plugin_name, plugin_version=plugin_version)

    def get_plugin_versions(self, plugin_name):
        return self.query_server('get_plugin_versions', plugin_name=plugin_name)

    def get_plugin_images(self, plugin_name, plugin_version):
        return self.query_server('get_plugin_images', plugin_name=plugin_name, plugin_version=plugin_version)

    def get_plugin(self, plugin_name, plugin_version):
        plugin_data = self.query_server('get_plugin', plugin_name=plugin_name, plugin_version=plugin_version)
        return BytesIO(plugin_data)

    def query_server(self, command, **params):
        response = requests.get(URL + 'get_access_token')
        token = response.content
        response = requests.get(URL + token + '/' + command, params=params)
        try:
            return response.json()
        except:
            return response.content

    def on_item_right_click(self, evt):
        """
        Handles wx.EVT_TREE_ITEM_RIGHT_CLICK events.
        """
        item_id = evt.GetItem()
        self.SelectItem(item_id)
        item_type = self.GetPyData(item_id)
        if item_type == VERSION_TYPE:
            plugin_version = self.GetItemText(item_id)
            plugin_id = self.GetItemParent(item_id)
            plugin_name = self.GetItemText(plugin_id)

            for info in eg.pluginManager.GetPluginInfoList():
                if (
                    info.name == plugin_name and
                    info.version == plugin_version
                ):
                    self.contextMenu.Enable(self.export_menu_id, True)
                    break

            else:
                self.contextMenu.Enable(self.export_menu_id, False)

            self.PopupMenu(self.contextMenu)

    def on_selection_changed(self, evt):
        """
        Handle the wx.EVT_TREE_SEL_CHANGED events.
        """
        item_id = evt.GetItem()
        item_type = self.GetPyData(item_id)

        if item_type == VERSION_TYPE:
            plugin_version = self.GetItemText(item_id)
            plugin_id = self.GetItemParent(item_id)
            plugin_name = self.GetItemText(plugin_id)
            plugin_info = self.get_plugin_detail(plugin_name, plugin_version)
            plugin_installed = self.is_plugin_version_installed(plugin_info['guid'], plugin_version)
            plugin_info['installed'] = plugin_installed

        elif item_type == PLUGIN_TYPE:
            plugin_name = self.GetItemText(item_id)
            kind_id = self.GetItemParent(item_id)
            plugin_kind = self.GetPyData(kind_id)
            plugin_versions = self.get_plugin_versions(plugin_name)
            plugin_guid = self.get_plugin_guid(plugin_name)
            plugin_installed = self.is_plugin_installed(plugin_guid)

            if plugin_installed:
                for i, plugin_version in enumerate(plugin_versions):
                    if self.is_plugin_version_installed(plugin_guid, plugin_version):
                        plugin_versions[i] += ' (installed)'

            plugin_info = dict(
                name=plugin_name,
                installed=plugin_installed,
                description='',
                kind=plugin_kind,
                canMultiLoad=None,
                createMacrosOnAdd=None,
                url=None,
                help=None,
                guid="",
                hardwareId="",
                author='',
                version=plugin_versions,
            )

        else:
            plugin_info = dict(
                name=self.GetItemText(item_id),
                installed=False,
                description=Text.noInfo,
                kind=None,
                canMultiLoad=None,
                createMacrosOnAdd=None,
                url=None,
                help=None,
                guid="",
                hardwareId="",
                author='',
                version=None,
            )

        eg.Notify('AddPluginSelectionChanged', plugin_info)

    def on_item_activated(self, evt):
        item_id = self.GetSelection()
        item_type = self.GetPyData(item_id)

        if item_type == VERSION_TYPE:
            plugin_version = self.GetItemText(item_id)
            plugin_id = self.GetItemParent(item_id)
            plugin_name = self.GetItemText(plugin_id)
            plugin_info = self.get_plugin_detail(plugin_name, plugin_version)

            eg.Notify('AddPluginSelectionChanged', plugin_info)
            eg.Notify('AddPluginActivated', plugin_info)
            return

        else:
            if self.IsExpanded(item_id):
                self.Collapse(item_id)
            else:
                self.Expand(item_id)

        evt.Skip()


# server side code

"""
import flask
import uuid
import os
import zipfile
import tempfile
import sys
import shutil
import base64
import __builtin__

app = flask.Flask(__name__)

plugin_path = r''


plugins = {}

plugin_groups = {
    'en': [
        ['other', 'Other'],
        ['core', 'Core'],
        ['remote', 'Remote'],
        ['program', 'Program'],
        ['external', 'External']
    ]
}


class EG(object):

    def __init__(self):
        sys.modules['eg'] = self
        __builtin__.eg = self
        plugin = ('', '')

    def RegisterPlugin(
        self,
        name=None,
        description=None,
        kind="other",
        author="[unknown author]",
        version="[unknown version]",
        icon=None,
        canMultiLoad=False,
        createMacrosOnAdd=False,
        url=None,
        help=None,
        guid="",
        hardwareId="",
        **kwargs
    ):
        if isinstance(name, unicode):
            name = name.encode('utf-8')

        if name not in plugins:
            plugins[name] = {}

        plugins[name][version] = dict(
            name=name,
            description=description,
            kind=kind,
            author=author,
            version=version,
            icon=icon,
            canMultiLoad=canMultiLoad,
            createMacrosOnAdd=createMacrosOnAdd,
            url=url,
            help=help,
            guid=guid,
            hardwareId=hardwareId
        )

        self.plugin = (name, version)


        raise RegisterPluginException()


class RegisterPluginException(Exception):
    pass


eg = EG()

for plugin_dir in os.listdir(plugin_path):
    plugin_dir = os.path.join(plugin_path, plugin_dir)
    if not os.path.isdir(plugin_dir):
        continue

    for plugin_zip in os.listdir(plugin_dir):
        print plugin_zip

        if not plugin_zip.endswith('.egplugin'):
            continue

        temp_dir = tempfile.mkdtemp()
        plugin_zip = os.path.join(plugin_dir, plugin_zip)

        z_file = zipfile.ZipFile(plugin_zip, "r", zipfile.ZIP_DEFLATED)
        z_file.extractall(temp_dir)
        z_file.close()
        for base_path in os.listdir(temp_dir):
            if os.path.isdir(os.path.join(temp_dir, base_path)):
                break
        else:
            shutil.rmtree(temp_dir)
            continue

        sys.path.append(temp_dir)
        try:
            __import__(base_path)
        except RegisterPluginException:
            plugin_name, plugin_version = eg.plugin
            plugins[plugin_name][plugin_version]['egplugin'] = plugin_zip
        except:
            import traceback
            traceback.print_exc()

        sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir)


from pkg_resources import parse_version


active_tokens = []

class Token(object):

    def __init__(self):
        self.token = str(uuid.uuid4()).replace('-', '')[1:-1].upper()

        app.add_url_rule('/' + self.token + '/get_plugin', endpoint=repr(self.get_plugin), view_func=self.get_plugin)
        app.add_url_rule('/' + self.token + '/get_plugin_images', endpoint=repr(self.get_plugin_images), view_func=self.get_plugin_images)
        app.add_url_rule('/' + self.token + '/get_plugin_versions', endpoint=repr(self.get_plugin_versions), view_func=self.get_plugin_versions)
        app.add_url_rule('/' + self.token + '/get_plugin_detail', endpoint=repr(self.get_plugin_detail), view_func=self.get_plugin_detail)
        app.add_url_rule('/' + self.token + '/get_plugin_guid', endpoint=repr(self.get_plugin_guid), view_func=self.get_plugin_guid)
        app.add_url_rule('/' + self.token + '/get_plugin_list', endpoint=repr(self.get_plugin_list), view_func=self.get_plugin_list)
        app.add_url_rule('/' + self.token + '/plugin_groups', endpoint=repr(self.plugin_groups), view_func=self.plugin_groups)
        app.add_url_rule('/' + self.token + '/get_plugin_icon', endpoint=repr(self.get_plugin_icon), view_func=self.get_plugin_icon)

    def destroy(self):
        rules = [
            'get_plugin',
            'get_plugin_images',
            'get_plugin_versions',
            'get_plugin_detail',
            'get_plugin_guid',
            'get_plugin_list',
            'plugin_groups',
            'get_plugin_icon'
        ]

        for rule in rules:
            rule = '/' + self.token + '/' + rule

            for item in app.url_map.iter_rules():
                if item.rule  == rule:
                    break
            else:
                raise RuntimeError('Unable to locate rule ' + rule)

            app.url_map._rules.remove(item)
            del app.url_map._rules_by_endpoint[item.endpoint]

        active_tokens.remove(self)

    def get_plugin(self):
        plugin_name = flask.request.args.get('plugin_name')
        plugin_version = flask.request.args.get('plugin_version')

        res = ''
        if plugin_name in plugins:
            plugin = plugins[plugin_name]
            if plugin_version in plugin:
                res = flask.send_file(plugin[plugin_version]['egplugin'])
        try:
            return res
        finally:
            self.destroy()

    def get_plugin_images(self):
        plugin_name = flask.request.args.get('plugin_name')
        plugin_version = flask.request.args.get('plugin_version')
        res = []

        if plugin_name in plugins:
            plugin = plugins[plugin_name]
            if plugin_version in plugin:
                temp_path = tempfile.mkdtemp()
                z_file = zipfile.ZipFile(plugin[plugin_version]['egplugin'],  "r", zipfile.ZIP_DEFLATED)
                z_file.extractall(temp_path)
                z_file.close()

                def iter_plugin(pth):
                    for p_file in os.listdir(pth):
                        if p_file.endswith('.py'):
                            continue

                        p_file = os.path.join(pth, p_file)

                        if os.path.isdir(p_file):
                            iter_plugin(p_file)
                        else:
                            with open(p_file, 'rb') as f:
                                data = f.read()

                            data = base64.encodestring(data)
                            res.append([p_file.replace(base_path, '')[1:], data])

                for base_path in os.listdir(temp_path):
                    base_path = os.path.join(temp_path, base_path)
                    if os.path.isdir(base_path):
                        iter_plugin(base_path)
                        break

                shutil.rmtree(temp_path)
        try:
            return flask.jsonify(res)
        finally:
            self.destroy()

    def get_plugin_versions(self):
        plugin_name = flask.request.args.get('plugin_name')
        res = []
        if plugin_name in plugins:
            res = sorted(list(plugins[plugin_name].keys()), key=parse_version)

        try:
            return flask.jsonify(res)
        finally:
            self.destroy()

    def get_plugin_detail(self):
        plugin_name = flask.request.args.get('plugin_name')
        plugin_version = flask.request.args.get('plugin_version')

        info = {}
        if plugin_name in plugins:
            plugin = plugins[plugin_name]
            if plugin_version in plugin:
                for key, value in plugin[plugin_version].items():
                    info[key] = value

                del info['egplugin']

        try:
            return flask.jsonify(info)
        finally:
            self.destroy()

    def get_plugin_guid(self):
        plugin_name = flask.request.args.get('plugin_name')
        res = ''
        if plugin_name in plugins:
            plugin_versions = plugins[plugin_name]
            for info in plugin_versions.values():
                res = info['guid']
                break

        try:
            return res
        finally:
            self.destroy()

    def get_plugin_list(self):
        kind = flask.request.args.get('kind')

        res = []

        for versions in plugins.values():
            for info in versions.values():
                if info['kind'] == kind and info['name'] not in res:
                    res += [info['name']]
        print res
        try:
            return flask.jsonify(res)
        finally:
            self.destroy()

    def get_plugin_icon(self):
        plugin_name = flask.request.args.get('plugin_name')
        res = None
        if plugin_name in plugins:
            plugin_versions = plugins[plugin_name]
            for info in plugin_versions.values():
                if info['icon'] is not None:
                    res = info['icon']
                    break
        try:
            return flask.jsonify([res])
        finally:
            self.destroy()

    def plugin_groups(self):
        language = flask.request.args.get('language')
        language = language.split('_')[0]

        if language not in plugin_groups:
            language = 'en'

        try:
            return flask.jsonify(plugin_groups[language])
        finally:
            self.destroy()

    def __str__(self):
        return self.token


@app.route('/get_access_token')
def get_access_token():
    token = Token()
    active_tokens.append(token)
    return str(token)


app.run(host='', port=52423)"""
