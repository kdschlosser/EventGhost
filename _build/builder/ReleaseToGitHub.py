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

import base64
import sys
import wx
from agithub.GitHub import GitHub
from os import environ
from os.path import join
from distutils.core import Command

from Utils import BuildError, IsCIBuild, NextPage

if sys.version_info[0:2] > (3, 0):
    import http.client
    import urllib.parse
else:
    import httplib as http
    http.client = http
    import urllib as urllib
    urllib.parse = urllib


class ReleaseToGitHub(Command):

    def initialize_options(self):
        self.build_setup = None
        self.chglog_file = "CHANGELOG.md"
        self.chglog_short = "CHANGELOG_THIS_RELEASE.md"

    def finalize_options(self):
        self.build_setup = self.distribution.get_command_obj('build')
        self.app_ver = "v" + self.build_setup.app_version

        self.setup_file = 'EventGhost_{0}_Setup.exe'.format(self.app_ver)
        self.setup_path = join(self.build_setup.output_dir, self.setup_file)
        self.chglog_path = join(self.build_setup.output_dir, self.chglog_file)

        self.git_config = self.build_setup.git_config
        token = self.git_config["token"]
        if not token:
            self.gh = None
        else:
            self.gh = GitHub(token=token)
            self.repo, self.branch = self.get_repo()

    def get_repo(self):
        user = self.git_config["user"]
        repo = self.git_config["repo"]
        branch = self.git_config["branch"]
        repo = self.gh.repos[user][repo]
        branch = repo.branches[branch]
        return repo, branch

    def run(self):
        build_setup = self.build_setup

        if self.gh is None:
            return

        print "reading changelog"
        try:
            f = open(self.chglog_path, 'r')
        except IOError:
            print (
                "ERROR: "
                "couldn't read changelog file ({0}).".format(self.chglog_file)
            )

            return
        else:
            changelog = f.read()
            f.close()

        print "loading installer file"
        try:
            f = open(self.setup_path, 'rb')
        except IOError:
            print "ERROR: '{0}' not found.".format(self.setup_file)
            return
        else:
            setup_file_content = f.read()
            f.close()

        # delete a temporary tag that were used to deploy a release
        if IsCIBuild():
            # when we are on CI, we only get here,
            #  when a deploy tag was created
            self.delete_deploy_tag()
            self.git_config["branch"] = 'master'
            self.repo, self.branch = self.get_repo()

        print "getting release info"
        release_exists = False
        release_id = None
        upload_url = None
        page = 1
        while page > 0:
            rc, data = self.repo.releases.get(
                sha=self.git_config["branch"],
                per_page=100,
                page=page
            )
            page = NextPage(self.gh)
            if rc == 200:
                for rel in data:
                    if rel['name'] == self.app_ver:
                        msg = (
                            "Found an existing GitHub release matching"
                            " '{0}'".format(self.app_ver)
                        )
                        if IsCIBuild():
                            raise BuildError(msg)

                        app = wx.GetApp()
                        win = app.GetTopWindow()
                        dlg = wx.MessageDialog(
                            win,
                            caption="Information",
                            message=msg + "\nOverwrite it?",
                            style=wx.YES_NO
                        )
                        if dlg.ShowModal() == wx.ID_NO:
                            return
                        release_id = rel["id"]
                        upload_url = str(rel['upload_url'][:-13])
                        release_exists = True
                        page = 0
                        break

        print "getting branch info"

        rc, data = self.branch.get()
        if rc != 200:
            raise BuildError("ERROR: couldn't get branch info.")
        commit_sha = data['commit']['sha']
        # if not uploadUrl:
        #     uploadUrl = str(data['upload_url'][:-13])

        rc, data = self.repo.contents[self.chglog_file].get(
            ref=self.git_config['branch']
        )
        if rc == 200:
            remote_changelog = base64.decodestring(data["content"])
        else:
            remote_changelog = None
        new_commit_sha = None
        if changelog != remote_changelog:
            new_commit_sha = self.commit_changelog(commit_sha, changelog)

        if not release_exists:
            print "reading changelog for this release"
            try:
                f = open(join(build_setup.output_dir, self.chglog_short), 'r')
            except IOError:
                print (
                    "ERROR: couldn't read changelog "
                    "file ({0}).".format(self.chglog_short)
                )
                rel_chglog = ""
            else:
                rel_chglog = f.read().strip()
                f.close()

            print "creating release"
            body = dict(
                tag_name=self.app_ver,
                target_commitish=new_commit_sha,
                name=self.app_ver,
                body=rel_chglog,
                draft=False,
                prerelease=("-" in self.app_ver)
            )
            rc, data = self.repo.releases.post(body=body)
            if rc != 201:
                raise BuildError(
                    "ERROR: couldn't create a release on GitHub."
                )
            upload_url = str(data['upload_url'][:-13])
        else:
            print 'deleting existing asset'
            rc, data = self.repo.releases[release_id].assets.get()
            if rc == 200:
                for asset in data:
                    if asset["name"] == self.setup_file:
                        rc, data = (
                            self.repo.releases.assets[asset["id"]].delete()
                        )
                        if rc != 204:
                            print "ERROR: couldn't delete existing asset."
                            return
                        break

        print "uploading setup file"
        url = upload_url + '?name={0}'.format(self.setup_file)
        headers = {
            'content-type':  'application/octet-stream',
            'authorization': 'Token {0}'.format(self.git_config['token']),
            'accept':        'application/vnd.github.v3+json',
            'user-agent':    'agithub/v2.0'
        }
        conn = http.client.HTTPSConnection('uploads.github.com')
        conn.request('POST', url, setup_file_content, headers)
        response = conn.getresponse()
        status = response.status
        conn.close()
        if status != 201:
            raise BuildError(
                "ERROR: couldn't upload installer file to GitHub."
            )

    def commit_changelog(self, commit_sha, changelog):
        ref = 'heads/{0}'.format(self.git_config["branch"])

        print "getting commit referenced by branch"
        rc, data = self.repo.git.commits[commit_sha].get()
        if rc != 200:
            raise BuildError("ERROR: couldn't get commit info.")
        tree_sha = data['tree']['sha']

        print "getting tree"
        rc, data = self.repo.git.trees[tree_sha].get()
        if rc != 200:
            raise BuildError("ERROR: couldn't get tree info.")

        blob = None
        print "getting blob for {0}".format(self.chglog_file)
        for entry in data['tree']:
            if entry['path'] == self.chglog_file and entry['type'] == 'blob':
                blob = entry
                break
        if blob is None:
            raise BuildError("ERROR: couldn't get blob info.")

        print "posting new changelog"
        body = dict(content=changelog, encoding='utf-8')
        rc, data = self.repo.git.blobs.post(body=body)
        if rc != 201:
            raise BuildError("ERROR: couldn't post new changelog contents.")
apart
        print "posting tree"
        newblob = dict(
            path=blob['path'],
            mode=blob['mode'],
            type=blob['type'],
            sha=data['sha']
        )
        body = dict(tree=[newblob], base_tree=tree_sha)
        rc, data = self.repo.git.trees.post(body=body)
        if rc != 201:
            raise BuildError("ERROR: couldn't post new tree.")
        new_tree_sha = data['sha']

        print "creating commit for changelog update"
        body = {
            'message': (
                "Add changelog for {0}\n[skip appveyor]".format(self.app_ver)
            ),
            'tree':    new_tree_sha,
            'parents': [commit_sha]
        }
        rc, data = self.repo.git.commits.post(body=body)
        if rc != 201:
            raise BuildError(
                "ERROR: couldn't create commit for changelog update."
            )
        new_commit_sha = data['sha']

        print "updating reference for branch to new commit"
        body = dict(sha=new_commit_sha)
        rc, data = self.repo.git.refs[ref].patch(body=body)
        if rc != 200:
            raise BuildError(
                "ERROR: couldn't update reference ({0}) "
                "with new commit.".format(ref)
            )

        return new_commit_sha

    def delete_deploy_tag(self):
        """
        Delete a temporary tag (github release) that was used to deploy
        a new release.
        """

        deploy_tag_name = environ.get('APPVEYOR_REPO_TAG_NAME')
        if not deploy_tag_name:
            return

        deploy_tag = None
        page = 1
        while page > 0:
            rc, data = self.repo.git.refs.tags.get(
                per_page=100,
                page=page
            )
            page = NextPage(self.gh)
            if rc == 200:
                for tag in data:
                    if tag['ref'].rsplit('/', 1)[1] == deploy_tag_name:
                        deploy_tag = tag
                        page = 0
                        break

        if deploy_tag and deploy_tag['object']['type'] == 'commit':
            rc, data = self.repo.git.releases.tags[deploy_tag_name].get(
                per_page=100,
                page=page
            )
            if rc == 200:
                rc, data2 = self.repo.git.releases[data['id']].delete()
                if rc == 204:
                    print "deploy github release deleted"

        if deploy_tag:
            rc, data = self.repo.git.git.refs.tags[deploy_tag_name].delete()
            if rc == 204:
                print "deploy tag deleted"
