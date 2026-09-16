"""Light and dark themes, built from ttk styles only so switching applies live."""
import tkinter as tk
from tkinter import ttk

PALETTES = {
    "dark": {
        "bg": "#1e1f22", "panel": "#26282c", "field": "#16171a", "heading": "#2f3237",
        "text": "#e6e8ec", "hint": "#9aa1ab", "error": "#ff7a7a", "status": "#f0b429",
        "accent": "#5b9dff", "border": "#3a3d42", "selection": "#2f5d9e", "on_selection": "#ffffff",
    },
    "light": {
        "bg": "#f4f5f7", "panel": "#ffffff", "field": "#ffffff", "heading": "#eceff3",
        "text": "#1f2328", "hint": "#5c6570", "error": "#b00020", "status": "#8a5a00",
        "accent": "#0a66c2", "border": "#d0d5dd", "selection": "#cfe2ff", "on_selection": "#1f2328",
    },
}
DEFAULT_FONT = ("Segoe UI", 10)


def system_prefers_dark() -> bool:
    """True when Windows is set to dark app mode (False anywhere else)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
    except (ImportError, OSError):
        return False


def apply(root: tk.Misc, mode: str) -> dict:
    """Style every widget class used by the editor. Returns the palette."""
    colors = PALETTES[mode]
    style = ttk.Style(root)
    style.theme_use("clam")
    root.tk.call("tk", "scaling", root.tk.call("tk", "scaling"))  # keep current scaling
    try:
        root.winfo_toplevel().configure(background=colors["bg"])
    except tk.TclError:
        pass

    style.configure(".", background=colors["bg"], foreground=colors["text"], font=DEFAULT_FONT,
                    fieldbackground=colors["field"], bordercolor=colors["border"],
                    lightcolor=colors["panel"], darkcolor=colors["panel"],
                    troughcolor=colors["panel"], focuscolor=colors["accent"])

    style.configure("TLabel", background=colors["bg"], foreground=colors["text"])
    style.configure("Hint.TLabel", foreground=colors["hint"])
    style.configure("Error.TLabel", foreground=colors["error"])
    style.configure("Status.TLabel", foreground=colors["status"])
    style.configure("Heading.TLabel", foreground=colors["text"], font=(DEFAULT_FONT[0], 10, "bold"))

    style.configure("TFrame", background=colors["bg"])
    style.configure("TLabelframe", background=colors["bg"], bordercolor=colors["border"])
    style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["hint"])

    style.configure("TButton", background=colors["panel"], foreground=colors["text"],
                    bordercolor=colors["border"], padding=(12, 5))
    style.map("TButton",
              background=[("pressed", colors["selection"]), ("active", colors["heading"])],
              foreground=[("disabled", colors["hint"])])
    style.configure("Accent.TButton", background=colors["accent"], foreground=colors["on_selection"])
    style.map("Accent.TButton", background=[("active", colors["selection"])])

    for entry in ("TEntry", "TSpinbox", "TCombobox"):
        style.configure(entry, fieldbackground=colors["field"], foreground=colors["text"],
                        bordercolor=colors["border"], insertcolor=colors["text"],
                        arrowcolor=colors["text"], padding=4)
        style.map(entry,
                  fieldbackground=[("readonly", colors["field"]), ("disabled", colors["bg"])],
                  foreground=[("disabled", colors["hint"])],
                  arrowcolor=[("disabled", colors["hint"])])
    root.option_add("*TCombobox*Listbox.background", colors["field"])
    root.option_add("*TCombobox*Listbox.foreground", colors["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", colors["selection"])
    root.option_add("*TCombobox*Listbox.selectForeground", colors["on_selection"])

    style.configure("TCheckbutton", background=colors["bg"], foreground=colors["text"],
                    indicatorcolor=colors["field"], focuscolor=colors["bg"])
    style.map("TCheckbutton",
              indicatorcolor=[("selected", colors["accent"]), ("disabled", colors["bg"])],
              foreground=[("disabled", colors["hint"])])

    style.configure("TNotebook", background=colors["bg"], bordercolor=colors["border"], tabmargins=(2, 6, 2, 0))
    style.configure("TNotebook.Tab", background=colors["panel"], foreground=colors["hint"],
                    bordercolor=colors["border"], padding=(14, 7))
    style.map("TNotebook.Tab",
              background=[("selected", colors["bg"])],
              foreground=[("selected", colors["text"])])

    style.configure("Treeview", background=colors["panel"], fieldbackground=colors["panel"],
                    foreground=colors["text"], bordercolor=colors["border"], rowheight=24)
    style.map("Treeview",
              background=[("selected", colors["selection"])],
              foreground=[("selected", colors["on_selection"])])
    style.configure("Treeview.Heading", background=colors["heading"], foreground=colors["hint"],
                    padding=(8, 6), relief="flat")
    style.map("Treeview.Heading", background=[("active", colors["selection"])])

    style.configure("Vertical.TScrollbar", background=colors["panel"], troughcolor=colors["bg"],
                    bordercolor=colors["border"], arrowcolor=colors["hint"])
    style.map("Vertical.TScrollbar", background=[("active", colors["selection"])])
    return colors
