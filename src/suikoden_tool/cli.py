"""Interface de linha de comando para o toolkit."""
import argparse
import json
from pathlib import Path
from suikoden_tool.bundle_inspector import inspect_bundle, inventory_bundles
from suikoden_tool.translation_schema import make_translation_entry

def _write_json(data: object, output: Path) -> None:
    """Grava JSON UTF-8 legível, preservando acentos."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def build_parser() -> argparse.ArgumentParser:
    """Define os comandos do CLI."""
    parser = argparse.ArgumentParser(prog="suikoden-tool", description="Toolkit Suikoden PT-BR")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("inspect", help="Inspeciona cabeçalho de bundle"); p.add_argument("bundle", type=Path); p.add_argument("-o", "--output", type=Path)
    p = commands.add_parser("inventory", help="Inventaria bundles em uma pasta"); p.add_argument("directory", type=Path); p.add_argument("-o", "--output", type=Path, default=Path("output/bundle_inventory.json"))
    p = commands.add_parser("template", help="Cria JSON de tradução de exemplo"); p.add_argument("-o", "--output", type=Path, default=Path("data/translations_template.json")); p.add_argument("--game", choices=["suikoden_i", "suikoden_ii"], default="suikoden_i")
    return parser

def main() -> None:
    """Executa o comando solicitado e apresenta erros de entrada."""
    parser = build_parser(); args = parser.parse_args()
    try:
        if args.command == "inspect":
            result = inspect_bundle(args.bundle); print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.output: _write_json(result, args.output)
        elif args.command == "inventory":
            records = inventory_bundles(args.directory); _write_json({"schema_version": 1, "bundle_count": len(records), "bundles": records}, args.output); print(f"Bundles encontrados: {len(records)}. Inventário: {args.output}")
        else:
            payload = {"schema_version": 1, "project": "Suikoden I & II HD Remaster PT-BR", "game": args.game, "entries": [make_translation_entry("example_0001", "Texto original de exemplo")]}
            _write_json(payload, args.output); print(f"Modelo JSON criado: {args.output}")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Erro: {exc}\n")

if __name__ == "__main__": main()
