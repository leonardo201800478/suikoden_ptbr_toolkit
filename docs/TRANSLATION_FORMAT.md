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

O exportador valida que a raiz contenha `textList`, que cada item seja um objeto com `id` e `text`, que `text` seja string e que IDs sejam únicos. IDs devem ser strings ou inteiros (booleanos não são aceitos). Se a saída já existir, o comando valida o catálogo e tenta uma mesclagem segura.

### Política de atualização segura

- ID e texto original compatíveis: preserva tradução, status e campos adicionais.
- ID existente com texto original alterado: atualiza `original`, preserva a tradução, grava `previous_original`, define `source_changed: true` e muda status para `needs_review`.
- ID novo: adiciona entrada com tradução vazia e status `pending`.
- ID ausente na nova extração: mantém a entrada e tradução, marcando status `orphaned`.
- Catálogo existente malformado, de outro recurso ou idioma: aborta sem modificar a saída.

A atualização não apaga silenciosamente traduções. Mudanças de origem exigem revisão humana; não se deve considerar a tradução automaticamente correta. Depois de revisar manualmente a tradução para o novo texto, o responsável pode atualizar o status para `translated` ou `reviewed` e remover `source_changed` e `previous_original` para encerrar o alerta de revisão.

## 2. Esquema geral inicial

O construtor `make_translation_entry` de `translation_schema.py` gera campos para um fluxo mais rico:

- `id`, `game`, `asset_name`, `asset_path`
- `object_path_id`, `text_id`
- `source_text`, `translation_pt_br`, `context`, `text_type`
- `max_characters`, `max_lines`, `max_width_px`
- `control_tokens`, `pointer_metadata`, `status`, `notes`

Esse esquema é inicial e não é o formato produzido por `text export`. A unificação dos formatos deve ser uma decisão explícita, com migração e testes.

## Validação e estatísticas

`suikoden-tool text validate --input catalog.json` verifica campos obrigatórios, tipos, IDs duplicados, status, traduções pendentes e entradas marcadas com mudança de origem. Também emite avisos quando uma tradução preenchida tem quantidade diferente do marcador conhecido `∠` ou de quebras de linha (`CRLF`, `LF` e `CR`) em relação ao original. Esses avisos são conservadores: não definem a semântica de `∠` nem bloqueiam a validação estrutural. Com `--source extracted.json`, também compara os IDs e os textos originais contra uma nova extração. Erros estruturais resultam em código de saída diferente de zero; pendências, possíveis alterações de layout e divergências de origem são avisos.

`suikoden-tool text stats --input catalog.json` mostra total, estados `pending`, `translated`, `reviewed`, `needs_review`, `orphaned` e percentual concluído. Os comandos de validação e estatística não alteram o catálogo.

## Tradução em lotes por CSV

`text batch-export` exporta por padrão até 100 entradas nos estados `pending` e `needs_review` para CSV UTF-8 com BOM. O CSV inclui `id`, `id_type`, `original`, `translation` e `status`. `id_type` preserva a diferença entre IDs numéricos e IDs textuais, inclusive quando ambos têm a mesma representação visual.

```powershell
suikoden-tool text batch-export --input catalog.json --output lote_001.csv --limit 100
suikoden-tool text batch-export --input catalog.json --output lote_002.csv --limit 100 --pending-only
suikoden-tool text batch-import --catalog catalog.json --input lote_001.csv
```

Edite somente a coluna `translation`. A importação verifica todos os IDs, duplicatas e correspondência exata de `original` antes de gravar qualquer alteração. Se uma linha for inválida, o catálogo permanece inalterado. Traduções vazias são ignoradas e não apagam conteúdo existente. Uma entrada `needs_review` continua nesse estado após a importação; a revisão deve ser confirmada separadamente. Recomenda-se fazer backup do catálogo antes de importar cada lote.

Estados reconhecidos: `pending`, `translated`, `reviewed`, `needs_review` e `orphaned`.

## Regras de preservação

- Não alterar o texto original ao traduzir.
- Preservar exatamente IDs, marcadores de controle, variáveis e quebras de linha até que seu significado seja confirmado.
- Não presumir que `∠` seja uma quebra de linha simples; sua semântica ainda está em investigação.
- Usar `null` para limites desconhecidos; não transformar estimativas em regras.
- Não usar um ID criado pelo toolkit como substituto de um identificador interno do jogo.
- Antes de importação/reconstrução, definir serialização determinística e testes de ida e volta.
- Catálogos reais extraídos do jogo devem permanecer fora do Git se contiverem material proprietário.
