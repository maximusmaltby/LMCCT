import os
import sys
import string
import requests
import webbrowser
from CTkListbox import *
from PIL import Image, ImageTk
import customtkinter as ctk
from customtkinter import CTkImage
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from tkinter import filedialog

ctk.set_appearance_mode("dark")

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
    IMG_DIR = os.path.join(base_path, 'lib', 'img')
    CONFIG_PATH = os.path.join(base_path, 'lib', 'lmcct.dat')
else:
    base_path = os.path.dirname(__file__)
    IMG_DIR = os.path.join(base_path, 'img')
    CONFIG_PATH = os.path.join(base_path, 'lib', 'lmcct.dat')

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

def get_mods_and_files(lml_folder):
    file_map = defaultdict(list)
    ignored_files = {"install.xml", "strings.gxt2"}

    for mod_folder in os.listdir(lml_folder):
        mod_path = os.path.join(lml_folder, mod_folder)
        if os.path.isdir(mod_path):
            for root, _, files in os.walk(mod_path):
                for file in files:
                    if file.lower() in ignored_files:
                        continue
                    priority = 2 if "stream" in root.lower() else 1 if "replace" in root.lower() else 0
                    file_map[file.lower()].append((mod_folder, priority))
    return file_map

def find_conflicts(file_map):
    conflicts = {}
    for file, mods in file_map.items():
        unique_mods = {mod for mod, _ in mods}
        if len(unique_mods) > 1:
            conflicts[file] = mods
    return conflicts

def get_load_order(mods_xml_path):
    tree = ET.parse(mods_xml_path)
    root = tree.getroot()
    return [mod.text for mod in root.find("LoadOrder")]
    
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
        mod_element.text = mod
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
            
def open_nexus_link():
    webbrowser.open("https://www.nexusmods.com/reddeadredemption2/mods/5180")

def display_conflict_summary(app, mods, conflicts, lml_folder):
    load_order = get_load_order(os.path.join(lml_folder, "mods.xml"))
    sorted_mods = [mod for mod in load_order if mod in mods]
    
    conflict_window = ctk.CTkToplevel(app)
    conflict_window.withdraw()
    conflict_window.title("LML Mod Conflict Checker Tool")
    conflict_window.geometry("1100x800")
    conflict_window.resizable(False, False)
    
    conflict_window.grid_rowconfigure(0, weight=1)
    conflict_window.grid_rowconfigure(1, weight=1)
    conflict_window.grid_rowconfigure(2, weight=1)
    
    conflict_window.grid_columnconfigure(0, weight=0)
    conflict_window.grid_columnconfigure(1, weight=1)
    conflict_window.grid_columnconfigure(2, weight=7)
    conflict_window.grid_columnconfigure(4, weight=1)

    icon_path = os.path.join(IMG_DIR, "lmcct.ico")
    conflict_window.after(201, lambda: conflict_window.iconbitmap(icon_path))

    sidebar_frame = ctk.CTkFrame(conflict_window, corner_radius=0)
    sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsw")
    sidebar_frame.grid_rowconfigure(5, weight=1)

    dark_image_path = os.path.join(IMG_DIR, "lmcct_dark.png")
    light_image_path = os.path.join(IMG_DIR, "lmcct_light.png")
    sidebar_dark_image = Image.open(dark_image_path).convert("RGBA")
    sidebar_light_image = Image.open(light_image_path).convert("RGBA")
    sidebar_ctk_image = ctk.CTkImage(dark_image=sidebar_dark_image, light_image=sidebar_light_image, size=(224, 77))
    sidebar_image_label = ctk.CTkLabel(sidebar_frame, image=sidebar_ctk_image, fg_color="transparent", text="")
    sidebar_image_label.grid(row=0, column=0, padx=25, pady=(40, 200))

    home_frame = ctk.CTkFrame(conflict_window, width=550, height=550, fg_color="transparent")
    home_frame.grid(row=0, column=2, columnspan=1, sticky="nsew")
    
    background_image_path = os.path.join(IMG_DIR, "background.png")
    background_image = ctk.CTkImage(Image.open(background_image_path), size=(850, 800))

    background_label = ctk.CTkLabel(home_frame, image=background_image, text="", fg_color="transparent")
    background_label.grid(row=0, column=0, rowspan=3, columnspan=1, sticky="nsew")
    
    home_frame.grid_rowconfigure(0, weight=1)
    home_frame.grid_rowconfigure(1, weight=1)
    home_frame.grid_columnconfigure(0, weight=1)

    mods_frame = ctk.CTkFrame(conflict_window, width=550, height=550, fg_color="transparent")
    conflicts_frame = ctk.CTkFrame(conflict_window, width=550, height=550, fg_color="transparent")

    def show_home_frame():
        home_frame.grid(row=0, column=2, columnspan=1, sticky="nswe")
        mods_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.grid_forget()

        home_button.configure(fg_color="#8b0000")
        mods_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#b22222")

    def show_mods_frame():
        mods_frame.grid(row=1, column=2, columnspan=1, sticky="nswe")
        home_frame.grid_forget()
        conflicts_frame.grid_forget()
        button_frame.grid(row=1, column=3, padx=5)

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#8b0000")
        conflicts_button.configure(fg_color="#b22222")

    def show_conflicts_frame():
        conflicts_frame.grid(row=1, column=2, columnspan=1, sticky="nswe")
        home_frame.grid_forget()
        mods_frame.grid_forget()
        button_frame.grid_forget()

        home_button.configure(fg_color="#b22222")
        mods_button.configure(fg_color="#b22222")
        conflicts_button.configure(fg_color="#8b0000")
    
    def change_appearance_mode(new_mode):
        ctk.set_appearance_mode(new_mode)

    home_button = ctk.CTkButton(sidebar_frame, text="Home", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_home_frame)
    home_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

    mods_button = ctk.CTkButton(sidebar_frame, text="Mods", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=10, command=show_mods_frame)
    mods_button.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

    conflicts_button = ctk.CTkButton(sidebar_frame, text="Conflicts", font=("Segoe UI", 18, "bold"), fg_color="#b22222", hover_color="#8b0000", height=40, border_spacing=8, command=show_conflicts_frame)
    conflicts_button.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
    
    appearance_mode_menu = ctk.CTkOptionMenu(
        sidebar_frame,
        values=["Light", "Dark", "System"],
        command=change_appearance_mode,
        fg_color="#b22222",
        button_color="#b22222",
        button_hover_color="#8b0000",
        font=("Segoe UI", 18, "bold"),
        dropdown_text_color="white",
    )
    appearance_mode_menu.grid(row=5, column=0, sticky="s", padx=10, pady=(5, 110))
    appearance_mode_menu.set("Dark")
    
    version_label = ctk.CTkLabel(sidebar_frame, text="Version 1.2.0", font=("Segoe UI", 18, "bold"))
    version_label.grid(row=5, column=0, sticky="s", padx=10, pady=0)
    
    nexus_label = ctk.CTkButton(
        sidebar_frame,
        text="Nexus Mods",
        font=("Segoe UI", 18, "bold"),
        fg_color="transparent",
        hover_color=sidebar_frame.cget("fg_color"),
        text_color="#b22222",
        command=open_nexus_link
    )
    nexus_label.grid(row=6, column=0, sticky="s", padx=10, pady=10)

    home_label = ctk.CTkLabel(
        home_frame, 
        text="\n     Now there is no need to manually search through your mod folders to check for conflicts!     \n"
             "This simple tool will iterate through the mods in your LML folder and check for any\n"
             "duplicate file names. It will then list the files that are conflicting, the mods\n"
             "they are being edited by, and where they currently are in the load order.\n\n"
             "Now with load order configuration!\n\n\n"
             "Version 1.2.0 changelog:\n"
             "- Major GUI update.\n"
             "- Added load order configuration.\n"
             "- Updated icon.\n"
             "- LML path is now saved.\n"
             "- Many bug fixes.\n",
        font=("Segoe UI", 16, "bold")
    )
    home_label.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="n")

    mods_header_frame = ctk.CTkFrame(mods_frame)
    mods_header_frame.pack(fill="x", anchor="nw", pady=(0, 5))
    ctk.CTkLabel(mods_header_frame, text="Mods", font=("Segoe UI", 22, "bold")).pack(side="left", padx=5)

    open_lml_button = ctk.CTkButton(
        mods_header_frame,
        text="Browse LML Folder",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        width=30,
        height=30,
        command=lambda: open_lml_folder(lml_folder)
    )
    open_lml_button.pack(side="right", padx=10, pady=10)

    browse_button = ctk.CTkButton(
        mods_header_frame,
        text="Open Mod Folder",
        state="disabled",
        fg_color="#b22222",
        hover_color="#8b0000",
        font=("Segoe UI", 16, "bold"),
        width=30,
        height=30,
        command=lambda: open_mod_folder(mod_listbox.get(), lml_folder)
    )
    browse_button.pack(side="right", padx=10, pady=10)

    button_frame = ctk.CTkFrame(conflict_window, width=50, height=100, fg_color="transparent")

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
        mods_frame,
        command=lambda x: browse_button.configure(state="normal"),
        height=650,
        width=500,
        highlight_color="#8b0000",
        hover_color="#b22222",
        font=mod_listbox_font
    )
    mod_listbox.pack(fill="both", expand=True)

    populate_listbox(mod_listbox, sorted_mods)

    conflicts_header_frame = ctk.CTkFrame(conflicts_frame)
    conflicts_header_frame.pack(fill="x", anchor="nw", pady=(0, 5))
    ctk.CTkLabel(conflicts_header_frame, text="Conflicts", font=("Segoe UI", 22, "bold")).pack(anchor="nw", pady=10, padx=5)

    conflict_text_frame = ctk.CTkFrame(conflicts_frame, fg_color="transparent")
    conflict_text_frame.pack(fill="both", expand=True)

    conflict_text = ctk.CTkTextbox(conflict_text_frame, wrap="word", font=("Segoe UI", 18), height=650, width=500, cursor="arrow")
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

    show_home_frame()

    conflict_window.update_idletasks()
    window_width = conflict_window.winfo_width()
    window_height = conflict_window.winfo_height()
    screen_width = conflict_window.winfo_screenwidth()
    screen_height = conflict_window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    conflict_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    conflict_window.deiconify()
    conflict_window.protocol("WM_DELETE_WINDOW", app.quit)

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

def check_conflicts(app, entry_or_path):
    selected_folder = entry_or_path.get() if hasattr(entry_or_path, "get") else entry_or_path
    lml_folder = os.path.join(selected_folder, "lml") if os.path.basename(selected_folder).lower() == "red dead redemption 2" else selected_folder
    if not os.path.isdir(lml_folder) or not os.access(lml_folder, os.R_OK):
        ctk.CTkMessagebox.show_warning(title="Error", message="Invalid or inaccessible folder path. Please select a valid LML folder.")
        return

    file_map = get_mods_and_files(lml_folder)
    conflicts = find_conflicts(file_map)
    mods = [mod for mod in os.listdir(lml_folder) if os.path.isdir(os.path.join(lml_folder, mod))]
    
    display_conflict_summary(app, mods, conflicts, lml_folder)
    app.withdraw()

def get_config_path():
    """Return the path to the configuration file in a user-writable location."""
    appdata_dir = os.getenv('APPDATA')
    app_folder = os.path.join(appdata_dir, 'LML Mod Conflict Checker Tool')
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, 'lmcct.dat')

def load_lml_path():
    """Load the LML path from the configuration file in a user-writable location."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            path = file.read().strip()
            if os.path.isdir(path):
                return path
    return None

def save_lml_path(path):
    """Save the LML path to the configuration file in a user-writable location."""
    config_path = get_config_path()
    with open(config_path, 'w') as file:
        file.write(path)
        
def check_and_save_path(app, entry):
    """Check the provided LML path, save it if valid, and display conflicts if accessible."""
    selected_folder = entry.get()
    lml_folder = os.path.join(selected_folder, "lml") if os.path.basename(selected_folder).lower() == "red dead redemption 2" else selected_folder
    if os.path.isdir(lml_folder) and os.access(lml_folder, os.R_OK):
        save_lml_path(lml_folder)
        check_conflicts(app, lml_folder)
    else:
        ctk.CTkMessagebox.show_warning(title="Error", message="Invalid or inaccessible folder path. Please select a valid LML folder.")

def show_splash():
    splash_width, splash_height = 600, 350
    splash_root = ctk.CTkToplevel()
    splash_root.overrideredirect(True)
    screen_width, screen_height = splash_root.winfo_screenwidth(), splash_root.winfo_screenheight()
    x, y = (screen_width - splash_width) // 2, (screen_height - splash_height) // 2
    splash_root.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    header_img = load_image("header.webp", splash_width, splash_height)
    if header_img:
        splash_label = ctk.CTkLabel(splash_root, image=header_img, text="")
        splash_label.pack()
    return splash_root

def main():
    app = ctk.CTk()
    app.title("LML Mod Conflict Checker Tool")
    app.geometry("800x120")
    app.resizable(False, False)
    
    icon_path = os.path.join(IMG_DIR, "lmcct.ico")
    app.iconbitmap(icon_path)

    splash_root = show_splash()

    def after_splash():
        splash_root.destroy()
        
        saved_path = load_lml_path()
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
            window_width = app.winfo_width()
            window_height = app.winfo_height()
            screen_width = app.winfo_screenwidth()
            screen_height = app.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            app.geometry(f"{window_width}x{window_height}+{x}+{y}")
            app.deiconify()

    splash_root.after(1500, after_splash)

    app.withdraw()
    app.mainloop()


if __name__ == "__main__":
    main()