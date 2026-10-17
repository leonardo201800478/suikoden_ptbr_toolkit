"""Interface para dividir JSONs de tradução em lotes controlados por ID."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any


class TranslationBatchTab:
    """Divide arquivos textList em lotes sem renumerar nem alterar as entradas."""

    def __init__(self, parent: ttk.Frame) -> None:
        self.parent = parent
        self.source_path: Path | None = None
        self.source_data: dict[str, Any] = {}
        self.entries: list[dict[str, Any]] = []
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.parent, padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)

        ttk.Label(frame, text="LOTES DE TRADUÇÃO", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text=(
                "Divida cada JSON textList em lotes rastreáveis por ID. "
                "As entradas são copiadas sem renumeração e os arquivos de origem não são alterados."
            ),
            style="Muted.TLabel",
            wraplength=1050,
        ).grid(row=1, column=0, sticky="w", pady=(8, 14))

        controls = ttk.Frame(frame)
        controls.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(controls, text="Selecionar JSON…", command=self.choose_file).pack(side="left")
        ttk.Label(controls, text="Entradas por lote:").pack(side="left", padx=(18, 6))
        self.batch_size_var = tk.StringVar(value="100")
        self.batch_size_combo = ttk.Combobox(
            controls, textvariable=self.batch_size_var, width=8,
            values=("50", "100", "150", "200"), state="normal",
        )
        self.batch_size_combo.pack(side="left")
        ttk.Button(
            controls, text="Dividir em lotes", command=self.split_file, style="Accent.TButton"
        ).pack(side="left", padx=(12, 0))
        ttk.Button(
            controls, text="Unificar lotes traduzidos…", command=self.merge_batches
        ).pack(side="left", padx=(8, 0))

        self.file_var = tk.StringVar(value="Nenhum arquivo selecionado.")
        ttk.Label(frame, textvariable=self.file_var, style="Muted.TLabel", wraplength=1100).grid(
            row=3, column=0, sticky="ew", pady=(0, 10)
        )

        list_frame = ttk.Frame(frame)
        list_frame.grid(row=4, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            list_frame, columns=("range", "count", "status"), show="headings"
        )
        self.tree.heading("range", text="INTERVALO / IDs DO LOTE")
        self.tree.heading("count", text="ENTRADAS")
        self.tree.heading("status", text="STATUS")
        self.tree.column("range", width=420, stretch=True)
        self.tree.column("count", width=110, stretch=False, anchor="center")
        self.tree.column("status", width=180, stretch=False)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.status_var = tk.StringVar(value="Selecione um JSON com a estrutura textList.")
        ttk.Label(frame, textvariable=self.status_var, style="Muted.TLabel", wraplength=1100).grid(
            row=5, column=0, sticky="ew", pady=(10, 0)
        )

    def choose_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Selecionar JSON de tradução",
            filetypes=(("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if not filename:
            return
        path = Path(filename)
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            entries = data.get("textList") if isinstance(data, dict) else None
            if not isinstance(entries, list):
                raise ValueError('O JSON deve conter uma lista "textList".')
            if not entries:
                raise ValueError('"textList" está vazia.')
            invalid = [
                index for index, entry in enumerate(entries)
                if not isinstance(entry, dict) or "id" not in entry or "text" not in entry
            ]
            if invalid:
                raise ValueError(
                    "Cada entrada deve ser um objeto com os campos id e text. "
                    f"Entradas inválidas (posição iniciada em 1): {', '.join(str(i + 1) for i in invalid[:20])}."
                )
            ids = [entry["id"] for entry in entries]
            if any(
                isinstance(entry_id, bool) or not isinstance(entry_id, (int, str))
                for entry_id in ids
            ):
                raise ValueError("Cada ID deve ser um número inteiro ou uma string.")
            duplicate_ids = []
            seen: set[tuple[type, Any]] = set()
            for entry_id in ids:
                key = (type(entry_id), entry_id)
                if key in seen:
                    duplicate_ids.append(entry_id)
                seen.add(key)
            if duplicate_ids:
                raise ValueError(
                    "Foram encontrados IDs duplicados: "
                    + ", ".join(map(str, duplicate_ids[:20]))
                    + ". Corrija a origem antes de dividir."
                )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("JSON inválido", str(exc), parent=self.parent)
            return

        self.source_path = path
        self.source_data = data
        self.entries = entries
        self.file_var.set(f"Arquivo: {path}  ·  {len(entries):,} entradas  ·  IDs únicos")
        self.status_var.set("Arquivo validado. Escolha a quantidade de entradas por lote.")
        self.tree.delete(*self.tree.get_children())

    def merge_batches(self) -> None:
        """Mescla os textos traduzidos nos objetos originais, usando IDs como chave."""
        source_filename = filedialog.askopenfilename(
            title="Selecionar JSON original completo",
            filetypes=(("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if not source_filename:
            return
        source_path = Path(source_filename)
        try:
            source_data = json.loads(source_path.read_text(encoding="utf-8-sig"))
            source_entries = source_data.get("textList") if isinstance(source_data, dict) else None
            if not isinstance(source_entries, list) or not source_entries:
                raise ValueError('O JSON original deve conter uma lista "textList" não vazia.')
            original_by_id: dict[tuple[type, Any], dict[str, Any]] = {}
            for entry in source_entries:
                if not isinstance(entry, dict) or "id" not in entry or "text" not in entry:
                    raise ValueError("Todas as entradas originais devem conter id e text.")
                entry_id = entry["id"]
                if isinstance(entry_id, bool) or not isinstance(entry_id, (int, str)):
                    raise ValueError("Os IDs originais devem ser inteiros ou strings.")
                key = (type(entry_id), entry_id)
                if key in original_by_id:
                    raise ValueError(f"ID duplicado no arquivo original: {entry_id!r}.")
                original_by_id[key] = entry
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("JSON original inválido", str(exc), parent=self.parent)
            return

        batch_dirname = filedialog.askdirectory(
            title="Selecionar pasta com os lotes JSON traduzidos",
            initialdir=str(source_path.parent),
        )
        if not batch_dirname:
            return
        batch_dir = Path(batch_dirname)
        batch_paths = sorted(
            path for path in batch_dir.glob("lote_*.json")
            if path.is_file() and path.name != "manifest_lotes.json"
        )
        if not batch_paths:
            messagebox.showerror(
                "Lotes não encontrados",
                "A pasta selecionada não contém arquivos lote_*.json.",
                parent=self.parent,
            )
            return

        translated_by_id: dict[tuple[type, Any], str] = {}
        errors: list[str] = []
        for batch_path in batch_paths:
            try:
                batch_data = json.loads(batch_path.read_text(encoding="utf-8-sig"))
                batch_entries = batch_data.get("textList") if isinstance(batch_data, dict) else None
                if not isinstance(batch_entries, list):
                    raise ValueError('não contém uma lista "textList".')
                for entry in batch_entries:
                    if not isinstance(entry, dict) or "id" not in entry or "text" not in entry:
                        raise ValueError("há uma entrada sem id ou text.")
                    entry_id = entry["id"]
                    if isinstance(entry_id, bool) or not isinstance(entry_id, (int, str)):
                        raise ValueError(f"ID com tipo inválido: {entry_id!r}.")
                    key = (type(entry_id), entry_id)
                    if key not in original_by_id:
                        errors.append(f"{batch_path.name}: ID extra {entry_id!r}.")
                        continue
                    if key in translated_by_id:
                        errors.append(f"{batch_path.name}: ID duplicado entre lotes {entry_id!r}.")
                        continue
                    if not isinstance(entry["text"], str):
                        errors.append(f"{batch_path.name}: text não é string para ID {entry_id!r}.")
                        continue
                    translated_by_id[key] = entry["text"]
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{batch_path.name}: {exc}")

        missing = [
            entry["id"] for entry in source_entries
            if (type(entry["id"]), entry["id"]) not in translated_by_id
        ]
        if missing:
            errors.append(
                "IDs ausentes nos lotes: " + ", ".join(map(str, missing[:40]))
                + ("…" if len(missing) > 40 else "") + "."
            )
        if errors:
            messagebox.showerror(
                "Unificação bloqueada",
                "Os lotes não correspondem exatamente ao catálogo original. "
                "Nenhum arquivo unificado foi criado.\n\n"
                + "\n".join(errors[:30])
                + (f"\n… e mais {len(errors) - 30} problema(s)." if len(errors) > 30 else ""),
                parent=self.parent,
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Salvar JSON completo traduzido",
            initialdir=str(source_path.parent),
            initialfile=f"{source_path.stem}_ptbr.json",
            defaultextension=".json",
            filetypes=(("Arquivos JSON", "*.json"),),
        )
        if not output_path:
            return

        merged_data = dict(source_data)
        merged_entries: list[dict[str, Any]] = []
        for original_entry in source_entries:
            entry = dict(original_entry)
            key = (type(entry["id"]), entry["id"])
            entry["text"] = translated_by_id[key]
            merged_entries.append(entry)
        merged_data["textList"] = merged_entries
        try:
            Path(output_path).write_text(
                json.dumps(merged_data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except (OSError, TypeError, ValueError) as exc:
            messagebox.showerror("Falha ao salvar JSON unificado", str(exc), parent=self.parent)
            return

        messagebox.showinfo(
            "Unificação concluída",
            f"Arquivo completo criado com {len(merged_entries)} entradas.\n"
            f"Todos os IDs foram conferidos e os textos foram associados por ID.\n"
            f"Arquivo: {output_path}\n\n"
            "O arquivo original e os lotes não foram alterados.",
            parent=self.parent,
        )

    def split_file(self) -> None:
        if self.source_path is None or not self.entries:
            messagebox.showinfo("Selecione um arquivo", "Selecione e valide um JSON primeiro.", parent=self.parent)
            return
        try:
            batch_size = int(self.batch_size_var.get().strip())
            if not 1 <= batch_size <= 200:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Tamanho inválido",
                "Informe um número inteiro entre 1 e 200 entradas por lote.",
                parent=self.parent,
            )
            return

        output_dir = filedialog.askdirectory(
            title="Selecionar pasta de destino dos lotes",
            initialdir=str(self.source_path.parent),
        )
        if not output_dir:
            return
        # Separar lotes dos catálogos completos e usar o nome integral do arquivo de origem.
        destination = Path(output_dir) / "lotes_traducao" / self.source_path.name
        if destination.exists() and any(destination.iterdir()):
            if not messagebox.askyesno(
                "Pasta já contém arquivos",
                f"A pasta de destino já existe e contém arquivos:\n{destination}\n\n"
                "Os nomes de lote coincidentes serão substituídos. Continuar?",
                parent=self.parent,
            ):
                return
        destination.mkdir(parents=True, exist_ok=True)

        manifest: dict[str, Any] = {
            "source_file": self.source_path.name,
            "source_path": str(self.source_path.resolve()),
            "output_folder": str(destination),
            "source_entry_count": len(self.entries),
            "batch_size": batch_size,
            "id_type": "IDs originais; não renumerados",
            "batches": [],
        }
        rows: list[tuple[str, int, int, str]] = []
        try:
            for start in range(0, len(self.entries), batch_size):
                batch_entries = self.entries[start : start + batch_size]
                number = start // batch_size + 1
                filename = f"lote_{number:03d}.json"
                batch_data = dict(self.source_data)
                batch_data["textList"] = batch_entries
                output_path = destination / filename
                output_path.write_text(
                    json.dumps(batch_data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                ids = [entry["id"] for entry in batch_entries]
                manifest["batches"].append({
                    "file": filename,
                    "entry_count": len(batch_entries),
                    "first_id": ids[0],
                    "last_id": ids[-1],
                    "ids": ids,
                    "status": "pending",
                })
                rows.append((filename, ids[0], ids[-1], len(batch_entries)))
            (destination / "manifest_lotes.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        except (OSError, TypeError, ValueError) as exc:
            messagebox.showerror("Falha ao criar lotes", str(exc), parent=self.parent)
            return

        self.tree.delete(*self.tree.get_children())
        for filename, first_id, last_id, count in rows:
            self.tree.insert(
                "", "end",
                values=(f"{first_id} → {last_id}  ({filename})", count, "Pendente"),
            )
        self.status_var.set(
            f"{len(rows)} lotes criados · {len(self.entries)} entradas · "
            f"tamanho máximo de {batch_size} entradas · destino: {destination}"
        )
        messagebox.showinfo(
            "Divisão concluída",
            f"Arquivo dividido em {len(rows)} lotes.\n"
            f"Entradas preservadas: {len(self.entries)}\n"
            f"Manifesto de controle: {destination / 'manifest_lotes.json'}\n\n"
            "O JSON original não foi alterado.",
            parent=self.parent,
        )
