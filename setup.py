import sys
import os
from cx_Freeze import setup, Executable

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
print (PYTHON_INSTALL_DIR)
os.environ['TCL_LIBRARY'] = r'C:\\Users\\Andy\\AppData\\Local\\Programs\\Python\\Python35\\tcl\\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\\Users\\Andy\\AppData\\Local\\Programs\\Python\\Python35\\tcl\\tk8.6'

options = {
    'build_exe': {
        "includes": ["tkinter"],
        'include_files':[
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
            'resource/'
         ],
    },
}

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('updater.py', base=base)
]

setup(name='simple_Tkinter',
      version='0.1',
      description='Sample cx_Freeze Tkinter script',
      options = options,
      executables=executables
      )
