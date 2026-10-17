# Formato JSON de tradução

**Status:** há dois formatos em uso no fluxo atual. O modelo geral de tradução e o catálogo exportado de `textList` têm campos diferentes; não os trate como intercambiáveis sem uma migração explícita.

## 1. Catálogo exportado por `suikoden-tool text export`

A entrada deve ser um JSON com uma lista `textList` cujos itens contenham `id` e `text`:

```json
{
  "textList": [
    {"id": 1, "text": "Power?"},
    {"id": 2, "text": "Is it power that we seek?"}
  ]
}
```

O comando:

```powershell
suikoden-tool text export --input extracted.json --output catalog.json --target-language pt-BR
```

gera:

```json
{
  "schema_version": 1,
  "resource": "extracted",
  "source_language": "en",
  "target_language": "pt-BR",
  "entries": [
    {
      "id": 1,
      "original": "Power?",
      "translation": "",
      "status": "pending"
    }
  ]
}
```

### Campos do catálogo exportado

| Campo | Significado |
|---|---|
| `schema_version` | Versão do formato de catálogo. |
| `resource` | Nome derivado do nome do arquivo de entrada, sem extensão. |
| `source_language` | Atualmente fixado como `en` pelo exportador. |
| `target_language` | Idioma passado em `--target-language`, padrão `pt-BR`. |
| `entries[].id` | ID original vindo do TextAsset; o exportador rejeita duplicatas. |
| `entries[].original` | Texto original, incluindo marcadores e quebras de linha. |
| `entries[].translation` | Tradução editável; começa vazia. |
| `entries[].status` | Começa como `pending`. O conjunto de estados ainda não está formalizado. |

O exportador valida que a raiz contenha `textList`, que cada item seja um objeto com `id` e `text`, que `text` seja string e que IDs sejam únicos. Não exige atualmente um tipo específico para `id` nem valida o conjunto de estados depois da exportação.

**Aviso de perda de dados:** cada execução cria um catálogo novo com traduções vazias. Não reexporte sobre um catálogo traduzido antes de fazer backup. A mesclagem segura ainda não está implementada.

## 2. Esquema geral inicial

O construtor `make_translation_entry` de `translation_schema.py` gera campos para um fluxo mais rico:

- `id`, `game`, `asset_name`, `asset_path`
- `object_path_id`, `text_id`
- `source_text`, `translation_pt_br`, `context`, `text_type`
- `max_characters`, `max_lines`, `max_width_px`
- `control_tokens`, `pointer_metadata`, `status`, `notes`

Esse esquema é inicial e não é o formato produzido por `text export`. A unificação dos formatos deve ser uma decisão explícita, com migração e testes.

## Regras de preservação

- Não alterar o texto original ao traduzir.
- Preservar exatamente IDs, marcadores de controle, variáveis e quebras de linha até que seu significado seja confirmado.
- Não presumir que `∠` seja uma quebra de linha simples; sua semântica ainda está em investigação.
- Usar `null` para limites desconhecidos; não transformar estimativas em regras.
- Não usar um ID criado pelo toolkit como substituto de um identificador interno do jogo.
- Antes de importação/reconstrução, definir serialização determinística e testes de ida e volta.
- Catálogos reais extraídos do jogo devem permanecer fora do Git se contiverem material proprietário.
