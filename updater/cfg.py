import configparser


class ConfigHandler:

    __module_name = "NordInvasion"
    __updater_version = "0.2.0"
    __publisher = "NordInvasion"
    __url = "https://nordinvasion.com"
    __default_channel = "master"
    __default_language = "eng"

    __auth_server = "https://nordinvasion.com/some-auth-service"

    __hash_addresses = {
        "master": [
            "http://odin.nordinvasion.com/mod/master.json",
            "http://thor.nordinvasion.com/mod/master.json"
        ]
    }
    __max_download_attempts = 3
    __self_update_address = "https://nordinvasion.com/ajax/updater-version.ajax.php"

    __display_channel_menu = False
    __display_debug_menu = True

    __drive_letters = ["C:\\", "D:\\"]
    __modules_dir_mask = r"mount(\&|)blade warband\\modules"
    __modules_dir_common = [
        ("Program Files (x86)\Steam", "Program Files (x86)\\Steam\\steamapps\\common\\MountBlade Warband\\Modules"),
        ("Program Files\Steam", "Program Files\\Steam\\steamapps\\common\\MountBlade Warband\\Modules"),
        ("Program Files (x86)\Warband", "Program Files (x86)\\Mount&Blade Warband\\Modules"),
        ("Program Files\Warband", "Program Files\\Mount&Blade Warband\\Modules"),
    ]

    __default_logging_level = 10

    def __init__(self, cfg_path):
        self.__cfg_path = cfg_path
        self.__cfg = configparser.ConfigParser()
        self.__cfg.read(self.__cfg_path)

    def __get(self, section, option, default=None):
        """Get a value from the external config file"""
        try:
            return self.__cfg.get(section, option, fallback=default)
        except configparser.Error:
            return default

    def __set(self, section, option, value):
        """Set and save a value to the external config file"""
        if not self.__cfg.has_section(section):
            self.__cfg.add_section(section)
        self.__cfg.set(section, option, value)
        with open(self.__cfg_path, "w") as configfile:
            self.__cfg.write(configfile)

    def auth_server(self):
        return str(self.__auth_server)

    def default_channel(self):
        return str(self.__default_channel)

    def display_channel_menu(self):
        return bool(self.__display_channel_menu)

    def display_debug_menu(self):
        return bool(self.__display_debug_menu)

    def drive_letters(self):
        return list(self.__drive_letters)

    def hash_addresses(self, *, set_value=None):
        if set_value:
            key, value = set_value
            self.__hash_addresses[key] = value
        else:
            return dict(self.__hash_addresses)

    def language(self, *, default=None, set_value=None):
        if set_value:
            self.__set("General", "language", set_value)
        else:
            return str(self.__get("General", "language", default if default else self.__default_language))

    def logging_level(self, *, default=None, set_value=None):
        if set_value:
            self.__set("General", "logging", set_value)
        return int(self.__get("General", "logging", default if default else self.__default_logging_level))

    def max_download_attempts(self):
        return int(self.__max_download_attempts)

    def module_name(self):
        return str(self.__module_name)

    def modules_dir_mask(self):
        return str(self.__modules_dir_mask)

    def modules_dir_common(self):
        return list(self.__modules_dir_common)

    def publisher(self):
        return str(self.__publisher)

    def self_update_address(self):
        return str(self.__self_update_address)

    def updater_version(self):
        return str(self.__updater_version)

    def url(self):
        return str(self.__url)
