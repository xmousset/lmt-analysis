import tkinter as tk
from tkinter import filedialog, messagebox

def start_processing():
    # Add your analysis logic here
    messagebox.showinfo("Processing")
    # Save results as needed


root = tk.Tk()
root.title("Analysis Tool")
root.geometry("400x300")

analysis = {
    "Alpha": tk.BooleanVar(),
    "Bravo": tk.BooleanVar(),
    "Charlie": tk.BooleanVar(),
    "Delta": tk.BooleanVar(),
    "Echo": tk.BooleanVar(),
    "Foxtrot": tk.BooleanVar(),
    "Golf": tk.BooleanVar(),
    "Hotel": tk.BooleanVar(),
    "India": tk.BooleanVar(),
    "Juliet": tk.BooleanVar(),
    "Kilo": tk.BooleanVar(),
    "Lima": tk.BooleanVar(),
    "Mike": tk.BooleanVar(),
    "November": tk.BooleanVar(),
    "Oscar": tk.BooleanVar(),
    "Papa": tk.BooleanVar(),
    "Quebec": tk.BooleanVar(),
    "Romeo": tk.BooleanVar(),
    "Sierra": tk.BooleanVar(),
    "Tango": tk.BooleanVar(),
    "Uniform": tk.BooleanVar(),
    "Victor": tk.BooleanVar(),
    "Whiskey": tk.BooleanVar(),
    "X-ray": tk.BooleanVar(),
    "Yankee": tk.BooleanVar(),
    "Zulu": tk.BooleanVar(),
}

max_buttons_in_column = 10
for i, (name, var) in enumerate(analysis.items()):
    row = i % max_buttons_in_column
    column = i // max_buttons_in_column
    tk.Checkbutton(root, text= name, variable= var).grid(row=row, column=column)

tk.Button(root, text="Start Processing", command=start_processing).grid(row=max_buttons_in_column + 1, column=0, sticky="w")

root.mainloop()