from cx_Freeze import setup, Executable
import os

base = "Win32GUI" if os.name == 'nt' else None

project_dir = os.path.abspath(os.path.dirname(__file__))
img_dir = os.path.join(project_dir, 'img')

executables = [
    Executable(
        script="LMCCT.py",
        base=base,
        icon=os.path.join(img_dir, "lmcct.ico"),
        target_name="LMCCT.exe",
        manifest="app.manifest",
    )
]

build_options = {
    "packages": [
        "os", "sys", "time", "PIL", "customtkinter", "CTkListbox", "xml", "tkinter"
    ],
    "include_files": [
        (img_dir, os.path.join("lib", "img"))
    ],
}

setup(
    name="LML Mod Conflict Checker Tool",
    version="1.2.0",
    description="LML Mod Conflict Checker Tool",
    author="generatedmax - Nexus Mods",
    options={"build_exe": build_options},
    executables=executables
)