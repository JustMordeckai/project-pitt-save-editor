"""Main editor window."""
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from . import store, theme
from .tabs import JsonTab, LevelsTab, ProgressTab, ResourcesTab

WINDOW_TITLE = "PITT Save Editor"
BACKUP_ROOT = Path(__file__).resolve().parent.parent / "backups"


class App(ttk.Frame):
    def __init__(self, master: tk.Tk | tk.Toplevel, save_dir: Path, backup_root: Path = BACKUP_ROOT,
                 game_running=store.is_game_running, mode: str | None = None):
        super().__init__(master, padding=14)
        self.master = master
        self.save_dir = save_dir
        self.backup_root = backup_root
        self.game_running = game_running
        self.doc: store.SaveDocument | None = None
        self.dirty = False
        self.slots: list[store.SlotInfo] = []
        self._slot_index = -1
        self.mode = mode or ("dark" if theme.system_prefers_dark() else "light")
        theme.apply(master, self.mode)

        bar = ttk.Frame(self)
        bar.pack(fill="x")
        ttk.Label(bar, text="Slot").pack(side="left", padx=(0, 8))
        self.slot_box = ttk.Combobox(bar, state="readonly", width=46)
        self.slot_box.pack(side="left", padx=(0, 12))
        self.slot_box.bind("<<ComboboxSelected>>", lambda e: self.open_selected())
        ttk.Button(bar, text="Reload", command=self.open_selected).pack(side="left")
        ttk.Button(bar, text="Save", style="Accent.TButton", command=self.save).pack(side="left", padx=8)
        self.theme_button = ttk.Button(bar, command=self.toggle_theme)
        self.theme_button.pack(side="right")
        self.status = ttk.Label(bar, text="", style="Status.TLabel")
        self.status.pack(side="left", padx=12)
        self._update_theme_button()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=(14, 0))
        self.tabs = [tab(self.notebook, lambda: self.set_dirty(True))
                     for tab in (ResourcesTab, LevelsTab, ProgressTab, JsonTab)]
        for tab in self.tabs:
            self.notebook.add(tab, text=tab.title)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_current_tab())
        master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_slots()

    def toggle_theme(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        theme.apply(self.master, self.mode)
        self._update_theme_button()

    def _update_theme_button(self):
        self.theme_button.configure(text="☀  Light" if self.mode == "dark" else "☾  Dark")

    def _slot_labels(self) -> list[str]:
        return [f"Slot {info.slot} · money {info.summary.get('money', '?')} · phase {info.summary.get('phase', '?')}"
                for info in self.slots]

    def refresh_slots(self):
        self.slots = store.list_slots(self.save_dir) if self.save_dir.exists() else []
        self.slot_box["values"] = self._slot_labels()
        if not self.slots:
            self.status.configure(text=f"No save found in {self.save_dir}")
            return
        self.slot_box.current(0)
        self.open_selected()

    def open_selected(self):
        index = self.slot_box.current()
        if index < 0:
            return
        if self.dirty and not messagebox.askyesno(
                "Unsaved changes", "Discard your current changes?", parent=self):
            self.slot_box.current(self._slot_index)
            return
        info = self.slots[index]
        try:
            self.doc = store.load(info.path, info.slot)
        except store.StoreError as error:
            messagebox.showerror("Cannot open save", str(error), parent=self)
            return
        self._slot_index = index
        self.set_dirty(False)
        self.refresh_current_tab()

    def refresh_current_tab(self):
        if self.doc is None:
            return
        for tab in self.tabs:
            tab.flush()
        self.notebook.nametowidget(self.notebook.select()).load(self.doc.data)

    def set_dirty(self, dirty: bool):
        self.dirty = dirty
        self.status.configure(text="● unsaved changes" if dirty else "")
        self.master.title(("* " if dirty else "") + WINDOW_TITLE)

    def save(self):
        if self.doc is None:
            return
        for tab in self.tabs:
            tab.flush()
        invalid = [tab.title for tab in self.tabs if tab.has_errors()]
        if invalid:
            messagebox.showerror("Invalid values",
                                 "Fix the highlighted fields first: " + ", ".join(invalid), parent=self)
            return
        try:
            result = store.write(self.doc, self.backup_root, game_running=self.game_running)
        except (store.StoreError, OSError) as error:
            messagebox.showerror("Save failed", str(error), parent=self)
            return
        self.set_dirty(False)
        self.slots = store.list_slots(self.save_dir)
        self.slot_box["values"] = self._slot_labels()
        self.slot_box.current(self._slot_index)
        message = f"Save written.\n\nBackup:\n{result.backup_dir}"
        if result.warning:
            message += f"\n\nWarning: {result.warning}"
        messagebox.showinfo("Saved", message, parent=self)

    def on_close(self):
        if self.dirty and not messagebox.askyesno(
                "Quit", "You have unsaved changes. Quit anyway?", parent=self):
            return
        self.master.destroy()


def main():
    try:  # crisp text on scaled displays
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("1000x720")
    root.minsize(820, 560)
    App(root, store.default_save_dir()).pack(fill="both", expand=True)
    root.mainloop()
