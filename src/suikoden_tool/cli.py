"""Interface de linha de comando para o toolkit."""

import argparse
import json
from pathlib import Path

from suikoden_tool.bundle_inspector import inspect_bundle, inventory_bundles
from suikoden_tool.text_catalog import (
    _read_json,
    catalog_stats,
    export_text_catalog,
    validate_catalog,
)
from suikoden_tool.text_batch import export_translation_batch, import_translation_batch
from suikoden_tool.translation_schema import make_translation_entry


def _write_json(data: object, output: Path) -> None:
    """Grava JSON UTF-8 legível, preservando acentos."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    """Define os comandos do CLI."""
    parser = argparse.ArgumentParser(prog="suikoden-tool", description="Toolkit Suikoden PT-BR")
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser("inspect", help="Inspeciona cabeçalho de bundle")
    p.add_argument("bundle", type=Path)
    p.add_argument("-o", "--output", type=Path)

    p = commands.add_parser("inventory", help="Inventaria bundles em uma pasta")
    p.add_argument("directory", type=Path)
    p.add_argument("-o", "--output", type=Path, default=Path("output/bundle_inventory.json"))

    p = commands.add_parser("template", help="Cria JSON de tradução de exemplo")
    p.add_argument("-o", "--output", type=Path, default=Path("data/translations_template.json"))
    p.add_argument("--game", choices=["suikoden_i", "suikoden_ii"], default="suikoden_i")

    text_commands = commands.add_parser("text", help="Operações com textos extraídos")
    text_subcommands = text_commands.add_subparsers(dest="text_command", required=True)

    p = text_subcommands.add_parser("export", help="Cria ou atualiza catálogo sem perder traduções")
    p.add_argument("--input", required=True, type=Path, help="JSON extraído do TextAsset")
    p.add_argument("--output", required=True, type=Path, help="Catálogo JSON de saída")
    p.add_argument("--target-language", default="pt-BR", help="Idioma de destino (padrão: pt-BR)")

    p = text_subcommands.add_parser("validate", help="Valida um catálogo de tradução")
    p.add_argument("--input", required=True, type=Path, help="Catálogo JSON")
    p.add_argument("--source", type=Path, help="JSON extraído para comparar textos de origem")

    p = text_subcommands.add_parser("stats", help="Mostra estatísticas do catálogo")
    p.add_argument("--input", required=True, type=Path, help="Catálogo JSON")

    p = text_subcommands.add_parser("batch-export", help="Exporta lote de tradução para CSV")
    p.add_argument("--input", required=True, type=Path, help="Catálogo JSON")
    p.add_argument("--output", required=True, type=Path, help="CSV de saída compatível com Excel")
    p.add_argument("--limit", type=int, default=100, help="Máximo de entradas (padrão: 100)")
    p.add_argument(
        "--pending-only",
        action="store_true",
        help="Exporta apenas entradas pending, sem needs_review",
    )

    p = text_subcommands.add_parser("batch-import", help="Importa traduções de CSV para o catálogo")
    p.add_argument("--input", required=True, type=Path, help="CSV preenchido")
    p.add_argument("--catalog", required=True, type=Path, help="Catálogo JSON a atualizar")
    return parser


def main() -> None:
    """Executa o comando solicitado e apresenta erros de entrada."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            result = inspect_bundle(args.bundle)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.output:
                _write_json(result, args.output)
        elif args.command == "inventory":
            records = inventory_bundles(args.directory)
            _write_json(
                {"schema_version": 1, "bundle_count": len(records), "bundles": records},
                args.output,
            )
            print(f"Bundles encontrados: {len(records)}. Inventário: {args.output}")
        elif args.command == "text" and args.text_command == "export":
            result = export_text_catalog(args.input, args.output, args.target_language)
            print(f"Catálogo atualizado: {args.output.resolve()}")
            print(f"Entradas novas: {result['new']}")
            print(f"Traduções preservadas: {result['preserved']}")
            print(f"Textos de origem alterados (revisão necessária): {result['changed']}")
            print(f"Entradas preservadas como órfãs: {result['orphaned']}")
        elif args.command == "text" and args.text_command == "validate":
            report = validate_catalog(_read_json(args.input), args.source)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if not report["valid"]:
                parser.exit(1, "Validação reprovada: corrija os erros listados.\n")
        elif args.command == "text" and args.text_command == "stats":
            stats = catalog_stats(_read_json(args.input))
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        elif args.command == "text" and args.text_command == "batch-export":
            result = export_translation_batch(
                args.input,
                args.output,
                limit=args.limit,
                include_needs_review=not args.pending_only,
            )
            print(f"Entradas exportadas: {result['exported']} de {result['available']}.")
            print(f"CSV: {args.output.resolve()}")
        elif args.command == "text" and args.text_command == "batch-import":
            result = import_translation_batch(args.catalog, args.input)
            print(f"Traduções importadas: {result['updated']}.")
            print(f"Linhas vazias ignoradas: {result['skipped_empty']}.")
        else:
            payload = {
                "schema_version": 1,
                "project": "Suikoden I & II HD Remaster PT-BR",
                "game": args.game,
                "entries": [make_translation_entry("example_0001", "Texto original de exemplo")],
            }
            _write_json(payload, args.output)
            print(f"Modelo JSON criado: {args.output}")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
