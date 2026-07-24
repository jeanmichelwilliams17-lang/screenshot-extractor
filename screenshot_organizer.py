"""
Screenshot Session Organizer
-----------------------------
A tiny desktop tool to speed up naming/organizing document screenshots.
Works the same on Windows and Mac (just needs Python 3 installed).

WORKFLOW:
1. Click "Create New Folder" -> type Year + Subject -> creates a folder
   like "2026_Biology" on your Desktop and opens it.
2. Click "Start Auto-Move" -> the tool now watches wherever your screen
   capture tool normally saves images (Pictures\\Screenshots on Windows,
   Desktop on Mac) and automatically moves any new screenshot into your
   session folder within a couple seconds. Just snip normally - nothing
   to save manually.
3. Get an ordered list of diagram/figure names (e.g. ask Claude to read
   your PDF and list the figures in the order they appear), then paste
   that list into the big text box - one name per line, same order as
   the document.
4. Click "Rename Screenshots" -> pick the folder with your images -> the
   tool sorts the images by the order they were created and renames them
   to match your list:
       01_Cell_Structure.png
       02_Mitosis_Phases.png
       ...

NOTE ON WINDOWS: auto-save to Pictures\\Screenshots only works if you're
using the modern Snipping Tool on Windows 11 (it's on by default there).
If you're on Windows 10's older Snip & Sketch, there's no auto-save, so
either upgrade the app via the Microsoft Store, or point "Source folder"
below at wherever you do manually save your snips.

HOW TO RUN:
See README.txt - after one-time setup, use Start_Windows.bat (Windows)
or Start_Mac.command (Mac) to launch this with a double-click.
"""

import os
import sys
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}


def default_screenshot_folder() -> Path:
    """Best guess at where the OS/snipping tool saves screenshots by default."""
    if sys.platform.startswith("win"):
        # OneDrive screenshots folder
        guess = Path(r"C:\Users\ralme\OneDrive\Pictures\Screenshots 1")
        return guess if guess.exists() else Path.home() / "Pictures"
    elif sys.platform == "darwin":
        # macOS saves screenshots straight to the Desktop by default
        return Path.home() / "Desktop"
    else:
        return Path.home()


def sanitize(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^\w\s\-]", "", name)  # strip punctuation
    name = re.sub(r"\s+", "_", name)  # spaces -> underscores
    return name or "untitled"


def open_folder(path: Path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CAPE Screenshot Organizer")
        self.geometry("620x760")
        self.current_folder = None
        self.watching = False
        self.pending = {}  # path -> last seen size, waiting to confirm write finished

        tk.Label(
            self, text="Step 1: Start a session folder", font=("Segoe UI", 12, "bold")
        ).pack(pady=(15, 5))

        frame = tk.Frame(self)
        frame.pack(pady=5)
        tk.Label(frame, text="Year:").grid(row=0, column=0, padx=5)
        self.year_entry = tk.Entry(frame, width=10)
        self.year_entry.insert(0, str(datetime.now().year))
        self.year_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Subject:").grid(row=0, column=2, padx=5)
        SUBJECTS = [
            "Accounting U1 P1",
            "Accounting U1 P2",
            "Accounting U2 P1",
            "Accounting U2 P2",
            "Applied Mathematics U1 P1",
            "Applied Mathematics U1 P2",
            "Applied Mathematics U2 P1",
            "Applied Mathematics U2 P2",
            "Computer Science U1 P1",
            "Computer Science U1 P2",
            "Computer Science U2 P1",
            "Computer Science U2 P2",
            "Economics U1 P1",
            "Economics U1 P2",
            "Economics U2 P1",
            "Economics U2 P2",
            "Entrepreneurship U1 P1",
            "Entrepreneurship U1 P2",
            "Entrepreneurship U2 P1",
            "Entrepreneurship U2 P2",
            "Information Technology (I.T) U1 P1",
            "Information Technology (I.T) U1 P2",
            "Information Technology (I.T) U2 P1",
            "Information Technology (I.T) U2 P2",
            "Physics U1 P1",
            "Physics U1 P2",
            "Physics U2 P1",
            "Physics U2 P2",
            "Literature U1 P1",
            "Literature U1 P2",
            "Literature U2 P1",
            "Literature U2 P2",
            "Management of Business (MOB) U1 P1",
            "Management of Business (MOB) U1 P2",
            "Management of Business (MOB) U2 P1",
            "Management of Business (MOB) U2 P2",
            "Sociology U1 P1",
            "Sociology U1 P2",
            "Sociology U2 P1",
            "Sociology U2 P2",
            "Tourism U1 P1",
            "Tourism U1 P2",
            "Tourism U2 P1",
            "Tourism U2 P2",
            "Custom...",
        ]
        self.subject_var = tk.StringVar(value=SUBJECTS[0])
        self.subject_menu = tk.OptionMenu(
            frame, self.subject_var, *SUBJECTS, command=self._on_subject_change
        )
        self.subject_menu.grid(row=0, column=3, padx=5)
        self.subject_custom = tk.Entry(frame, width=20)
        self.subject_custom.grid(row=1, column=2, columnspan=2, padx=5, pady=(4, 0))
        self.subject_custom.grid_remove()  # hidden until "Custom..." is selected

        tk.Button(self, text="Create New Folder", command=self.create_folder).pack(
            pady=8
        )

        self.folder_label = tk.Label(
            self, text="No folder created yet.", fg="gray", wraplength=560
        )
        self.folder_label.pack(pady=(0, 15))

        tk.Label(
            self,
            text="Step 2: Auto-move screenshots into that folder",
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(5, 5))

        src_frame = tk.Frame(self)
        src_frame.pack(pady=5)
        tk.Label(
            src_frame, text="Source folder (where your capture tool saves images):"
        ).pack(anchor="w")
        src_row = tk.Frame(src_frame)
        src_row.pack(fill="x")
        self.source_entry = tk.Entry(src_row, width=55)
        self.source_entry.insert(0, str(default_screenshot_folder()))
        self.source_entry.pack(side="left", padx=(0, 5))
        tk.Button(src_row, text="Browse", command=self.browse_source).pack(side="left")

        self.watch_button = tk.Button(
            self,
            text="Start Auto-Move",
            command=self.toggle_watch,
            bg="#1565c0",
            fg="white",
        )
        self.watch_button.pack(pady=8)

        self.watch_status = tk.Label(self, text="Not watching.", fg="gray")
        self.watch_status.pack()

        tk.Label(self, text="Moved files:", fg="gray").pack(pady=(8, 0))
        self.log_box = tk.Listbox(self, width=70, height=6)
        self.log_box.pack(pady=(2, 15))

        tk.Label(
            self,
            text="Step 3: Paste diagram names, one per line, in page order",
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(5, 5))
        self.names_box = tk.Text(self, width=64, height=10)
        self.names_box.pack(pady=5)

        tk.Button(
            self,
            text="Rename Screenshots",
            command=self.rename_screenshots,
            bg="#2e7d32",
            fg="white",
        ).pack(pady=15)

    def _on_subject_change(self, value):
        if value == "Custom...":
            self.subject_custom.grid()
            self.subject_custom.focus()
        else:
            self.subject_custom.grid_remove()

    def _get_subject(self) -> str:
        val = self.subject_var.get()
        if val == "Custom...":
            return self.subject_custom.get()
        return val

    def create_folder(self):
        year = sanitize(self.year_entry.get())
        subject = sanitize(self._get_subject())
        if not subject:
            messagebox.showwarning("Missing subject", "Please type a subject name.")
            return
        base = Path.home() / "Desktop"
        if not base.exists():
            base = Path.home()
        folder = base / f"{year}_{subject}"
        folder.mkdir(parents=True, exist_ok=True)
        self.current_folder = folder
        self.folder_label.config(text=f"Folder ready: {folder}", fg="green")
        open_folder(folder)

    def browse_source(self):
        folder = filedialog.askdirectory(
            title="Select the folder your screen capture tool saves to",
            initialdir=self.source_entry.get() or str(Path.home()),
        )
        if folder:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)

    def toggle_watch(self):
        if not self.watching:
            if not self.current_folder:
                messagebox.showwarning(
                    "No session folder", "Create a session folder first (Step 1)."
                )
                return
            source = Path(self.source_entry.get())
            if not source.exists():
                messagebox.showwarning(
                    "Folder not found", f"Source folder doesn't exist:\n{source}"
                )
                return
            self.watching = True
            self.pending = {}
            self.watch_button.config(text="Stop Auto-Move", bg="#c62828")
            self.watch_status.config(
                text=f"Watching {source}  ->  {self.current_folder.name}", fg="green"
            )
            self.poll_source()
        else:
            self.watching = False
            self.watch_button.config(text="Start Auto-Move", bg="#1565c0")
            self.watch_status.config(text="Not watching.", fg="gray")

    def poll_source(self):
        if not self.watching:
            return
        source = Path(self.source_entry.get())
        try:
            candidates = [f for f in source.iterdir() if f.suffix.lower() in IMAGE_EXTS]
        except Exception:
            candidates = []

        still_pending = {}
        for f in candidates:
            try:
                size = f.stat().st_size
            except Exception:
                continue
            if f in self.pending and self.pending[f] == size:
                # size unchanged since last poll -> file finished writing, safe to move
                try:
                    dest = self.current_folder / f.name
                    counter = 1
                    while dest.exists():
                        dest = self.current_folder / f"{f.stem}_{counter}{f.suffix}"
                        counter += 1
                    shutil.move(str(f), str(dest))
                    self.log_box.insert(tk.END, f"Moved: {dest.name}")
                    self.log_box.see(tk.END)
                except Exception:
                    pass
            else:
                still_pending[f] = size
        self.pending = still_pending

        # poll again in 1 second
        self.after(1000, self.poll_source)

    def rename_screenshots(self):
        names_raw = self.names_box.get("1.0", tk.END).strip().splitlines()
        names = [n for n in (line.strip() for line in names_raw) if n]
        if not names:
            messagebox.showwarning("No names", "Paste at least one diagram name first.")
            return

        folder = filedialog.askdirectory(
            title="Select the folder containing your screenshots",
            initialdir=str(self.current_folder)
            if self.current_folder
            else str(Path.home()),
        )
        if not folder:
            return
        folder = Path(folder)

        images = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTS]
        images.sort(key=lambda f: f.stat().st_mtime)  # order taken = order on disk

        if not images:
            messagebox.showwarning("No images", "No image files found in that folder.")
            return

        count = min(len(images), len(names))
        if len(images) != len(names):
            proceed = messagebox.askyesno(
                "Count mismatch",
                f"Found {len(images)} images but {len(names)} names.\n"
                f"I'll rename the first {count} in order. Continue?",
            )
            if not proceed:
                return

        width = len(str(count))
        renamed = []
        for i in range(count):
            img = images[i]
            new_name = f"{sanitize(names[i])}{img.suffix.lower()}"
            new_path = img.parent / new_name
            counter = 1
            while new_path.exists():
                new_path = (
                    img.parent
                    / f"{new_name.rsplit('.', 1)[0]}_{counter}{img.suffix.lower()}"
                )
                counter += 1
            img.rename(new_path)
            renamed.append(new_path.name)

        messagebox.showinfo(
            "Done", f"Renamed {count} screenshots:\n\n" + "\n".join(renamed)
        )


if __name__ == "__main__":
    App().mainloop()
