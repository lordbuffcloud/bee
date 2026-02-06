from __future__ import annotations

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

    def search_memory(self) -> None:
        query = self.memory_query.get().strip()
        if not query:
            return

        payload = {"search_query": query, "result_limit": 6}

        def handle(data: dict) -> None:
            self.memory_text.delete("1.0", tk.END)
            if not data.get("ok"):
                self.memory_text.insert(tk.END, "Search failed.\n")
                return
            results = data.get("result", {}).get("memory_list", [])
            if not results:
                self.memory_text.insert(tk.END, "No results.\n")
                return
            for idx, item in enumerate(results, start=1):
                title = item.get("title") or f"Memory {idx}"
                content = item.get("content") or ""
                stamp = item.get("create_time") or ""
                self.memory_text.insert(tk.END, f"{title}\n{content}\n{stamp}\n\n")

        self._run_async(lambda: self._request("POST", "/api/evermem/search", payload), handle)


def main() -> None:
    app = BeeUI()
    app.mainloop()


if __name__ == "__main__":
    main()
