from cx_Freeze import setup, Executable

import os
import sys
import shutil

base = "Win32GUI"

project_dir = os.path.abspath(os.path.dirname(__file__))
lib_dir = os.path.join(project_dir, "lib")

executables = [
    Executable(
        script="RDMT.py",
        base=base,
        icon=os.path.join(lib_dir, "img", "rdmt.ico"),
        target_name="Red Dead Modding Tool.exe",
        manifest="app.manifest",
    )
]

build_options = {
    "packages": [
        "os",
        "re",
        "sys",
        "uuid",
        "json",
        "time",
        "toml",
        "base64",
        "string",
        "shutil",
        "winreg",
        "zipfile",
        "difflib",
        "requests",
        "patoolib",
        "threading",
        "win32pipe",
        "win32file",
        "subprocess",
        "webbrowser",
        "customtkinter",
        "PIL",
        "xml.etree.ElementTree",
        "pathlib",
        "xml.dom.minidom",
        "tkinter",
        "collections",
        "websocket",
        "cryptography",
        "CTkListbox",
        "CTkToolTip",
        "CTkMessagebox",
        "tklinenums",
        "datetime",
    ],
    "excludes": ["tkinter.test", "unittest", "websocket.policyserver", "websocket.server"],
    "include_files": [
        (lib_dir, "lib"),
    ],
    "include_msvcr": True,
    "build_exe": os.path.join(project_dir, "build"),
}

def after_build(build_dir):
    lib_target_dir = os.path.join(build_dir, "lib", "msvcr")
    os.makedirs(lib_target_dir, exist_ok=True)
    
    msvcr_files = [f for f in os.listdir(build_dir) if f.startswith("api-ms-win") or f.startswith("vcruntime")]
    for dll in msvcr_files:
        dll_path = os.path.join(build_dir, dll)
        shutil.move(dll_path, os.path.join(lib_target_dir, dll))
        
    license_file = os.path.join(build_dir, "frozen_application_license.txt")
    if os.path.exists(license_file):
        os.remove(license_file)

class CustomBuild:
    def __init__(self, build_exe_dir):
        self.build_exe_dir = build_exe_dir

    def run(self):
        after_build(self.build_exe_dir)

setup(
    name="Red Dead Modding Tool",
    version="2.0.1",
    description="Red Dead Modding Tool",
    author="generatedmax - Nexus Mods",
    options={"build_exe": build_options},
    executables=executables
)

if "build" in sys.argv:
    build_dir = os.path.join(project_dir, "build")
    post_build = CustomBuild(build_dir)
    post_build.run()