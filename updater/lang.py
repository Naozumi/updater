# -*- coding: utf-8 -*-
import configparser
import os


class LanguageHandler:
    __languages = []
    lang_name = ""
    lang_code = ""
    # [
    #     ("eng", "English"),
    #     ("fre", "Français"),
    #     ("ger", "Deutsch"),
    #     ("ita", "Italiano"),
    #     ("nor", "Norsk"),
    #     ("rus", "Русский"),
    #     ("spa", "Español")
    # ]

    def __init__(self, lang_dir, lang):
        self.lang_dir = lang_dir
        self.lang = configparser.ConfigParser()
        self.lang.read(os.path.join(self.lang_dir, lang + ".ini"), encoding="utf8")
        self.lang_name = self.__get("Header", "name")
        self.lang_code = self.__get("Header", "code")

    def get_language_list(self):
        """Get a list of language files present"""
        __lang = configparser.ConfigParser()
        # Only scan the folder if there is not already a list of languages
        if not self.__languages:
            for file in os.listdir(os.path.join(self.lang_dir)):
                # The language code is the file name
                code = os.path.splitext(os.path.basename(file))[0]
                # Load the language file to get the name
                __lang.read(os.path.join(self.lang_dir, code + ".ini"), encoding="utf8") #cp1250
                name = __lang.get("Header", "name", fallback=None)
                # Only append the language if a code and name were found
                if code and name:
                    self.__languages.append((code, name))
        # Return the list of languages
        return self.__languages

    def __get(self, section, key, *args):
        key = str(key)
        string = self.lang.get(section, key, fallback="<{0}:{1} not found>".format(section, key))
        return string.format(*args)

    def act_check_updates(self):
        return self.__get("Action", "1")

    def act_launch_mod(self, module_name):
        return self.__get("Action", "2", module_name)

    def act_select_module_dir(self):
        return self.__get("Action", "3")

    def act_open_mod_dir(self):
        return self.__get("Action", "4")

    def act_exit(self):
        return self.__get("Action", "5")

    def act_install(self, path):
        return self.__get("Action", "6", path)

    def act_install_custom(self):
        return self.__get("Action", "7")

    def act_about(self):
        return self.__get("Action", "8")

    def men_file(self):
        return self.__get("Menu", "1")

    def men_language(self):
        return self.__get("Menu", "2")

    def men_channel(self):
        return self.__get("Menu", "3")

    def men_debug(self):
        return self.__get("Menu", "4")

    def men_help(self):
        return self.__get("Menu", "5")

    def sta_ready(self):
        return self.__get("Status", "1")

    def sta_waiting_on_user(self):
        return self.__get("Status", "2")

    def sta_error_hash(self):
        return self.__get("Status", "3")

    def sta_checking_version(self):
        return self.__get("Status", "4")

    def sta_checking_files(self):
        return self.__get("Status", "5")

    def sta_already_updated(self):
        return self.__get("Status", "6")

    def sta_download_progress(self, files_completed, files_total):
        return self.__get("Status", "7", files_completed, files_total)

    def sta_download_complete(self, files_downloaded):
        return self.__get("Status", "8", files_downloaded)

    def sta_lang_changed(self):
        return self.__get("Status", "9", self.lang_name)

    def tex_about(self, module_name, updater_version):
        return self.__get("Text", "1", module_name, updater_version, module_name)

    def tex_version_available(self, module_name, module_version):
        return self.__get("Text", "2", module_name, module_version)

    def tex_error_download(self, error_count):
        return self.__get("Text", "7", error_count)

    def tex_error_hash(self):
        return self.__get("Text", "3")

    def tex_enter_password(self):
        return self.__get("Text", "4")

    def tex_select_directory(self):
        return self.__get("Text", "5")

    def tex_self_update(self, new_version):
        return self.__get("Text", "8", new_version)

    def tex_invalid_directory(self):
        return self.__get("Text", "6")

    def title_normal(self, module_name):
        return self.__get("Title", "1", module_name)

    def title_about(self, module_name):
        return self.__get("Title", "2", module_name)

    def title_error(self, module_name):
        return self.__get("Title", "3", module_name)

    def title_updates(self, module_name):
        return self.__get("Title", "4", module_name)

    def title_auth(self, module_name):
        return self.__get("Title", "5", module_name)
