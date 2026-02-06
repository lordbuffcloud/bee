from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

import httpx


BASE_URL = os.getenv("BEE_BASE_URL", "http://localhost:8080")


class BeeUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("B.E.E. Hive Manager")
        self.geometry("960x720")
        self.minsize(820, 640)

        self.status_vars = {
            "heartbeat": tk.StringVar(value="..."),
            "interval": tk.StringVar(value="..."),
            "last_tick": tk.StringVar(value="..."),
            "evermem": tk.StringVar(value="..."),
            "endpoint": tk.StringVar(value="..."),
            "group": tk.StringVar(value="..."),
        }
        self.heartbeat_running = False

        self.risk_var = tk.IntVar(value=5)
        self.risk_label = tk.StringVar(value="5")

        self.goal_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar()]

        self.memory_query = tk.StringVar()

        self.meta_vars = {
            "group_id": tk.StringVar(),
            "scene": tk.StringVar(value="assistant"),
            "name": tk.StringVar(),
            "description": tk.StringVar(),
            "scene_desc": tk.StringVar(),
            "timezone": tk.StringVar(),
            "tags": tk.StringVar(),
        }

        self._build_ui()
        self.refresh_status()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(root, text="B.E.E. Hive Manager", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        status_frame = ttk.LabelFrame(root, text="Status", padding=12)
        status_frame.pack(fill=tk.X, pady=(0, 12))
        self._status_row(status_frame, "Heartbeat", self.status_vars["heartbeat"], 0)
        self._status_row(status_frame, "Interval (sec)", self.status_vars["interval"], 1)
        self._status_row(status_frame, "Last tick", self.status_vars["last_tick"], 2)
        self._status_row(status_frame, "EvermemOS", self.status_vars["evermem"], 3)
        self._status_row(status_frame, "Endpoint", self.status_vars["endpoint"], 4)
        self._status_row(status_frame, "Group", self.status_vars["group"], 5)

        status_actions = ttk.Frame(status_frame)
        status_actions.grid(row=0, column=2, rowspan=6, padx=12, sticky="ne")
        self.heartbeat_button = ttk.Button(
            status_actions, text="Start Heartbeat", command=self.toggle_heartbeat
        )
        self.heartbeat_button.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(status_actions, text="Refresh", command=self.refresh_status).pack(fill=tk.X)

        settings_frame = ttk.LabelFrame(root, text="Settings", padding=12)
        settings_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(settings_frame, text="Risk Tolerance").grid(row=0, column=0, sticky="w")
        risk_scale = ttk.Scale(
            settings_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            value=5,
            command=self._on_risk_change,
        )
        risk_scale.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Label(settings_frame, textvariable=self.risk_label, width=3).grid(row=0, column=2)
        ttk.Button(settings_frame, text="Save Risk", command=self.save_risk).grid(
            row=0, column=3, padx=(8, 0)
        )
        settings_frame.columnconfigure(1, weight=1)

        goals_frame = ttk.LabelFrame(root, text="Directive Goals (3)", padding=12)
        goals_frame.pack(fill=tk.X, pady=(0, 12))
        for idx, var in enumerate(self.goal_vars):
            ttk.Entry(goals_frame, textvariable=var).grid(row=idx, column=0, sticky="ew", pady=4)
        ttk.Button(goals_frame, text="Save Goals", command=self.save_goals).grid(
            row=0, column=1, rowspan=3, padx=(12, 0), sticky="ns"
        )
        goals_frame.columnconfigure(0, weight=1)

        meta_frame = ttk.LabelFrame(root, text="Conversation Meta", padding=12)
        meta_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(meta_frame, text="Group ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["group_id"]).grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="Scene").grid(row=1, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["scene"]).grid(
            row=1, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="Name").grid(row=2, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["name"]).grid(
            row=2, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="Description").grid(row=3, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["description"]).grid(
            row=3, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="Scene Desc").grid(row=4, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["scene_desc"]).grid(
            row=4, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="Timezone").grid(row=5, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["timezone"]).grid(
            row=5, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="Tags (comma)").grid(row=6, column=0, sticky="w")
        ttk.Entry(meta_frame, textvariable=self.meta_vars["tags"]).grid(
            row=6, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(meta_frame, text="User Details (JSON)").grid(
            row=7, column=0, sticky="nw", pady=(6, 0)
        )
        self.meta_user_details = tk.Text(meta_frame, height=6, wrap="word")
        self.meta_user_details.grid(
            row=7, column=1, sticky="ew", padx=(0, 8), pady=(6, 0)
        )
        meta_actions = ttk.Frame(meta_frame)
        meta_actions.grid(row=0, column=2, rowspan=8, sticky="ne")
        ttk.Button(meta_actions, text="Load", command=self.load_conversation_meta).pack(
            fill=tk.X, pady=(0, 6)
        )
        ttk.Button(meta_actions, text="Save", command=self.save_conversation_meta).pack(
            fill=tk.X, pady=(0, 6)
        )
        ttk.Button(meta_actions, text="Update", command=self.patch_conversation_meta).pack(
            fill=tk.X
        )
        meta_frame.columnconfigure(1, weight=1)

        memory_frame = ttk.LabelFrame(root, text="Memory Search", padding=12)
        memory_frame.pack(fill=tk.BOTH, expand=True)
        entry = ttk.Entry(memory_frame, textvariable=self.memory_query)
        entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(memory_frame, text="Search", command=self.search_memory).grid(
            row=0, column=1, padx=(8, 0)
        )
        memory_frame.columnconfigure(0, weight=1)

        self.memory_text = tk.Text(memory_frame, height=12, wrap="word")
        self.memory_text.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        memory_frame.rowconfigure(1, weight=1)

    @staticmethod
    def _status_row(parent: ttk.LabelFrame, label: str, var: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=2)
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", pady=2)

    def _run_async(self, func: Callable[[], Any], on_success: Callable[[Any], None]) -> None:
        def wrapper() -> None:
            try:
                result = func()
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("B.E.E", str(exc)))
                return
            self.after(0, lambda: on_success(result))

        threading.Thread(target=wrapper, daemon=True).start()

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        with httpx.Client(timeout=20) as client:
            if method.upper() == "GET":
                resp = client.request(method, url, params=payload)
            else:
                resp = client.request(method, url, json=payload)
            resp.raise_for_status()
            return resp.json()

    def refresh_status(self) -> None:
        self._run_async(lambda: self._request("GET", "/api/status"), self._apply_status)

    def _apply_status(self, data: dict) -> None:
        self.heartbeat_running = bool(data.get("heartbeat_running"))
        self.status_vars["heartbeat"].set("Running" if self.heartbeat_running else "Stopped")
        self.status_vars["interval"].set(str(data.get("heartbeat_interval_sec", "?")))
        self.status_vars["last_tick"].set(data.get("last_tick") or "Never")
        self.status_vars["evermem"].set("Connected" if data.get("evermem_enabled") else "Disabled")
        self.status_vars["endpoint"].set(data.get("evermem_endpoint") or "Not set")
        self.status_vars["group"].set(data.get("evermem_group_id") or "Default")
        if not self.meta_vars["group_id"].get():
            self.meta_vars["group_id"].set(data.get("evermem_group_id") or "")

        self.risk_var.set(int(data.get("risk_tolerance", 5)))
        self.risk_label.set(str(self.risk_var.get()))
        goals = data.get("memory_goals", {}).get("goals", [])
        for idx, var in enumerate(self.goal_vars):
            var.set(goals[idx] if idx < len(goals) else "")

        self.heartbeat_button.config(
            text="Stop Heartbeat" if self.heartbeat_running else "Start Heartbeat"
        )

    def toggle_heartbeat(self) -> None:
        endpoint = "/api/heartbeat/stop" if self.heartbeat_running else "/api/heartbeat/start"
        self._run_async(lambda: self._request("POST", endpoint), lambda _: self.refresh_status())

    def _on_risk_change(self, value: str) -> None:
        try:
            self.risk_var.set(int(float(value)))
            self.risk_label.set(str(self.risk_var.get()))
        except ValueError:
            pass

    def save_risk(self) -> None:
        payload = {"risk_tolerance": self.risk_var.get()}
        self._run_async(lambda: self._request("POST", "/api/config", payload), lambda _: None)

    def save_goals(self) -> None:
        goals = [var.get().strip() for var in self.goal_vars]
        payload = {"goals": goals}

        def handle(_: dict) -> None:
            messagebox.showinfo("B.E.E", "Goals saved.")

        self._run_async(lambda: self._request("POST", "/api/memory/goals", payload), handle)

    def load_conversation_meta(self) -> None:
        payload = {"group_id": self.meta_vars["group_id"].get().strip() or None}

        def handle(data: dict) -> None:
            if not data.get("ok"):
                messagebox.showerror("B.E.E", "Failed to load conversation meta.")
                return
            wrapper = data.get("result", {})
            meta = wrapper.get("result") if isinstance(wrapper, dict) else None
            if not isinstance(meta, dict):
                meta = wrapper if isinstance(wrapper, dict) else {}

            self.meta_vars["group_id"].set(meta.get("group_id") or "")
            self.meta_vars["scene"].set(meta.get("scene") or "")
            self.meta_vars["name"].set(meta.get("name") or "")
            self.meta_vars["description"].set(meta.get("description") or "")

            scene_desc = meta.get("scene_desc") or {}
            if isinstance(scene_desc, dict):
                self.meta_vars["scene_desc"].set(scene_desc.get("description") or json.dumps(scene_desc))
            else:
                self.meta_vars["scene_desc"].set(str(scene_desc))

            self.meta_vars["timezone"].set(meta.get("default_timezone") or "")

            tags = meta.get("tags") or []
            if isinstance(tags, list):
                self.meta_vars["tags"].set(", ".join([str(t) for t in tags]))
            else:
                self.meta_vars["tags"].set(str(tags))

            details = meta.get("user_details") or {}
            if isinstance(details, dict) and details:
                self.meta_user_details.delete("1.0", tk.END)
                self.meta_user_details.insert(tk.END, json.dumps(details, indent=2))
            else:
                self.meta_user_details.delete("1.0", tk.END)

        self._run_async(
            lambda: self._request("GET", "/api/evermem/conversation-meta", payload),
            handle,
        )

    def _parse_meta_user_details(self) -> dict | None:
        raw = self.meta_user_details.get("1.0", tk.END).strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            messagebox.showerror("B.E.E", "User Details must be valid JSON.")
            return None
        if not isinstance(parsed, dict):
            messagebox.showerror("B.E.E", "User Details JSON must be an object.")
            return None
        return parsed

    def _parse_meta_tags(self) -> list[str] | None:
        raw = self.meta_vars["tags"].get().strip()
        if not raw:
            return None
        return [item.strip() for item in raw.split(",") if item.strip()]

    def save_conversation_meta(self) -> None:
        user_details = self._parse_meta_user_details()
        if user_details is None and self.meta_user_details.get("1.0", tk.END).strip():
            return

        scene_desc = self.meta_vars["scene_desc"].get().strip()
        payload = {
            "group_id": self.meta_vars["group_id"].get().strip() or None,
            "scene": self.meta_vars["scene"].get().strip() or None,
            "scene_desc": {"description": scene_desc} if scene_desc else None,
            "name": self.meta_vars["name"].get().strip() or None,
            "description": self.meta_vars["description"].get().strip() or None,
            "default_timezone": self.meta_vars["timezone"].get().strip() or None,
            "tags": self._parse_meta_tags(),
            "user_details": user_details,
        }

        def handle(data: dict) -> None:
            if data.get("ok"):
                messagebox.showinfo("B.E.E", "Conversation meta saved.")
            else:
                messagebox.showerror("B.E.E", "Failed to save conversation meta.")

        self._run_async(
            lambda: self._request("POST", "/api/evermem/conversation-meta", payload),
            handle,
        )

    def patch_conversation_meta(self) -> None:
        user_details = self._parse_meta_user_details()
        if user_details is None and self.meta_user_details.get("1.0", tk.END).strip():
            return

        payload: dict[str, Any] = {
            "group_id": self.meta_vars["group_id"].get().strip() or None
        }
        name = self.meta_vars["name"].get().strip()
        if name:
            payload["name"] = name
        description = self.meta_vars["description"].get().strip()
        if description:
            payload["description"] = description
        scene_desc = self.meta_vars["scene_desc"].get().strip()
        if scene_desc:
            payload["scene_desc"] = {"description": scene_desc}
        timezone = self.meta_vars["timezone"].get().strip()
        if timezone:
            payload["default_timezone"] = timezone
        tags = self._parse_meta_tags()
        if tags is not None:
            payload["tags"] = tags
        if user_details is not None:
            payload["user_details"] = user_details

        def handle(data: dict) -> None:
            if data.get("ok"):
                messagebox.showinfo("B.E.E", "Conversation meta updated.")
            else:
                messagebox.showerror("B.E.E", "Failed to update conversation meta.")

        self._run_async(
            lambda: self._request("PATCH", "/api/evermem/conversation-meta", payload),
            handle,
        )

    def search_memory(self) -> None:
        query = self.memory_query.get().strip()
        if not query:
            return

        payload = {"query": query, "top_k": 6}

        def extract_rows(result: dict) -> list[tuple[str, str, str]]:
            rows: list[tuple[str, str, str]] = []
            memory_list = result.get("memory_list")
            if isinstance(memory_list, list):
                for idx, item in enumerate(memory_list, start=1):
                    if not isinstance(item, dict):
                        continue
                    title = item.get("title") or f"Memory {idx}"
                    content = item.get("content") or ""
                    stamp = item.get("create_time") or ""
                    rows.append((title, content, stamp))
                return rows

            memories = result.get("memories", [])
            if isinstance(memories, list):
                for group in memories:
                    if not isinstance(group, dict):
                        continue
                    for mem_type, items in group.items():
                        if not isinstance(items, list):
                            continue
                        for entry in items:
                            if not isinstance(entry, dict):
                                continue
                            title = entry.get("title") or entry.get("summary") or mem_type or "Memory"
                            content = entry.get("content") or entry.get("summary") or ""
                            stamp = entry.get("timestamp") or entry.get("create_time") or ""
                            rows.append((title, content, stamp))

            pending = result.get("pending_messages", [])
            if isinstance(pending, list):
                for entry in pending:
                    if not isinstance(entry, dict):
                        continue
                    content = entry.get("content") or ""
                    stamp = entry.get("message_create_time") or entry.get("created_at") or ""
                    if content:
                        rows.append(("Pending message", content, stamp))

            return rows

        def handle(data: dict) -> None:
            self.memory_text.delete("1.0", tk.END)
            if not data.get("ok"):
                self.memory_text.insert(tk.END, "Search failed.\n")
                return
            outer = data.get("result", {})
            inner = outer.get("result") if isinstance(outer, dict) else None
            result = inner if isinstance(inner, dict) else (outer if isinstance(outer, dict) else {})
            rows = extract_rows(result)
            if not rows:
                self.memory_text.insert(tk.END, "No results.\n")
                return
            for title, content, stamp in rows:
                self.memory_text.insert(tk.END, f"{title}\n{content}\n{stamp}\n\n")

        self._run_async(lambda: self._request("POST", "/api/evermem/search", payload), handle)


def main() -> None:
    app = BeeUI()
    app.mainloop()


if __name__ == "__main__":
    main()
