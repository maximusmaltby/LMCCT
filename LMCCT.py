# --- 1. Imports and Constants ---

import os
import sys
import string
import shutil
import difflib
import requests
import subprocess
import webbrowser
import customtkinter as ctk
import xml.etree.ElementTree as ET

from CTkListbox import *
from pathlib import Path
from xml.dom import minidom
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
from customtkinter import CTkImage
from difflib import SequenceMatcher
from collections import defaultdict
from tklinenums import TkLineNumbers

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
    IMG_DIR = os.path.join(base_path, 'lib', 'img')
    CONFIG_PATH = os.path.join(base_path, 'lib', 'lmcct.dat')
else:
    base_path = os.path.dirname(__file__)
    IMG_DIR = os.path.join(base_path, 'img')
    CONFIG_PATH = os.path.join(base_path, 'lib', 'lmcct.dat')


# --- 2. Utility Functions ---

def load_image(filename, width, height):
    try:
        img_path = os.path.join(IMG_DIR, filename)
        pil_image = Image.open(img_path).resize((width, height), Image.LANCZOS)
        return CTkImage(pil_image, size=(width, height))
    except FileNotFoundError:
        print(f"Error: Image file {filename} not found in {IMG_DIR}.")
        return None

def browse_folder(entry):
    folder_path = filedialog.askdirectory(title="Select your 'lml' folder")
    if folder_path:
        entry.delete(0, ctk.END)
        entry.insert(0, folder_path)

def search_lml_folder():
    possible_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"C:\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"C:\Games\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"D:\Program Files (x86)\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"D:\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"D:\Games\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"E:\Program Files (x86)\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"E:\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"E:\Games\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"F:\Program Files (x86)\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"F:\Steam\steamapps\common\Red Dead Redemption 2\lml",
        r"F:\Games\Steam\steamapps\common\Red Dead Redemption 2\lml"
    ]

    for path in possible_paths:
        if os.path.isdir(path) and os.access(path, os.R_OK):
            return path
    return ""


# --- 3. Data Management Functions ---

def get_mods_and_files(lml_folder):
    """
    Traverse the LML folder to identify mods and their associated files.
    A mod is identified if any folder contains an install.xml file.
    """
    file_map = defaultdict(list)
    ignored_files = {"install.xml", "strings.gxt2", "__folder_managed_by_vortex"}

    def find_mod_folders(folder_path):
        """Recursively scan folders for install.xml and identify mods."""
        mod_folders = []
        for root, dirs, files in os.walk(folder_path):
            if "install.xml" in files:
                mod_folders.append(root)
        return mod_folders

    mod_folders = find_mod_folders(lml_folder)

    for mod_path in mod_folders:
        mod_name = os.path.relpath(mod_path, lml_folder).replace("\\", "/")

        for root, _, files in os.walk(mod_path):
            for file in files:
                if file.lower() not in ignored_files:
                    priority = (
                        2 if "stream" in root.lower() else
                        1 if "replace" in root.lower() else
                        0
                    )
                    file_map[file.lower()].append((mod_name, priority))
    return file_map

def find_conflicts(file_map):
    conflicts = {}
    for file, mods in file_map.items():
        if file.lower() == "content.xml":
            continue
        unique_mods = {mod for mod, _ in mods}
        if len(unique_mods) > 1:
            conflicts[file] = mods
    return conflicts

def get_load_order(mods_xml_path):
    tree = ET.parse(mods_xml_path)
    root = tree.getroot()
    return [mod.text.replace("\\", "/") for mod in root.find("LoadOrder")]
    
def update_load_order(mods_xml_path, items):
    """Update the load order in the mods.xml file based on the given items list."""
    tree = ET.parse(mods_xml_path)
    root = tree.getroot()

    load_order_element = root.find("LoadOrder")
    if load_order_element is None:
        raise ValueError("No <LoadOrder> element found in mods.xml")

    load_order_element.clear()

    for mod in items:
        mod_element = ET.Element("Mod")
        mod_element.text = mod.replace("\\", "/")
        load_order_element.append(mod_element)

    indent_xml(root)
    tree.write(mods_xml_path, encoding="utf-8", xml_declaration=True)

def indent_xml(elem, level=0):
    """Helper function to indent XML elements for custom formatting."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for subelem in elem:
            indent_xml(subelem, level + 1)
            if not subelem.tail or not subelem.tail.strip():
                subelem.tail = i + "  "
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# --- 4. GUI Layout Functions ---

def populate_listbox(listbox, items):
    """Helper function to populate the listbox with items, temporarily hiding it during redraw."""
    listbox.pack_forget()
    listbox.delete(0, ctk.END)

    for item in items:
        listbox.insert(ctk.END, item)

    listbox.pack(fill="both", expand=True)

def get_listbox_items(listbox):
    """Retrieve all items from the listbox as a list."""
    return [listbox.get(i) for i in range(listbox.size())]

def move_up(listbox, mods_xml_path):
    """Move the selected item up in the list and update the listbox."""
    try:
        selected_index = listbox.curselection()
        if selected_index > 0:
            listbox.move_up(selected_index)
            items = get_listbox_items(listbox)
            update_load_order(mods_xml_path, items)
    except (IndexError, AttributeError):
        pass

def move_down(listbox, mods_xml_path):
    """Move the selected item down in the list and update the listbox."""
    try:
        selected_index = listbox.curselection()
        if selected_index < listbox.size() - 1:
            listbox.move_down(selected_index)
            items = get_listbox_items(listbox)
            update_load_order(mods_xml_path, items)
    except (IndexError, AttributeError):
        pass


# --- 5. Application Logic Functions ---

def open_nexus_link():
    webbrowser.open("https://www.nexusmods.com/reddeadredemption2/mods/5180")
    
def check_for_update(version_label):
    """Check for updates and update the version label if a new version is available."""
    try:
        response = requests.get("https://pastebin.com/raw/gGXu4uA8", timeout=5)
        response.raise_for_status()
        remote_version = response.text.strip()

        if remote_version != "1.4.0":
            version_label.configure(text="Update " + remote_version + " Available!", text_color="#f88379")
    except requests.RequestException:
        print("Failed to check for updates.")
    
def open_mod_folder(selected_mod, lml_folder):
    selected_mod = selected_mod.replace(" (Lowest Priority)", "").replace(" (Highest Priority)", "")
    mod_folder_path = os.path.join(lml_folder, selected_mod)
    if os.path.isdir(mod_folder_path):
        os.startfile(mod_folder_path)
    else:
        print(f"Error: Folder '{mod_folder_path}' does not exist.")
        
def open_lml_folder(lml_folder):
    if os.path.isdir(lml_folder):
        os.startfile(lml_folder)
    else:
        print(f"Error: LML folder '{lml_folder}' does not exist.")
        
def open_game_folder(lml_folder):
    if os.path.isdir(lml_folder):
        os.startfile(os.path.dirname(lml_folder))
    else:
        print(f"Error: LML folder '{lml_folder}' does not exist.")

def check_conflicts(app, entry_or_path):
    selected_folder = entry_or_path.get() if hasattr(entry_or_path, "get") else entry_or_path
    lml_folder = os.path.join(selected_folder, "lml") if os.path.basename(selected_folder).lower() == "red dead redemption 2" else selected_folder
    if not os.path.isdir(lml_folder) or not os.access(lml_folder, os.R_OK):
        ctk.CTkMessagebox.show_warning(title="Error", message="Invalid or inaccessible folder path. Please select a valid LML folder.")
        return

    file_map = get_mods_and_files(lml_folder)
    conflicts = find_conflicts(file_map)
    mods = [mod for mod in os.listdir(lml_folder) if os.path.isdir(os.path.join(lml_folder, mod))]
    
    display_main_window(app, mods, conflicts, lml_folder)
    app.withdraw()

def get_config_path():
    """Return the path to the configuration file in a user-writable location."""
    appdata_dir = os.getenv('APPDATA')
    app_folder = os.path.join(appdata_dir, 'LML Mod Conflict Checker Tool')
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, 'lmcct.dat')

def load_config():
    """Load the configuration from lmcct.dat, upgrading older formats if needed."""
    config_path = get_config_path()
    config = {"path": None, "theme": "Dark"}

    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            lines = file.readlines()

        if len(lines) == 1 and not lines[0].startswith("path="):
            config["path"] = lines[0].strip()
            with open(config_path, 'w') as upgrade_file:
                upgrade_file.write(f'path="{config["path"]}"\n')
                upgrade_file.write(f'theme="{config["theme"]}"\n')
        else:
            for line in lines:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"')
                if key in config:
                    config[key] = value

    return config

def save_config(path=None, theme=None):
    """Save the configuration to lmcct.dat."""
    config_path = get_config_path()

    current_config = {"path": None, "theme": "Dark"}
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            lines = file.readlines()
        for line in lines:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"')
            if key in current_config:
                current_config[key] = value

    if path is not None:
        current_config["path"] = path
    if theme is not None:
        current_config["theme"] = theme

    with open(config_path, 'w') as file:
        for key, value in current_config.items():
            file.write(f'{key}="{value}"\n')

def check_and_save_path(app, entry):
    """Check the provided LML path, save it if valid, and display conflicts if accessible."""
    selected_folder = entry.get()
    lml_folder = os.path.join(selected_folder, "lml") if os.path.basename(selected_folder).lower() == "red dead redemption 2" else selected_folder
    if os.path.isdir(lml_folder) and os.access(lml_folder, os.R_OK):
        save_config(path=lml_folder)
        check_conflicts(app, lml_folder)
    else:
        ctk.CTkMessagebox.show_warning(title="Error", message="Invalid or inaccessible folder path. Please select a valid LML folder.")

def refresh_modlist(mod_listbox, lml_folder, mods_xml_path, browse_button):
    """Refresh the mod list by reloading mods from the LML folder and updating the listbox."""
    try:
        file_map = get_mods_and_files(lml_folder)
        mods = {mod.replace("\\", "/") for _, mod_list in file_map.items() for mod, _ in mod_list}

        load_order = get_load_order(mods_xml_path)

        sorted_mods = [mod for mod in load_order if mod in mods] + [mod for mod in mods if mod not in load_order]

        populate_listbox(mod_listbox, sorted_mods)

        browse_button.configure(state="disabled")
    except Exception as e:
        error_message = f"Error refreshing mod list: {str(e)}"
        messagebox.showerror("Error", error_message)

def refresh_asi(asi_listbox, lml_folder):
    """Refresh the list of ASI mods in the game folder."""
    try:
        asi_folder = os.path.dirname(lml_folder)
        
        if not os.path.isdir(asi_folder):
            raise FileNotFoundError(f"Game root folder '{asi_folder}' does not exist or is inaccessible.")
        
        asi_files = [file for file in os.listdir(asi_folder) if file.lower().endswith(".asi")]

        asi_listbox.delete(0, ctk.END)
        if asi_files:
            for asi_file in asi_files:
                asi_listbox.insert(ctk.END, asi_file)
        else:
            asi_listbox.insert(ctk.END, "No ASI mods found.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh ASI mods: {e}")

def clean_mods(lml_folder):
    """Move non-game files from the game root to the LMCCT backup folder."""
    root_dir = os.path.dirname(lml_folder)
    backup_dir = os.path.join(root_dir, "LMCCT")

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    game_files = {
        "index.bin", "RDR2.exe", "uninstall.exe", "amd_ags_x64.dll", "bink2w64.dll", 
        "dxilconv7.dll", "ffx_fsr2_api_dx12_x64.dll", "ffx_fsr2_api_vk_x64.dll", 
        "ffx_fsr2_api_x64.dll", "NvLowLatencyVk.dll", "nvngx_dlss.dll", "oo2core_5_win64.dll", 
        "anim_0.rpf", "appdata0_update.rpf", "common_0.rpf", "data_0.rpf", "hd_0.rpf", 
        "levels_0.rpf", "levels_1.rpf", "levels_2.rpf", "levels_3.rpf", "levels_4.rpf", 
        "levels_5.rpf", "levels_6.rpf", "levels_7.rpf", "movies_0.rpf", "packs_0.rpf", 
        "packs_1.rpf", "rowpack_0.rpf", "shaders_x64.rpf", "textures_0.rpf", "textures_1.rpf", 
        "update_1.rpf", "update_2.rpf", "update_3.rpf", "update_4.rpf", "title.rgl", "steam_appid.txt",
        "EOSSDK-Win64-Shipping.dll", "PlayRDR2.exe", "steam_api64.dll", "installscript.vdf", "installscript_sdk.vdf"
    }

    for filename in os.listdir(root_dir):
        file_path = os.path.join(root_dir, filename)
        
        if os.path.isfile(file_path) and filename not in game_files:
            try:
                shutil.move(file_path, os.path.join(backup_dir, filename))
                print(f"Moved: {filename}")
            except Exception as e:
                print(f"Failed to move {filename}: {e}")

def restore_mods(lml_folder):
    """Restore files from the LMCCT backup folder to the game root."""
    root_dir = os.path.dirname(lml_folder)
    backup_dir = os.path.join(root_dir, "LMCCT")

    if os.path.exists(backup_dir):
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            try:
                shutil.move(file_path, os.path.join(root_dir, filename))
                print(f"Restored: {filename}")
            except Exception as e:
                print(f"Failed to restore {filename}: {e}")
        try:
            os.rmdir(backup_dir)
            print(f"Removed backup directory: {backup_dir}")
        except Exception as e:
            print(f"Failed to remove backup directory: {e}")
    else:
        print(f"No backup folder found at {backup_dir}")
        
def update_restore_button_state(lml_folder, restore_button):
    """Enable or disable the restore button based on the presence of the LMCCT folder."""
    root_dir = os.path.dirname(lml_folder)
    lmcct_dir = os.path.join(root_dir, "LMCCT")
    
    if os.path.exists(lmcct_dir) and os.path.isdir(lmcct_dir):
        restore_button.configure(state="normal")
    else:
        restore_button.configure(state="disabled")
        
def restart_program(lml_path_entry):
    """Restart the program."""
    save_config(path=lml_path_entry.get().strip())
    python_executable = sys.executable
    script_path = sys.argv[0]
    subprocess.Popen([python_executable, script_path])
    sys.exit()

def show_splash():
    splash_width, splash_height = 600, 350
    splash_root = ctk.CTkToplevel()
    splash_root.overrideredirect(True)
    screen_width, screen_height = splash_root.winfo_screenwidth(), splash_root.winfo_screenheight()
    x, y = max(0, (screen_width - splash_width) // 2), max(0, (screen_height - splash_height) // 2)
    splash_root.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    header_img = load_image("header.webp", splash_width, splash_height)
    if header_img:
        progressbar = ctk.CTkProgressBar(master=splash_root, width=600, progress_color="#b22222")
        progressbar.pack(side="bottom")
        progressbar.set(0)
        progressbar.start()
        splash_label = ctk.CTkLabel(splash_root, image=header_img, text="")
        splash_label.pack()
    
    return splash_root


# --- 6. Main Functions ---

def display_main_window(app, mods, conflicts, lml_folder):
    global config
    
    load_order = get_load_order(os.path.join(lml_folder, "mods.xml"))
    sorted_mods = [mod for mod in load_order if mod in mods]
    
    main_window = ctk.CTkToplevel(app)
    main_window.withdraw()
    main_window.title("LML Mod Conflict Checker Tool")
    
    is_fullscreen = False

    def toggle_fullscreen(event=None):
        nonlocal is_fullscreen
        is_fullscreen = not is_fullscreen
        main_window.attributes("-fullscreen", is_fullscreen)

    main_window.bind("<F11>", toggle_fullscreen)
    main_window.bind("<Alt-Return>", toggle_fullscreen)
    main_window.bind("<Escape>", lambda event: main_window.attributes("-fullscreen", False))
    
    main_window.grid_rowconfigure(0, weight=1)
    main_window.grid_rowconfigure(1, weight=1)
    main_window.grid_rowconfigure(2, weight=1)
    
    main_window.grid_columnconfigure(0, weight=0)
    main_window.grid_columnconfigure(1, weight=1)
    main_window.grid_columnconfigure(2, weight=7)
    main_window.grid_columnconfigure(4, weight=1)

    icon_path = os.path.join(IMG_DIR, "lmcct.ico")
    main_window.after(201, lambda: main_window.iconbitmap(icon_path))

    sidebar_frame = ctk.CTkFrame(main_window, corner_radius=0)
    sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsw")
    sidebar_frame.grid_rowconfigure(0, weight=1)
    sidebar_frame.grid_rowconfigure(1, weight=1)
    sidebar_frame.grid_rowconfigure(2, weight=1)
    sidebar_frame.grid_rowconfigure(3, weight=1)
    sidebar_frame.grid_rowconfigure(4, weight=1)
    sidebar_frame.grid_rowconfigure(5, weight=1)

    sidebar_dark_image_path = os.path.join(IMG_DIR, "lmcct_dark.png")
    sidebar_light_image_path = os.path.join(IMG_DIR, "lmcct_light.png")
    sidebar_dark_image = Image.open(sidebar_dark_image_path).convert("RGBA")
    sidebar_light_image = Image.open(sidebar_light_image_path).convert("RGBA")
    sidebar_ctk_image = ctk.CTkImage(dark_image=sidebar_dark_image, light_image=sidebar_light_image, size=(224, 77))
    sidebar_image_label = ctk.CTkLabel(sidebar_frame, image=sidebar_ctk_image, fg_color="transparent", text="")
    sidebar_image_label.grid(row=0, column=0, padx=25, pady=(40, 0), sticky="n")

    home_frame = ctk.CTkFrame(main_window, fg_color="transparent")
    
    background_image_path = os.path.join(IMG_DIR, "background.png")
    background_image = ctk.CTkImage(Image.open(background_image_path), size=(3840, 2160))

    background_label = ctk.CTkLabel(home_frame, image=background_image, text="", fg_color="transparent")
    background_label.grid(row=0, column=0, rowspan=3, columnspan=1, sticky="nsew")
    
    home_frame.grid_rowconfigure(0, weight=0)
    home_frame.grid_rowconfigure(1, weight=1)
    home_frame.grid_columnconfigure(0, weight=1)

    mods_frame = ctk.CTkFrame(main_window, fg_color="transparent")
    asi_frame = ctk.CTkFrame(main_window, fg_color="transparent")
    conflicts_frame = ctk.CTkFrame(main_window, fg_color="transparent")
    merge_frame = ctk.CTkFrame(main_window, fg_color="transparent")
    settings_frame = ctk.CTkFrame(main_window, fg_color="transparent")

    def show_home_frame():
        home_frame.grid(row=0, column=2, columnspan=1, rowspan=3, sticky="nsew")
        mods_frame.grid_forget()
        asi_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.grid_forget()
        merge_frame.grid_forget()
        settings_frame.grid_forget()

        home_button.configure(fg_color="#8b0000")
        mods_button.configure(fg_color="#b22222")
        asi_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#b22222")
        merge_button.configure(fg_color="#b22222")
        settings_button.configure(fg_color="#b22222")

    def show_mods_frame():
        mods_frame.grid(row=0, column=2, columnspan=1, pady=10, rowspan=3, sticky="nswe")
        home_frame.grid_forget()
        asi_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.pack(side="right")
        merge_frame.grid_forget()
        settings_frame.grid_forget()

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#8b0000")
        asi_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#b22222")
        merge_button.configure(fg_color="#b22222")
        settings_button.configure(fg_color="#b22222")
        
    def show_asi_frame():
        asi_frame.grid(row=0, column=2, columnspan=1, pady=10, rowspan=3, sticky="nswe")
        home_frame.grid_forget()
        mods_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.grid_forget()
        merge_frame.grid_forget()
        settings_frame.grid_forget()

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#b22222")
        asi_button.configure(fg_color="#8b0000")
        conflicts_button.configure(fg_color="#b22222")
        merge_button.configure(fg_color="#b22222")
        settings_button.configure(fg_color="#b22222")

    def show_conflicts_frame():
        conflicts_frame.grid(row=0, column=2, columnspan=1, pady=10, rowspan=3, sticky="nswe")
        home_frame.grid_forget()
        mods_frame.grid_forget()
        asi_frame.grid_forget()
        button_frame.grid_forget()
        merge_frame.grid_forget()
        settings_frame.grid_forget()

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#b22222")
        asi_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#8b0000")
        merge_button.configure(fg_color="#b22222")
        settings_button.configure(fg_color="#b22222")
        
    def show_merge_frame():
        merge_frame.grid(row=0, column=2, columnspan=1, pady=10, rowspan=3, sticky="nswe")
        home_frame.grid_forget()
        mods_frame.grid_forget()
        asi_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.grid_forget()
        settings_frame.grid_forget()

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#b22222")
        asi_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#b22222")
        merge_button.configure(fg_color="#8b0000")
        settings_button.configure(fg_color="#b22222")
        
    def show_settings_frame():
        settings_frame.grid(row=0, column=2, columnspan=1, pady=10, rowspan=3, sticky="nswe")
        home_frame.grid_forget()
        mods_frame.grid_forget()
        asi_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.grid_forget()
        merge_frame.grid_forget()

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#b22222")
        asi_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#b22222")
        merge_button.configure(fg_color="#b22222")
        settings_button.configure(fg_color="#8b0000")
    
    def change_appearance_mode(new_mode):
        ctk.set_appearance_mode(new_mode)
        save_config(theme=new_mode)
    
    
    # Sidebar frame
    button_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
    button_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(100, 10))
    
    home_button = ctk.CTkButton(button_frame, text="Home", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_home_frame)
    home_button.pack(fill="x", padx=10, pady=5)
    
    asi_button = ctk.CTkButton(button_frame, text="ASI Mods", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_asi_frame)
    asi_button.pack(fill="x", padx=10, pady=5)

    mods_button = ctk.CTkButton(button_frame, text="LML Mods", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_mods_frame)
    mods_button.pack(fill="x", padx=10, pady=5)

    conflicts_button = ctk.CTkButton(button_frame, text="Conflicts", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_conflicts_frame)
    conflicts_button.pack(fill="x", padx=10, pady=5)

    merge_button = ctk.CTkButton(button_frame, text="Merge", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_merge_frame)
    merge_button.pack(fill="x", padx=10, pady=5)
    
    settings_button = ctk.CTkButton(button_frame, text="Settings", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_settings_frame)
    settings_button.pack(fill="x", padx=10, pady=5)
    
    version_label = ctk.CTkLabel(sidebar_frame, text="Version 1.4.0", font=("Segoe UI", 18, "bold"))
    version_label.grid(row=5, column=0, sticky="s", padx=10, pady=0)
    
    check_for_update(version_label)
    
    nexus_label = ctk.CTkButton(
        sidebar_frame,
        text="Nexus Mods",
        font=("Segoe UI", 18, "bold"),
        fg_color="transparent",
        hover_color=sidebar_frame.cget("fg_color"),
        text_color="#b22222",
        command=open_nexus_link
    )
    nexus_label.grid(row=6, column=0, sticky="s", padx=10, pady=(0, 10))
    
    
    # Home frame
    home_textbox_container = ctk.CTkFrame(home_frame, fg_color="transparent")
    home_textbox_container.grid(row=1, column=0, padx=20, pady=20, sticky="")
    
    home_textbox = ctk.CTkLabel(
        home_textbox_container, 
        text="\n     Now there is no need to manually search through your mod folders to check for conflicts!     \n"
             "This simple tool will iterate through the mods in your LML folder and check for any\n"
             "duplicate file names. It will then list the files that are conflicting, the mods\n"
             "they are being edited by, and where they currently are in the load order.\n\n"
             "Now with an auto-merge tool!\n\n\n"
             "Version 1.4.0 changelog:\n"
             "-----\n"
             "- Added ASI mod manager.\n"
             "- Added mod cleaning and restoring options (for safe online play).\n"
             "- Fixed progress bar.\n"
             "- Fixed issue with Online Content Unlocker.\n"
             "-----\n",
        font=("Segoe UI", 16, "bold"),
        fg_color="transparent"
    )
    home_textbox.pack(fill="both", expand=True, padx=5, pady=5)
    
    
    # Mods frame
    mods_header_frame = ctk.CTkFrame(mods_frame)
    mods_header_frame.pack(fill="x", anchor="n", pady=(0, 5))
    ctk.CTkLabel(mods_header_frame, text="LML Mods", font=("Segoe UI", 22, "bold")).pack(side="left", padx=5, pady=10)

    refresh_mods_button = ctk.CTkButton(
        mods_header_frame,
        text="Refresh",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        command=lambda: refresh_modlist(mod_listbox, lml_folder, os.path.join(lml_folder, "mods.xml"), browse_button)
    )
    refresh_mods_button.pack(side="right", padx=10, pady=10)

    open_lml_button = ctk.CTkButton(
        mods_header_frame,
        text="Browse LML Folder",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        command=lambda: open_lml_folder(lml_folder)
    )
    open_lml_button.pack(side="right")

    browse_button = ctk.CTkButton(
        mods_header_frame,
        text="Open Mod Folder",
        state="disabled",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        command=lambda: open_mod_folder(mod_listbox.get(), lml_folder)
    )
    browse_button.pack(side="right", padx=10)
    
    mods_container_frame = ctk.CTkFrame(mods_frame, fg_color="transparent")
    mods_container_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    button_frame = ctk.CTkFrame(mods_container_frame, fg_color="transparent")
    button_frame.pack(side="left", padx=10, pady=10, anchor="center")

    up_button = ctk.CTkButton(
        button_frame,
        text="▲",
        width=30,
        height=30,
        fg_color="#b22222",
        hover_color="#8b0000",
        command=lambda: move_up(mod_listbox, os.path.join(lml_folder, "mods.xml"))
    )
    up_button.grid(row=0, column=0, padx=5, pady=5)

    down_button = ctk.CTkButton(
        button_frame,
        text="▼",
        width=30,
        height=30,
        fg_color="#b22222",
        hover_color="#8b0000",
        command=lambda: move_down(mod_listbox, os.path.join(lml_folder, "mods.xml"))
    )
    down_button.grid(row=1, column=0, padx=5, pady=5)
    
    mod_listbox_font = ctk.CTkFont(family="Segoe UI", size=16)
    
    mod_listbox = CTkListbox(
        mods_container_frame,
        command=lambda x: browse_button.configure(state="normal"),
        height=650,
        width=500,
        highlight_color="#8b0000",
        hover_color="#b22222",
        border_width=2,
        border_color="#545454",
        font=mod_listbox_font
    )
    mod_listbox.pack(side="left", fill="both", expand=True)

    refresh_modlist(mod_listbox, lml_folder, os.path.join(lml_folder, "mods.xml"), browse_button)
    
    # ASI Frame
    asi_header_frame = ctk.CTkFrame(asi_frame)
    asi_header_frame.pack(fill="x", anchor="n", pady=(0, 5))
    ctk.CTkLabel(asi_header_frame, text="ASI Mods", font=("Segoe UI", 22, "bold")).pack(side="left", padx=5, pady=10)
    
    refresh_asi_button = ctk.CTkButton(
        asi_header_frame,
        text="Refresh",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        command=lambda: refresh_asi(asi_listbox, lml_folder)
    )
    refresh_asi_button.pack(side="right", padx=10, pady=10)
    
    asi_game_folder_button = ctk.CTkButton(
        asi_header_frame,
        text="Browse RDR2 Folder",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        command=lambda: open_game_folder(lml_folder)
    )
    asi_game_folder_button.pack(side="right")       
    
    asi_container_frame = ctk.CTkFrame(asi_frame, fg_color="transparent")
    asi_container_frame.pack(fill="both", expand=True, padx=10, pady=10)    
    
    asi_listbox = CTkListbox(
        asi_container_frame,
        height=650,
        width=500,
        highlight_color="#8b0000",
        hover_color="#b22222",
        border_width=2,
        border_color="#545454",
        font=mod_listbox_font
    )
    asi_listbox.pack(side="left", fill="both", expand=True)
    
    refresh_asi(asi_listbox, lml_folder)
    
    # Conflicts frame
    conflicts_header_frame = ctk.CTkFrame(conflicts_frame)
    conflicts_header_frame.pack(fill="x", anchor="n", pady=(0, 5))
    ctk.CTkLabel(conflicts_header_frame, text="Conflicts", font=("Segoe UI", 22, "bold")).pack(side="left", padx=5, pady=10)
    
    conflicts_container_frame = ctk.CTkFrame(conflicts_frame, fg_color="transparent")
    conflicts_container_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    conflict_text = ctk.CTkTextbox(conflicts_container_frame, wrap="none", font=("Segoe UI", 18), height=650, width=500, border_width=2, border_color="#545454", cursor="arrow")
    conflict_text.pack(side="left", fill="both", expand=True)
    
    conflict_text.bind("<Button-1>", lambda e: "break")
    conflict_text.bind("<B1-Motion>", lambda e: "break")
    conflict_text.bind("<Control-a>", lambda e: "break")
    conflict_text.bind("<Shift-Left>", lambda e: "break")
    conflict_text.bind("<Shift-Right>", lambda e: "break")

    if conflicts:
        for file, mods in conflicts.items():
            conflict_text.insert(ctk.END, f"File '{file}' is modified by:\n")
            for mod, priority in mods:
                label = f"{mod} (stream)" if priority == 2 else (f"{mod} (replace)" if priority == 1 else mod)
                conflict_text.insert(ctk.END, f" - {label}\n")
            conflict_text.insert(ctk.END, "\n")
    else:
        conflict_text.insert(ctk.END, "No conflicts found.")

    conflict_text.configure(state=ctk.DISABLED)
    
    
    # Merge frame

    def auto_merge(fileA_path, fileB_path, main_window):
        """Merge two XML files with optional manual conflict resolution or auto-merge."""
        try:
            merge_mode = merge_mode_dialog(main_window)
            if merge_mode == "cancel":
                return

            with open(fileA_path.get(), "r", encoding="utf-8-sig") as fA, open(fileB_path.get(), "r", encoding="utf-8-sig") as fB:
                fileA_lines = fA.readlines()
                fileB_lines = fB.readlines()
                
            normalized_inputs = sorted([fileA_lines, fileB_lines], key=lambda x: "".join(x))
            fileA_lines, fileB_lines = normalized_inputs

            if merge_mode == "auto-merge":
                original_file = filedialog.askopenfilename(
                    title="Select the Original Game File",
                    filetypes=[("All Files", "*.*")]
                )
                if not original_file:
                    return

                with open(original_file, "r", encoding="utf-8-sig") as fC:
                    fileC_lines = fC.readlines()

            merged_lines = []
            conflicts_detected = False

            if merge_mode == "auto-merge":
                matcher_c_to_a = SequenceMatcher(None, fileC_lines, fileA_lines)
                matcher_c_to_b = SequenceMatcher(None, fileC_lines, fileB_lines)

                c_index = 0
                for tag_c, i1_c, i2_c, _, _ in matcher_c_to_a.get_opcodes():
                    while c_index < i1_c:
                        merged_lines.append(fileC_lines[c_index])
                        c_index += 1

                    block_a = fileA_lines[i1_c:i2_c]
                    block_b = fileB_lines[i1_c:i2_c]

                    if tag_c == "equal":
                        merged_lines.extend(block_a)
                        c_index = i2_c
                    else:
                        for i in range(i1_c, i2_c):
                            line_a = fileA_lines[i] if i < len(fileA_lines) else None
                            line_b = fileB_lines[i] if i < len(fileB_lines) else None

                            if line_a == line_b:
                                merged_lines.append(line_a)
                            elif line_a and line_b:
                                line_c = fileC_lines[i] if i < len(fileC_lines) else None
                                if line_a == line_c:
                                    merged_lines.append(line_b)
                                elif line_b == line_c:
                                    merged_lines.append(line_a)
                                else:
                                    if not conflicts_detected:
                                        resolution_mode = conflict_resolution_mode_dialog(main_window)
                                        conflicts_detected = True
                                    if resolution_mode == "A":
                                        merged_lines.append(line_a)
                                    elif resolution_mode == "B":
                                        merged_lines.append(line_b)
                                    else:
                                        merged_lines.append(fileC_lines[i])
                            elif line_a:
                                merged_lines.append(line_a)
                            elif line_b:
                                merged_lines.append(line_b)

                merged_lines.extend(fileC_lines[c_index:])

            elif merge_mode == "manual":
                matcher_a_to_b = SequenceMatcher(None, fileA_lines, fileB_lines)

                for tag, i1, i2, j1, j2 in matcher_a_to_b.get_opcodes():
                    if tag == "equal":
                        merged_lines.extend(fileA_lines[i1:i2])
                    elif tag == "replace":
                        for k in range(max(i2 - i1, j2 - j1)):
                            line_a = fileA_lines[i1 + k] if i1 + k < i2 else None
                            line_b = fileB_lines[j1 + k] if j1 + k < j2 else None

                            if line_a and line_b and line_a != line_b:
                                choice = manual_conflict_resolution_dialog(main_window, [line_a], [line_b])
                                if choice == "A":
                                    merged_lines.append(line_a)
                                elif choice == "B":
                                    merged_lines.append(line_b)
                                elif choice == "cancel":
                                    return
                                else:
                                    merged_lines.append(line_a + "\n")
                                    merged_lines.append(line_b + "\n")
                            elif line_a and not line_b:
                                merged_lines.append(line_a)
                            elif line_b and not line_a:
                                merged_lines.append(line_b)
                    elif tag == "delete":
                        merged_lines.extend(fileA_lines[i1:i2])
                    elif tag == "insert":
                        merged_lines.extend(fileB_lines[j1:j2])
            
            merged_lines.extend(fileA_lines[len(merged_lines):])
            merged_lines.extend(fileB_lines[len(merged_lines):])

            default_file_name = os.path.basename(fileA_path.get())
            file_extension = os.path.splitext(default_file_name)[-1]
            filetypes = [(f"{file_extension.upper()} Files", f"*{file_extension}"), ("All Files", "*.*")]
            save_path = filedialog.asksaveasfilename(
                title="Save Merged File",
                defaultextension=file_extension,
                initialfile=default_file_name,
                filetypes=filetypes
            )
            if save_path:
                with open(save_path, "w", encoding="utf-8") as f_out:
                    f_out.writelines(merged_lines)

                success_dialog = ctk.CTkToplevel(main_window)
                success_dialog.title("Merge Successful")
                
                screen_width = success_dialog.winfo_screenwidth()
                screen_height = success_dialog.winfo_screenheight()
                initial_width = min(600, int(screen_width * 0.9))
                initial_height = min(150, int(screen_height * 0.9))

                x = max(0, (screen_width - initial_width) // 2)
                y = max(0, (screen_height - initial_height) // 2)

                success_dialog.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
                success_dialog.wm_minsize(initial_width, initial_height)
                success_dialog.resizable(False, False)
                
                icon_path = os.path.join(IMG_DIR, "lmcct.ico")
                success_dialog.after(201, lambda: success_dialog.iconbitmap(icon_path))
                
                ctk.CTkLabel(success_dialog, text=f"Files merged successfully to:\n{save_path}", font=("Segoe UI", 14, "bold")).pack(pady=20)
                ctk.CTkButton(success_dialog, text="OK", fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 14, "bold"), command=success_dialog.destroy).pack(pady=10)
                
                success_dialog.transient(main_window)
                success_dialog.grab_set()
                success_dialog.wait_window()

        except Exception as e:
            error_dialog = ctk.CTkToplevel(main_window)
            error_dialog.title("Error")
            
            screen_width = error_dialog.winfo_screenwidth()
            screen_height = error_dialog.winfo_screenheight()
            initial_width = min(600, int(screen_width * 0.9))
            initial_height = min(150, int(screen_height * 0.9))

            x = max(0, (screen_width - initial_width) // 2)
            y = max(0, (screen_height - initial_height) // 2)

            error_dialog.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
            error_dialog.wm_minsize(initial_width, initial_height)
            error_dialog.resizable(False, False)
            
            icon_path = os.path.join(IMG_DIR, "lmcct.ico")
            error_dialog.after(201, lambda: error_dialog.iconbitmap(icon_path))
            
            ctk.CTkLabel(error_dialog, text=f"An error occurred during the merge:\n{str(e)}", font=("Segoe UI", 14)).pack(pady=20)
            ctk.CTkButton(error_dialog, text="OK", command=error_dialog.destroy).pack(pady=10)
            error_dialog.transient(main_window)
            error_dialog.grab_set()
            error_dialog.wait_window()

    def merge_mode_dialog(main_window):
        """Ask the user to select between manual conflict resolution or auto-merge."""
        dialog = ctk.CTkToplevel(main_window)
        dialog.title("Merge Mode")
        
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        initial_width = min(480, int(screen_width * 0.9))
        initial_height = min(100, int(screen_height * 0.9))

        x = max(0, (screen_width - initial_width) // 2)
        y = max(0, (screen_height - initial_height) // 2)

        dialog.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        dialog.wm_minsize(initial_width, initial_height)
        dialog.resizable(False, False)
        
        icon_path = os.path.join(IMG_DIR, "lmcct.ico")
        dialog.after(201, lambda: dialog.iconbitmap(icon_path))

        result = {"choice": "cancel"}

        def set_choice(choice):
            result["choice"] = choice
            dialog.destroy()

        ctk.CTkLabel(dialog, text="Choose merge mode:", font=("Segoe UI", 14, "bold")).grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkButton(dialog, text="Auto-Merge", command=lambda: set_choice("auto-merge"), fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 14, "bold")).grid(row=1, column=0, padx=10)
        ctk.CTkButton(dialog, text="Manual Merge", command=lambda: set_choice("manual"), fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 14, "bold")).grid(row=1, column=1, padx=10)
        ctk.CTkButton(dialog, text="Cancel", command=lambda: set_choice("cancel"), fg_color="darkgrey", hover_color="grey", font=("Segoe UI", 14, "bold")).grid(row=1, column=2, padx=10)

        dialog.transient(main_window)
        dialog.grab_set()
        dialog.wait_window()

        return result["choice"]

    def conflict_resolution_mode_dialog(main_window):
        """Display a dialog to select the conflict resolution mode."""
        dialog = ctk.CTkToplevel(main_window)
        dialog.title("Conflict Resolution Mode")

        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        initial_width = min(600, int(screen_width * 0.9))
        initial_height = min(150, int(screen_height * 0.9))

        x = max(0, (screen_width - initial_width) // 2)
        y = max(0, (screen_height - initial_height) // 2)

        dialog.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        dialog.wm_minsize(initial_width, initial_height)
        dialog.resizable(False, False)
        
        icon_path = os.path.join(IMG_DIR, "lmcct.ico")
        dialog.after(201, lambda: dialog.iconbitmap(icon_path))

        result = {"choice": "cancel"}

        def set_choice(choice):
            result["choice"] = choice
            dialog.destroy()

        label = ctk.CTkLabel(
            dialog,
            text=" Both mods edit the same code. Select how you want to resolve conflicts:",
            font=("Segoe UI", 14, "bold"),
            wraplength=350
        )
        label.pack(pady=20)

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)

        file_a_button = ctk.CTkButton(
            button_frame,
            text="Always File A",
            fg_color="#b22222",
            hover_color="#8b0000",
            font=("Segoe UI", 14, "bold"),
            command=lambda: set_choice("A")
        )
        file_a_button.grid(row=0, column=0, padx=10)

        file_b_button = ctk.CTkButton(
            button_frame,
            text="Always File B",
            fg_color="#b22222",
            hover_color="#8b0000",
            font=("Segoe UI", 14, "bold"),
            command=lambda: set_choice("B")
        )
        file_b_button.grid(row=0, column=1, padx=10)

        manual_button = ctk.CTkButton(
            button_frame,
            text="Resolve Manually",
            fg_color="#b22222",
            hover_color="#8b0000",
            font=("Segoe UI", 14, "bold"),
            command=lambda: set_choice("manual")
        )
        manual_button.grid(row=0, column=2, padx=10)

        dialog.transient(main_window)
        dialog.grab_set()
        dialog.wait_window()

        return result["choice"]

    def manual_conflict_resolution_dialog(main_window, fileA_lines, fileB_lines):
        """Display a dialog to manually resolve a conflict."""
        dialog = ctk.CTkToplevel(main_window)
        dialog.title("Resolve Conflict")

        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        initial_width = min(800, int(screen_width * 0.9))
        initial_height = min(400, int(screen_height * 0.9))

        x = max(0, (screen_width - initial_width) // 2)
        y = max(0, (screen_height - initial_height) // 2)

        dialog.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        dialog.wm_minsize(initial_width, initial_height)
        dialog.resizable(True, True)
        
        icon_path = os.path.join(IMG_DIR, "lmcct.ico")
        dialog.after(201, lambda: dialog.iconbitmap(icon_path))

        result = {"choice": "cancel"}

        def set_choice(choice):
            result["choice"] = choice
            dialog.destroy()

        label = ctk.CTkLabel(
            dialog,
            text="A conflict has been detected. Choose which version to keep:",
            font=("Segoe UI", 14, "bold"),
            wraplength=550
        )
        label.pack(pady=10)

        text_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        fileA_textbox = ctk.CTkTextbox(
            text_frame, wrap="none", font=("Segoe UI", 12), height=150
        )
        fileA_textbox.insert("1.0", "".join(fileA_lines))
        fileA_textbox.configure(state="disabled")
        fileA_textbox.pack(side="left", fill="both", expand=True, padx=5)

        fileB_textbox = ctk.CTkTextbox(
            text_frame, wrap="none", font=("Segoe UI", 12), height=150
        )
        fileB_textbox.insert("1.0", "".join(fileB_lines))
        fileB_textbox.configure(state="disabled")
        fileB_textbox.pack(side="right", fill="both", expand=True, padx=5)

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)

        file_a_button = ctk.CTkButton(
            button_frame,
            text="Keep File A",
            fg_color="#b22222",
            hover_color="#8b0000",
            font=("Segoe UI", 14, "bold"),
            command=lambda: set_choice("A")
        )
        file_a_button.grid(row=0, column=0, padx=10)

        file_b_button = ctk.CTkButton(
            button_frame,
            text="Keep File B",
            fg_color="#b22222",
            hover_color="#8b0000",
            font=("Segoe UI", 14, "bold"),
            command=lambda: set_choice("B")
        )
        file_b_button.grid(row=0, column=1, padx=10)

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="darkgray",
            hover_color="gray",
            font=("Segoe UI", 14, "bold"),
            command=lambda: set_choice("cancel")
        )
        cancel_button.grid(row=0, column=2, padx=10)

        dialog.transient(main_window)
        dialog.grab_set()
        dialog.wait_window()

        return result["choice"]

    merge_header_frame = ctk.CTkFrame(merge_frame)
    merge_header_frame.pack(fill="x", anchor="n", padx=10, pady=(0, 5))
    ctk.CTkLabel(merge_header_frame, text="Merge (BETA)", font=("Segoe UI", 22, "bold")).pack(side="left", padx=10, pady=10)
    ctk.CTkLabel(merge_header_frame, text="Auto-Merge requires original game file. More information on Nexus Mods.", font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)
    
    auto_merge_button = ctk.CTkButton(
        merge_header_frame,
        text="Merge",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        state="disabled",
        command=lambda: auto_merge(fileA_path, fileB_path, main_window)
    )
    auto_merge_button.pack(side="right", padx=10, pady=10)
    
    fileA_frame = ctk.CTkFrame(merge_frame, border_width=2, border_color="#545454")
    fileA_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fileB_frame = ctk.CTkFrame(merge_frame, border_width=2, border_color="#545454")
    fileB_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    fileA_label = ctk.CTkLabel(fileA_frame, text="File A:", font=("Segoe UI", 16, "bold"))
    fileA_label.pack(anchor="nw", padx=10, pady=(10, 5))

    fileA_path = ctk.CTkEntry(fileA_frame, width=400, font=("Segoe UI", 14, "bold"))
    fileA_path.pack(anchor="nw", padx=10, pady=(0, 5))

    browse_fileA_button = ctk.CTkButton(
        fileA_frame, text="Browse", fg_color="#b22222", hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"), command=lambda: browse_file(fileA_path, fileA_textbox)
    )
    browse_fileA_button.pack(anchor="nw", padx=10, pady=(5, 10))

    fileA_textbox = ctk.CTkTextbox(fileA_frame, wrap="none", font=("Segoe UI", 14), height=650, state="disabled", cursor="arrow")
    fileA_textbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    
    fileA_linenums = TkLineNumbers(fileA_frame, fileA_textbox, justify="right", border=False, width=5, colors=("#7f7f7f", "#2b2b2b"))
    fileA_linenums.pack(side="left", fill="y", padx=(10,0), pady=10)

    def on_modified(event):
        fileA_textbox.edit_modified(False)
        main_window.after_idle(linenums.redraw)

    fileA_textbox.bind("<<Modified>>", lambda event: main_window.after_idle(fileA_linenums.redraw), add=True)
    
    fileA_textbox.bind("<Button-1>", lambda e: "break")
    fileA_textbox.bind("<B1-Motion>", lambda e: "break")
    fileA_textbox.bind("<Control-a>", lambda e: "break")
    fileA_textbox.bind("<Shift-Left>", lambda e: "break")
    fileA_textbox.bind("<Shift-Right>", lambda e: "break")

    fileB_label = ctk.CTkLabel(fileB_frame, text="File B:", font=("Segoe UI", 16, "bold"))
    fileB_label.pack(anchor="nw", padx=10, pady=(10, 5))

    fileB_path = ctk.CTkEntry(fileB_frame, width=400, font=("Segoe UI", 14, "bold"))
    fileB_path.pack(anchor="nw", padx=10, pady=(0, 5))

    browse_fileB_button = ctk.CTkButton(
        fileB_frame, text="Browse", fg_color="#b22222", hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"), command=lambda: browse_file(fileB_path, fileB_textbox)
    )
    browse_fileB_button.pack(anchor="nw", padx=10, pady=(5, 10))

    fileB_textbox = ctk.CTkTextbox(fileB_frame, wrap="none", font=("Segoe UI", 14), height=650, state="disabled", cursor="arrow")
    fileB_textbox.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    
    fileB_linenums = TkLineNumbers(fileB_frame, fileB_textbox, justify="right", border=False, width=5, colors=("#7f7f7f", "#2b2b2b"))
    fileB_linenums.pack(side="left", fill="y", padx=(10,0), pady=10)
    
    fileB_textbox.bind("<<Modified>>", lambda event: main_window.after_idle(fileB_linenums.redraw), add=True)
    
    fileB_textbox.bind("<Button-1>", lambda e: "break")
    fileB_textbox.bind("<B1-Motion>", lambda e: "break")
    fileB_textbox.bind("<Control-a>", lambda e: "break")
    fileB_textbox.bind("<Shift-Left>", lambda e: "break")
    fileB_textbox.bind("<Shift-Right>", lambda e: "break")

    def browse_file(entry_field, textbox):
        """Open file dialog, load file path into entry, and display contents in textbox"""
        file_path = filedialog.askopenfilename(title="Select a file to merge")
        
        if file_path:
            textbox.configure(state="normal", cursor="")
            textbox.unbind("<Button-1>", None)
            textbox.unbind("<B1-Motion>", None)
            textbox.unbind("<Control-a>", None)
            textbox.unbind("<Shift-Left>", None)
            textbox.unbind("<Shift-Right>", None)
            entry_field.delete(0, ctk.END)
            entry_field.insert(0, file_path)
            entry_field.xview_moveto(1.0)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                textbox.delete("1.0", ctk.END)
                textbox.insert("1.0", content)
        
            check_and_compare()

    def check_and_compare():
        path1 = fileA_path.get().strip()
        path2 = fileB_path.get().strip()
        
        if path1 and path2 and os.path.isfile(path1) and os.path.isfile(path2):
            compare_files()

    def compare_files():
        if not fileA_path or not fileB_path:
            return
        
        fileA_textbox.delete("1.0", "end")
        fileB_textbox.delete("1.0", "end")

        fileA_textbox.tag_config("unique", foreground="blue")
        fileB_textbox.tag_config("unique", foreground="blue")
        fileA_textbox.tag_config("conflict", foreground="red")
        fileB_textbox.tag_config("conflict", foreground="red")

        with open(fileA_path.get(), "r", encoding="utf-8-sig") as fA, open(fileB_path.get(), "r", encoding="utf-8-sig") as fB:
            fileA_lines = fA.read().splitlines()
            fileB_lines = fB.read().splitlines()

        matcher = SequenceMatcher(None, fileA_lines, fileB_lines)
        opcodes = matcher.get_opcodes()

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for line in fileA_lines[i1:i2]:
                    fileA_textbox.insert("end", line + "\n")
                for line in fileB_lines[j1:j2]:
                    fileB_textbox.insert("end", line + "\n")
            elif tag == "replace":
                for line in fileA_lines[i1:i2]:
                    fileA_textbox.insert("end", f"{line}\n", "conflict")
                for line in fileB_lines[j1:j2]:
                    fileB_textbox.insert("end", f"{line}\n", "conflict")
            elif tag == "delete":
                for line in fileA_lines[i1:i2]:
                    if line not in fileB_lines:
                        fileA_textbox.insert("end", f"{line}\n", "unique")
                    else:
                        fileA_textbox.insert("end", f"{line}\n")
            elif tag == "insert":
                for line in fileB_lines[j1:j2]:
                    if line not in fileA_lines:
                        fileB_textbox.insert("end", f"{line}\n", "unique")
                    else:
                        fileB_textbox.insert("end", f"{line}\n")

        auto_merge_button.configure(state="enabled")
        
        
    # Settings frame
    
    settings_header_frame = ctk.CTkFrame(settings_frame)
    settings_header_frame.pack(fill="x", anchor="n", pady=(0, 5))
    ctk.CTkLabel(settings_header_frame, text="Settings", font=("Segoe UI", 22, "bold")).pack(side="left", padx=5, pady=10)
    
    settings_game_folder_button = ctk.CTkButton(
        settings_header_frame,
        text="Browse RDR2 Folder",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        height=30,
        command=lambda: open_game_folder(lml_folder)
    )
    settings_game_folder_button.pack(side="right", padx=10, pady=10)    
    
    settings_container_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    settings_container_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    lml_path_label = ctk.CTkLabel(settings_container_frame, text="LML Folder Path:", font=("Segoe UI", 17, "bold"))
    lml_path_label.grid(row=0, column=0, sticky="nw", padx=10, pady=10)
    lml_path_entry = ctk.CTkEntry(settings_container_frame, width=500, font=("Segoe UI", 15, "bold"))
    lml_path_entry.grid(row=0, column=1, sticky="nw", padx=10, pady=10)
    lml_path = config["path"]
    lml_path_entry.insert(0, lml_path if lml_path else "")
    lml_browse_button = ctk.CTkButton(settings_container_frame, text="Browse", command=lambda: browse_folder(lml_path_entry), fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 16, "bold"))
    lml_browse_button.grid(row=0, column=2, sticky="nw", padx=10, pady=10)
    lml_restart_button = ctk.CTkButton(settings_container_frame, text="Apply", command=lambda: restart_program(lml_path_entry), fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 16, "bold"))
    lml_restart_button.grid(row=1, column=2, sticky="n")
    
    appearance_mode_label = ctk.CTkLabel(settings_container_frame, text="Theme:", font=("Segoe UI", 18, "bold"))
    appearance_mode_label.grid(row=3, column=0, sticky="nw", padx=10, pady=10)
    appearance_mode_menu = ctk.CTkOptionMenu(
        settings_container_frame,
        values=["Light", "Dark", "System"],
        command=change_appearance_mode,
        fg_color="#b22222",
        button_color="#b22222",
        button_hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        dropdown_text_color="white",
        dropdown_fg_color="#2b2b2b"
    )
    appearance_mode_menu.grid(row=3, column=1, sticky="nw", padx=10, pady=10)
    appearance_mode_menu.set(load_config()["theme"])
    
    clean_button = ctk.CTkButton(settings_container_frame, text="Clean Mods", command=lambda: [clean_mods(lml_folder), update_restore_button_state(lml_folder, restore_button)], fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 16, "bold"))
    clean_button.grid(row=4, column=0, sticky="n", pady=(50, 15))
    
    restore_button = ctk.CTkButton(settings_container_frame, text="Restore Mods", command=lambda: [restore_mods(lml_folder), update_restore_button_state(lml_folder, restore_button)], fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 16, "bold"))
    restore_button.grid(row=4, column=1, sticky="nw", pady=(50, 15), padx=10)
    
    update_restore_button_state(lml_folder, restore_button)
    
    backup_label = ctk.CTkLabel(settings_container_frame, text="Allows you to play RDO safely.\nMods are stored in 'Red Dead Redemption 2\\LMCCT'.\nRun as Administrator or Take Ownership of your game folder if you have issues.", justify="left", text_color="grey", font=("Segoe UI", 16, "bold"))
    backup_label.grid(row=5, columnspan=2, column=0, sticky="nw", padx=10)
    
    show_home_frame()

    main_window.update_idletasks()
    
    screen_width = main_window.winfo_screenwidth()
    screen_height = main_window.winfo_screenheight()
    initial_width = min(1200, int(screen_width * 0.9))
    initial_height = min(800, int(screen_height * 0.9))

    x = max(0, (screen_width - initial_width) // 2)
    y = max(0, (screen_height - initial_height) // 2)

    main_window.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
    main_window.wm_minsize(1200, 600)
    main_window.resizable(True, True)

    main_window.deiconify()
    main_window.protocol("WM_DELETE_WINDOW", app.quit)

def main():
    app = ctk.CTk()
    app.title("LML Mod Conflict Checker Tool")
    
    icon_path = os.path.join(IMG_DIR, "lmcct.ico")
    app.iconbitmap(icon_path)

    splash_root = show_splash()

    def after_splash():
        global config
        
        splash_root.destroy()
        
        config = load_config()
        saved_path = config["path"]
        theme = config["theme"]
        
        ctk.set_appearance_mode(theme)
        
        if saved_path:
            check_conflicts(app, saved_path)
        else:
            ctk.CTkLabel(app, text="Enter LML Folder Path:", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="e")
            lml_path = search_lml_folder()
            entry = ctk.CTkEntry(app, width=400, font=("Segoe UI", 14, "bold"))
            entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

            browse_button = ctk.CTkButton(app, text="Browse", command=lambda: browse_folder(entry), fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 16, "bold"))
            browse_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")
            
            check_button = ctk.CTkButton(app, text="Continue", command=lambda: check_and_save_path(app, entry), fg_color="#b22222", hover_color="#8b0000", font=("Segoe UI", 16, "bold"))
            check_button.grid(row=1, column=0, columnspan=3, pady=20)

            if lml_path:
                entry.insert(0, lml_path)

            app.update_idletasks()  
            
            screen_width = app.winfo_screenwidth()
            screen_height = app.winfo_screenheight()
            initial_width = min(800, int(screen_width * 0.9))
            initial_height = min(120, int(screen_height * 0.9))

            x = max(0, (screen_width - initial_width) // 2)
            y = max(0, (screen_height - initial_height) // 2)

            app.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
            app.wm_minsize(initial_width, initial_height)
            app.resizable(True, True)
            
            app.deiconify()

    splash_root.after(1500, after_splash)

    app.withdraw()
    app.mainloop()

if __name__ == "__main__":
    main()
