import os
import sys
from cx_Freeze import setup, Executable

#usage : python setup.py build

# Dependencies are automatically detected, but it might need fine tuning.
base_path = "" # example is C:\Users\Dela\AppData\Local\Programs\Python\Python36-32
working_directory = os.getcwd()
print(sys.path)
for current_path in sys.path:
    if (len(current_path) < len(base_path) or base_path == "") and len(current_path) > 0 and current_path != working_directory and "Python" in current_path:
        base_path = current_path
os.environ['TCL_LIBRARY'] = base_path + r"\tcl\tcl8.6"
os.environ['TK_LIBRARY'] = base_path + r"\tcl\tk8.6"
include_files = [base_path + r"\DLLs\tcl86t.dll", \
                 base_path + r"\DLLs\tk86t.dll"]
include_packages = ["os", "sys"]
exclude_packages = ["email", "http", "logging", "pydoc_data", "unittest", "urllib", "xml"]
build_exe_options = {"packages": include_packages, "include_files": include_files, "excludes": exclude_packages}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "ProgressTwinCatScanner",
        version = "0.1",
        description = "Get some basic info",
        options = {"build_exe": build_exe_options},
        executables = [Executable("twincatscannergui.py", base=base)])