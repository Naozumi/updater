import certifi
import hashlib
import json
import time
import os.path
import queue
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
import zlib


class HashHandler:

    hash_dict = None
    hash_addresses = None
    downloads_failed_list = []
    downloads_total_counter = 0
    downloads_completed_counter = 0

    def __init__(self, *, addresses, max_attempts, logging):
        self.log = logging
        self.hash_addresses = addresses
        self.download_queue = queue.Queue()
        self.validate_queue = queue.Queue()

        self.max_attempts = max_attempts

        self.download_callback_lock = threading.Lock()
        self.validate_callback_lock = threading.Lock()

        self.ssl_context = ssl.create_default_context()
        self.ssl_context.load_verify_locations(certifi.where())

    def build_validate_queue(self, path=None, hash_dict=None):
        """ Build the validate queue from a hash dictionary.

        Loop through a hash dictionary to create one entry for each file that needs to be validated.
        If the dictionary entry is a file, generate extra information and store it in the queue entry.
        If the dictionary entry is a directory, pass it back into this function to process its entries.

        :param dict hash_dict: The dictionary to parse
        :param list path: The path of the files in this dictionary
        """
        if not path:
            path = []
        if not hash_dict:
            hash_dict = self.hash_dict["files"]
        for key in hash_dict:
            if "hash" in hash_dict[key]:
                # If a hash is present, fill out the rest of the file info
                hash_dict[key]["attempted"] = 0
                hash_dict[key]["name"] = key
                hash_dict[key]["path"] = str.join("/", path)
                hash_dict[key]["url"] = self.__make_url(self.hash_dict["host"], self.hash_dict["version"],
                                                        hash_dict[key]["path"], hash_dict[key]["name"] + ".gz")
                self.validate_queue.put(hash_dict[key])
            else:
                # If there is no hash, this is a directory which needs to be processed
                dir_path = path.copy()
                dir_path.append(key)
                self.build_validate_queue(dir_path, hash_dict[key])
        return

    def download_hash(self):
        """ Download and store the fastest most recent copy of the hash file.

        Download each hash file in the address list.  Time each download to determine the best option.  Pick the fastest
        download unless it is an older version of the hash file.
        """
        context = ssl.create_default_context()
        context.load_verify_locations(certifi.where())
        # Check each address for hash files
        for address in self.hash_addresses:
            try:
                # Download the hash file and record the download time
                start_time = time.perf_counter()
                request = urllib.request.urlopen(address, context=context)
                download_time = time.perf_counter() - start_time
                # Parse the response into a dictionary
                text = request.read().decode("utf-8")
                hash_dict = json.loads(text)
                # Check if this is the best hash file so far
                if self.hash_dict is None:
                    self.hash_dict = hash_dict
                    continue
                version_diff = self.__compare_versions(self.hash_dict["version"], hash_dict["version"])
                if version_diff > 0:
                    self.log.info("Newer: " + address)
                    self.hash_dict = hash_dict
                    continue
                elif version_diff < 0:
                    self.log.info("Older: " + address)
                    continue
                elif download_time < self.hash_dict["download_time"]:
                    self.log.info("Faster: " + address)
                    self.hash_dict = hash_dict
                    continue
            except urllib.error.HTTPError:
                self.log.error("Hash Download Failed", tb=True)
            except ValueError:
                self.log.error("Invalid Hash", tb=True)
            except:
                self.log.error("Unknown Error", tb=True)
        return

    def get_downloads_failed_list(self):
        """ Getter for the list of failed downloads.

        :return list:
        """
        return self.downloads_failed_list

    def get_downloads_failed(self):
        return len(self.downloads_failed_list)

    def get_downloads_total(self):
        return self.downloads_total_counter

    def get_downloads_completed(self):
        return self.downloads_completed_counter

    def get_downloads_remaining(self):
        return self.downloads_total_counter - self.downloads_completed_counter

    def get_version(self):
        """ Getter for the version of the hash dictionary.

        :return str: version if a hash dictionary is present, otherwise None
        """
        if self.hash_dict:
            return str(self.hash_dict["version"])
        else:
            return None

    def start_downloading(self, *, callback=None, destination=None, threads=1, wait=False):
        """ Spawn file download processing threads.

        :param int threads: The number of concurrent threads to spawn
        :param callable callback: A callback function to run after each download
        :param bool wait: Determines whether to block this function until the download queue is empty
        :return:
        """
        self.downloads_failed_list.clear()
        for i in range(threads):
            t = threading.Thread(target=self.__download_processor, daemon=True,
                                 kwargs={"callback": callback, "destination": destination})
            t.start()
        if wait:
            self.download_queue.join()
        return

    def start_validating(self, *, callback=None, threads=1, wait=False):
        """ Spawn file validation processing threads.

        :param int threads: The number of concurrent threads to spawn
        :param callable callback: A callback function to run after each validation
        :param bool wait: Determines whether to block this function until the validate queue is empty
        :return:
        """
        for i in range(threads):
            t = threading.Thread(target=self.__validate_processor, daemon=True, kwargs={"callback": callback})
            t.start()
        if wait:
            self.validate_queue.join()
        return

    @staticmethod
    def __compare_versions(version1, version2):
        """ Compares two version strings to find which is newer.

        Compares each segment of the version strings individually to see which version is the newest.

        :param str version1: the first version
        :param str version2: the second version (the one to test)
        :return int: 1 for newer, -1 for older, 0 for equal
        """
        # Convert the version strings to lists
        version1_list = version1.split(".")
        version2_list = version2.split(".")
        # Pad the version lists if needed
        max_length = max([len(version1_list), len(version2_list)])
        if len(version1_list) < max_length:
            version1_list += [0] * (max_length - len(version1_list))
        if len(version2_list) < max_length:
            version2_list += [0] * (max_length - len(version2_list))
        # Compare the lists
        for i in range(0, max_length):
            if version2_list[i] > version1_list[i]:
                return 1
            elif version2_list[i] < version1_list[i]:
                return -1
        return 0

    @staticmethod
    def __get_hash(data):
        """ Return the sha1 hash of some data.

        :param data: The data to hash
        :return: The hash
        """
        return hashlib.sha1(data).hexdigest()

    @staticmethod
    def __read_file(file_path):
        """ Open a file and return its contents.

        :param str file_path: The file to read
        :return str: The file contents
        """
        return open(file_path, 'rb').read()

    def __create_path(self, path):
        base = os.path.split(path)[0]
        if not os.path.exists(base):
            self.__create_path(base)
        os.mkdir(path)

    def __save_file(self, data, file_path):
        """ Save data to a file.

        :param data: The data to save
        :param str file_path: The file to save to
        :return:
        """
        folder = os.path.split(file_path)[0]
        if not os.path.exists(folder):
            self.__create_path(folder)
        file = open(file_path, 'wb')
        file.write(data)
        file.close()
        return

    def __validate_file(self, file_path, file_name, file_hash):
        """ Validate that the file matches its hash.

        :param str file_path: The path of the file
        :param str file_name: The name of the file
        :param str file_hash: The hash of the file
        :return bool: True if the file validates, False if it does not
        """
        full_path = os.path.join(file_path, file_name)
        if os.path.exists(full_path) and self.__get_hash(self.__read_file(full_path)) == file_hash:
            return True
        else:
            return False

    def __validate_processor(self, callback=None):
        """ A processor task which keeps checking a queue for more files to validate.

        :param callable callback: A callback function to run after each validation
        """
        # Keep this function running on a timer
        while True:
            # If the queue is empty, wait a while before checking again
            if self.validate_queue.empty():
                time.sleep(1)
            # Get the validation entry
            entry = self.validate_queue.get()
            # If the file does not validate, add it to the download queue
            if not self.__validate_file(entry["path"], entry["name"], entry["hash"]):
                self.download_queue.put(entry)
                self.downloads_total_counter += 1
            # Either way, mark the task as done
            self.validate_queue.task_done()
            if callback and callable(callback):
                with self.validate_callback_lock:
                    callback()

    def __download_file(self, source, destination, validation_hash=None):
        """ Download a file.

        :param str source: The address to download from
        :param str destination: The location to save the file
        :param str validation_hash: The hash to validate against
        :return:
        :raise ValueError: The download integrity could not be validated
        """
        data = urllib.request.urlopen(source, context=self.ssl_context).read()
        if source.endswith(".gz"):
            data = zlib.decompress(data, 15+32)
        if hash and not self.__get_hash(data) == validation_hash:
            raise ValueError
        self.__save_file(data, destination)
        return

    def __download_processor(self, *, callback=None, destination):
        """ A processor task which keeps checking a queue for more files to download.

        :param callable callback: A callback function to run after each download
        """
        # Keep this function running on a timer
        while True:
            # If the queue is empty, wait a while before checking again
            if self.download_queue.empty():
                time.sleep(1)
            # Get the download entry
            entry = self.download_queue.get()
            # Retry the download until a success or an exception handler breaks out
            while True:
                try:
                    # Increment the attempt counter and try to download
                    entry["attempted"] += 1
                    path = os.path.join(destination, entry["path"], entry["name"])
                    self.__download_file(entry["url"], path, entry["hash"])
                    # If you get this far, the download succeeded - break from the retry loop
                    self.downloads_completed_counter += 1
                    break
                except:
                    if entry["attempted"] < self.max_attempts:
                        # Log the exception
                        self.log.warning("Download failed: " + entry["name"], tb=True)
                    else:
                        # If the max number of attempts has been reached, log it and break from the retry loop
                        self.log.error("Download failed: " + entry["name"], tb=True)
                        self.downloads_failed_list.append(entry)
                        break
            # Whether successful or not, this task is now down
            self.download_queue.task_done()
            if callback and callable(callback):
                with self.download_callback_lock:
                    callback()

    @staticmethod
    def __make_url(*args):
        return os.path.join(*args).replace("\\", "/").replace(" ", "%20")

    class DownloadException(Exception):
        pass

    class DownloadValidateException(DownloadException):
        pass

    class DownloadMaxAttemptException(DownloadException):
        pass
