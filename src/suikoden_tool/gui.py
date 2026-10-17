"""Interface desktop escura para editar catálogos de tradução."""

from __future__ import annotations

import argparse
import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from suikoden_tool.app_settings import (
    find_game_assets_directory,
    load_settings,
    save_settings,
    validate_game_directory,
)
from suikoden_tool.gui_resource_tab import ResourceCatalogTab
from suikoden_tool.gui_service import (
    get_catalog_stats,
    load_catalog,
    save_entry,
    suggest_translation,
)
from suikoden_tool.text_catalog import export_text_catalog
from suikoden_tool.text_discovery import discover_text_assets
from suikoden_tool.unity_text_extractor import extract_textasset_json, resolve_unity_data_tool

BG = "#17191f"
PANEL = "#20232b"
PANEL_ALT = "#282c36"
FG = "#e8eaf0"
MUTED = "#a0a6b5"
ACCENT = "#8b7cff"

TARGET_BUNDLE_NAMES = (
    "03cf0288ba3ecaca0776d7fadf1f0bb6.bundle",
    "0573e2f60d0cda7892d60f38dfd7282c.bundle",
    "49d65af6f8fea7a9e8008c6b2c688fc3.bundle",
    "700bf7ec8ded4a20613b92988e3f8142.bundle",
)


class TranslationApp:
    """Editor de catálogo com lista, filtros, salvamento seguro e sugestão opcional de IA."""

    def __init__(self, root: tk.Tk, catalog_path: Path | None = None) -> None:
        self.root = root
        self.root.title("Suikoden I & II — Editor de Tradução PT-BR")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG)

        self.catalog_path: Path | None = None
        self.catalog: dict[str, Any] = {}
        self.entries: list[dict[str, Any]] = []
        self.visible_entries: list[dict[str, Any]] = []
        self.current_id: tuple[type, object] | None = None
        self.dirty = False
        self._ai_busy = False
        self._ai_entry_id: tuple[type, object] | None = None
        self._loading_entry = False
        self.settings = load_settings()
        self.game_directory = self.settings.get("game_directory", "")

        self._configure_style()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.editor_tab = ttk.Frame(self.notebook)
        self.extraction_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.editor_tab, text="Editor atual")
        self.notebook.add(self.extraction_tab, text="Extração dos 4 bundles")
        self._build_layout()
        self._build_extraction_tab()
        self._bind_events()
        self.game_directory_var.set(self.game_directory)
        self._refresh_game_directory_status()
        self._locate_target_bundles()
        startup_catalog = catalog_path
        if startup_catalog is None:
            remembered = self.settings.get("last_catalog_path", "")
            if remembered:
                startup_catalog = Path(remembered)
        if startup_catalog is not None:
            if startup_catalog.is_file():
                self.open_catalog(startup_catalog)
            elif not catalog_path:
                self.message_var.set(
                    "O último catálogo salvo não foi encontrado. Abra o catálogo novamente."
                )

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            ".",
            background=BG,
            foreground=FG,
            fieldbackground=PANEL_ALT,
            bordercolor="#3a3e49",
            lightcolor=PANEL_ALT,
            darkcolor=PANEL,
            troughcolor=PANEL,
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Panel.TLabel", background=PANEL, foreground=FG)
        style.configure("Header.TLabel", font=("Segoe UI Semibold", 17), foreground=FG)
        style.configure("TButton", padding=(12, 7), background=PANEL_ALT, foreground=FG)
        style.map("TButton", background=[("active", "#383d49")])
        style.configure(
            "Accent.TButton", background=ACCENT, foreground="#ffffff", padding=(12, 8)
        )
        style.map("Accent.TButton", background=[("active", "#a094ff")])
        style.configure(
            "Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=FG,
            rowheight=31,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=PANEL_ALT,
            foreground=MUTED,
            padding=(7, 8),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#484064")])
        style.configure("TCombobox", fieldbackground=PANEL_ALT, background=PANEL_ALT)
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL_ALT, background=ACCENT)

    def _build_layout(self) -> None:
        header = ttk.Frame(self.editor_tab, padding=(18, 14, 18, 10))
        header.pack(fill="x")
        ttk.Label(header, text="SUIKODEN  I  /  II", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="EDITOR DE LOCALIZAÇÃO  ·  PT-BR", style="Muted.TLabel").pack(
            side="left", padx=(16, 0), pady=(5, 0)
        )
        ttk.Button(header, text="Abrir catálogo", command=self.choose_catalog).pack(side="right")
        self.file_label = ttk.Label(header, text="Nenhum catálogo aberto", style="Muted.TLabel")
        self.file_label.pack(side="right", padx=14)

        game_path_frame = ttk.Frame(self.editor_tab, padding=(18, 0, 18, 8))
        game_path_frame.pack(fill="x")
        ttk.Label(game_path_frame, text="PASTA DO JOGO", style="Muted.TLabel").pack(side="left")
        self.game_directory_var = tk.StringVar()
        self.game_directory_entry = ttk.Entry(
            game_path_frame, textvariable=self.game_directory_var
        )
        self.game_directory_entry.pack(side="left", fill="x", expand=True, padx=(10, 8))
        ttk.Button(
            game_path_frame, text="Selecionar pasta…", command=self.choose_game_directory
        ).pack(side="left")
        ttk.Button(
            game_path_frame, text="Aplicar", command=self.apply_game_directory
        ).pack(side="left", padx=(7, 0))
        self.game_directory_status = ttk.Label(
            self.editor_tab, text="", style="Muted.TLabel", padding=(18, 0, 18, 8)
        )
        self.game_directory_status.pack(fill="x")

        self.stats_label = ttk.Label(
            self.editor_tab,
            text="Abra catalogo_pt_br.json para começar.",
            style="Muted.TLabel",
            padding=(18, 0, 18, 10),
        )
        self.stats_label.pack(fill="x")

        body = ttk.Frame(self.editor_tab, padding=(14, 0, 14, 12))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3, minsize=340)
        body.columnconfigure(1, weight=5, minsize=540)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Panel.TFrame", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(body, style="Panel.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)

        ttk.Label(left, text="CATÁLOGO", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 9)
        )
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(left, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.search_entry.insert(0, "")
        self.status_var = tk.StringVar(value="Todas")
        self.status_combo = ttk.Combobox(
            left,
            textvariable=self.status_var,
            state="readonly",
            values=("Todas", "Pendentes", "Traduzidas", "Revisadas", "Revisar", "Órfãs"),
        )
        self.status_combo.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        tree_frame = ttk.Frame(left, style="Panel.TFrame")
        tree_frame.grid(row=3, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            tree_frame, columns=("status", "original"), show="headings", selectmode="browse"
        )
        self.tree.heading("status", text="STATUS")
        self.tree.heading("original", text="TEXTO ORIGINAL")
        self.tree.column("status", width=90, minwidth=80, stretch=False)
        self.tree.column("original", width=300, minwidth=160, stretch=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        ttk.Label(right, text="EDITOR DE ENTRADA", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_meta = ttk.Label(right, text="Selecione uma entrada na lista.", style="Muted.TLabel")
        self.entry_meta.grid(row=1, column=0, sticky="w", pady=(4, 12))

        ttk.Label(right, text="ORIGINAL · INGLÊS", style="Panel.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 6)
        )
        self.original_text = tk.Text(
            right, height=7, wrap="word", bg="#1a1c23", fg=FG, insertbackground=FG,
            relief="flat", padx=12, pady=10, font=("Consolas", 11),
            selectbackground="#484064", state="disabled",
        )
        self.original_text.grid(row=3, column=0, sticky="nsew")
        self.original_text.configure(height=7)

        ttk.Label(right, text="TRADUÇÃO · PORTUGUÊS BRASILEIRO", style="Panel.TLabel").grid(
            row=4, column=0, sticky="w", pady=(14, 6)
        )
        self.translation_text = tk.Text(
            right, height=8, wrap="word", bg=PANEL_ALT, fg=FG, insertbackground=FG,
            relief="flat", padx=12, pady=10, font=("Segoe UI", 11),
            selectbackground="#484064",
        )
        self.translation_text.grid(row=5, column=0, sticky="nsew")
        self.translation_text.bind("<<Modified>>", self._on_translation_modified)
        right.rowconfigure(5, weight=1)

        ttk.Label(right, text="CONTEXTO OPCIONAL PARA A SUGESTÃO DE IA", style="Panel.TLabel").grid(
            row=6, column=0, sticky="w", pady=(12, 5)
        )
        self.context_entry = ttk.Entry(right)
        self.context_entry.grid(row=7, column=0, sticky="ew")

        actions = ttk.Frame(right, style="Panel.TFrame")
        actions.grid(row=8, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="← Anterior", command=self.previous_entry).pack(side="left")
        ttk.Button(actions, text="Próxima pendente →", command=self.next_pending).pack(
            side="left", padx=(7, 0)
        )
        ttk.Button(actions, text="Sugerir com IA", command=self.request_ai).pack(
            side="right", padx=(7, 0)
        )
        ttk.Button(actions, text="Salvar revisada", command=self.save_reviewed).pack(
            side="right", padx=(7, 0)
        )
        ttk.Button(actions, text="Salvar tradução", style="Accent.TButton", command=self.save).pack(
            side="right"
        )

        footer = ttk.Frame(self.editor_tab, padding=(18, 0, 18, 12))
        footer.pack(fill="x")
        self.progress = ttk.Progressbar(footer, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 7))
        self.message_var = tk.StringVar(value="Pronto.")
        ttk.Label(footer, textvariable=self.message_var, style="Muted.TLabel").pack(anchor="w")

    def _bind_events(self) -> None:
        self.search_var.trace_add("write", lambda *_: self.refresh_list())
        self.status_var.trace_add("write", lambda *_: self.refresh_list())
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_extraction_tab(self) -> None:
        frame = ttk.Frame(self.extraction_tab, padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(6, weight=1)
        ttk.Label(frame, text="CATÁLOGOS DOS QUATRO BUNDLES", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Os quatro bundles são localizados automaticamente na pasta Addressables do jogo. Não é necessária seleção manual.", style="Muted.TLabel", wraplength=1050).grid(row=1, column=0, sticky="w", pady=(8, 14))
        key_frame = ttk.LabelFrame(frame, text="API OpenAI — sugestões de tradução", padding=10)
        key_frame.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        key_frame.columnconfigure(1, weight=1)
        ttk.Label(key_frame, text="Chave da API").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.api_key_var = tk.StringVar(value=self.settings.get("openai_api_key", ""))
        self.api_key_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, show="•")
        self.api_key_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(key_frame, text="Mostrar/ocultar", command=self._toggle_api_key).grid(row=0, column=2, padx=6)
        ttk.Button(key_frame, text="Salvar chave", command=self._save_api_key).grid(row=0, column=3)
        ttk.Label(key_frame, text="A chave é salva localmente em settings.json. Não compartilhe esse arquivo.", style="Muted.TLabel").grid(row=1, column=1, columnspan=3, sticky="w", pady=(6, 0))
        actions = ttk.Frame(frame)
        actions.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(actions, text="Localizar os 4 bundles", command=self._locate_target_bundles).pack(side="left")
        ttk.Button(actions, text="Extrair catálogos", style="Accent.TButton", command=self._start_extraction).pack(side="left", padx=8)
        ttk.Button(actions, text="Reconstruir e instalar no jogo", command=self._rebuild_bundles).pack(side="left")
        self.extraction_files = tk.StringVar(value="Informe/aplique a pasta do jogo para localizar os bundles.")
        ttk.Label(frame, textvariable=self.extraction_files, wraplength=1100).grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self.extraction_status = tk.StringVar(value="Aguardando localização dos bundles.")
        ttk.Label(frame, textvariable=self.extraction_status).grid(row=5, column=0, sticky="ew", pady=(0, 8))
        self.extraction_log = tk.Text(frame, height=15, wrap="word", bg=PANEL, fg=FG, insertbackground=FG, relief="flat", padx=10, pady=8)
        self.extraction_log.grid(row=6, column=0, sticky="nsew")
        self.selected_bundles = ()
        self._api_key_visible = False
        self._locate_target_bundles()

    def _locate_target_bundles(self) -> tuple[Path, ...]:
        if not self.game_directory:
            self.selected_bundles = ()
            self.extraction_files.set("Defina primeiro a pasta de instalação do jogo.")
            self.extraction_status.set("Pasta do jogo não configurada.")
            return ()
        game_dir = Path(self.game_directory).expanduser()
        if not game_dir.is_dir():
            self.selected_bundles = ()
            self.extraction_files.set("A pasta configurada não existe. Selecione novamente a pasta do jogo.")
            self.extraction_status.set("Pasta do jogo não encontrada.")
            return ()
        assets_dir = find_game_assets_directory(game_dir)
        found = []
        missing = []
        for name in TARGET_BUNDLE_NAMES:
            candidate = assets_dir / name
            if candidate.is_file():
                found.append(candidate.resolve())
            else:
                missing.append(name)
        self.selected_bundles = tuple(found)
        details = [f"Encontrado: {p.name} ({p.stat().st_size:,} bytes)" for p in found]
        details.extend(f"Ausente: {name}" for name in missing)
        self.extraction_files.set("\\n".join(details) if details else f"Nenhum bundle encontrado em: {assets_dir}")
        self.extraction_status.set(f"{len(found)}/4 bundles encontrados." if missing else "4/4 bundles encontrados. Pronto para extrair.")
        return self.selected_bundles

    def _rebuild_bundles(self) -> None:
        messagebox.showwarning("Reconstrução ainda não implementada", "A extração está disponível, mas a reinserção/reconstrução de bundles Unity Addressables ainda não possui um motor validado. Nenhum arquivo foi alterado. Precisamos implementar e testar a reinserção em cópias, incluindo metadados e CRC, antes de instalar arquivos reconstruídos.", parent=self.root)
    def _toggle_api_key(self) -> None:
        self._api_key_visible = not self._api_key_visible
        self.api_key_entry.configure(show="" if self._api_key_visible else "•")

    def _save_api_key(self) -> None:
        key = self.api_key_var.get().strip()
        if key:
            self.settings["openai_api_key"] = key
        else:
            self.settings.pop("openai_api_key", None)
        try:
            save_settings(self.settings)
        except OSError as exc:
            messagebox.showerror("Configurações", f"Não foi possível salvar a chave: {exc}", parent=self.root)
            return
        self.message_var.set("Chave da API salva localmente." if key else "Chave da API removida.")
        messagebox.showinfo(
            "Configurações",
            "Chave salva. A API OpenAI tem faturamento separado da assinatura do ChatGPT.",
            parent=self.root,
        )

    def _start_extraction(self) -> None:
        bundles = self._locate_target_bundles()
        if len(bundles) != 4:
            messagebox.showwarning("Bundles incompletos", "A extração exige os quatro arquivos conhecidos na pasta do jogo. Confira a instalação e tente localizar novamente.", parent=self.root)
            return
        tool = Path(__file__).resolve().parents[2] / "tools" / "UnityDataTools" / "UnityDataTool.exe"
        try:
            executable = resolve_unity_data_tool(tool) if tool.is_file() else resolve_unity_data_tool()
        except ValueError as exc:
            messagebox.showerror("UnityDataTool", str(exc), parent=self.root)
            return
        self.extraction_status.set("Extração em andamento. Os bundles originais não serão alterados.")
        self.extraction_log.delete("1.0", "end")
        threading.Thread(
            target=self._extraction_worker,
            args=(bundles, executable),
            daemon=True,
        ).start()

    def _extraction_worker(self, bundles: tuple[Path, ...], executable: Path) -> None:
        output_dir = Path(__file__).resolve().parents[2] / "work" / "bundle_analysis"
        results: list[tuple[Path, Path, str, int]] = []
        errors: list[str] = []
        for index, bundle in enumerate(bundles, start=1):
            try:
                self.root.after(
                    0,
                    lambda i=index, name=bundle.name: self.extraction_status.set(
                        f"Analisando bundle {i}/4: {name}"
                    ),
                )
                report = discover_text_assets(bundle, executable=executable)
                record = report["bundles"][0]
                if record.get("error"):
                    raise ValueError(record["error"])
                candidates = [
                    asset for asset in record["textassets"]
                    if asset.get("json_textlist") and asset.get("name")
                ]
                if not candidates:
                    raise ValueError("Nenhum TextAsset JSON com textList foi identificado.")
                preferred = [asset for asset in candidates if asset["name"] == "text_add_en"]
                selected = preferred[0] if preferred else max(
                    candidates, key=lambda item: item.get("textlist_count") or 0
                )
                if len(candidates) > 1 and not preferred:
                    candidate_count = len(candidates)
                    chosen_name = selected["name"]
                    self.root.after(
                        0,
                        lambda name=bundle.name, count=candidate_count, chosen=chosen_name:
                        self._append_extraction_log(
                            f"Aviso: {name} contém {count} TextAssets textList; "
                            f"selecionado '{chosen}' por ter a maior quantidade de entradas."
                        ),
                    )
                safe_name = "".join(
                    char if char.isalnum() or char in "-_." else "_" for char in selected["name"]
                )
                source_json = output_dir / "sources" / f"{bundle.stem}__{safe_name}.json"
                catalog_json = output_dir / "catalogs" / f"{bundle.stem}__{safe_name}_pt_br.json"
                extract_textasset_json(
                    bundle, source_json, executable=executable,
                    asset_name=selected["name"], force=True,
                )
                export_text_catalog(source_json, catalog_json, target_language="pt-BR")
                count = selected.get("textlist_count") or 0
                results.append((bundle, catalog_json, selected["name"], count))
                self.root.after(
                    0,
                    lambda b=bundle.name, a=selected["name"], n=count:
                    self._append_extraction_log(f"OK: {b} → recurso '{a}', {n} entradas."),
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{bundle.name}: {exc}")
                self.root.after(0, lambda msg=errors[-1]: self._append_extraction_log("ERRO: " + msg))
        self.root.after(0, lambda: self._finish_extraction(results, errors))

    def _append_extraction_log(self, text: str) -> None:
        self.extraction_log.insert("end", text + "\n")
        self.extraction_log.see("end")

    def _finish_extraction(
        self, results: list[tuple[Path, Path, str, int]], errors: list[str]
    ) -> None:
        for _bundle, catalog_path, asset_name, count in results:
            try:
                tab = ttk.Frame(self.notebook)
                ResourceCatalogTab(tab, catalog_path, asset_name)
                label = f"{_bundle.stem[:8]} · {asset_name} ({count})"
                self.notebook.add(tab, text=label)
            except (OSError, ValueError) as exc:
                errors.append(f"{catalog_path.name}: não foi possível abrir a guia: {exc}")
        if errors:
            self.extraction_status.set(
                f"Concluído parcialmente: {len(results)}/4 guias abertas; {len(errors)} erro(s)."
            )
        else:
            self.extraction_status.set("Extração concluída: quatro catálogos abertos em guias separadas.")
        if results:
            self.notebook.select(self.notebook.tabs()[-1])
        if errors:
            messagebox.showwarning(
                "Extração concluída com avisos", "\n".join(errors), parent=self.root
            )

    def choose_game_directory(self) -> None:
        """Permite selecionar a pasta de instalação do jogo."""
        selected = filedialog.askdirectory(
            title="Selecione a pasta que contém o executável de Suikoden I & II HD Remaster",
            initialdir=self.game_directory or None,
            mustexist=True,
        )
        if selected:
            self.game_directory_var.set(selected)
            self.apply_game_directory()

    def apply_game_directory(self) -> None:
        """Valida e persiste a pasta do jogo como caminho absoluto."""
        try:
            directory = validate_game_directory(self.game_directory_var.get())
            self.settings["game_directory"] = str(directory)
            save_settings(self.settings)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Pasta do jogo inválida", str(exc), parent=self.root)
            return
        self.game_directory = str(directory)
        self.settings["game_directory"] = self.game_directory
        self.game_directory_var.set(self.game_directory)
        self._refresh_game_directory_status()
        self._locate_target_bundles()
        self.message_var.set("Pasta do jogo salva nas configurações da ferramenta.")

    def _refresh_game_directory_status(self) -> None:
        """Mostra se a pasta e os recursos Addressables ainda estão disponíveis."""
        if not self.game_directory:
            self.game_directory_status.configure(
                text="Pasta não configurada. O catálogo continua podendo ser editado sem ela."
            )
            return
        directory = Path(self.game_directory).expanduser()
        if not directory.is_dir():
            self.game_directory_status.configure(
                text="Pasta salva, mas não encontrada. Selecione novamente a instalação do jogo."
            )
            return
        assets_directory = find_game_assets_directory(directory)
        if assets_directory.is_dir():
            detail = f"Recursos do jogo detectados: {assets_directory}"
        else:
            detail = "Pasta válida; diretório Addressables StandaloneWindows64 não detectado ainda."
        self.game_directory_status.configure(text=detail)

    def choose_catalog(self) -> None:
        filename = filedialog.askopenfilename(
            title="Abrir catálogo de tradução",
            filetypes=(("Catálogos JSON", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if filename:
            self.open_catalog(Path(filename))

    def open_catalog(self, path: Path) -> None:
        if self.dirty and not self._confirm_discard():
            return
        try:
            catalog = load_catalog(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Não foi possível abrir", str(exc), parent=self.root)
            return
        self.catalog_path = path.resolve()
        self.settings["last_catalog_path"] = str(self.catalog_path)
        save_settings(self.settings)
        self.catalog = catalog
        self.entries = catalog["entries"]
        self.current_id = None
        self.dirty = False
        self.file_label.configure(text=path.name)
        self.refresh_list()
        self._update_stats()
        self.message_var.set(f"Catálogo carregado: {len(self.entries)} entradas.")

    def refresh_list(self) -> None:
        selected_key = self.current_id
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get().casefold().strip()
        status_filter = self.status_var.get()
        labels = {
            "pending": "Pendente",
            "translated": "Traduzida",
            "reviewed": "Revisada",
            "needs_review": "Revisar",
            "orphaned": "Órfã",
        }
        status_map = {
            "Pendentes": {"pending"},
            "Traduzidas": {"translated"},
            "Revisadas": {"reviewed"},
            "Revisar": {"needs_review"},
            "Órfãs": {"orphaned"},
        }
        self.visible_entries = []
        for entry in self.entries:
            original = entry.get("original", "")
            translation = entry.get("translation", "")
            entry_id = entry.get("id")
            if query and query not in original.casefold() and query not in translation.casefold() and query not in str(entry_id).casefold():
                continue
            allowed = status_map.get(status_filter)
            if allowed and entry.get("status") not in allowed:
                continue
            self.visible_entries.append(entry)
            iid = self._iid(entry)
            snippet = " ".join(self._markers_to_lines(original).split())
            if len(snippet) > 95:
                snippet = snippet[:92] + "..."
            status = entry.get("status")
            status_label = labels.get(status, status) if isinstance(status, str) else "?"
            self.tree.insert(
                "", "end", iid=iid,
                values=(status_label, snippet),
            )
        if selected_key:
            for entry in self.visible_entries:
                if self._key(entry) == selected_key:
                    self.tree.selection_set(self._iid(entry))
                    self.tree.see(self._iid(entry))
                    break

    @staticmethod
    def _key(entry: dict[str, Any]) -> tuple[type, object]:
        return type(entry["id"]), entry["id"]

    @staticmethod
    def _iid(entry: dict[str, Any]) -> str:
        return f"{'i' if isinstance(entry['id'], int) and not isinstance(entry['id'], bool) else 's'}:{entry['id']}"

    def _on_select(self, _event: tk.Event | None = None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        entry = next((item for item in self.visible_entries if self._iid(item) == selected[0]), None)
        if entry is None or self._key(entry) == self.current_id:
            return
        if self.dirty and not self._confirm_discard():
            if self.current_id:
                current = next(
                    (item for item in self.visible_entries if self._key(item) == self.current_id), None
                )
                if current:
                    self.tree.selection_set(self._iid(current))
            return
        self._display_entry(entry)

    def _display_entry(self, entry: dict[str, Any]) -> None:
        self._loading_entry = True
        self.current_id = self._key(entry)
        self.dirty = False
        self.entry_meta.configure(
            text=f"ID: {entry['id']}   ·   Status: {entry['status']}   ·   Recurso: {self.catalog.get('resource', '-')}"
        )
        original_display = self._markers_to_lines(entry.get("original", ""))
        previous_original = entry.get("previous_original")
        if previous_original is not None:
            previous_original = self._markers_to_lines(previous_original)
        if previous_original is not None:
            original_display = (
                f"[TEXTO ATUAL]\n{original_display}\n\n"
                f"[TEXTO ANTERIOR — REVISAR]\n{previous_original}"
            )
        self._set_text(self.original_text, original_display, readonly=True)
        self._set_text(
            self.translation_text, self._markers_to_lines(entry.get("translation", ""))
        )
        self.translation_text.edit_modified(False)
        self._loading_entry = False
        self.context_entry.delete(0, "end")
        if entry.get("previous_original") is not None:
            self.message_var.set("Atenção: a fonte mudou. Compare com o texto anterior antes de revisar.")
        else:
            self.message_var.set("Edição não salva." if entry.get("status") == "pending" else "Entrada carregada.")

    @staticmethod
    def _markers_to_lines(value: str) -> str:
        """Mostra o marcador de quebra de linha do jogo como quebra real no editor."""
        return value.replace("∠", "\n")

    @staticmethod
    def _lines_to_markers(value: str) -> str:
        """Converte quebras editadas para o marcador exigido pelo formato do jogo."""
        return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "∠")

    @staticmethod
    def _set_text(widget: tk.Text, value: str, readonly: bool = False) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.edit_modified(False)
        if readonly:
            widget.configure(state="disabled")

    def _on_translation_modified(self, _event: tk.Event | None = None) -> None:
        if self.translation_text.edit_modified():
            self.translation_text.edit_modified(False)
            if not self._loading_entry and self.current_id is not None:
                self.dirty = True
                self.message_var.set("Alterações não salvas.")

    def _current_entry(self) -> dict[str, Any] | None:
        if self.current_id is None:
            return None
        return next((entry for entry in self.entries if self._key(entry) == self.current_id), None)

    def save(self) -> None:
        self._save("translated")

    def save_reviewed(self) -> None:
        self._save("reviewed")

    def _save(self, status: str) -> None:
        entry = self._current_entry()
        if entry is None or self.catalog_path is None:
            messagebox.showinfo("Selecione uma entrada", "Abra um catálogo e selecione uma entrada.")
            return
        translation = self._lines_to_markers(
            self.translation_text.get("1.0", "end-1c")
        )
        try:
            saved = save_entry(self.catalog_path, entry["id"], translation, status)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Falha ao salvar", str(exc), parent=self.root)
            return
        entry.update(saved)
        self.dirty = False
        self._update_stats()
        self.refresh_list()
        self.message_var.set(f"Entrada {entry['id']} salva como {status}.")
        self.entry_meta.configure(text=f"ID: {entry['id']}   ·   Status: {status}")

    def _update_stats(self) -> None:
        if not self.catalog:
            return
        stats = get_catalog_stats(self.catalog)
        self.stats_label.configure(
            text=(
                f"{stats['total']} entradas    ·    {stats['translated']} traduzidas    ·    "
                f"{stats['reviewed']} revisadas    ·    {stats['pending']} pendentes    ·    "
                f"{stats['needs_review']} para revisar    ·    {stats['completion_percent']}% concluído"
            )
        )
        self.progress.configure(value=stats["completion_percent"])

    def next_pending(self) -> None:
        self._navigate("next")

    def previous_entry(self) -> None:
        self._navigate("previous")

    def _navigate(self, direction: str) -> None:
        if not self.visible_entries:
            return
        if self.dirty and not self._confirm_discard():
            return
        current_index = next(
            (i for i, entry in enumerate(self.visible_entries) if self._key(entry) == self.current_id),
            -1,
        )
        if direction == "next":
            candidates = [
                (i, entry) for i, entry in enumerate(self.visible_entries)
                if i > current_index and entry.get("status") in {"pending", "needs_review"}
            ]
            if not candidates:
                candidates = [
                    (i, entry) for i, entry in enumerate(self.visible_entries)
                    if entry.get("status") in {"pending", "needs_review"}
                ]
            target = candidates[0][1] if candidates else (
                self.visible_entries[min(current_index + 1, len(self.visible_entries) - 1)]
            )
        else:
            target = self.visible_entries[max(current_index - 1, 0)]
        self.tree.selection_set(self._iid(target))
        self.tree.see(self._iid(target))
        self._display_entry(target)

    def request_ai(self) -> None:
        entry = self._current_entry()
        if entry is None:
            messagebox.showinfo("Selecione uma entrada", "Selecione uma entrada para sugerir tradução.")
            return
        if self._ai_busy:
            return
        original = entry.get("original", "")
        context = self.context_entry.get()
        self._ai_entry_id = self.current_id
        self._ai_busy = True
        self.message_var.set("Solicitando sugestão de tradução…")
        self._set_ai_buttons_state("disabled")

        def worker() -> None:
            try:
                suggestion = suggest_translation(
                    original, context, api_key=self.settings.get("openai_api_key", "")
                )
            except (OSError, ValueError) as exc:
                self.root.after(0, lambda error=str(exc): self._ai_finished(error=error))
            else:
                self.root.after(0, lambda text=suggestion: self._ai_finished(suggestion=text))

        threading.Thread(target=worker, daemon=True).start()

    def _set_ai_buttons_state(self, state: str) -> None:
        def visit(parent: tk.Misc) -> None:
            for widget in parent.winfo_children():
                if isinstance(widget, ttk.Button) and widget.cget("text") == "Sugerir com IA":
                    widget.configure(state=state)
                visit(widget)

        visit(self.root)

    def _ai_finished(self, suggestion: str | None = None, error: str | None = None) -> None:
        self._ai_busy = False
        self._set_ai_buttons_state("normal")
        if error:
            self.message_var.set("Não foi possível obter a sugestão.")
            messagebox.showerror("Assistência de IA", error, parent=self.root)
            return
        if suggestion is not None:
            if self.current_id != self._ai_entry_id:
                self.message_var.set("Sugestão recebida para outra entrada; ela não foi aplicada.")
                return
            self._set_text(self.translation_text, suggestion)
            self.dirty = True
            self.message_var.set("Sugestão inserida no editor. Revise e salve para confirmar.")

    def _confirm_discard(self) -> bool:
        return messagebox.askyesno(
            "Descartar alterações?",
            "Há alterações não salvas. Deseja descartá-las?",
            parent=self.root,
        )

    def close(self) -> None:
        if self.dirty and not self._confirm_discard():
            return
        self.root.destroy()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Editor gráfico de tradução Suikoden I & II")
    parser.add_argument("--catalog", type=Path, help="Catálogo JSON a abrir ao iniciar")
    args = parser.parse_args(argv)
    root = tk.Tk()
    TranslationApp(root, args.catalog)
    root.mainloop()


if __name__ == "__main__":
    main()
