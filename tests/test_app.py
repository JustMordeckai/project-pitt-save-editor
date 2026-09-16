import tkinter as tk

import pytest

from pitt_save import app as app_module
from pitt_save import store, theme


@pytest.fixture(scope="session")
def tk_root():
    # One Tk interpreter per process: recreating one can fail on Windows (auto.tcl).
    try:
        window = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available")
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture
def root(tk_root):
    window = tk.Toplevel(tk_root)
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture
def ui(root, save_dir, tmp_path, monkeypatch):
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(app_module.messagebox, "showerror", lambda *a, **k: pytest.fail(f"error dialog: {a}"))
    return app_module.App(root, save_dir, backup_root=tmp_path / "backups",
                          game_running=lambda: False, mode="dark")


def show(ui, index):
    ui.notebook.select(index)
    ui.refresh_current_tab()
    return ui.tabs[index]


def test_all_tabs_render(ui):
    assert ui.doc.data["game_state"]["money"] == "6"
    for index in range(len(ui.tabs)):
        show(ui, index)
    levels = ui.tabs[1]
    assert levels.trees["products"].get_children("products/duck")


def test_edit_money_and_save(ui, save_dir):
    resources = show(ui, 0)
    resources.vars["money"].set("6000")
    assert ui.dirty
    ui.save()
    assert not ui.dirty
    assert store.load(save_dir / "savegame.save", 0).data["game_state"]["money"] == "6000"


def test_invalid_money_blocks_save(ui, save_dir, monkeypatch):
    errors = []
    monkeypatch.setattr(app_module.messagebox, "showerror", lambda *a, **k: errors.append(a))
    before = (save_dir / "savegame.save").read_bytes()
    resources = show(ui, 0)
    resources.vars["money"].set("1e9")
    ui.save()
    assert errors
    assert (save_dir / "savegame.save").read_bytes() == before


def test_resource_error_names_remaining_invalid_field(ui):
    resources = show(ui, 0)
    resources.vars["total_money_spent"].set("xyz")
    resources.vars["money"].set("abc")
    resources.vars["money"].set("10")
    text = resources.error.cget("text")
    assert text.startswith("total_money_spent:")
    assert "\nmoney:" not in text and not text.startswith("money:")
    assert resources.has_errors()


def test_progress_and_json_edits(ui):
    progress = show(ui, 2)
    progress.ms_tree.focus("unlock_sprint")
    progress._toggle_milestone("unlock_sprint")
    assert "unlock_sprint" not in ui.doc.data["unlocked_milestones"]

    json_tab = show(ui, 3)
    iid = next(i for i, path in json_tab.paths.items() if path == ("phase",))
    json_tab.tree.selection_set(iid)
    json_tab._on_select(None)
    json_tab.value_var.set("2")
    json_tab._apply()
    assert ui.doc.data["phase"] == 2


def test_theme_toggle_switches_palette(ui):
    assert ui.mode == "dark"
    assert ui.theme_button.cget("text").endswith("Light")
    ui.toggle_theme()
    assert ui.mode == "light"
    assert ui.theme_button.cget("text").endswith("Dark")
    ui.toggle_theme()
    assert ui.mode == "dark"


def test_theme_styles_use_palette_colors(root):
    from tkinter import ttk
    colors = theme.apply(root, "dark")
    assert colors is theme.PALETTES["dark"]
    style = ttk.Style(root)
    assert style.lookup("Treeview", "background") == colors["panel"]
    assert style.lookup("Error.TLabel", "foreground") == colors["error"]
    assert isinstance(theme.system_prefers_dark(), bool)
