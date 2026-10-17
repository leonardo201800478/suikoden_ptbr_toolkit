# Formato JSON de tradução (rascunho)

**Status:** esquema inicial, ainda não é um contrato estável. Os campos podem evoluir conforme os assets reais forem identificados. O campo `schema_version` deve ser incrementado quando houver alterações incompatíveis.

## Estrutura do documento

```json
{
  "schema_version": 1,
  "project": "Suikoden I & II HD Remaster PT-BR",
  "game": "suikoden_i",
  "entries": []
}
```

Valores esperados para `game`: `suikoden_i` ou `suikoden_ii`.

## Campos de uma entrada

| Campo | Propósito |
|---|---|
| `id` | Identificador estável definido pelo toolkit; não presumir que seja o ID interno do jogo. |
| `game` | Jogo ao qual a entrada pertence, quando conhecido. |
| `asset_name`, `asset_path` | Nome e caminho do asset de origem. |
| `object_path_id`, `text_id` | Identificadores técnicos descobertos na extração. |
| `source_text` | Texto original, preservado sem tradução. |
| `translation_pt_br` | Tradução brasileira. |
| `context` | Contexto narrativo ou funcional para o tradutor. |
| `text_type` | Categoria como diálogo, menu ou descrição, após classificação. |
| `max_characters`, `max_lines`, `max_width_px` | Limites conhecidos; usar `null` se não confirmados. |
| `control_tokens` | Tokens de controle identificados e sua ordem, quando aplicável. |
| `pointer_metadata` | Metadados de referências/ponteiros, se descobertos. |
| `status` | Estado de tradução/revisão. |
| `notes` | Observações e evidências. |

## Recomendações

- Use `null` para limites desconhecidos; não converta estimativas em regras confirmadas.
- Não remova tags, tokens, variáveis dinâmicas ou quebras de linha do texto original.
- Registre o significado dos tokens somente quando houver evidência.
- Não use `id` gerado pelo toolkit como substituto de um ID interno do jogo.
- Guarde exemplos sintéticos nos testes; não versionar dumps de texto proprietários.
- Antes de uma exportação/importação real, definir serialização determinística e testes de ida e volta.
