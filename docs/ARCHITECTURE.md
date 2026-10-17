# Arquitetura e roteiro técnico

## Estado atual

O pacote usa a estrutura `src/`:

- `src/suikoden_tool/bundle_inspector.py`: inspeção de cabeçalho UnityFS, SHA-256 e inventário recursivo.
- `src/suikoden_tool/translation_schema.py`: construtor de uma entrada para o esquema inicial de tradução.
- `src/suikoden_tool/cli.py`: CLI com `inspect`, `inventory`, `template` e `text export`.
- `tests/`: testes automatizados, incluindo exportação de catálogos.
- `data/`: modelos iniciais versionáveis.
- `work/`: resultados locais de investigação; não assumir que existem em outro clone e não versionar dumps proprietários.
- `tools/` (opcional e local): ferramentas externas para investigação de assets; ignoradas pelo Git e não necessárias para instalar o pacote.

## Responsabilidades atuais da CLI

| Comando | Entrada | Resultado | Limites conhecidos |
|---|---|---|---|
| `inspect` | Um bundle | Cabeçalho/metadados e hash | Não interpreta todos os objetos internos. |
| `inventory` | Diretório | Inventário recursivo JSON | Não extrai nem classifica texto. |
| `template` | Jogo selecionado | Modelo JSON de tradução | Não representa uma extração real. |
| `text export` | JSON com `textList` | Catálogo traduzível JSON | Não extrai do bundle; reexportação não preserva traduções existentes. |

## Fluxo pretendido

```text
Bundles originais (somente leitura)
          |
          v
Inventário + hashes + metadados
          |
          v
Extração/inspeção de assets com ferramenta compatível
          |
          v
TextAssets/objetos identificados
          |
          v
Exportação para catálogo JSON versionado
          |
          v
Mesclagem segura + validação + tradução/revisão
          |
          v
Importação/reconstrução em cópia de trabalho
          |
          v
Comparação de integridade + teste no jogo
```

Somente a inspeção básica, o inventário, o modelo e a exportação de JSON previamente extraído estão implementados. Extração automatizada, merge seguro, validação avançada, editor e reconstrução ainda são etapas futuras.

## Ferramentas externas

AssetRipper, UABEA e UnityDataTool são ferramentas auxiliares em avaliação. Não são importadas pelo código Python e não devem ser tratadas como dependências obrigatórias. Instale-as separadamente a partir das fontes oficiais. Consulte [Ferramentas externas](EXTERNAL_TOOLS.md).

O `.gitignore` exclui pastas locais dessas ferramentas e extensões binárias comuns. Isso evita novos commits de executáveis, mas não elimina automaticamente objetos grandes que já façam parte do histórico Git. Se um push for rejeitado por arquivos grandes, faça backup e limpe o histórico local não publicado; não tente resolver apenas adicionando regras ao `.gitignore`.

## Regras de engenharia

1. **Reversibilidade:** não descartar dados desconhecidos necessários para reconstruir o asset.
2. **Rastreabilidade:** associar cada entrada ao jogo, asset, identificador e origem quando essas informações forem descobertas.
3. **Integridade:** manter o texto original separado da tradução.
4. **Tokens:** preservar tokens, variáveis, marcadores e quebras de linha até confirmar sua semântica.
5. **Limites baseados em evidência:** separar limites confirmados de observações e avisos heurísticos.
6. **Versionamento:** versionar o esquema JSON e criar migrações para mudanças incompatíveis.
7. **Testes:** incluir casos válidos, inválidos, Unicode, strings vazias, tokens e IDs duplicados.
8. **Dependências externas:** registrar ferramenta, versão, hash de entrada, parâmetros e resultado.
9. **Não destrutivo:** nunca substituir silenciosamente um catálogo com traduções existentes.
10. **Documentação para IA:** atualizar `docs/AI_CONTEXT.md`, `docs/AI_PROMPTS.md` e este documento quando a arquitetura ou os comandos mudarem.

## Descoberta de formatos

A assinatura UnityFS não basta para determinar a estrutura interna ou o procedimento seguro de reconstrução. A descoberta de `text_add_en` está documentada em [Registro de engenharia reversa](REVERSE_ENGINEERING_LOG.md). O marcador `∠` foi observado em entradas de texto, mas seu significado não está confirmado.

## Critérios para considerar uma etapa concluída

- Existem exemplos reproduzíveis e testes automatizados.
- Os dados de entrada não são alterados.
- Metadados desconhecidos são preservados ou explicitamente documentados.
- Falhas apresentam mensagens úteis.
- O resultado é comparado com a entrada por hash quando aplicável.
- Qualquer afirmação sobre compatibilidade/reconstrução é apoiada por teste real.
