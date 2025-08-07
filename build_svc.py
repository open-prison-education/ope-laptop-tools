import os


project_name = "OPEService"
current_dir = os.path.dirname(os.path.abspath(__file__))
main_file = os.path.join(current_dir, "opeService", f"{project_name}.py")

# If you get corrupted errors, use this
clean = " --clean "
remove_spec_file = True

spec_file = os.path.join(current_dir, "opeService", f"{project_name}.spec")

# delete the spec file if it exists, to avoid corrupted errors
# a new spec file will be created in the opeService directory using build params
if remove_spec_file and os.path.exists(spec_file):
    os.unlink(spec_file)

#--noconsole
CUSTOM_EVENT_LOG_DLL="" # " --add-data mgmt_EventLogMessages.dll;. "

# All hidden imports used in build params
py_imports = [
    "win32timezone",
    "servicemanager", 
    "simplejson",
    "pathlib",
    "win32service",
    "win32event",
    "win32evtlog",
    "win32ts",
    "win32gui",
    "win32gui_struct",
    "win32con",
    "pythoncom",
    "pyad",
    "pyad.pyad",
    "wmi",
    "winsys",
    "winsys.accounts",
    "winsys.registry",
    "winsys.security",
    "win32api",
    "win32security",
    "win32process",
    "win32profile",
    "win32netcon",
    "win32net",
    "ntsecuritycon",
    "ctypes",
    "threading",
    "subprocess",
    "traceback",
    "collections",
    "random",
    "time",
    "socket",
    "sys",
    "os",
    "shutil",
    "psutil",
    "logging",
    "logging.handlers",
    "colorama",
    "PIL",
    "PIL.Image",
    "PIL.ImageFont",
    "PIL.ImageDraw"
]

hidden_imports_str = " ".join([f"--hidden-import {package}" for package in py_imports])

# Add --specpath flag to put the spec file in the opeService directory
spec_path = os.path.join(current_dir, "opeService")
build_params = (
    "python -m PyInstaller " + clean +
    hidden_imports_str + " --noupx " + 
    f" --add-data {os.path.join(current_dir, 'common')};common " + CUSTOM_EVENT_LOG_DLL +
    f" --add-data {os.path.join(current_dir, 'mgmt')};mgmt" +
    f" --noconfirm --icon {os.path.join(current_dir, 'common', 'logo_icon.ico')}" +
    f" --specpath {spec_path}"
)
# == Build the app for windows using pyinstaller ==
print(build_params)
if os.path.exists(spec_file):
    # Build using the existing spec file
    print("Building w existing spec file...")
    os.system(build_params + " {0}.spec".format(project_name))
else:
    print("Building fresh copy...")
    os.system(build_params + " --name {0} {1}".format(project_name, main_file))

print("Done!")
