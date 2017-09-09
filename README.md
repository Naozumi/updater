# NordInvasion Updater

Language: Python 3.6

The packager generates a json file containing an index of all the mod file hashes.

The updater finds the newest hash file and fastest server to download the latest version of NordInvasion.

Requirements:
    Pillow
        https://pypi.python.org/pypi/Pillow/2.9.0
        $ pip install Pillow
    Cerifi
        https://pypi.python.org/pypi/certifi
        $ pip install certifi
    Win32
        https://github.com/pywin32/pypiwin32
        $ pip install pypiwin32
        
Troubleshooting Compile Errors:
    WARNING: file already exists but should not: C:\Users\username\AppData\Local\Temp\_MEI55122\pywintypes34.dll
        Disable Python34\Lib\site-packages\PyInstaller\hooks\hook-pywintypes.py by appending .disabled