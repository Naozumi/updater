import certifi
import json
import os.path
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request


class UpdateHandler:

    def __init__(self, logging):
        self.log = logging
        self.update_address = None

        self.script_path = sys.argv[0]
        self.script_dir, self.script_name = os.path.split(self.script_path)

        self.ssl_context = ssl.create_default_context()
        self.ssl_context.load_verify_locations(certifi.where())

    def get_version_available(self, address):
        """Get information about the latest version of the updater.

        :return str: Updater version
        """
        self.log.debug("get_version_available", address, func=True)
        request = urllib.request.Request(address)
        try:
            with urllib.request.urlopen(request) as r:
                updater = json.loads(r.read().decode("utf-8"))
                self.update_address = updater["address"]
                return updater["version"]
        except urllib.error.HTTPError as e:
            self.log.error(str(e.code) + ": " + e.reason, tb=True)

    def get_update(self):
        """ Download the latest version of the updater.

        :return:
        """
        self.log.debug("get_update", func=True)
        data = urllib.request.urlopen(self.update_address, context=self.ssl_context).read()
        self.log.debug("downloaded updater")
        output_path = os.path.join(self.script_dir, "_" + self.script_name)
        with open(output_path, 'wb') as file:
            self.log.debug("opened a local file")
            file.write(data)
            self.log.debug("wrote the data")
            file.close()
        return

    def launch_update(self):
        """ Launch the script in update mode.

        :return:
        """
        self.log.debug("launch_update", func=True)
        subprocess.Popen(os.path.join(self.script_dir, "_" + self.script_name) + " --update", cwd=self.script_dir)
        return

    def install_update(self):
        """ Remove the original script, copy this script in its place, and run the new script with the cleanup argument.

        :return:
        """
        self.log.debug("install_update", func=True)
        actual_script_path = os.path.join(self.script_dir, self.script_name[1:])
        os.remove(actual_script_path)
        shutil.copy(self.script_path, actual_script_path)
        subprocess.Popen(actual_script_path + " --cleanup-update", cwd=self.script_dir)
        return

    def cleanup(self):
        """ Remove the old update script.

        :return:
        """
        self.log.debug("cleanup", func=True)
        installer_path = os.path.normpath(os.path.join(self.script_dir, "_" + self.script_name))
        if os.path.exists(installer_path):
            os.remove(installer_path)
        if os.path.exists(installer_path.replace(".exe", ".log")):
            os.remove(installer_path.replace(".exe", ".log"))
        return
