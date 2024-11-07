import os
import sys
import time
import pyi_splash
import tkinter as tk
import xml.etree.ElementTree as ET
from collections import defaultdict
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and similar tools."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, "img", relative_path)

def browse_folder(entry):
    """Open a file dialog to select a folder and set it in the entry box."""
    folder_path = filedialog.askdirectory(title="Select your 'lml' folder")
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

def search_lml_folder():
    """Search common installation paths for the 'lml' folder."""
    common_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"C:\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"C:\Games\Steam\steamapps\common\Red Dead Redemption 2\lml"
    ]
    for path in common_paths:
        if os.path.isdir(path) and os.access(path, os.R_OK):
            return path
    return ""

def get_mods_and_files(lml_folder):
    """Collect filenames from each mod folder in the 'lml' directory, ignoring subfolder structure within each mod."""
    file_map = defaultdict(list)
    ignored_files = {"install.xml", "strings.gxt2"}
    
    for mod_folder in os.listdir(lml_folder):
        mod_path = os.path.join(lml_folder, mod_folder)
        
        if os.path.isdir(mod_path):
            for root, _, files in os.walk(mod_path):
                for file in files:
                    if file.lower() in ignored_files:
                        continue
                    
                    if "stream" in root.lower():
                        priority = 2
                    elif "replace" in root.lower():
                        priority = 1
                    else:
                        priority = 0
                    
                    file_map[file.lower()].append((mod_folder, priority))
    return file_map

def find_conflicts(file_map):
    """Identify files that are modified by more than one mod, ignoring folder structure and filtering within the same mod."""
    conflicts = {}
    for file, mods in file_map.items():
        unique_mods = {mod for mod, _ in mods}
        
        if len(unique_mods) > 1:
            conflicts[file] = mods
    return conflicts

def get_load_order(mods_xml_path):
    """Parse mods.xml to get the mod load order."""
    tree = ET.parse(mods_xml_path)
    root = tree.getroot()
    load_order = []
    for mod in root.find("LoadOrder"):
        load_order.append(mod.text)
    return load_order

def display_message(app, title, message):
    """Create a themed message window with custom icon and content, centered and replacing the main window."""
    msg_window = ttk.Toplevel(app)
    msg_window.title(title)
    msg_window.iconbitmap(resource_path("RDR2.ico"))

    lines = message.count("\n") + 1
    max_line_length = max(len(line) for line in message.split("\n"))
    window_width = min(600, max(300, max_line_length * 7))
    window_height = min(500, max(150, lines * 20))
    screen_width = msg_window.winfo_screenwidth()
    screen_height = msg_window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    msg_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    ttk.Label(msg_window, text=message, padding=20, anchor="center", wraplength=window_width - 20).pack(expand=True)
    ttk.Button(
        msg_window,
        text="OK",
        command=lambda: close_message(msg_window, app),
        style="Custom.TButton"
    ).pack(pady=10)

    msg_window.protocol("WM_DELETE_WINDOW", lambda: close_message(msg_window, app))

def close_message(msg_window, app):
    """Close the message window and ensure the main application window is fully closed."""
    msg_window.destroy()
    if not app.winfo_exists():
        app.quit()

def display_conflicts(app, conflicts, load_order):
    """Display conflicts and mod precedence based on load order, prioritizing 'stream' over 'replace' folders."""
    if conflicts:
        conflict_message = "Conflicting files found:\n"
        for file, mods in conflicts.items():
            mods_sorted = sorted(
                mods,
                key=lambda mod: (-mod[1], load_order.index(mod[0]) if mod[0] in load_order else -1)
            )
            conflict_message += f"\nFile '{file}' is modified by the following mods (in order of precedence):\n"
            for mod, priority in mods_sorted:
                label = f"{mod} (stream)" if priority == 2 else (f"{mod} (replace)" if priority == 1 else mod)
                conflict_message += f" - {label}\n"
        display_message(app, "LML Mod Conflict Checker Tool", conflict_message)
    else:
        display_message(app, "LML Mod Conflict Checker Tool", "No conflicts found.")

def check_conflicts(app, entry):
    lml_folder = entry.get()
    if not os.path.isdir(lml_folder) or not os.access(lml_folder, os.R_OK):
        display_message(app, "Error", "Invalid or inaccessible folder path. Please select a valid LML folder.")
        return

    file_map = get_mods_and_files(lml_folder)
    conflicts = find_conflicts(file_map)

    mods_xml_path = os.path.join(lml_folder, "mods.xml")
    if not os.path.isfile(mods_xml_path) or not os.access(mods_xml_path, os.R_OK):
        display_message(app, "Error", "mods.xml not found or inaccessible in the selected folder. Exiting.")
        return
    load_order = get_load_order(mods_xml_path)

    display_conflicts(app, conflicts, load_order)

def main():
    # Close the splash screen if present
    pyi_splash.close()
    
    app = ttk.Window(themename="cosmo")
    app.title("LML Mod Conflict Checker Tool")

    app.protocol("WM_DELETE_WINDOW", app.quit)

    window_width = 580
    window_height = 120
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    app.geometry(f"{window_width}x{window_height}+{x}+{y}")
    app.resizable(False, False)
    app.iconbitmap(resource_path("RDR2.ico"))

    ttk.Label(app, text="Enter LML Folder Path:").grid(row=0, column=0, padx=10, pady=10, sticky="e")

    lml_path = search_lml_folder()
    entry = ttk.Entry(app, width=55)
    entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    if lml_path:
        entry.insert(0, lml_path)

    style = ttk.Style()
    style.configure(
        "Custom.TButton",
        foreground="white",
        background="#b22222",
        borderwidth=0,
        padding=(5, 3),
        focusthickness=0,
        focuscolor="none",
        relief="flat"
    )
    style.map(
        "Custom.TButton",
        background=[("active", "#8b0000")],
    )

    browse_button = ttk.Button(app, text="Browse", style="Custom.TButton", command=lambda: browse_folder(entry))
    browse_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

    check_button = ttk.Button(app, text="Check Conflicts", style="Custom.TButton", command=lambda: check_conflicts(app, entry))
    check_button.grid(row=1, column=0, columnspan=3, pady=20)

    app.mainloop()

if __name__ == "__main__":
    main()
