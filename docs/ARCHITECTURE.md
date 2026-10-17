# Arquitetura e roteiro técnico

## Estado atual

O pacote usa a estrutura `src/`:

- `src/suikoden_tool/bundle_inspector.py`: inspeção de cabeçalho UnityFS, SHA-256 e inventário recursivo.
- `src/suikoden_tool/translation_schema.py`: construtor de uma entrada para o esquema inicial de tradução.
- `src/suikoden_tool/cli.py`: CLI com inspeção, inventário, catálogo, validação, estatísticas e operações CSV em lote.
- `src/suikoden_tool/text_batch.py`: exportação/importação CSV com validação integral antes da gravação.
- `src/suikoden_tool/unity_text_extractor.py`: integração opcional com UnityDataTool para localizar e extrair `m_Script` de um `TextAsset` com JSON `textList`.
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
| `text extract` | Bundle + UnityDataTool + seleção opcional de entrada/asset | JSON extraído de um `TextAsset` | Depende do formato do dump; não altera o bundle e recusa sobrescrever saída sem `--force`. |
| `text export` | JSON com `textList` + saída opcional existente | Cria/mescla catálogo JSON | Preserva traduções compatíveis; marca origem alterada e IDs órfãos. |
| `text validate` | Catálogo + fonte opcional | Relatório JSON de erros/avisos | Não modifica arquivos. |
| `text stats` | Catálogo JSON | Contagem por status e percentual concluído | Não modifica arquivos. |\n| `text batch-export` | Catálogo JSON | CSV UTF-8 com BOM para Excel | Exporta até o limite configurado; por padrão inclui `pending` e `needs_review`. |\n| `text batch-import` | CSV + catálogo JSON | Atualiza traduções correspondentes | Valida IDs e texto original; células vazias não apagam traduções; `needs_review` é preservado. |

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

A inspeção básica, o inventário, o modelo, a extração experimental de TextAssets via UnityDataTool, a exportação/mesclagem de catálogos, a validação estrutural, avisos conservadores sobre diferenças na quantidade de `∠` e quebras de linha, as estatísticas, o fluxo CSV em lote e o editor gráfico estão implementados. A extração automatizada ainda precisa de validação local com a versão externa e bundles reais; interpretação semântica dos marcadores e reconstrução permanecem etapas futuras.

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
9. **Não destrutivo:** mesclar traduções compatíveis; preservar entradas removidas como `orphaned`; marcar mudanças de origem como `needs_review`; abortar se o catálogo existente estiver inválido.
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
