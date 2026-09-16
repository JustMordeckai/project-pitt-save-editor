"""Editor tabs. Each tab edits the loaded save dict in place."""
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from . import catalog, model

CHECK = "✔"
CROSS = "✘"


def _scrolled_tree(parent, **options) -> ttk.Treeview:
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, **options)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return tree


class Tab(ttk.Frame):
    title = ""

    def __init__(self, master, on_change: Callable[[], None]):
        super().__init__(master, padding=14)
        self.on_change = on_change
        self.data: dict | None = None
        self.invalid: set[str] = set()

    def load(self, data: dict) -> None:
        self.data = data
        self.refresh()

    def refresh(self) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        """Commit an in-progress edit (open cell editor)."""

    def has_errors(self) -> bool:
        return bool(self.invalid)


class ResourcesTab(Tab):
    title = "Resources"

    def __init__(self, master, on_change):
        super().__init__(master, on_change)
        self._loading = False
        self.messages: dict[str, str] = {}  # error message per invalid field
        self.vars: dict[str, tk.StringVar] = {}
        self.entries: dict[str, ttk.Entry] = {}
        for row, key in enumerate(catalog.RESOURCE_FIELDS):
            ttk.Label(self, text=key).grid(row=row, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            entry = ttk.Entry(self, textvariable=var, width=40)
            entry.grid(row=row, column=1, sticky="w", padx=12)
            var.trace_add("write", lambda *_, k=key: self._changed(k))
            self.vars[key], self.entries[key] = var, entry
        last = len(catalog.RESOURCE_FIELDS)
        self.error = ttk.Label(self, text="", style="Error.TLabel")
        self.error.grid(row=last, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Label(self, style="Hint.TLabel", wraplength=660, text=(
            "Positive integers only. The game stores money as text so it can hold very large "
            "numbers, so you can type as many digits as you like."
        )).grid(row=last + 1, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def refresh(self):
        game_state = self.data.get("game_state", {})
        self._loading = True
        for key, var in self.vars.items():
            var.set(model.format_value(game_state[key]) if key in game_state else "")
            self.entries[key].configure(state="normal" if key in game_state else "disabled")
        self._loading = False
        self.invalid.clear()
        self.messages.clear()
        self.error.configure(text="")

    def _changed(self, key):
        if self._loading or self.data is None:
            return
        game_state = self.data["game_state"]
        try:
            value = model.parse_resource(game_state[key], self.vars[key].get())
        except ValueError as error:
            self.invalid.add(key)
            self.messages[key] = f"{key}: {error}"
        else:
            self.invalid.discard(key)
            self.messages.pop(key, None)
            if value != game_state[key]:
                game_state[key] = value
                self.on_change()
        self.error.configure(text="\n".join(self.messages.values()))


class LevelsTab(Tab):
    title = "Upgrades"

    def __init__(self, master, on_change):
        super().__init__(master, on_change)
        ttk.Label(self, style="Hint.TLabel", wraplength=880, text=(
            "Double-click “Enabled” to toggle it, “Level” to edit it (Enter confirms, Escape cancels). "
            "Enabling a tool or toy does not necessarily make it appear in the world."
        )).pack(anchor="w", pady=(0, 10))
        inner = ttk.Notebook(self)
        inner.pack(fill="both", expand=True)
        self.trees: dict[str, ttk.Treeview] = {}
        self.paths: dict[str, tuple[str, ...]] = {}
        self.editor = None  # (entry, var, tree, iid)
        for category in catalog.LEVEL_CATEGORIES:
            page = ttk.Frame(inner, padding=(0, 8, 0, 0))
            inner.add(page, text=category)
            tree = _scrolled_tree(page, columns=("enabled", "level"), selectmode="browse")
            tree.heading("#0", text="Item")
            tree.heading("enabled", text="Enabled")
            tree.heading("level", text="Level")
            tree.column("#0", width=320)
            tree.column("enabled", width=100, anchor="center")
            tree.column("level", width=100, anchor="center")
            tree.bind("<Double-1>", lambda event, t=tree: self._on_double_click(t, event))
            self.trees[category] = tree

    def refresh(self):
        self._close_editor(commit=False)
        game_state = self.data.get("game_state", {})
        self.paths.clear()
        for category, tree in self.trees.items():
            opened = {iid for iid in tree.get_children() if tree.item(iid, "open")}
            tree.delete(*tree.get_children())
            for node in model.level_nodes(game_state, category):
                iid = "/".join(node.path)
                tree.insert("", "end", iid=iid, text=node.path[-1], open=iid in opened,
                            values=self._values(model.get_in(game_state, node.path)))
                self.paths[iid] = node.path
                for child in node.children:
                    child_iid = "/".join(child)
                    tree.insert(iid, "end", iid=child_iid, text=child[-1],
                                values=self._values(model.get_in(game_state, child)))
                    self.paths[child_iid] = child

    @staticmethod
    def _values(item: dict) -> tuple[str, str]:
        enabled = item.get("enabled")
        enabled_text = "" if enabled is None else (CHECK if enabled else CROSS)
        level_text = model.format_value(item["level"]) if "level" in item else ""
        return enabled_text, level_text

    def _on_double_click(self, tree, event):
        iid = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not iid or self.data is None:
            return None
        item = model.get_in(self.data["game_state"], self.paths[iid])
        if column == "#1" and "enabled" in item:
            item["enabled"] = not item["enabled"]
            tree.set(iid, "enabled", CHECK if item["enabled"] else CROSS)
            self.on_change()
            return "break"
        if column == "#2" and "level" in item:
            self._open_editor(tree, iid, item)
            return "break"
        return None

    def _open_editor(self, tree, iid, item):
        self._close_editor(commit=True)
        box = tree.bbox(iid, "level")
        if not box:
            return
        x, y, width, height = box
        var = tk.StringVar(value=model.format_value(item["level"]))
        entry = ttk.Entry(tree, textvariable=var, justify="center")
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.select_range(0, "end")
        entry.bind("<Return>", lambda e: self._close_editor(commit=True))
        entry.bind("<Escape>", lambda e: self._close_editor(commit=False))
        entry.bind("<FocusOut>", lambda e: self._close_editor(commit=True))
        self.editor = (entry, var, tree, iid)

    def _close_editor(self, commit: bool):
        if self.editor is None:
            return
        entry, var, tree, iid = self.editor
        self.editor = None
        if commit and self.data is not None:
            item = model.get_in(self.data["game_state"], self.paths[iid])
            try:
                value = model.parse_count(item["level"], var.get())
            except ValueError as error:
                messagebox.showerror("Invalid level", f"{iid}: {error}", parent=self)
            else:
                if value != item["level"]:
                    item["level"] = value
                    tree.set(iid, "level", model.format_value(value))
                    self.on_change()
        entry.destroy()

    def flush(self):
        self._close_editor(commit=True)


class ProgressTab(Tab):
    title = "Progress"

    def __init__(self, master, on_change):
        super().__init__(master, on_change)
        self._loading = False
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="phase").grid(row=0, column=0, sticky="w", pady=5)
        self.phase_var = tk.StringVar()
        self.phase_box = ttk.Combobox(top, textvariable=self.phase_var, state="readonly", width=6,
                                      values=[str(phase) for phase in catalog.PHASES])
        self.phase_box.grid(row=0, column=1, sticky="w", padx=12)
        self.phase_box.bind("<<ComboboxSelected>>", lambda e: self._set_phase())
        ttk.Label(top, text="pickaxe_tier").grid(row=1, column=0, sticky="w", pady=5)
        self.tier_var = tk.StringVar()
        self.tier_entry = ttk.Spinbox(top, from_=0, to=99, textvariable=self.tier_var, width=6)
        self.tier_entry.grid(row=1, column=1, sticky="w", padx=12)
        self.tier_var.trace_add("write", lambda *_: self._set_tier())
        self.error = ttk.Label(top, text="", style="Error.TLabel")
        self.error.grid(row=1, column=2, sticky="w")

        flags = ttk.LabelFrame(self, text="Flags", padding=10)
        flags.pack(fill="x", pady=12)
        self.flag_vars: dict[str, tuple[tk.BooleanVar, ttk.Checkbutton]] = {}
        for index, flag in enumerate(catalog.FLAGS):
            var = tk.BooleanVar()
            box = ttk.Checkbutton(flags, text=flag, variable=var, command=lambda f=flag: self._set_flag(f))
            box.grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 36), pady=3)
            self.flag_vars[flag] = (var, box)

        milestones = ttk.LabelFrame(self, text="Unlocks (unlocked_milestones)", padding=10)
        milestones.pack(fill="both", expand=True)
        ttk.Label(milestones, style="Hint.TLabel", wraplength=880, text=(
            "Unlock events that have already fired (double-click or Space to toggle). "
            "To actually get an item, enable it in the Upgrades tab instead."
        )).pack(anchor="w", pady=(0, 8))
        self.ms_tree = _scrolled_tree(milestones, columns=("done",), selectmode="browse")
        self.ms_tree.heading("#0", text="Unlock")
        self.ms_tree.heading("done", text="Fired")
        self.ms_tree.column("#0", width=380)
        self.ms_tree.column("done", width=100, anchor="center")
        self.ms_tree.bind("<Double-1>", lambda e: self._toggle_milestone(self.ms_tree.identify_row(e.y)))
        self.ms_tree.bind("<space>", lambda e: self._toggle_milestone(self.ms_tree.focus()))

    def refresh(self):
        self._loading = True
        phase = self.data.get("phase")
        self.phase_var.set("" if phase is None else str(phase))
        self.phase_box.configure(state="disabled" if phase is None else "readonly")
        game_state = self.data.get("game_state", {})
        tier = game_state.get("pickaxe_tier")
        self.tier_var.set("" if tier is None else model.format_value(tier))
        self.tier_entry.configure(state="disabled" if tier is None else "normal")
        for flag, (var, box) in self.flag_vars.items():
            var.set(bool(game_state.get(flag, False)))
            box.configure(state="normal" if flag in game_state else "disabled")
        self.ms_tree.delete(*self.ms_tree.get_children())
        for name, done in model.milestone_rows(self.data):
            self.ms_tree.insert("", "end", iid=name, text=name, values=(CHECK if done else "",))
        self.invalid.clear()
        self.error.configure(text="")
        self._loading = False

    def _set_phase(self):
        if self._loading or self.data is None:
            return
        phase = int(self.phase_var.get())
        if self.data.get("phase") != phase:
            self.data["phase"] = phase
            self.on_change()

    def _set_tier(self):
        if self._loading or self.data is None:
            return
        game_state = self.data["game_state"]
        try:
            tier = model.parse_count(game_state["pickaxe_tier"], self.tier_var.get())
        except ValueError as error:
            self.invalid.add("pickaxe_tier")
            self.error.configure(text=str(error))
            return
        self.invalid.discard("pickaxe_tier")
        self.error.configure(text="")
        if tier != game_state["pickaxe_tier"]:
            game_state["pickaxe_tier"] = tier
            self.on_change()

    def _set_flag(self, flag):
        if self.data is None:
            return
        self.data["game_state"][flag] = self.flag_vars[flag][0].get()
        self.on_change()

    def _toggle_milestone(self, iid):
        if not iid or self.data is None:
            return "break"
        unlocked = self.ms_tree.set(iid, "done") != CHECK
        model.set_milestone(self.data, iid, unlocked)
        self.ms_tree.set(iid, "done", CHECK if unlocked else "")
        self.on_change()
        return "break"


class JsonTab(Tab):
    title = "Raw JSON"

    def __init__(self, master, on_change):
        super().__init__(master, on_change)
        self.tree = _scrolled_tree(self, columns=("value",), selectmode="browse")
        self.tree.heading("#0", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", width=340)
        self.tree.column("value", width=460)
        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(12, 0))
        self.path_label = ttk.Label(bottom, text="", style="Hint.TLabel")
        self.path_label.pack(anchor="w")
        row = ttk.Frame(bottom)
        row.pack(fill="x", pady=(6, 0))
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(row, textvariable=self.value_var)
        self.value_entry.pack(side="left", fill="x", expand=True)
        self.value_entry.bind("<Return>", lambda e: self._apply())
        self.apply_button = ttk.Button(row, text="Apply", command=self._apply)
        self.apply_button.pack(side="left", padx=(10, 0))
        self.paths: dict[str, tuple] = {}
        self.selected_iid: str | None = None

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.paths.clear()
        self._insert_children("", ())
        self.selected_iid = None
        self._update_editor()

    def _insert_children(self, parent_iid, path):
        container = model.get_in(self.data, path)
        items = container.items() if isinstance(container, dict) else enumerate(container)
        for key, value in items:
            iid = self.tree.insert(parent_iid, "end", text=str(key), values=(model.preview(value),))
            self.paths[iid] = path + (key,)
            if isinstance(value, (dict, list)) and value:
                self.tree.insert(iid, "end", text="…")  # replaced by real children when expanded

    def _on_open(self, event):
        iid = self.tree.focus()
        children = self.tree.get_children(iid)
        if len(children) == 1 and children[0] not in self.paths:
            self.tree.delete(children[0])
            self._insert_children(iid, self.paths[iid])

    def _on_select(self, event):
        selection = self.tree.selection()
        self.selected_iid = selection[0] if selection and selection[0] in self.paths else None
        self._update_editor()

    def _update_editor(self):
        if self.selected_iid is None:
            self.path_label.configure(text="Select a value in the tree.")
            self.value_var.set("")
            self.value_entry.configure(state="disabled")
            self.apply_button.configure(state="disabled")
            return
        path = self.paths[self.selected_iid]
        value = model.get_in(self.data, path)
        label = " › ".join(str(part) for part in path) + f"  ({model.type_name(value)})"
        editable = not isinstance(value, (dict, list))
        if not editable:
            label += ", expand it to edit its items"
        self.path_label.configure(text=label)
        self.value_entry.configure(state="normal" if editable else "disabled")
        self.apply_button.configure(state="normal" if editable else "disabled")
        self.value_var.set(model.format_value(value) if editable else "")

    def _apply(self):
        if self.selected_iid is None:
            return
        path = self.paths[self.selected_iid]
        parent = model.get_in(self.data, path[:-1])
        old = parent[path[-1]]
        try:
            new = model.coerce_like(old, self.value_var.get())
        except ValueError as error:
            messagebox.showerror("Invalid value", str(error), parent=self)
            return
        if new != old:
            parent[path[-1]] = new
            self.tree.set(self.selected_iid, "value", model.preview(new))
            self.on_change()
