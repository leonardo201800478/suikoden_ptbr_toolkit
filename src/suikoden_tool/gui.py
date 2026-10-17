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
from suikoden_tool.gui_batch_tab import TranslationBatchTab
from suikoden_tool.gui_service import (
    get_catalog_stats,
    load_catalog,
    save_entry,
    suggest_translation,
)
from suikoden_tool.dump_catalog_import import import_dump_to_catalog
from suikoden_tool.textasset_json_converter import convert_textasset_batch
from suikoden_tool.text_catalog import export_text_catalog
from suikoden_tool.text_discovery import discover_text_assets
from suikoden_tool.textasset_dump_export import export_textasset_dumps
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
        self.batch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.editor_tab, text="Editor atual")
        self.notebook.add(self.extraction_tab, text="Extração dos 4 bundles")
        self.notebook.add(self.batch_tab, text="Lotes de tradução")
        self._build_layout()
        self._build_extraction_tab()
        TranslationBatchTab(self.batch_tab)
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
        ttk.Button(header, text="Comparar JSON por ID", command=self.compare_translation_jsons).pack(side="right", padx=(0, 8))
        ttk.Button(header, text="Carregar JSON preparado", command=self.choose_prepared_text_json).pack(side="right", padx=(0, 8))
        ttk.Button(header, text="Importar dumps TextAsset", command=self.choose_textasset_dumps).pack(side="right", padx=(0, 8))
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
        self.translation_text.tag_configure("over_limit", foreground="#ff6b75")
        self.translation_text.bind("<<Modified>>", self._on_translation_modified)
        right.rowconfigure(5, weight=1)

        self.translation_counter_var = tk.StringVar(
            value="Limite por linha: 66 caracteres · Marcadores de nome contam como 10."
        )
        self.translation_counter = ttk.Label(
            right, textvariable=self.translation_counter_var, style="Muted.TLabel"
        )
        self.translation_counter.grid(row=6, column=0, sticky="ew", pady=(5, 0))

        ttk.Label(right, text="CONTEXTO OPCIONAL PARA A SUGESTÃO DE IA", style="Panel.TLabel").grid(
            row=7, column=0, sticky="w", pady=(12, 5)
        )
        self.context_entry = ttk.Entry(right)
        self.context_entry.grid(row=8, column=0, sticky="ew")

        actions = ttk.Frame(right, style="Panel.TFrame")
        actions.grid(row=9, column=0, sticky="ew", pady=(14, 0))
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
        ttk.Button(actions, text="Exportar dumps TextAsset (UABEA)", style="Accent.TButton", command=self._start_dump_export).pack(side="left", padx=8)
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
        self.extraction_files.set("\n".join(details) if details else f"Nenhum bundle encontrado em: {assets_dir}")
        self.extraction_status.set(f"{len(found)}/4 bundles encontrados." if missing else "4/4 bundles encontrados. Pronto para extrair.")
        return self.selected_bundles

    def _start_dump_export(self) -> None:
        """Exporta todos os TextAssets encontrados nos bundles selecionados, mesmo sem JSON válido."""
        bundles = self._locate_target_bundles()
        if not bundles:
            messagebox.showwarning(
                "Bundles não encontrados",
                "Configure a pasta do jogo e localize os bundles antes de exportar.",
                parent=self.root,
            )
            return
        tool = Path(__file__).resolve().parents[2] / "tools" / "UnityDataTools" / "UnityDataTool.exe"
        try:
            executable = resolve_unity_data_tool(tool) if tool.is_file() else resolve_unity_data_tool()
        except ValueError as exc:
            messagebox.showerror("UnityDataTool", str(exc), parent=self.root)
            return
        output_dir = Path(__file__).resolve().parents[2] / "work" / "bundle_analysis" / "uabea_dumps"
        self.extraction_status.set("Exportando dumps brutos de TextAsset. Os bundles originais não serão alterados.")
        self.extraction_log.delete("1.0", "end")
        threading.Thread(
            target=self._dump_export_worker,
            args=(bundles, executable, output_dir),
            daemon=True,
        ).start()

    def _dump_export_worker(self, bundles: tuple[Path, ...], executable: Path, output_dir: Path) -> None:
        try:
            report = export_textasset_dumps(bundles, executable, output_dir)
        except (OSError, ValueError) as exc:
            self.root.after(0, lambda msg=str(exc): self._finish_dump_export(None, msg))
            return
        self.root.after(0, lambda result=report: self._finish_dump_export(result, None))

    def _finish_dump_export(self, report: dict[str, Any] | None, error: str | None) -> None:
        if error:
            self.extraction_status.set("Falha na exportação de dumps.")
            self._append_extraction_log("ERRO: " + error)
            messagebox.showerror("Exportação TextAsset", error, parent=self.root)
            return
        assert report is not None
        self._append_extraction_log(f"Dumps exportados: {report['exported_count']}")
        self._append_extraction_log(f"Pasta: {report['output_dir']}")
        for item in report["exported"]:
            self._append_extraction_log(
                f"OK: {item['bundle']} | {item['asset_name']} | ID {item['object_id']} "
                f"({item['bytes']:,} bytes) → {Path(item['path']).name}"
            )
        for item in report["errors"]:
            self._append_extraction_log("AVISO: " + item)
        self.extraction_status.set(
            f"Exportação concluída: {report['exported_count']} dump(s); "
            f"{len(report['errors'])} aviso(s)."
        )
        messagebox.showinfo(
            "Exportação TextAsset",
            f"{report['exported_count']} dump(s) exportados para:\n{report['output_dir']}\n\n"
            "Os arquivos preservam o dump completo para usar no UABEA (Import Dump). "
            "Nenhum bundle original foi alterado.",
            parent=self.root,
        )

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
                entry_name = selected.get("entry")
                safe_entry = "".join(
                    char if char.isalnum() or char in "-_." else "_"
                    for char in (entry_name or "default")
                )
                source_json = output_dir / "sources" / f"{bundle.stem}__{safe_entry}__{safe_name}.json"
                catalog_json = output_dir / "catalogs" / f"{bundle.stem}__{safe_entry}__{safe_name}_pt_br.json"
                extract_textasset_json(
                    bundle, source_json, executable=executable,
                    entry=entry_name, asset_name=selected["name"], force=True,
                )
                export_text_catalog(source_json, catalog_json, target_language="pt-BR")
                count = selected.get("textlist_count") or 0
                results.append((bundle, catalog_json, selected["name"], count))
                self.root.after(
                    0,
                    lambda b=bundle.name, a=selected["name"], n=count, e=entry_name:
                    self._append_extraction_log(
                        f"OK: {b} → entrada '{e or 'única'}', recurso '{a}', {n} entradas."
                    ),
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

    def choose_prepared_text_json(self) -> None:
        """Carrega JSONs text_gsd1_en/text_gsd2_en/text_add_en para catálogos editáveis."""
        filenames = filedialog.askopenfilenames(
            title="Selecionar JSONs de texto preparados",
            filetypes=(("JSON de textos TextAsset", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if not filenames:
            return

        output_dir = Path.cwd() / "output" / "catalogos"
        results: list[tuple[Path, dict[str, Any]]] = []
        errors: list[str] = []
        for filename in filenames:
            source = Path(filename)
            destination = output_dir / f"{source.stem}.catalog.json"
            try:
                report = export_text_catalog(source, destination, target_language="pt-BR")
                results.append((destination, report))
            except (OSError, ValueError) as exc:
                errors.append(f"{source.name}: {exc}")

        lines = [
            f"{path.name}: {report.get('created', 0) or report.get('new', 0)} novas, "
            f"{report.get('preserved', 0)} preservadas, {report.get('changed', 0)} alteradas, "
            f"{report.get('orphaned', 0)} órfãs"
            for path, report in results
        ]
        if errors:
            lines.extend(["", "Falhas:"] + errors)
        messagebox.showinfo(
            "Carga de JSON preparado",
            f"Catálogos processados: {len(results)}\nFalhas: {len(errors)}\n"
            f"Destino: {output_dir}\n\n" + "\n".join(lines),
            parent=self.root,
        )
        if len(results) == 1 and not errors:
            self.open_catalog(results[0][0])

    def choose_textasset_dumps(self) -> None:
        """Converte dumps TextAsset em JSONs validados numa pasta separada."""
        filenames = filedialog.askopenfilenames(
            title="Selecionar dumps TextAsset (.txt)",
            filetypes=(("Dumps TextAsset", "*.txt"), ("Todos os arquivos", "*.*")),
        )
        if not filenames:
            return
        output_dir = Path.cwd() / "output" / "json_convertidos"
        if not messagebox.askyesno(
            "Substituir JSON existentes?",
            f"Saídas: {output_dir}\n\nArquivos JSON existentes com o mesmo nome serão substituídos. Continuar?",
            parent=self.root,
        ):
            return
        try:
            batch = convert_textasset_batch(
                [Path(name) for name in filenames], output_dir, overwrite=True
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Conversão interrompida", str(exc), parent=self.root)
            return

        errors: list[dict[str, str]] = []
        results: list[dict[str, Any]] = []
        log_path = ""
        for item in batch:
            if "batch_errors" in item:
                errors.extend(item["batch_errors"])
                log_path = item.get("log_path", log_path)
            elif "log_path" in item and "source" not in item:
                log_path = item["log_path"]
            else:
                results.append(item)

        lines = [
            f"{Path(item['source']).name} → {Path(item['output']).relative_to(output_dir).as_posix()} "
            f"({item['entries']} entradas)"
            for item in results
        ]
        if errors:
            lines.append("\nArquivos que falharam:")
            lines.extend(f"{Path(item['source']).name}: {item['error']}" for item in errors)
        title = "Conversão concluída" if not errors else "Conversão parcial"
        messagebox.showinfo(
            title,
            f"JSONs válidos criados/substituídos: {len(results)}\nFalhas: {len(errors)}\n"
            f"Pasta: {output_dir}\n\n" + "\n".join(lines) +
            "\n\nOs dumps .txt originais foram preservados.",
            parent=self.root,
        )

    def compare_translation_jsons(self) -> None:
        """Compara JSON original e traduzido por ID, sem alterar nenhum arquivo."""
        original_name = filedialog.askopenfilename(
            title="Selecione o JSON original em inglês",
            filetypes=(("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if not original_name:
            return
        translated_name = filedialog.askopenfilename(
            title="Selecione o JSON já traduzido",
            initialdir=str(Path(original_name).parent),
            filetypes=(("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if not translated_name:
            return

        def load_text_entries(filename: str) -> tuple[dict[str, Any], dict[tuple[type, Any], dict[str, Any]]]:
            try:
                data = json.loads(Path(filename).read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Não foi possível ler {Path(filename).name}: {exc}") from exc
            if not isinstance(data, dict) or not isinstance(data.get("textList"), list):
                raise ValueError(
                    f"{Path(filename).name} não possui uma lista 'textList'. "
                    "Selecione os JSONs de origem/lote, não um catálogo interno do editor."
                )
            entries: dict[tuple[type, Any], dict[str, Any]] = {}
            for position, entry in enumerate(data["textList"], start=1):
                if not isinstance(entry, dict) or "id" not in entry or not isinstance(entry.get("text"), str):
                    raise ValueError(
                        f"{Path(filename).name}: entrada {position} precisa conter 'id' e 'text' textual."
                    )
                entry_id = entry["id"]
                if isinstance(entry_id, bool) or not isinstance(entry_id, (int, str)):
                    raise ValueError(
                        f"{Path(filename).name}: tipo de ID inválido na entrada {position}: {entry_id!r}."
                    )
                key = (type(entry_id), entry_id)
                if key in entries:
                    raise ValueError(f"{Path(filename).name}: ID duplicado {entry_id!r}.")
                entries[key] = entry
            return data, entries

        try:
            _original_data, original_entries = load_text_entries(original_name)
            _translated_data, translated_entries = load_text_entries(translated_name)
        except ValueError as exc:
            messagebox.showerror("Não foi possível comparar os JSONs", str(exc), parent=self.root)
            return

        original_keys = set(original_entries)
        translated_keys = set(translated_entries)
        all_keys = original_keys | translated_keys

        def display_id(key: tuple[type, Any]) -> str:
            return str(key[1])

        def compare_sort(key: tuple[type, Any]) -> tuple[int, Any, str]:
            value = key[1]
            return (0, value, key[0].__name__) if isinstance(value, int) else (1, str(value), key[0].__name__)

        window = tk.Toplevel(self.root)
        window.title("Comparação de tradução por ID")
        window.geometry("1250x760")
        window.minsize(900, 560)
        window.configure(bg=BG)
        window.transient(self.root)

        top = ttk.Frame(window, padding=12)
        top.pack(fill="x")
        summary_var = tk.StringVar()
        ttk.Label(top, text=f"Original: {Path(original_name).name}", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(top, text=f"Traduzido: {Path(translated_name).name}", style="Muted.TLabel").pack(anchor="w", pady=(2, 5))
        ttk.Label(top, textvariable=summary_var, style="Header.TLabel").pack(anchor="w", pady=(4, 0))

        controls = ttk.Frame(window, padding=(12, 0, 12, 8))
        controls.pack(fill="x")
        filter_var = tk.StringVar(value="Todos")
        filter_combo = ttk.Combobox(
            controls,
            textvariable=filter_var,
            state="readonly",
            values=("Todos", "Diferentes/traduzidos", "Sem tradução", "Sem ID correspondente", "Idênticos"),
            width=24,
        )
        filter_combo.pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(controls, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        search_entry.insert(0, "")
        ttk.Label(controls, text="Buscar por ID ou texto").pack(side="right", padx=(8, 0))
        ttk.Button(controls, text="Importar todos os textos traduzidos para o editor", command=lambda: import_translations_into_editor()).pack(side="right", padx=(8, 0))

        table_frame = ttk.Frame(window, padding=(12, 0, 12, 8))
        table_frame.pack(fill="both", expand=True)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(table_frame, columns=("id", "status", "original", "translated"), show="headings")
        for col, title, width in (
            ("id", "ID", 90), ("status", "COMPARAÇÃO", 150),
            ("original", "ORIGINAL EM INGLÊS", 440), ("translated", "TEXTO TRADUZIDO", 440),
        ):
            tree.heading(col, text=title)
            tree.column(col, width=width, minwidth=70, stretch=(col in {"original", "translated"}))
        tree.tag_configure("missing", foreground="#ff8585")
        tree.tag_configure("same", foreground=MUTED)
        tree.tag_configure("changed", foreground=FG)
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        detail = ttk.Frame(window, padding=(12, 0, 12, 12))
        detail.pack(fill="x")
        detail.columnconfigure(0, weight=1)
        detail.columnconfigure(1, weight=1)
        ttk.Label(detail, text="ORIGINAL COMPLETO", style="Panel.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(detail, text="TRADUÇÃO COMPLETA", style="Panel.TLabel").grid(row=0, column=1, sticky="w", pady=(0, 4), padx=(8, 0))
        original_detail = tk.Text(detail, height=4, wrap="word", bg=PANEL, fg=FG, relief="flat", padx=8, pady=6, state="disabled")
        translated_detail = tk.Text(detail, height=4, wrap="word", bg=PANEL_ALT, fg=FG, relief="flat", padx=8, pady=6, state="disabled")
        original_detail.grid(row=1, column=0, sticky="ew")
        translated_detail.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        row_keys: dict[str, tuple[type, Any]] = {}
        ordered_keys = sorted(all_keys, key=compare_sort)

        def import_translations_into_editor() -> None:
            if self.catalog_path is None or not self.catalog or not self.entries:
                messagebox.showwarning(
                    "Editor sem catálogo",
                    "Antes de importar, abra o catálogo de trabalho na aba Editor.",
                    parent=window,
                )
                return
            if self.dirty and not self._confirm_discard():
                return

            editor_by_id: dict[tuple[type, Any], dict[str, Any]] = {}
            for editor_entry in self.entries:
                if isinstance(editor_entry, dict) and "id" in editor_entry:
                    editor_by_id[self._key(editor_entry)] = editor_entry

            matched = [key for key in translated_entries if key in editor_by_id]
            if not matched:
                messagebox.showerror(
                    "Nenhum ID correspondente",
                    "O JSON traduzido não possui IDs correspondentes às entradas do catálogo aberto no editor.",
                    parent=window,
                )
                return

            # Entradas sem texto nos dois JSONs não têm conteúdo para importar.
            # Elas são ignoradas; texto traduzido sem original exige revisão.
            empty_both = [
                key for key in matched
                if not (original_entries.get(key, {}).get("text", "").strip())
                and not translated_entries[key].get("text", "").strip()
            ]
            translated_without_original = [
                key for key in matched
                if not original_entries.get(key, {}).get("text", "").strip()
                and translated_entries[key].get("text", "").strip()
            ]
            if translated_without_original:
                ids = ", ".join(display_id(key) for key in translated_without_original[:20])
                suffix = "…" if len(translated_without_original) > 20 else ""
                messagebox.showwarning(
                    "Importação cancelada",
                    "Há textos traduzidos sem texto correspondente no original. "
                    f"Revise os IDs: {ids}{suffix}. Nenhum texto foi alterado.",
                    parent=window,
                )
                return

            blank = [
                key for key in matched
                if original_entries.get(key, {}).get("text", "").strip()
                and not translated_entries[key].get("text", "").strip()
            ]
            if blank:
                ids = ", ".join(display_id(key) for key in blank[:20])
                suffix = "…" if len(blank) > 20 else ""
                messagebox.showwarning(
                    "Importação cancelada",
                    f"Foram encontrados {len(blank)} textos traduzidos vazios para originais preenchidos. "
                    f"Revise os IDs: {ids}{suffix}. Nenhum texto foi alterado.",
                    parent=window,
                )
                return

            importable = [key for key in matched if key not in empty_both]
            if not importable:
                messagebox.showinfo(
                    "Nada para importar",
                    "Todas as entradas correspondentes estão vazias tanto no original quanto no traduzido. "
                    "Nenhum texto precisa ser importado.",
                    parent=window,
                )
                return

            if not messagebox.askyesno(
                "Confirmar importação",
                f"Importar {len(importable)} textos do JSON traduzido para o catálogo aberto?\\n\\n"
                f"{len(empty_both)} entradas vazias nos dois JSONs serão ignoradas. "
                "Os textos correspondentes existentes no editor serão substituídos e salvos como traduzidos. "
                "IDs sem correspondência serão ignorados. Esta ação não pode ser desfeita automaticamente.",
                parent=window,
            ):
                return

            try:
                for key in importable:
                    entry = editor_by_id[key]
                    saved = save_entry(
                        self.catalog_path,
                        entry["id"],
                        translated_entries[key]["text"],
                        "translated",
                    )
                    entry.update(saved)
            except (OSError, ValueError) as exc:
                messagebox.showerror(
                    "Falha durante a importação",
                    f"A importação foi interrompida: {exc}\\n\\n"
                    "Verifique o catálogo antes de continuar, pois entradas anteriores podem já ter sido salvas.",
                    parent=window,
                )
                self.refresh_list()
                self._update_stats()
                return

            self.dirty = False
            self.refresh_list()
            self._update_stats()
            if self.current_id is not None:
                current = self._current_entry()
                if current is not None:
                    self._display_entry(current)
            self.message_var.set(f"{len(importable)} textos importados do JSON traduzido.")
            messagebox.showinfo(
                "Importação concluída",
                f"Foram importados {len(importable)} textos por ID para o catálogo do editor. "
                f"{len(empty_both)} entradas vazias nos dois JSONs foram ignoradas.",
                parent=window,
            )

        def set_detail(widget: tk.Text, text: str) -> None:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", text)
            widget.configure(state="disabled")

        def row_info(key: tuple[type, Any]) -> tuple[str, str, str, str, str]:
            original_entry = original_entries.get(key)
            translated_entry = translated_entries.get(key)
            original_text = original_entry.get("text", "") if original_entry else ""
            translated_text = translated_entry.get("text", "") if translated_entry else ""
            if original_entry is None:
                status = "Só no traduzido"
            elif translated_entry is None:
                status = "ID ausente"
            elif not translated_text.strip():
                status = "Sem tradução"
            elif original_text == translated_text:
                status = "Idêntico"
            else:
                status = "Diferente"
            return display_id(key), status, original_text, translated_text, status

        def refresh_rows(*_args: Any) -> None:
            tree.delete(*tree.get_children())
            row_keys.clear()
            filter_value = filter_var.get()
            query = search_var.get().casefold().strip()
            for key in ordered_keys:
                id_text, status, original_text, translated_text, _ = row_info(key)
                if filter_value == "Diferentes/traduzidos" and status != "Diferente":
                    continue
                if filter_value == "Sem tradução" and status != "Sem tradução":
                    continue
                if filter_value == "Sem ID correspondente" and status not in {"ID ausente", "Só no traduzido"}:
                    continue
                if filter_value == "Idênticos" and status != "Idêntico":
                    continue
                if query and query not in id_text.casefold() and query not in original_text.casefold() and query not in translated_text.casefold():
                    continue
                tag = "missing" if status in {"ID ausente", "Só no traduzido", "Sem tradução"} else "same" if status == "Idêntico" else "changed"
                iid = f"row_{len(row_keys)}"
                row_keys[iid] = key
                tree.insert("", "end", iid=iid, values=(id_text, status, original_text, translated_text), tags=(tag,))
            tree.selection_remove(tree.selection())

        def on_row_selected(_event: Any = None) -> None:
            selection = tree.selection()
            if not selection:
                return
            key = row_keys.get(selection[0])
            if key is None:
                return
            _id, _status, original_text, translated_text, _ = row_info(key)
            set_detail(original_detail, original_text)
            set_detail(translated_detail, translated_text)

        filter_var.trace_add("write", refresh_rows)
        search_var.trace_add("write", refresh_rows)
        tree.bind("<<TreeviewSelect>>", on_row_selected)
        tree.bind("<Double-1>", on_row_selected)

        translated_count = sum(
            1 for key in original_keys & translated_keys
            if translated_entries[key].get("text", "").strip()
            and translated_entries[key].get("text") != original_entries[key].get("text")
        )
        empty_count = sum(
            1 for key in original_keys & translated_keys
            if not translated_entries[key].get("text", "").strip()
        )
        missing_count = len(original_keys - translated_keys)
        extra_count = len(translated_keys - original_keys)
        summary_var.set(
            f"Original: {len(original_entries)} IDs · Traduzido: {len(translated_entries)} IDs · "
            f"Diferentes: {translated_count} · Vazios: {empty_count} · Ausentes: {missing_count} · Extras: {extra_count}"
        )
        refresh_rows()
        if tree.get_children():
            first = tree.get_children()[0]
            tree.selection_set(first)
            tree.focus(first)
            on_row_selected()

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
            # A lista pode resumir espaços/quebras para caber na coluna, mas o editor
            # de entrada exibe o conteúdo completo e literal.
            snippet = " ".join(original.split())
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
        self._update_translation_counter()
        self.context_entry.delete(0, "end")
        if entry.get("previous_original") is not None:
            self.message_var.set("Atenção: a fonte mudou. Compare com o texto anterior antes de revisar.")
        else:
            self.message_var.set("Edição não salva." if entry.get("status") == "pending" else "Entrada carregada.")

    @staticmethod
    def _markers_to_lines(value: str) -> str:
        """Exibe ∠ com uma quebra e ∨ com duas quebras visuais."""
        return value.replace("∠", "∠\n").replace("∨", "∨\n\n")

    @staticmethod
    def _lines_to_markers(value: str) -> str:
        """Remove a quebra real de exibição colocada imediatamente após ∠."""
        value = value.replace("∠\r\n", "∠").replace("∠\n", "∠")
        # Remove apenas as duas quebras visuais adicionadas após o marcador de caixa.
        value = value.replace("∨\r\n\r\n", "∨").replace("∨\n\n", "∨")
        # Preserva quaisquer outras quebras e caracteres digitados pelo usuário.
        return value

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
            self._update_translation_counter()
            if not self._loading_entry and self.current_id is not None:
                self.dirty = True
                self.message_var.set("Alterações não salvas.")

    def _update_translation_counter(self) -> None:
        """Atualiza a contagem e pinta de vermelho o texto das linhas excedentes."""
        import re

        visible_text = self.translation_text.get("1.0", "end-1c")
        source_text = self._lines_to_markers(visible_text)
        lengths = self._dialogue_line_lengths(source_text)
        over_limit = {line for line, count in lengths if count > 66}

        self.translation_text.tag_remove("over_limit", "1.0", "end")
        pieces = re.split(r"([∠∨])", source_text)
        logical_line = 1
        physical_line = 1
        for index, piece in enumerate(pieces):
            if index % 2 == 0:
                if logical_line in over_limit:
                    self.translation_text.tag_add(
                        "over_limit", f"{physical_line}.0", f"{physical_line}.end"
                    )
                logical_line += 1
            elif piece == "∠":
                physical_line += 1
            elif piece == "∨":
                physical_line += 2

        if over_limit:
            details = ", ".join(f"L{line}: {count}/66" for line, count in lengths if count > 66)
            self.translation_counter.configure(foreground="#ff7b86")
            self.translation_counter_var.set(f"⚠ Linhas acima do limite: {details}")
        else:
            self.translation_counter.configure(foreground="#83d6a5")
            self.translation_counter_var.set(
                f"✓ Todas as {len(lengths)} linhas dentro do limite de 66 caracteres."
            )

    def _current_entry(self) -> dict[str, Any] | None:
        if self.current_id is None:
            return None
        return next((entry for entry in self.entries if self._key(entry) == self.current_id), None)

    def save(self) -> None:
        self._save("translated")

    def save_reviewed(self) -> None:
        self._save("reviewed")

    @staticmethod
    def _dialogue_line_lengths(value: str) -> list[tuple[int, int]]:
        """Retorna (número da linha, caracteres exibidos) segundo as regras conhecidas."""
        import re

        # Marcadores de nome são substituições dinâmicas; reservar 10 caracteres cada.
        name_tokens = ("♂㈱", "♂①", "♂②", "♂⑩")
        # ∠ encerra uma linha; ∨ encerra uma caixa. Nenhum dos dois conta no limite.
        lines = re.split(r"[∠∨]", value)
        results: list[tuple[int, int]] = []
        for line_number, line in enumerate(lines, start=1):
            count = 0
            i = 0
            while i < len(line):
                # /"texto"/ aparece no jogo como "texto": contar o texto e as aspas.
                if line.startswith('/"', i):
                    end = line.find('"/', i + 2)
                    if end >= 0:
                        count += len(line[i + 1:end + 1])
                        i = end + 2
                        continue
                token = next((token for token in name_tokens if line.startswith(token, i)), None)
                if token:
                    count += 10
                    i += len(token)
                else:
                    count += 1
                    i += 1
            results.append((line_number, count))
        return results

    def _save(self, status: str) -> None:
        entry = self._current_entry()
        if entry is None or self.catalog_path is None:
            messagebox.showinfo("Selecione uma entrada", "Abra um catálogo e selecione uma entrada.")
            return
        raw_translation = self.translation_text.get("1.0", "end-1c")
        over_limit = [
            (line_number, count)
            for line_number, count in self._dialogue_line_lengths(raw_translation)
            if count > 66
        ]
        if over_limit:
            details = "\\n".join(
                f"Linha {line_number}: {count} caracteres (limite: 66)"
                for line_number, count in over_limit
            )
            messagebox.showwarning(
                "Limite de caracteres excedido",
                "A tradução não foi salva. Cada linha de diálogo pode ter no máximo 66 caracteres.\\n\\n"
                + details
                + "\\n\\nRevise as linhas indicadas e tente salvar novamente.",
                parent=self.root,
            )
            return
        translation = self._lines_to_markers(raw_translation)
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
