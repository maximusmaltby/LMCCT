import os
import sys
import string
from CTkListbox import *
from PIL import Image, ImageTk
import customtkinter as ctk
import xml.etree.ElementTree as ET
from collections import defaultdict
from tkinter import filedialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
    IMG_DIR = os.path.join(base_path, 'lib', 'img')
else:
    base_path = os.path.dirname(__file__)
    IMG_DIR = os.path.join(base_path, 'img')

def load_image(filename):
    try:
        img_path = os.path.join(IMG_DIR, filename)
        return Image.open(img_path)
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

def display_conflict_summary(app, mods, conflicts, lml_folder):
    load_order = get_load_order(os.path.join(lml_folder, "mods.xml"))
    sorted_mods = [mod for mod in load_order if mod in mods]
    
    conflict_window = ctk.CTkToplevel(app)
    conflict_window.withdraw()
    conflict_window.title("LML Mod Conflict Checker Tool")
    conflict_window.geometry("800x600")
    conflict_window.resizable(False, False)

    icon_path = os.path.join(IMG_DIR, "RDR2.ico")
    conflict_window.after(201, lambda: conflict_window.iconbitmap(icon_path))

    left_frame = ctk.CTkFrame(conflict_window, width=350, height=550)
    right_frame = ctk.CTkFrame(conflict_window, width=350, height=550)

    left_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
    right_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)

    top_left_frame = ctk.CTkFrame(left_frame)
    top_left_frame.pack(fill="x", anchor="nw", pady=(0, 5))

    ctk.CTkLabel(top_left_frame, text="Mods", font=("Inter", 18, "bold")).pack(side="left", padx=5)

    open_lml_button = ctk.CTkButton(
        top_left_frame,
        text="Browse LML Folder",
        fg_color="#b22222",
        hover_color="#8b0000",
        command=lambda: open_lml_folder(lml_folder)
    )
    open_lml_button.pack(side="left", padx=20)

    browse_button = ctk.CTkButton(
        top_left_frame,
        text="Open Mod Folder",
        state="disabled",
        fg_color="#b22222",
        hover_color="#8b0000",
        command=lambda: open_mod_folder(mod_listbox.get(), lml_folder)
    )
    browse_button.pack(side="right", padx=10)
    browse_button.pack(side="top", pady=10)

    mod_listbox = CTkListbox(
        left_frame,
        command=lambda x: browse_button.configure(state="normal"),
        height=500,
        width=350,
        highlight_color="#8b0000",
        hover_color="#b22222"
    )
    mod_listbox.pack(fill="both", expand=True)

    max_mod_name_length = max(len(mod) for mod in sorted_mods)

    for index, mod in enumerate(sorted_mods):
        if index == 0:
            mod_display = f"{mod:<{max_mod_name_length}} (Lowest Priority)"
        elif index == len(sorted_mods) - 1:
            mod_display = f"{mod:<{max_mod_name_length}} (Highest Priority)"
        else:
            mod_display = mod
        mod_listbox.insert(ctk.END, mod_display)

    ctk.CTkLabel(right_frame, text="Conflicts", font=("Inter", 18, "bold")).pack(anchor="nw", pady=10, padx=5)

    conflict_text = ctk.CTkTextbox(right_frame, wrap="word", height=500, width=350)
    conflict_text.pack(fill="both", expand=True)

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

    def update_scrollbar():
        if conflict_text.yview()[1] < 1.0:
            conflict_scrollbar.pack(side="right", fill="y")
        else:
            conflict_scrollbar.pack_forget()
    
    conflict_scrollbar = ctk.CTkScrollbar(right_frame, command=conflict_text.yview)
    conflict_text.configure(yscrollcommand=lambda *args: (conflict_scrollbar.set(*args), update_scrollbar()))

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

def open_mod_folder(selected_mod, lml_folder):
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

def check_conflicts(app, entry):
    selected_folder = entry.get()
    lml_folder = os.path.join(selected_folder, "lml") if os.path.basename(selected_folder).lower() == "red dead redemption 2" else selected_folder
    if not os.path.isdir(lml_folder) or not os.access(lml_folder, os.R_OK):
        ctk.CTkMessagebox.show_warning(title="Error", message="Invalid or inaccessible folder path. Please select a valid LML folder.")
        return

    file_map = get_mods_and_files(lml_folder)
    conflicts = find_conflicts(file_map)
    mods = [mod for mod in os.listdir(lml_folder) if os.path.isdir(os.path.join(lml_folder, mod))]
    
    display_conflict_summary(app, mods, conflicts, lml_folder)
    app.withdraw()

def show_splash():
    splash_width, splash_height = 600, 350
    splash_root = ctk.CTk()
    splash_root.overrideredirect(True)
    screen_width, screen_height = splash_root.winfo_screenwidth(), splash_root.winfo_screenheight()
    x, y = (screen_width - splash_width) // 2, (screen_height - splash_height) // 2
    splash_root.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    header_img = load_image("header.webp")
    if header_img:
        header_img = header_img.resize((splash_width, splash_height), Image.LANCZOS)
        splash_img = ImageTk.PhotoImage(header_img)
        splash_label = ctk.CTkLabel(splash_root, image=splash_img, text="")
        splash_label.pack()
        splash_root.splash_img = splash_img
        splash_root.after(2000, splash_root.destroy)
        splash_root.mainloop()
    else:
        splash_root.destroy()

def main():
    show_splash()
    
    app = ctk.CTk()
    app.title("LML Mod Conflict Checker Tool")
    app.geometry("640x120")
    app.resizable(False, False)
    
    icon_path = os.path.join(IMG_DIR, "RDR2.ico")
    app.after(201, lambda: app.iconbitmap(icon_path))

    ctk.CTkLabel(app, text="Enter LML Folder Path:").grid(row=0, column=0, padx=10, pady=10, sticky="e")

    lml_path = search_lml_folder()
    entry = ctk.CTkEntry(app, width=300)
    entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    browse_button = ctk.CTkButton(app, text="Browse", command=lambda: browse_folder(entry), fg_color="#b22222", hover_color="#8b0000")
    browse_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")
    
    check_button = ctk.CTkButton(app, text="Check Conflicts", command=lambda: check_conflicts(app, entry), fg_color="#b22222", hover_color="#8b0000")
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

    app.mainloop()

if __name__ == "__main__":
    main()
