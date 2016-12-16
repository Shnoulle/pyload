# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals

from builtins import str
from builtins import pypath
from past.builtins import basestring
import subprocess
from os import listdir, access, X_OK, makedirs
from os.path import join, exists, basename, abspath


from pyload.plugins.addon import Addon, add_event_listener
from pyload.utils.fs import safe_join


class ExternalScripts(Addon):
    __name__ = "ExternalScripts"
    __version__ = "0.23"
    __description__ = """Run external scripts"""
    __config__ = [("activated", "bool", "Activated", True)]
    __author_name__ = ("mkaay", "RaNaN", "spoob")
    __author_mail__ = ("mkaay@mkaay.de", "ranan@pyload.net", "spoob@pyload.net")


    def activate(self):
        self.scripts = {}

        folders = ['download_preparing', 'download_finished', 'package_finished',
                   'before_reconnect', 'after_reconnect', 'extracting_finished',
                   'all_dls_finished', 'all_dls_processed']

        for folder in folders:
            self.scripts[folder] = []

            self.init_plugin_type(folder, join(pypath, 'scripts', folder))
            self.init_plugin_type(folder, join('scripts', folder))

        for script_type, names in self.scripts.items():
            if names:
                self.log_info((_("Installed scripts for %s: ") % script_type) + ", ".join([basename(x) for x in names]))

    def init_plugin_type(self, folder, path):
        if not exists(path):
            try:
                makedirs(path)
            except Exception:
                self.log_debug("Script folder %s not created" % folder)
                return

        for f in listdir(path):
            if f.startswith("#") or f.startswith(".") or f.startswith("_") or f.endswith("~") or f.endswith(".swp"):
                continue

            if not access(join(path, f), X_OK):
                self.log_warning(_("Script not executable:") + " %s/%s" % (folder, f))

            self.scripts[folder].append(join(path, f))

    def call_script(self, script, *args):
        try:
            cmd = [script] + [str(x) if not isinstance(x, basestring) else x for x in args]
            self.log_debug("Executing %(script)s: %(cmd)s" % {"script": abspath(script), "cmd": " ".join(cmd)})
            #output goes to pyload
            subprocess.Popen(cmd, bufsize=-1)
        except Exception as e:
            self.log_error(_("Error in %(script)s: %(error)s") % {"script": basename(script), "error": str(e)})

    def download_preparing(self, pyfile):
        for script in self.scripts['download_preparing']:
            self.call_script(script, pyfile.pluginname, pyfile.url, pyfile.fid)

    def download_finished(self, pyfile):
        for script in self.scripts['download_finished']:
            self.call_script(script, pyfile.pluginname, pyfile.url, pyfile.name,
                            safe_join(self.config['general']['download_folder'],
                                      pyfile.package().folder, pyfile.name), pyfile.fid)

    def package_finished(self, pypack):
        for script in self.scripts['package_finished']:
            folder = self.config['general']['download_folder']
            folder = safe_join(folder, pypack.folder)

            self.call_script(script, pypack.name, folder, pypack.password, pypack.pid)

    def before_reconnecting(self, ip):
        for script in self.scripts['before_reconnect']:
            self.call_script(script, ip)

    def after_reconnecting(self, ip):
        for script in self.scripts['after_reconnect']:
            self.call_script(script, ip)

    @add_event_listener("extracting:finished")
    def extracting_finished(self, folder, fname):
        for script in self.scripts["extracting_finished"]:
            self.call_script(script, folder, fname)

    @add_event_listener("download:allFinished")
    def all_downloads_finished(self):
        for script in self.scripts["all_dls_finished"]:
            self.call_script(script)

    @add_event_listener("download:allProcessed")
    def all_downloads_processed(self):
        for script in self.scripts["all_dls_processed"]:
            self.call_script(script)
