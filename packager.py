import os
import hashlib
import json
import gzip
import argparse


class Packager:
    output = {
        "files": {},
        "host": None,
        "version": None
    }
    hosts = {
        "odin": "http://odin.nordinvasion.com/mod",
        "thor": "http://thor.nordinvasion.com/mod"
    }
    input_dir = None
    output_dir = None
    output_file = None
    exclude_items = [".git", ".revision"]

    def __init__(self):
        # Set up the accepted arguments
        parser = argparse.ArgumentParser(description="NI Update Packager Args")
        parser.add_argument("-i", "--input", help="Input Directory", required=True)
        parser.add_argument("-o", "--output", help="Output Directory", required=True)
        parser.add_argument("-v", "--version", help="Module Version", required=True)
        parser.add_argument("-H", "--host", help="Host Name", required=True)
        parser.add_argument("-f", "--file", help="File Name", required=False)
        # Store the arguments
        args = parser.parse_args()
        self.input_dir = os.path.abspath(args.input)
        self.output_dir = os.path.abspath(args.output)
        self.output["version"] = args.version
        if args.file:
            self.output_file = args.file
        else:
            self.output_file = "master.json"
        if args.host:
            if args.host in self.hosts:
                self.output["host"] = self.hosts[args.host]
            else:
                print("Error: The host " + args.host + " does not exist!")
        else:
            if len(self.hosts) is 1:
                self.output["host"] = list(self.hosts.values())[0]
                exit()
            else:
                print("Error: The host must be specified!")
                exit()
        # Begin standard operations
        self.check_input_dir()
        self.check_output_dir()
        self.process_dir(self.input_dir)
        self.create_output_file()

    def check_input_dir(self):
        # Check that the input directory exists
        if not os.path.exists(self.input_dir):
            print("Error: Input directory " + self.input_dir + " does not exist!")
            exit()

    def check_output_dir(self):
        # Check that the output directory exists
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        if not os.path.exists(os.path.join(self.output_dir, self.output["version"])):
            os.mkdir(os.path.join(self.output_dir, self.output["version"]))

    def compress_file(self, path):
        # Compress the file and put it in the output directory
        original_file = open(path, "rb")
        relative_path = os.path.relpath(path, self.input_dir)
        print("Compressing " + relative_path)
        gz_file = gzip.open(os.path.join(self.output_dir, self.output["version"], relative_path + ".gz"), "wb")
        gz_file.writelines(original_file)
        gz_file.close()
        original_file.close()

    def create_output_file(self):
        # Save the hashes to a file
        file = open(os.path.join(self.output_dir, self.output_file), "wt")
        file.write(json.dumps(self.output, separators=(",", ":"), sort_keys=True, indent=4))
        file.close()
        print("Hash generation complete.")
        exit()

    def process_dir(self, path):
        # Loop through the input directory to generate hashes
        for item in os.listdir(path):
            if item in self.exclude_items:
                continue
            absolute_path = os.path.join(path, item)
            relative_path = os.path.relpath(absolute_path, self.input_dir)
            if os.path.isdir(absolute_path):
                output_path = os.path.join(self.output_dir, self.output["version"], relative_path)
                if not os.path.exists(output_path):
                    os.mkdir(output_path)
                self.process_dir(absolute_path)
            else:
                file_hash = generate_hash(absolute_path)
                self.record_hash(relative_path, file_hash)
                self.compress_file(absolute_path)

    def record_hash(self, relative_path, file_hash):
        # Record a file's hash to the output array
        path = split_path(relative_path)
        _current_key = self.output["files"]
        for i in range(len(path)):
            if not path[i] in _current_key:
                _current_key[path[i]] = {}
            _current_key = _current_key[path[i]]
        _current_key["hash"] = file_hash


def generate_hash(path):
    # Return the hash of the file
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()


def split_path(path):
    # Split a path into an array of directories
    path = os.path.normcase(path)
    return path.split(os.path.sep)

Packager()
