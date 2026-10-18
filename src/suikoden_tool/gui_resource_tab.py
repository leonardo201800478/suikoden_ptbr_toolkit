"""Aba independente para editar um catálogo extraído de um bundle."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from suikoden_tool.app_settings import load_settings
from suikoden_tool.gui_service import load_catalog, save_entry, suggest_translation


class ResourceCatalogTab:
    """Editor compacto, isolado por catálogo de recurso."""

    def __init__(self, parent: ttk.Frame, path: Path, resource_label: str) -> None:
        self.parent = parent
        self.path = path
        self.resource_label = resource_label
        self.catalog: dict[str, Any] = load_catalog(path)
        self.entries = self.catalog["entries"]
        self.current: dict[str, Any] | None = None
        self.dirty = False
        self.api_busy = False
        self._loading = False
        self.settings = load_settings()
        self._build()

    def _build(self) -> None:
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(1, weight=1)
        ttk.Label(
            self.parent,
            text=f"Recurso: {self.resource_label}   |   Arquivo: {self.path.name}   |   "
            f"Entradas: {len(self.entries)}",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=10)

        body = ttk.Frame(self.parent, padding=12)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        search = ttk.Entry(left, textvariable=self.search_var)
        search.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.tree = ttk.Treeview(left, columns=("id", "original"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("original", text="TEXTO ORIGINAL")
        self.tree.column("id", width=80, stretch=False)
        self.tree.column("original", width=300)
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        scroll.grid(row=1, column=1, sticky="ns")

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)
        ttk.Label(right, text="ORIGINAL").grid(row=0, column=0, sticky="w")
        self.original = tk.Text(right, height=6, wrap="word", state="disabled")
        self.original.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
        ttk.Label(right, text="TRADUÇÃO PT-BR").grid(row=2, column=0, sticky="w")
        self.translation = tk.Text(right, height=7, wrap="word")
        self.translation.grid(row=3, column=0, sticky="nsew", pady=(4, 8))
        self.translation.bind("<<Modified>>", self._on_modified)
        self.context = ttk.Entry(right)
        self.context.insert(0, "Contexto opcional para a IA")
        self.context.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        actions = ttk.Frame(right)
        actions.grid(row=5, column=0, sticky="ew")
        ttk.Button(actions, text="Sugerir com IA", command=self._suggest).pack(side="right")
        ttk.Button(actions, text="Salvar", command=self._save).pack(side="right", padx=8)
        self.status = tk.StringVar(value="Selecione uma entrada.")
        ttk.Label(self.parent, textvariable=self.status).grid(
            row=2, column=0, sticky="ew", padx=12, pady=(0, 10)
        )
        self.search_var.trace_add("write", lambda *_: self._refresh())
        self.tree.bind("<<TreeviewSelect>>", self._select)
        self._refresh()

    @staticmethod
    def _display(text: str) -> str:
        return text.replace("∠", "\n")

    @staticmethod
    def _store(text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "∠")

    def _refresh(self) -> None:
        query = self.search_var.get().casefold().strip()
        self.tree.delete(*self.tree.get_children())
        for entry in self.entries:
            original = entry.get("original", "")
            if query and query not in str(entry.get("id", "")).casefold() and query not in original.casefold():
                continue
            snippet = " ".join(self._display(original).split())
            self.tree.insert("", "end", iid=str(len(self.tree.get_children())), values=(entry["id"], snippet))

    def _selected(self, iid: str) -> dict[str, Any] | None:
        values = self.tree.item(iid, "values")
        if not values:
            return None
        entry_id = values[0]
        return next((e for e in self.entries if str(e.get("id")) == str(entry_id)), None)

    def _select(self, _event: tk.Event | None = None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        if self.dirty and not messagebox.askyesno(
            "Descartar alterações?", "A tradução atual não foi salva. Deseja descartá-la?",
            parent=self.parent,
        ):
            return
        entry = self._selected(selected[0])
        if entry is None:
            return
        self.current = entry
        self._loading = True
        self.original.configure(state="normal")
        self.original.delete("1.0", "end")
        self.original.insert("1.0", self._display(entry.get("original", "")))
        self.original.configure(state="disabled")
        self.translation.delete("1.0", "end")
        self.translation.insert("1.0", self._display(entry.get("translation", "")))
        self.translation.edit_modified(False)
        self.dirty = False
        self._loading = False
        self.status.set(f"ID {entry['id']} · Status: {entry.get('status', 'pending')}")

    def _on_modified(self, _event: tk.Event | None = None) -> None:
        if self.translation.edit_modified():
            self.translation.edit_modified(False)
            if not self._loading and self.current is not None:
                self.dirty = True
                self.status.set("Alterações não salvas.")

    def _save(self) -> None:
        if self.current is None:
            messagebox.showinfo("Selecione uma entrada", "Selecione uma entrada primeiro.")
            return
        value = self._store(self.translation.get("1.0", "end-1c"))
        status = "reviewed" if self.current.get("status") == "needs_review" else "translated"
        try:
            saved = save_entry(self.path, self.current["id"], value, status)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Falha ao salvar", str(exc), parent=self.parent)
            return
        self.current.update(saved)
        self.dirty = False
        self.status.set(f"ID {self.current['id']} salvo como {status}.")

    def _suggest(self) -> None:
        if self.current is None:
            messagebox.showinfo("Selecione uma entrada", "Selecione uma entrada primeiro.")
            return
        if self.api_busy:
            return
        original = self.current.get("original", "")
        context = self.context.get()
        key = self.settings.get("openai_api_key", "")
        self.api_busy = True
        self.status.set("Solicitando sugestão de IA…")

        def worker() -> None:
            try:
                result = suggest_translation(original, context, api_key=key)
            except (OSError, ValueError) as exc:
                self.parent.after(0, lambda msg=str(exc): self._finish_suggestion(error=msg))
            else:
                self.parent.after(0, lambda text=result: self._finish_suggestion(text=text))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_suggestion(self, text: str | None = None, error: str | None = None) -> None:
        self.api_busy = False
        if error:
            self.status.set("Falha na sugestão.")
            messagebox.showerror("Assistência de IA", error, parent=self.parent)
            return
        if text is not None:
            self._loading = True
            self.translation.delete("1.0", "end")
            self.translation.insert("1.0", self._display(text))
            self.translation.edit_modified(False)
            self._loading = False
            self.dirty = True
            self.status.set("Sugestão inserida. Revise e salve.")
