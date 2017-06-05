import os
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
base_path = r"C:\Users\Dela\AppData\Local\Programs\Python\Python36-32"
os.environ['TCL_LIBRARY'] = base_path + r"\tcl\tcl8.6"
os.environ['TK_LIBRARY'] = base_path + r"\tcl\tk8.6"
include_files = [base_path + r"\DLLs\tcl86t.dll", \
                 base_path + r"\DLLs\tk86t.dll"]
include_packages = ["os","sys"]
build_exe_options = {"packages": include_packages, "include_files": include_files}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "ProgressTwinCatScanner",
        version = "0.1",
        description = "Get some basic info",
        options = {"build_exe": build_exe_options},
        executables = [Executable("app.py", base=base)])