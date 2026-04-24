import customtkinter as ctk
import json
import os
from datetime import datetime

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATA_FILE = "tasks.json"


# ── Data helpers ───────────────────────────────────────────────────────────────
def load_tasks() -> list:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks: list) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


# ── Task Card widget ───────────────────────────────────────────────────────────
class TaskCard(ctk.CTkFrame):
    def __init__(self, master, task, on_toggle, on_delete, **kwargs):
        super().__init__(master, corner_radius=10, fg_color="#1e1e2e", **kwargs)
        self.task = task
        self.on_toggle = on_toggle
        self.on_delete = on_delete

        self.columnconfigure(1, weight=1)

        # Checkbox
        self.var = ctk.BooleanVar(value=task["done"])
        self.cb = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.var,
            width=28,
            checkbox_width=22,
            checkbox_height=22,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self._toggle,
        )
        self.cb.grid(row=0, column=0, padx=(12, 6), pady=12)

        # Task text
        display = task["text"]
        self.label = ctk.CTkLabel(
            self,
            text=display,
            anchor="w",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                slant="roman" if not task["done"] else "italic",
            ),
            text_color="#a1a1aa" if task["done"] else "#e4e4f0",
        )
        self.label.grid(row=0, column=1, sticky="ew", padx=4)

        # Date badge
        date_str = task.get("date", "")
        if date_str:
            self.date_lbl = ctk.CTkLabel(
                self,
                text=date_str,
                font=ctk.CTkFont(size=10),
                text_color="#52525b",
            )
            self.date_lbl.grid(row=0, column=2, padx=8)

        # Delete button
        self.del_btn = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#3f1515",
            text_color="#ef4444",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._delete,
        )
        self.del_btn.grid(row=0, column=3, padx=(4, 10), pady=8)

    def _toggle(self):
        self.task["done"] = self.var.get()
        self.on_toggle()

    def _delete(self):
        self.on_delete(self.task)


# ── Main Application ───────────────────────────────────────────────────────────
class ToDoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✅  To-Do  •  Stay on track")
        self.geometry("560x680")
        self.minsize(460, 520)
        self.configure(fg_color="#0f0f1a")

        self.tasks = load_tasks()
        self.filter_mode = "all"  # all | active | done

        self._build_ui()
        self._refresh()

    # ── UI construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text="My Tasks",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#e4e4f0",
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#71717a",
        )
        self.count_lbl.pack(side="right", pady=(6, 0))

        # ── Input row ─────────────────────────────────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=12)
        input_frame.pack(fill="x", padx=24, pady=16)
        input_frame.columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Add a new task…",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=0,
            height=44,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(12, 4), pady=4)
        self.entry.bind("<Return>", lambda e: self._add_task())

        add_btn = ctk.CTkButton(
            input_frame,
            text="+ Add",
            width=80,
            height=36,
            corner_radius=8,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._add_task,
        )
        add_btn.grid(row=0, column=1, padx=(0, 8), pady=4)

        # ── Filter tabs ───────────────────────────────────────────────────────
        tabs = ctk.CTkFrame(self, fg_color="transparent")
        tabs.pack(fill="x", padx=24, pady=(0, 8))

        self.tab_btns = {}
        for label, mode in [("All", "all"), ("Active", "active"), ("Done", "done")]:
            btn = ctk.CTkButton(
                tabs,
                text=label,
                width=80,
                height=30,
                corner_radius=8,
                fg_color="#1e1e2e",
                hover_color="#2d2d42",
                font=ctk.CTkFont(size=12),
                command=lambda m=mode: self._set_filter(m),
            )
            btn.pack(side="left", padx=(0, 6))
            self.tab_btns[mode] = btn

        # Separator
        ctk.CTkFrame(self, fg_color="#2d2d42", height=1).pack(fill="x", padx=24)

        # ── Scrollable task list ──────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color="#3f3f5a"
        )
        self.scroll.pack(fill="both", expand=True, padx=16, pady=8)

        # ── Footer actions ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(4, 18))

        self.clear_btn = ctk.CTkButton(
            footer,
            text="Clear completed",
            width=140,
            height=30,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="#3f3f5a",
            hover_color="#2d1515",
            text_color="#71717a",
            font=ctk.CTkFont(size=12),
            command=self._clear_done,
        )
        self.clear_btn.pack(side="right")

    # ── Logic ──────────────────────────────────────────────────────────────────
    def _add_task(self):
        text = self.entry.get().strip()
        if not text:
            return
        task = {
            "id": datetime.now().isoformat(),
            "text": text,
            "done": False,
            "date": datetime.now().strftime("%b %d"),
        }
        self.tasks.append(task)
        self.entry.delete(0, "end")
        save_tasks(self.tasks)
        self._refresh()

    def _toggle(self):
        save_tasks(self.tasks)
        self._refresh()

    def _delete(self, task):
        self.tasks = [t for t in self.tasks if t["id"] != task["id"]]
        save_tasks(self.tasks)
        self._refresh()

    def _clear_done(self):
        self.tasks = [t for t in self.tasks if not t["done"]]
        save_tasks(self.tasks)
        self._refresh()

    def _set_filter(self, mode):
        self.filter_mode = mode
        self._refresh()

    def _refresh(self):
        # Clear list
        for w in self.scroll.winfo_children():
            w.destroy()

        # Update tab highlights
        for mode, btn in self.tab_btns.items():
            btn.configure(
                fg_color="#7c3aed" if mode == self.filter_mode else "#1e1e2e"
            )

        # Filter tasks
        if self.filter_mode == "active":
            visible = [t for t in self.tasks if not t["done"]]
        elif self.filter_mode == "done":
            visible = [t for t in self.tasks if t["done"]]
        else:
            visible = self.tasks[:]

        # Update counter
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t["done"])
        self.count_lbl.configure(text=f"{done}/{total} done")

        if not visible:
            ctk.CTkLabel(
                self.scroll,
                text="No tasks here 🎉",
                font=ctk.CTkFont(size=14),
                text_color="#3f3f5a",
            ).pack(pady=40)
            return

        for task in visible:
            card = TaskCard(
                self.scroll,
                task,
                on_toggle=self._toggle,
                on_delete=self._delete,
            )
            card.pack(fill="x", padx=4, pady=4)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ToDoApp()
    app.mainloop()
