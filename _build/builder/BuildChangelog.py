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

import codecs
from agithub.GitHub import GitHub
from collections import OrderedDict
from os.path import join
from shutil import copy2
from time import localtime, strftime
from distutils.core import Command

# Local imports
from Utils import BuildError, EscapeMarkdown, NextPage


class BuildChangelog(Command):

    def initialize_options(self):
        self.build_setup = None

    def finalize_options(self):
        self.build_setup = self.distribution.get_command_obj('build')

    def run(self):
        if not self.build_setup.gitConfig["token"]:
            print "WARNING: Skipping changelog build due to invalid token."
            return

        build_setup = self.build_setup
        changelog_path = join(build_setup.outputDir, "CHANGELOG.md")
        copy2(
            join(build_setup.sourceDir, "CHANGELOG.md"),
            changelog_path
        )

        token = build_setup.gitConfig["token"]
        user = build_setup.gitConfig["user"]
        repo = build_setup.gitConfig["repo"]
        branch = build_setup.gitConfig["branch"]
        gh = GitHub(token=token)

        # fetch all tags from github
        page = 1
        all_tags = []
        while page > 0:
            rc, data = gh.repos[user][repo].git.refs.tags.get(
                sha=branch,
                per_page=100,
                page=page
            )
            if rc != 200:
                raise BuildError(data["message"])
            all_tags.extend(data)
            page = NextPage(gh)

        # get release date for tags
        for tag in all_tags:
            tag["pulls"] = []
            if tag["object"]["type"] == "commit":
                rc, data = gh.repos[user][repo].git.commits[
                    tag["object"]["sha"]].get(sha=branch)
                tag["release_date"] = data["committer"]["date"]
            elif tag["object"]["type"] == "tag":
                rc, data = gh.repos[user][repo].git.tags[
                    tag["object"]["sha"]].get(sha=branch)
                tag["release_date"] = data["tagger"]["date"]
            else:
                raise BuildError("unknown tag type")

        # the search api is marked as beta,
        # thats why we have to do the following:
        old_accept = gh.client.default_headers["accept"]
        gh.client.default_headers[
            "accept"] = 'application/vnd.github.cloak-preview'

        # get merge commits since last release
        page = 1
        future_release = []
        while page > 0:
            rc, data = gh.search.issues.get(
                sha=branch,
                per_page=100,
                page=page,
                q=(
                    'type:pr merged:>' + all_tags[-1]["release_date"]
                    + ' user:' + user
                    + ' repo:' + repo
                    + ' -label:internal'
                ),
            )
            data["items"].reverse()
            future_release.extend(data["items"])
            page = NextPage(gh)

        # undo the beta api patch
        gh.client.default_headers["accept"] = old_accept

        # now filter and group the pull requests
        title_notice = "Important changes for plugin developers"
        title_enhancement = "Enhancements"
        title_bug = "Fixed bugs"
        title_other = "Other changes"
        prs = OrderedDict()
        prs[title_notice] = []
        prs[title_enhancement] = []
        prs[title_bug] = []
        prs[title_other] = []

        for pr in future_release:
            labels = [l["name"] for l in pr["labels"]]
            if "notice" in labels:
                prs[title_notice].append(pr)
            elif "enhancement" in labels:
                prs[title_enhancement].append(pr)
            elif any(lbl in ["bug", "bugfix"] for lbl in labels):
                prs[title_bug].append(pr)
            else:
                prs[title_other].append(pr)

        # prepare the grouped output
        build_date = strftime("%Y-%m-%d", localtime(build_setup.build_time))
        release_url = "https://github.com/{0}/{1}/releases/tag/v{2}".format(
            user, repo, build_setup.app_version
        )
        changes = dict(
            md=["## [{0}]({1}) ({2})\n".format(
                build_setup.appVersion,
                release_url,
                build_date
            )],
            bb=["[size=150][b][url={0}]{1}[/url] ({2})[/b][/size]\n".format(
                release_url,
                build_setup.app_version,
                build_date
            )]
        )
        print "## {0} ({1})".format(build_setup.appVersion, build_date)
        for title, items in prs.items():
            if items:
                changes['md'].append("\n**{0}:**\n\n".format(title))
                changes['bb'].append("\n[b]{0}:[/b]\n[list]\n".format(title))
                print "\n{0}:\n".format(title)
                for pr in items:
                    changes['md'].append(
                        "* {0} [\#{1}]({2}) ([{3}]({4}))\n".format(
                            EscapeMarkdown(pr["title"]),
                            pr["number"],
                            pr["html_url"],
                            EscapeMarkdown(pr["user"]["login"]),
                            pr["user"]["html_url"],
                        )
                    )
                    changes['bb'].append(
                        "[*] {0} [url={1}]{2}[/url] "
                        "([url={3}]{4}[/url])\n".format(
                            pr["title"],
                            pr["html_url"],
                            pr["number"],
                            pr["user"]["html_url"],
                            EscapeMarkdown(pr["user"]["login"])
                        )
                    )
                    print u"* {0} #{1} ({2})".format(
                        pr["title"],
                        pr["number"],
                        pr["user"]["login"],
                    )
                changes['bb'].append("[/list]")

        if len(changes['md']) == 1:
            text = "\nOnly minor changes in this release.\n"
            changes['md'].append(text)
            changes['bb'].append(text)
            print text.strip()

        # write a changelog file in bbcode for the news section in forum
        changes['bb'].append(
            "\n\n[size=110][url=https://github.com/EventGhost/EventGhost/"
            "releases/download/v{0}/EventGhost_{0}_Setup.exe]Download now"
            "[/url][/size]\n".format(build_setup.appVersion)
        )
        try:
            fn = join(build_setup.outputDir, "CHANGELOG_THIS_RELEASE.bb")
            out = codecs.open(fn, "w", "utf8")
            out.writelines(changes['bb'])
            out.close()
        except:
            pass

        # write a file with current changes in markdown for release description
        try:
            fn = join(build_setup.outputDir, "CHANGELOG_THIS_RELEASE.md")
            out = codecs.open(fn, "w", "utf8")
            out.writelines(changes['md'][1:])
            out.close()
        except:
            pass

        # and now the full changelog file (in markdown format)
        # read the existing changelog...
        try:
            infile = codecs.open(changelog_path, "r", "utf8")
        except IOError:
            old_changes = ''
        else:
            old_changes = infile.read()
            infile.close()

        # ... and put the new changelog on top
        try:
            outfile = codecs.open(changelog_path, "w+", "utf8")
        except IOError:
            import sys
            import wx
            parent = wx.GetApp().GetTopWindow()

            msg = "CHANGELOG.md couldn't be written.\n({0})".format(
                sys.exc_value
            )
            dlg = wx.MessageDialog(parent, msg, caption="Error",
                                   style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
        else:
            outfile.writelines(changes['md'])
            if old_changes:
                outfile.write('\n\n')
                outfile.write(old_changes)

            outfile.close()




