import ctypes
import os
import shutil
import sys
import win32com.client
import winreg

MOVEFILE_DELAY_UNTIL_REBOOT = 4


class SetupHandler:

    def __init__(self, module_name, logging, *, file=None, path=None, publisher=None, version=None, url=None):
        """Initialize the class with options"""
        self.log = logging
        self.log.debug("SetupHandler", module_name, file, path, publisher, version, url, func=True)
        self.__module_name = module_name
        # Optional values
        if file and path and publisher and version and url:
            self.__file = file
            self.__path = os.path.normpath(path)
            self.__publisher = publisher
            self.__url = url
            self.__version = version
        # Internal values
        self.__registry_uninstall_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        self.__script_name = module_name + " Updater"
        self.__start_menu_shortcut_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows",
                                                       "Start Menu", "Programs", self.__script_name + ".lnk")

    def create_files(self):
        """Copy the updater to the destination folder"""
        self.log.debug("create_files", func=True)
        destination = None
        # Determine the current path and the destination path
        try:
            source = sys.argv[0]
            script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
            destination = os.path.normpath(os.path.join(self.__path, script_name + ".exe"))
            self.log.info("Installing to " + destination + " from " + source)
            shutil.copy(source, destination)
        except OSError as e:
            self.log.error(str(e.args), tb=True)
        return destination

    def create_start_menu_shortcut(self, target, working_dir="", icon=None):
        """Create a new shortcut in the start menu"""
        self.log.debug("create_start_menu_shortcut", target, working_dir, icon, func=True)
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(self.__start_menu_shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = working_dir
        if icon:
            shortcut.IconLocation = icon
        shortcut.save()
        return

    def create_registry_uninstall_entry(self):
        """Create the uninstall entry"""
        self.log.debug("create_registry_uninstall_entry", func=True)
        reg_path = self.__registry_uninstall_path + "\\" + self.__script_name
        # reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        try:
            self.log.debug("Open the uninstall key: " + reg_path)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS)
        except OSError:
            self.log.debug("Uninstall key does not exist.  Create it.")
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_path)
        try:
            self.log.debug("Set uninstall key values.")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(self.__path, self.__file))
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, self.__script_name)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, self.__version)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.__path)
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, self.__publisher)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                              os.path.join(self.__path, self.__file + " --uninstall"))
            winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, self.__url)
            winreg.CloseKey(key)
        except OSError as e:
            self.log.error("Error registering uninstall entry\n" + str(e.args), tb=True)
        return

    @staticmethod
    def create_uninstall_bat():
        script_dir = os.path.dirname(sys.argv[0])
        with open(os.path.join(script_dir, "_uninstall.bat"), 'w') as file:
            cmd = "@ECHO OFF\n" \
                  "TASKKILL /F /IM \"updater.exe\" >null 2>&1\n" \
                  "del \"{0}\"\n" \
                  "del \"{1}\"\n" \
                  "echo Updater uninstall complete.\n" \
                  "echo.\n" \
                  "echo Press any key to exit..." \
                  "pause >null 2>&1\n" \
                  "DEL \"%~f0\"".format(os.path.join(script_dir, "updater.exe"),
                                        os.path.join(script_dir, "updater.log"))
            file.write(cmd)

    def remove_files(self):
        """Remove the script files"""
        self.log.debug("remove_files", func=True)
        script_dir = os.path.dirname(sys.argv[0])
        try:
            os.remove(os.path.join(script_dir, "updater.ini"))
        except FileNotFoundError:
            self.log.info("updater.ini not found")
        # try:
        #     ctypes.windll.kernel32.MoveFileExA(os.path.join(script_dir, "updater.log"), None,
        #                                        MOVEFILE_DELAY_UNTIL_REBOOT)
        # except FileNotFoundError as e:
        #     self.log.error("updater.log not found\n" + str(e.args), tb=True)
        # try:
        #     ctypes.windll.kernel32.MoveFileExA(os.path.join(script_dir, self.__file), None,
        #                                        MOVEFILE_DELAY_UNTIL_REBOOT)
        # except FileNotFoundError as e:
        #     self.log.error(self.__file + " not found\n" + str(e.args), tb=True)
        return

    def remove_registry_uninstall_entry(self):
        """Remove the uninstall entry"""
        self.log.debug("remove_registry_uninstall_entry", func=True)
        try:
            reg_path = self.__registry_uninstall_path
            self.log.debug("Open the uninstall registry key and delete it: " + reg_path)
            key = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteKey(key, self.__script_name)
            winreg.CloseKey(key)
        except OSError as e:
            self.log.info("Uninstall registry key not found.")
        except Exception as e:
            self.log.error("Unexpected error removing uninstall registry keys.")
        return

    def remove_start_menu_shortcut(self):
        """Remove the shortcut in the start menu"""
        self.log.debug("remove_start_menu_shortcut", func=True)
        try:
            os.remove(self.__start_menu_shortcut_path)
        except FileNotFoundError as e:
            self.log.info(e.args[1] + ": Start menu shortcut")
        return
