# Contexto canônico do projeto para assistentes de IA

Leia este documento no início de qualquer sessão de IA que vá alterar, analisar ou documentar o toolkit. Ele resume o estado conhecido; os arquivos do código e os testes atuais prevalecem se houver divergência.

## Missão

Construir em Python uma ferramenta prática, eficiente e segura para investigar, extrair, organizar, traduzir, validar e, futuramente, reinserir textos de Suikoden I & II HD Remaster para PT-BR.

## Ambiente e tecnologias

- Plataforma de desenvolvimento: Windows e PowerShell.
- Python: >= 3.11.
- Pacote: `suikoden-ptbr-toolkit`.
- CLI: `suikoden-tool`.
- Código-fonte em `src/suikoden_tool/`.
- Testes em `tests/`.
- Ferramentas Unity opcionais em `tools/`, ignoradas pelo Git.
- Dados de investigação local em `work/`; não presumir que existam em outro clone.

## Funcionalidades existentes

- `inspect`: inspeção não destrutiva de cabeçalho UnityFS e SHA-256.
- `inventory`: inventário recursivo de bundles.
- `template`: criação de um JSON inicial de tradução.
- `text export`: cria ou mescla um catálogo de JSON já extraído com `textList`; preserva traduções compatíveis, marca mudanças de origem para revisão e preserva IDs removidos como `orphaned`.
- `text validate`: verifica estrutura, IDs duplicados, campos, status e traduções pendentes; com `--source`, compara IDs e textos contra uma extração atual.
- `text stats`: conta entradas por status e percentual concluído sem alterar o catálogo.

Exemplo de entrada para `text export`:

```json
{
  "textList": [
    {"id": 1, "text": "Power?"},
    {"id": 2, "text": "Is it power that we seek?"}
  ]
}
```

Os comandos de texto não extraem diretamente objetos de dentro dos bundles; operam sobre JSON previamente extraído. A mesclagem segura de catálogos está implementada. Quando a origem muda, a tradução existente é mantida, `previous_original` é preservado, `source_changed` fica verdadeiro e o status passa a `needs_review`. IDs removidos da extração são mantidos como `orphaned`.

## Evidência de engenharia reversa

- Um bundle local de `Backup_Translation`, nome `700bf7ec8ded4a20613b92988e3f8142.bundle`, foi analisado.
- UnityDataTool 2.4.0 listou um objeto `AssetBundle` e um `TextAsset` chamado `text_add_en`.
- O objeto contém JSON `textList` com 1.443 entradas, cada uma com `id` e `text`.
- A checagem encontrou zero IDs duplicados/ausentes e zero textos ausentes; três textos vazios, 27 textos contendo `∠` e uma entrada com quebra de linha.
- O marcador `∠` precisa ser preservado. Seu significado e regras de serialização ainda não foram confirmados.
- Algumas entradas são narrativas, menus e descrições. Não está provado que a tabela inclua todos os diálogos da história nem todos os recursos dos dois jogos.
- Os arquivos e dumps mencionados acima são locais; não devem ser presumidos presentes no repositório.

Detalhes, hashes e limitações: `docs/REVERSE_ENGINEERING_LOG.md`.

## Regras obrigatórias para mudanças

1. Inspecionar o código e os testes atuais antes de propor uma alteração.
2. Não tratar planos ou exemplos de CLI como funcionalidade existente sem conferir `--help` e implementação.
3. Preservar o original byte a byte quando possível; nunca sobrescrever arquivos originais do jogo.
4. Manter original e tradução em campos separados.
5. Preservar IDs, ordenação, tokens, marcadores, variáveis e quebras de linha até que as regras sejam confirmadas.
6. Não inventar limites de caracteres, semântica de tokens, mapeamento de IDs ou estrutura de reconstrução.
7. Preferir funções pequenas, tipadas e testáveis; manter dependências de runtime em zero quando possível.
8. Adicionar testes para caminho válido, dados inválidos, Unicode, strings vazias, marcadores, IDs duplicados, preservação de traduções, mudanças de origem e IDs órfãos.
9. Não incluir bundles, executáveis de ferramentas, dumps integrais ou textos proprietários do jogo no Git.
10. Documentar hipóteses, comandos exatos, versão da ferramenta, hash de entrada e resultados.
11. Se um comando for destrutivo ou puder substituir traduções, alertar claramente e implementar proteção/backup antes de recomendá-lo.
12. Não declarar testes aprovados sem executá-los ou sem citar um resultado fornecido pelo usuário.

## Linha de base conhecida

Na branch `feature/text-catalog-export`, o usuário executou com sucesso:
- `suikoden-tool text export --input work/bundle_analysis/text_add_en.json --output work/bundle_analysis/catalogo_pt_br.json --target-language pt-BR`
- `python -m pytest -q` → 4 testes aprovados.
- `suikoden-tool --help` e `suikoden-tool text export --help`.

A branch ainda é de desenvolvimento e não deve ser confundida com `main`.

## Como responder

- Usar português brasileiro, ser direto e técnico.
- Separar fatos comprovados, inferências e próximos passos.
- Fornecer comandos PowerShell que possam ser copiados, especificando a pasta de execução.
- Pedir apenas logs relevantes quando houver erro; evitar repetir etapas já concluídas.
- Para mudanças grandes, indicar arquivos afetados, riscos, testes e forma de validar.
