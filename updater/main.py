# -*- coding: utf-8 -*-
import argparse
import json
import os
import winreg
import PIL.Image
import PIL.ImageTk
import queue
import subprocess
import threading
import time
from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.ttk
import updater.cfg
import updater.hash
import updater.lang
import updater.log
# import updater.setup
import updater.update
import urllib.error
import urllib.parse
import urllib.request



class Main:
    # Tk master window
    master = None
    main_frame = None
    main_image = None
    # Tk master status bar
    status_frame = None
    status_label = None
    progress = None
    # Tk master menus
    main_menu = None
    file_menu = None
    language_menu = None
    channel_menu = None
    debug_menu = None
    help_menu = None
    # Tk buttons
    update_button = None
    # Tk master menu status variables
    channel = None
    logging_level = None
    language = None
    status = None

    def __init__(self):
        """Initialize the program"""

        # Calculate script path information
        self.working_dir = os.getcwd()
        self.script_path = os.path.dirname(sys.argv[0])
        self.script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.working_dir_valid = False
        os.chdir(self.working_dir)

        # Load user config
        self.cfg = updater.cfg.ConfigHandler(os.path.join(self.script_path, self.script_name + ".ini"))

        # Initialize empty objects
        self.hash_handler = None
        self.backend_queue = queue.Queue()
        self.backend_thread = threading.Thread(target=self.process_backend_queue, daemon=True)
        self.backend_thread.start()

        # Set the logging options
        self.log = updater.log.Logger(os.path.join(self.script_path, self.script_name + ".log"),
                                      logging_level=self.cfg.logging_level())
        sys.excepthook = self.log.unhandled
        self.log.debug("Updater Launched - " + self.cfg.updater_version())

        # Parse any arguments passed in
        parser = argparse.ArgumentParser(description=self.cfg.module_name() + " Updater Args")
        parser.add_argument("--cleanup-installer", dest="installer_path",
                            help="Cleanup the installation files at the provided path")
        parser.add_argument("--cleanup-updater", dest="cleanup_update", action="store_true",
                            help="Cleanup the update files in the script's current directory")
        parser.add_argument("-l", "--language", dest="language",
                            help="The language to launch the updater with")
        parser.add_argument("--uninstall", dest="uninstall", action="store_true",
                            help="Trigger the uninstall routine")
        parser.add_argument("--update", dest="update", action="store_true",
                            help="Trigger the update installation routine")
        self.args = parser.parse_args()

        # Check if an old file needs to be removed
        if self.args.installer_path and matches_mask(self.args.installer_path, self.script_name + ".exe"):
            try:
                if os.path.exists(self.args.installer_path):
                    os.remove(self.args.installer_path)
                self.log.debug("Removed installer")
                if os.path.exists(os.path.splitext(self.args.installer_path)[0] + ".log"):
                    os.remove(os.path.splitext(self.args.installer_path)[0] + ".log")
                self.log.debug("Removed installer log")
                if self.args.language and not self.args.language == self.cfg.language():
                    self.log.debug("Attempt to set language")
                    self.cfg.language(set_value=self.args.language)
                self.log.debug("Set language")
            except:
                self.log.error("Unknown error cleaning up installation files", tb=True)

        # Check if the update installation routine has been called
        if self.args.update:
            try:
                self.log.debug(self.script_name.strip("_") + ".exe")
                while process_exists(self.script_name.strip("_") + ".exe"):
                    time.sleep(1)
                update_handler = updater.update.UpdateHandler(self.log)
                update_handler.install_update()
            except:
                self.log.error("Unknown error in update routine", tb=True)
            sys.exit()

        # Check if the update cleanup routine has been called
        if self.args.cleanup_update:
            try:
                self.log.info("cleanup update")
                while process_exists("_" + self.script_name + ".exe"):
                    time.sleep(1)
                update_handler = updater.update.UpdateHandler(self.log)
                update_handler.cleanup()
                if self.working_dir_valid:
                    self.backend_queue.put(self.check_for_updates)
            except:
                self.log.error("Unknown error cleaning up self-update files", tb=True)

        # Check if the uninstall routine has been called
        # if self.args.uninstall:
        #     try:
        #         setup = updater.setup.SetupHandler(self.cfg.module_name(), self.log)
        #         setup.remove_start_menu_shortcut()
        #         setup.remove_registry_uninstall_entry()
        #         setup.remove_files()
        #         setup.create_uninstall_bat()
        #         subprocess.Popen(os.path.join(self.script_path, "_uninstall.bat"))
        #     except:
        #         self.log.error("Unknown error during uninstall routine", tb=True)
        #     sys.exit()

        # Set the language options
        self.lang = updater.lang.LanguageHandler(resource_path("lang"), self.cfg.language(default=self.args.language))

        # Determine if the current directory is valid
        if matches_mask(self.working_dir, self.cfg.modules_dir_mask() + r"\\" + self.cfg.module_name()):
            self.working_dir_valid = True
        else:
            self.working_dir_valid = False

        # Initialize tk
        self.init_tk_window()
        self.init_tk_menus()
        self.init_tk_status_bar()
        if self.working_dir_valid:
            self.init_tk_buttons_update()
        else:
            self.init_tk_buttons_install()
        self.load_launcher_image()

        self.master.mainloop()

    # === Tk related methods ===========================================================================================

    def init_tk_window(self):
        """Initialize the master tk window with its core properties, a main frame, and a blank image."""
        # Setup the tkinter window
        self.master = Tk()
        icon_path = resource_path("favicon.ico")
        self.master.iconbitmap(icon_path)
        self.master.resizable(0, 0)
        self.master.protocol("WM_DELETE_WINDOW", self.exit)
        self.master.title(self.lang.title_normal(self.cfg.module_name()))
        self.master.option_add("*tearOff", False)
        self.master.bind("<Control-Key-l>", lambda e: self.display_auth_prompt())
        self.main_frame = tkinter.ttk.Frame(self.master, padding="0")
        self.main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.main_image = tkinter.ttk.Label(self.main_frame, padding="0")
        self.main_image.grid(column=0, row=0, sticky=(N, W, E, S))

    def init_tk_menus(self):
        """Setup the menu bar."""
        # Set string variables
        self.channel = StringVar()
        self.channel.set(self.cfg.default_channel())
        self.logging_level = StringVar()
        self.logging_level.set(self.cfg.logging_level())
        self.language = StringVar()
        self.language.set(self.cfg.language(default=self.args.language))
        self.status = StringVar()
        self.status.set(self.lang.sta_ready())
        # Build the menu bar
        self.main_menu = Menu(self.master)
        # File menu
        self.file_menu = Menu(self.main_menu)
        self.file_menu.add_command(label=self.lang.act_launch_mod(self.cfg.module_name()), command=self.launch_warband)
        self.file_menu.add_command(label=self.lang.act_check_updates(), command=self.check_for_updates)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.lang.act_select_module_dir(), command=self.display_module_dir_prompt)
        self.file_menu.add_command(label=self.lang.act_open_mod_dir(), command=self.open_module_dir)
        if not self.working_dir_valid:
            self.file_menu.entryconfig(self.lang.act_open_mod_dir(), state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.lang.act_exit(), command=self.exit)
        # Language Menu
        self.language_menu = Menu(self.main_menu)
        for lang_code, lang_name in self.lang.get_language_list():
            self.language_menu.add_radiobutton(label=lang_name, value=lang_code,
                                               variable=self.language, command=self.set_language)
        # Channel menu
        self.channel_menu = Menu(self.main_menu)
        self.channel_menu.add_radiobutton(label="Master/Live", variable=self.channel, value="master")
        # Debug menu
        self.debug_menu = Menu(self.main_menu)
        self.debug_menu.add_radiobutton(label="Debug", value=self.log.DEBUG,
                                        variable=self.logging_level, command=self.set_logging_level())
        self.debug_menu.add_radiobutton(label="Info", value=self.log.INFO,
                                        variable=self.logging_level, command=self.set_logging_level())
        self.debug_menu.add_radiobutton(label="Warning", value=self.log.WARNING,
                                        variable=self.logging_level, command=self.set_logging_level())
        self.debug_menu.add_radiobutton(label="Error", value=self.log.ERROR,
                                        variable=self.logging_level, command=self.set_logging_level())
        self.debug_menu.add_radiobutton(label="Critical", value=self.log.CRITICAL,
                                        variable=self.logging_level, command=self.set_logging_level())
        # Help menu
        self.help_menu = Menu(self.main_menu)
        self.help_menu.add_command(label=self.lang.act_about(), command=self.display_about)
        self.master.config(menu=self.main_menu)
        self.main_menu.add_cascade(label=self.lang.men_file(), menu=self.file_menu)
        self.main_menu.add_cascade(label=self.lang.men_language(), menu=self.language_menu)
        if self.cfg.display_channel_menu():
            self.main_menu.add_cascade(label=self.lang.men_channel(), menu=self.channel_menu)
        if self.cfg.display_debug_menu():
            self.main_menu.add_cascade(label=self.lang.men_debug(), menu=self.debug_menu)
        self.main_menu.add_cascade(label=self.lang.men_help(), menu=self.help_menu)

    def init_tk_status_bar(self):
        """Setup the status bar and all it's elements."""
        self.status_frame = tkinter.ttk.Frame(self.main_frame)
        self.status_label = tkinter.ttk.Label(self.status_frame, textvariable=self.status)
        self.status_label.pack(side=LEFT)
        self.progress = tkinter.ttk.Progressbar(self.status_frame, mode="determinate", length=100)
        self.progress.pack(side=RIGHT)
        self.status_frame.grid(column=0, row=2, sticky=(W, E))

    def init_tk_buttons_install(self):
        """Setup the buttons for each installation option."""
        module_dir_options = self.get_installation_dir_options()
        # Add the directory selection options
        buttons = []
        for i, module_dir in enumerate(module_dir_options):
            label, path = module_dir
            path = os.path.join(path, self.cfg.module_name())
            buttons.append(Button(self.main_frame, text=self.lang.act_install(label),
                                  command=lambda _path=path: self.set_module_dir(_path),
                                  font=("Trebuchet MS", 10), bg="maroon", fg="white", width=45, height=1))
            buttons[i].place(rely=1, x=172, y=-34 * (i + 2) + 4, anchor=S)
        # Add the custom selection option
        location_select_button = Button(self.main_frame, text=self.lang.act_install_custom(),
                                        command=self.display_module_dir_prompt,
                                        font=("Trebuchet MS", 10), bg="maroon", fg="white", width=45, height=1)
        location_select_button.place(rely=1, x=172, y=-30, anchor=S)

    def init_tk_buttons_update(self):
        """Setup the button for updating."""
        self.update_button = Button(self.main_frame, text=self.lang.act_check_updates(),
                                    command=lambda: self.backend_queue.put(self.check_for_updates),
                                    font=("Trebuchet MS", 12), bg="maroon", fg="white", width=17, height=1)
        self.update_button.place(relx=1, rely=1, x=-8, y=-30, anchor=SE)

    def display_about(self):
        """Display a gui with information describing the updater"""
        tkinter.messagebox.showinfo(self.lang.title_about(self.cfg.module_name()),
                                    self.lang.tex_about(self.cfg.module_name(), self.cfg.updater_version()))

    def display_auth_prompt(self):
        """Display a prompt for the user's password"""
        password = tkinter.simpledialog.askstring(self.lang.title_auth(self.cfg.module_name()),
                                                  self.lang.tex_enter_password(), show="*")
        channel = self.unlock_channel("", password, self.cfg.auth_server())
        if channel:
            self.cfg.hash_addresses(set_value=(channel["code"], channel["hash_addresses"]))
            self.add_channel(channel["name"], channel["code"])

    def display_download_error(self, error_count):
        """Display a download error instructing the user to try again or get assistance"""
        tkinter.messagebox.showerror(title=self.lang.title_error(self.cfg.module_name()),
                                     message=self.lang.tex_error_download(error_count))

    def display_download_prompt(self, version):
        """Display a prompt asking if the update should be downloaded"""
        return tkinter.messagebox.askyesno(title=self.lang.title_updates(self.cfg.module_name()),
                                           message=self.lang.tex_version_available(self.cfg.module_name(), version))

    def display_hash_file_error(self):
        """Display an error for no hash file being found"""
        self.status.set(self.lang.sta_error_hash())
        tkinter.messagebox.showerror(self.lang.title_updates(self.cfg.module_name()), self.lang.tex_error_hash())
        self.enable_input()
        self.status.set(self.lang.sta_ready())

    def display_module_dir_prompt(self):
        """Click handler for selecting the correct module directory"""
        path = "/"
        while True:
            path = tkinter.filedialog.askdirectory(parent=self.master, initialdir=path,
                                                   title=self.lang.tex_select_directory())
            # Check that the path is valid
            if not path:
                break
            elif matches_mask(path, self.cfg.modules_dir_mask()):
                self.set_module_dir(path + r"\\" + self.cfg.module_name(), skip_mask_check=True)
            else:
                tkinter.messagebox.showerror(self.lang.title_updates(self.cfg.module_name()),
                                             self.lang.tex_invalid_directory())

    def display_self_update_prompt(self, version):
        """Display a prompt asking if the updater should be updated"""
        return tkinter.messagebox.askyesno(title=self.lang.title_updates(self.cfg.module_name()),
                                           message=self.lang.tex_self_update(version))

    def disable_input(self):
        """Disable all inputs which could interfere with checking for updates"""
        self.update_button.config(state="disabled")
        for lang in self.lang.get_language_list():
            code, name = lang
            self.language_menu.entryconfig(name, state="disabled")
        self.file_menu.entryconfig(self.lang.act_launch_mod(self.cfg.module_name()), state="disabled")
        self.file_menu.entryconfig(self.lang.act_check_updates(), state="disabled")
        self.file_menu.entryconfig(self.lang.act_select_module_dir(), state="disabled")
        self.master.unbind("<Control-Key-l>")

    def enable_input(self):
        """Enable all the inputs which could have interfered with checking for updates"""
        self.update_button.config(state="normal")
        for lang in self.lang.get_language_list():
            code, name = lang
            self.language_menu.entryconfig(name, state="normal")
        self.file_menu.entryconfig(self.lang.act_launch_mod(self.cfg.module_name()), state="normal")
        self.file_menu.entryconfig(self.lang.act_check_updates(), state="normal")
        self.file_menu.entryconfig(self.lang.act_select_module_dir(), state="normal")
        self.master.bind("<Control-Key-l>", lambda e: self.display_auth_prompt())

    def exit(self):
        """Exit the program properly"""
        self.log.debug("exit", func=True)
        self.master.destroy()
        sys.exit(0)

    def load_launcher_image(self):
        """Load either the local module logo or the embedded logo into an existing tk image object."""
        logo_path = os.path.join(self.working_dir, "main.bmp")
        if not os.path.exists(logo_path):
            logo_path = resource_path("logo.bmp")
        while True:
            try:
                logo = PIL.ImageTk.PhotoImage(PIL.Image.open(logo_path))
                break
            except IOError:
                logo_path = resource_path("logo.bmp")
        self.main_image.config(image=logo)
        self.main_image.logo = logo

    def set_progressbar_pulsing(self):
        """Make the progress bar pulse"""
        self.log.debug("set_progressbar_pulsing", func=True)
        self.progress.configure(mode="indeterminate", maximum=100)
        self.progress.start()

    def set_progressbar_value(self, value=0, maximum=100):
        """Set the progressbar to a specific value"""
        self.log.debug("set_progressbar_value", value, maximum, func=True)
        self.progress.stop()
        self.progress.configure(mode="determinate", value=value, maximum=maximum)

    # === Backend methods ==============================================================================================

    def add_channel(self, name, code):
        """Add another channel to the menu"""
        # Check if the channel menu is visible
        try:
            self.main_menu.index(self.lang.men_channel())
        except TclError:
            self.main_menu.insert_cascade(1, label=self.lang.men_channel(), menu=self.channel_menu)
        # Check if the channel entry already exists
        try:
            self.channel_menu.index(name)
        except TclError:
            self.channel_menu.add_radiobutton(label=name, variable=self.channel, value=code)

    def check_for_updates(self):
        """ Check for updates and download them as needed.

        Check for updates, ask the user whether to proceed, check which files actually need to be updated, and download.
        :return:
        """
        self.log.debug("check_for_updates", func=True)
        self.disable_input()
        # Initialize the check for updates system
        self.status.set(self.lang.sta_checking_version())
        self.set_progressbar_pulsing()
        # Check if the updater has an update available
        self.log.debug("Initialize the UpdateHandler")
        self_updater = updater.update.UpdateHandler(self.log)
        self.log.debug("Get the updater version available")
        updater_version = self_updater.get_version_available(self.cfg.self_update_address())
        self.log.info("Updater " + str(updater_version) + " is available.")
        if not updater_version == self.cfg.updater_version():
            # Ask the user whether to update now
            self.status.set(self.lang.sta_waiting_on_user())
            self.set_progressbar_value()
            self.log.info("Prompt for self update")
            if self.display_self_update_prompt(updater_version):
                # Download and launch the update before exiting
                self.status.set("Downloading update")
                self.set_progressbar_pulsing()
                self.log.debug("Self update confirmed")
                self_updater.get_update()
                self_updater.launch_update()
                self.exit()
            else:
                # Set the status bar back to checking for updates
                self.status.set(self.lang.sta_checking_version())
                self.set_progressbar_pulsing()
                self.log.debug("Self update declined")
        self.hash_handler = updater.hash.HashHandler(addresses=self.cfg.hash_addresses()[self.channel.get()],
                                                     max_attempts=self.cfg.max_download_attempts(),
                                                     logging=self.log)
        # Load the best hash file
        self.hash_handler.download_hash()
        # Check if a hash was not found
        self.status.set(self.lang.sta_waiting_on_user())
        self.set_progressbar_value()
        version = self.hash_handler.get_version()
        if not version:
            self.display_hash_file_error()
            return
        # Check if the user wants to download the version
        download_response = self.display_download_prompt(version)
        if download_response is False:
            self.enable_input()
            self.status.set(self.lang.sta_ready())
            return
        # Validate local files
        self.status.set(self.lang.sta_checking_files())
        self.set_progressbar_pulsing()
        self.hash_handler.build_validate_queue()
        self.hash_handler.start_validating(threads=8, wait=True)
        # Check if there is anything to update
        self.set_progressbar_value()
        if self.hash_handler.download_queue.empty():
            self.enable_input()
            self.status.set(self.lang.sta_already_updated())
            return
        # Download the updated files
        self.__mod_file_download_callback()
        self.hash_handler.start_downloading(threads=2, wait=True, callback=self.__mod_file_download_callback,
                                            destination=self.working_dir)
        self.set_progressbar_value()
        self.status.set(self.lang.sta_download_complete(str(self.hash_handler.downloads_completed_counter)))
        self.load_launcher_image()
        # Display an error if any files failed to download
        if self.hash_handler.get_downloads_failed() > 0:
            self.display_download_error(self.hash_handler.get_downloads_failed())
        self.enable_input()
        return

    def get_installation_dir_options(self):
        """Get a list of common warband module directories that exist on this computer."""
        options = []
        try:
            for drive in self.cfg.drive_letters():
                for module_dir in self.cfg.modules_dir_common():
                    label, path = module_dir
                    full_path = os.path.normpath(os.path.join(drive, path))
                    if os.path.exists(full_path):
                        options.append((drive + label, full_path))
        except:
            self.log.error("Unknown error getting dir options", tb=True)
        return options

    def launch_warband(self):
        """Open the Warband launcher with this mod selected by default"""
        try:
            # Set the default Warband module
            set_last_module_warband(self.cfg.module_name())
            # Launch the Warband launcher
            subprocess.Popen(os.path.join(self.working_dir, "..", "..", "mb_warband.exe"))
        except:
            self.log.error("Unexpected error launching Warband", tb=True)
        # Exit the updater
        self.exit()

    def open_module_dir(self):
        """Click handler for launch Windows Explorer to the currently set module dir"""
        subprocess.Popen("explorer.exe " + self.working_dir)

    def set_language(self):
        """Set the language of the launcher.  Save to a config if installed."""
        if not self.language == self.lang.lang_code:
            try:
                if self.working_dir_valid:
                    self.cfg.language(set_value=self.language.get())
                subprocess.Popen(sys.argv[0] + " -l " + self.language.get(), cwd=self.working_dir)
            except:
                self.log.error("Unexpected error opening the module directory", tb=True)
            self.exit()

    def set_logging_level(self):
        """Set and save the logging level."""
        if not int(self.logging_level.get()) == self.cfg.logging_level():
            if self.working_dir_valid:
                self.cfg.logging_level(set_value=self.logging_level.get())
            self.log.set_level(self.logging_level.get())

    def set_module_dir(self, path, *, skip_mask_check=False):
        """Move the updater to its new location"""
        self.log.debug("set_module_dir", path, func=True)
        # Check that the directory matches the mask
        if not skip_mask_check and not matches_mask(path, self.cfg.modules_dir_mask() + r"\\" + self.cfg.module_name()):
            self.log.error("Invalid module directory: " + path)
            return
        # Create the module directory if needed
        _path = os.path.normpath(path)
        if not os.path.exists(_path):
            self.log.info("Create " + _path)
            os.mkdir(_path)
        # Copy this updater to the new location, run it, and exit
        # setup = updater.setup.SetupHandler(self.cfg.module_name(), self.log,
        #                                   file=self.script_name + ".exe",
        #                                   path=_path,
        #                                   publisher=self.cfg.publisher(),
        #                                   version=self.cfg.updater_version(),
        #                                   url=self.cfg.url())
        # new_file = setup.create_files()
        # setup.create_start_menu_shortcut(new_file, _path)
        # setup.create_registry_uninstall_entry()
        # time.sleep(1)
        # # Build the argument string
        # try:
        #     arguments = " --cleanup-installer " + sys.argv[0]
        #     if self.args.language is not None:
        #         arguments += " -l " + self.args.language
        #     self.log.debug("Launch " + new_file + arguments)
        #     subprocess.Popen(new_file + arguments, cwd=_path)
        # except:
        #     self.log.error("Unexpected error launching installed updater: " + new_file, tb=True)
        self.exit()

    def process_backend_queue(self):
        """Process tasks in the backend queue"""
        while True:
            if not self.backend_queue.empty():
                task = self.backend_queue.get()
                task()
            else:
                time.sleep(1)

    def unlock_channel(self, username, password, address):
        """Attempt to login to the authentication server"""
        data = urllib.parse.urlencode({"username": username, "password": password})
        data = data.encode("utf-8")
        request = urllib.request.Request(address)
        request.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
        try:
            with urllib.request.urlopen(request, data) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self.log.error(str(e.code) + ": " + e.reason, tb=True)

    def __mod_file_download_callback(self):
        self.set_progressbar_value(self.hash_handler.get_downloads_completed(), self.hash_handler.get_downloads_total())
        self.status.set(self.lang.sta_download_progress(str(self.hash_handler.get_downloads_completed()),
                                                        str(self.hash_handler.get_downloads_total())))


def matches_mask(path, mask):
    """Checks to see if the given directory ends with the mask filter"""
    path = os.path.normcase(path)
    mask = mask.lower()
    if re.search(mask, path) is None:
        return False
    else:
        return True


def process_exists(process_name):
    tlcall = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    # shell=True hides the shell window, stdout to PIPE enables
    # communicate() to get the tasklist command result
    tlproc = subprocess.Popen(tlcall, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    # trimming it to the actual lines with information
    tlout = str(tlproc.communicate()[0].strip(), 'UTF-8')
    tlout = tlout.split(u'\r\n')
    # if TASKLIST returns single line without process_name: it's not running
    if len(tlout) > 1 and process_name in tlout[-1]:
        return True
    else:
        return False


def set_last_module_warband(module_name):
    """Set the last Warband module in the registry"""
    reg_path = r"Software\MountAndBladeWarbandKeys"
    try:
        key = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, reg_path, 0, access=winreg.KEY_ALL_ACCESS)
    except OSError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
    winreg.SetValueEx(key, "last_module_warband", 0, winreg.REG_SZ, module_name)
    winreg.CloseKey(key)


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # noinspection PyUnresolvedReferences,PyProtectedMember
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(sys.argv[0])
    return os.path.normpath(os.path.join(base_path, "resource", relative_path))
