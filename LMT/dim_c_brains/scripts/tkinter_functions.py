import tkinter as tk
from tkinter import filedialog

from pathlib import Path


def select_sqlite_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select SQLite file",
        filetypes=[("SQLite files", "*.sqlite"), ("All files", "*.*")],
    )
    root.destroy()
    return Path(file_path)


def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder")
    root.destroy()
    return Path(folder_path)
