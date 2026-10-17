""""Interface de linha de comando para o toolkit."""
import argparse
import json
from pathlib import Path
from typing import Any

from suikoden_tool.bundle_inspector import inspect_bundle, inventory_bundles
from suikoden_tool.translation_schema import make_translation_entry


def _write_json(data: object, output: Path) -> None:
    """Grava JSON UTF-8 legível, preservando acentos."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _export_text_catalog(
    source: Path, output: Path, target_language: str
) -> dict[str, Any]:
    """Converte um TextAsset JSON com textList para um catálogo traduzível."""
    if source.resolve() == output.resolve():
        raise ValueError("A entrada e a saída não podem ser o mesmo arquivo.")

    try:
        data = json.loads(source.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON de entrada inválido: {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("textList"), list):
        raise ValueError(
            "Formato inválido: esperado um objeto JSON com uma lista 'textList'."
        )

    entries = data["textList"]
    exported = []
    seen_ids = set()

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Entrada {index} não é um objeto JSON.")
        if "id" not in entry or "text" not in entry:
            raise ValueError(f"Entrada {index} precisa conter 'id' e 'text'.")
        if not isinstance(entry["text"], str):
            raise ValueError(f"O texto da entrada {index} precisa ser uma string.")

        entry_id = entry["id"]
        if entry_id in seen_ids:
            raise ValueError(f"ID duplicado no catálogo de origem: {entry_id!r}.")
        seen_ids.add(entry_id)

        exported.append({
            "id": entry_id,
            "original": entry["text"],
            "translation": "",
            "status": "pending",
        })

    return {
        "schema_version": 1,
        "resource": source.stem,
        "source_language": "en",
        "target_language": target_language,
        "entries": exported,
    }


def build_parser() -> argparse.ArgumentParser:
    """Define os comandos do CLI."""
    parser = argparse.ArgumentParser(
        prog="suikoden-tool",
        description="Toolkit Suikoden PT-BR",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser("inspect", help="Inspeciona cabeçalho de bundle")
    p.add_argument("bundle", type=Path)
    p.add_argument("-o", "--output", type=Path)

    p = commands.add_parser("inventory", help="Inventaria bundles em uma pasta")
    p.add_argument("directory", type=Path)
    p.add_argument(
        "-o", "--output", type=Path,
        default=Path("output/bundle_inventory.json"),
    )

    p = commands.add_parser("template", help="Cria JSON de tradução de exemplo")
    p.add_argument(
        "-o", "--output", type=Path,
        default=Path("data/translations_template.json"),
    )
    p.add_argument(
        "--game", choices=["suikoden_i", "suikoden_ii"], default="suikoden_i"
    )

    text_commands = commands.add_parser("text", help="Operações com textos extraídos")
    text_subcommands = text_commands.add_subparsers(dest="text_command", required=True)
    p = text_subcommands.add_parser(
        "export", help="Exporta textList JSON para um catálogo traduzível"
    )
    p.add_argument("--input", required=True, type=Path, help="JSON extraído do TextAsset")
    p.add_argument("--output", required=True, type=Path, help="Catálogo JSON de saída")
    p.add_argument("--target-language", default="pt-BR", help="Idioma de destino (padrão: pt-BR)")

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
                {
                    "schema_version": 1,
                    "bundle_count": len(records),
                    "bundles": records,
                },
                args.output,
            )
            print(f"Bundles encontrados: {len(records)}. Inventário: {args.output}")
        elif args.command == "text" and args.text_command == "export":
            catalog = _export_text_catalog(
                args.input, args.output, args.target_language
            )
            _write_json(catalog, args.output)
            print(f"Catálogo criado: {args.output.resolve()}")
            print(f"Entradas exportadas: {len(catalog['entries'])}")
            print(f"Idioma de destino: {args.target_language}")
        else:
            payload = {
                "schema_version": 1,
                "project": "Suikoden I & II HD Remaster PT-BR",
                "game": args.game,
                "entries": [
                    make_translation_entry("example_0001", "Texto original de exemplo")
                ],
            }
            _write_json(payload, args.output)
            print(f"Modelo JSON criado: {args.output}")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
