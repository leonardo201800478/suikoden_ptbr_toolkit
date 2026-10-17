# Arquitetura e roteiro técnico

## Estado atual

O pacote usa uma estrutura `src/`:

- `src/suikoden_tool/bundle_inspector.py`: inspeção não destrutiva do cabeçalho UnityFS, hash SHA-256 e inventário recursivo.
- `src/suikoden_tool/translation_schema.py`: construtor de uma entrada de tradução com metadados iniciais.
- `src/suikoden_tool/cli.py`: interface de linha de comando (`inspect`, `inventory`, `template`).
- `tests/`: testes automatizados.
- `data/translations_template.json`: modelo vazio para iniciar o trabalho de tradução.

## Fluxo pretendido

```text
Bundles originais (somente leitura)
          |
          v
Inventário + hashes + metadados
          |
          v
Inspeção de assets com ferramenta compatível
          |
          v
Extração de texto e metadados -> JSON versionado
          |
          v
Editor de tradução + validação
          |
          v
Importação/reconstrução em cópia de trabalho
          |
          v
Teste no jogo e relatório de regressões
```

A extração, a edição visual e a reconstrução ainda são etapas futuras, não funcionalidades disponíveis hoje.

## Regras de engenharia

1. **Reversibilidade:** não descartar dados desconhecidos necessários para reconstruir o asset.
2. **Rastreabilidade:** associar cada entrada ao jogo, asset, identificador e origem quando essas informações forem descobertas.
3. **Integridade:** manter o texto original separado da tradução e não modificar o original durante a edição.
4. **Tokens:** representar tokens e variáveis de modo explícito; validar que não sejam removidos ou reordenados sem autorização.
5. **Limites baseados em evidência:** separar limites confirmados pelo jogo de observações visuais e avisos heurísticos.
6. **Versionamento:** versionar o esquema JSON e criar migrações quando houver mudanças incompatíveis.
7. **Testes:** incluir casos válidos, inválidos, truncados, strings vazias, Unicode e dados com tokens.

## Descoberta de formatos

Avaliar AssetRipper, UABEA e UnityDataTools em cópias dos arquivos. Registrar versão da ferramenta, hash do arquivo de entrada, resultado, limitações e se a operação preserva dados. A assinatura UnityFS não basta para determinar a estrutura interna ou o procedimento seguro de reconstrução.

## Critérios para considerar uma etapa concluída

- Há exemplos reproduzíveis e testes automatizados.
- Os dados de entrada não são alterados.
- Os metadados desconhecidos são preservados ou explicitamente documentados.
- Falhas são apresentadas com mensagens úteis.
- O resultado foi comparado com o arquivo original por hash e, quando aplicável, testado no jogo.
