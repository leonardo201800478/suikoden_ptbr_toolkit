# Suikoden I & II HD Remaster — Toolkit PT-BR

Toolkit em Python para investigar recursos da versão Windows de **Suikoden I & II HD Remaster** e construir um fluxo reproduzível de localização para português brasileiro.

> **Estado:** engenharia reversa inicial. O toolkit inspeciona cabeçalhos UnityFS, inventaria bundles, cria modelos de tradução e exporta catálogos a partir de JSON extraído de objetos Unity `TextAsset`. Ainda não extrai sozinho os objetos internos dos bundles e não reconstrói nem injeta textos em bundles.

## Objetivos e princípios

- Priorizar uma ferramenta prática, eficiente e reproduzível para tradução PT-BR.
- Manter texto original separado da tradução.
- Preservar IDs, marcadores de controle, quebras de linha e Unicode.
- Trabalhar com cópias e manter os arquivos originais do jogo intactos.
- Registrar evidências e separar fatos confirmados de hipóteses.
- Não versionar executáveis de terceiros, bundles do jogo ou dumps integrais.

## Funcionalidades atuais

- `suikoden-tool inspect`: inspeciona o cabeçalho de um bundle UnityFS e calcula SHA-256.
- `suikoden-tool inventory`: inventaria recursivamente bundles de uma pasta.
- `suikoden-tool template`: gera um modelo inicial de tradução.
- `suikoden-tool text export`: converte um JSON com a estrutura `{"textList":[{"id":1,"text":"..."}]}` em um catálogo traduzível.
- `suikoden-tool text validate` e `text stats`: validam e acompanham o progresso do catálogo.
- `suikoden-tool text batch-export` e `text batch-import`: exportam/importam lotes CSV compatíveis com Excel, validando IDs e textos originais.
- `suikoden-tool gui` / `suikoden-gui`: editor gráfico escuro com busca, filtros de status, salvamento seguro e sugestão de tradução por IA opcional.
- Testes automatizados para exportação, preservação de texto, validação e fluxo CSV.

O comando `text export` **não extrai o TextAsset diretamente do bundle**. A extração do objeto foi feita durante a investigação com UnityDataTool; o comando recebe o JSON já extraído. Se o catálogo de saída já existir, a exportação mescla os dados com segurança.

## Estado comprovado da investigação

Um dos bundles de `Backup_Translation`, `700bf7ec8ded4a20613b92988e3f8142.bundle`, foi inspecionado localmente. A ferramenta UnityDataTool 2.4.0 listou um objeto `AssetBundle` e um `TextAsset` chamado `text_add_en`. O dump do TextAsset contém um JSON com `textList`, que foi convertido em catálogo com **1.443 entradas**. Consulte [o registro de investigação](docs/REVERSE_ENGINEERING_LOG.md).

Isso comprova a existência dessa tabela de textos, mas **não comprova que ela contenha todos os diálogos da história** nem que o formato possa ser reinserido sem análise adicional.

## Requisitos

- Windows 10/11 no ambiente de desenvolvimento inicial.
- Python 3.11 ou superior.
- Git recomendado.
- Ferramentas externas opcionais para investigação de assets Unity.

## Instalação

No PowerShell, na raiz do repositório:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use uma versão instalada do Python 3.11 ou superior se Python 3.12 não estiver disponível.

## Uso da CLI

### Inspecionar um bundle

```powershell
suikoden-tool inspect "C:\caminho\arquivo.bundle"
suikoden-tool inspect "C:\caminho\arquivo.bundle" -o output\bundle_info.json
```

### Inventariar bundles

```powershell
suikoden-tool inventory "C:\caminho\StandaloneWindows64" -o output\bundle_inventory.json
```

### Gerar modelo de tradução

```powershell
suikoden-tool template --game suikoden_i -o data\suikoden_i_template.json
suikoden-tool template --game suikoden_ii -o data\suikoden_ii_template.json
```

### Exportar catálogo a partir de JSON extraído

```powershell
suikoden-tool text export `
    --input work\bundle_analysis\text_add_en.json `
    --output work\bundle_analysis\catalogo_pt_br.json `
    --target-language pt-BR
```

O exportador valida a estrutura `textList`, exige `id` e `text`, rejeita IDs duplicados e preserva o texto original. Na atualização, entradas com ID e texto original compatíveis mantêm tradução e status; entradas com texto de origem alterado mantêm a tradução anterior, guardam `previous_original` e recebem `needs_review`; IDs que sumiram da fonte são preservados como `orphaned`. Catálogos existentes inválidos ou de outro idioma/recurso são recusados sem alteração.

### Validar e acompanhar o catálogo

```powershell
suikoden-tool text validate --input work\\bundle_analysis\\catalogo_pt_br.json
suikoden-tool text validate --input work\\bundle_analysis\\catalogo_pt_br.json --source work\\bundle_analysis\\text_add_en.json
suikoden-tool text stats --input work\\bundle_analysis\\catalogo_pt_br.json
```

`validate` retorna erros estruturais e avisos para traduções pendentes, mudanças de texto e divergências com a fonte. `stats` conta `pending`, `translated`, `reviewed`, `needs_review` e `orphaned` sem alterar o arquivo.

### Editor gráfico de tradução\n\nAbra o catálogo de trabalho em uma interface com lista à esquerda e editor à direita:\n\n```powershell\nsuikoden-tool gui --catalog work\\bundle_analysis\\catalogo_pt_br.json\n# ou, sem catálogo inicial:\nsuikoden-gui\n```\n\nA interface permite pesquisar por ID, original ou tradução, filtrar por status, editar manualmente, avançar para pendências e acompanhar as estatísticas. `Salvar tradução` marca a entrada como `translated`; `Salvar revisada` marca como `reviewed`. Entradas `needs_review` só podem ser confirmadas pelo salvamento explícito como revisadas. O catálogo é validado antes de cada gravação e as alterações são gravadas atomicamente, preservando campos extras e o texto original.\n\n**Assistência de IA opcional:** o botão `Sugerir com IA` envia somente o texto original selecionado e o contexto opcional para a API OpenAI. A sugestão aparece no editor, mas nunca é gravada automaticamente; revise e salve manualmente. Configure `OPENAI_API_KEY` no ambiente antes de usar o recurso. Opcionalmente, defina `OPENAI_MODEL` (padrão `gpt-4o-mini`). A chave não é armazenada no catálogo nem na interface. A chamada à API pode gerar custos conforme sua conta. A edição manual funciona sem chave e sem dependências Python extras.\n\n### Traduzir em lotes com CSV/Excel

```powershell
# Exporta até 100 entradas pendentes e que precisam de revisão
suikoden-tool text batch-export --input work\\bundle_analysis\\catalogo_pt_br.json --output work\\bundle_analysis\\lote_001.csv --limit 100

# Para exportar somente entradas pending
suikoden-tool text batch-export --input work\\bundle_analysis\\catalogo_pt_br.json --output work\\bundle_analysis\\lote_001.csv --limit 100 --pending-only

# Depois de preencher a coluna translation no Excel, importe o lote
suikoden-tool text batch-import --catalog work\\bundle_analysis\\catalogo_pt_br.json --input work\\bundle_analysis\\lote_001.csv
```

O CSV usa UTF-8 com BOM para facilitar a abertura no Excel. Não edite as colunas `id`, `id_type` e `original`. A importação rejeita IDs duplicados, IDs desconhecidos e originais divergentes antes de gravar qualquer alteração. Traduções vazias são ignoradas; o texto original nunca é substituído. Entradas `needs_review` permanecem nesse estado até revisão explícita. Faça uma cópia de segurança do catálogo antes de importar lotes.

### Testes e ajuda

```powershell
python -m pytest -q
ruff check .
suikoden-tool --help
suikoden-tool text export --help
suikoden-tool text validate --help
suikoden-tool text stats --help
```

Execute esses comandos na branch atual após atualizar o clone local. Não considere os novos testes aprovados até executar a suíte.

Antes da implementação do fluxo CSV, o usuário confirmou 16 testes aprovados e `ruff check .` sem erros. O novo fluxo CSV acrescenta testes que ainda precisam ser executados no clone local; não considere a ampliação validada até obter um novo resultado.

## Ferramentas externas

AssetRipper, UABEA e UnityDataTool são auxiliares locais, não dependências obrigatórias do pacote Python. Obtenha-as nas fontes oficiais e mantenha-as em pastas ignoradas pelo Git. Consulte [docs/EXTERNAL_TOOLS.md](docs/EXTERNAL_TOOLS.md).

## Documentação para pessoas e assistentes de IA

- [Arquitetura e roteiro](docs/ARCHITECTURE.md)
- [Formato dos catálogos](docs/TRANSLATION_FORMAT.md)
- [Ferramentas externas](docs/EXTERNAL_TOOLS.md)
- [Registro de engenharia reversa](docs/REVERSE_ENGINEERING_LOG.md)
- [Contexto do projeto para IA](docs/AI_CONTEXT.md)
- [Prompts reutilizáveis para IA](docs/AI_PROMPTS.md)

## Próximas prioridades

1. Documentar o comportamento atual e estabelecer uma linha de base reproduzível.
2. Ampliar validação de tokens, variáveis e consistência linguística com regras confirmadas.
3. Adicionar testes de integração da CLI e validar fluxos com catálogos reais em cópias locais.
4. Automatizar a extração de TextAssets usando uma ferramenta externa detectada/configurada, mantendo o parser desacoplado.
5. Inventariar outros bundles e localizar recursos de diálogo dos dois jogos.
6. Só então projetar importação/reconstrução, com testes de ida e volta e cópias de segurança.

## Licença e direitos

O código-fonte do toolkit é distribuído sob MIT conforme `LICENSE`. Isso não concede direitos sobre os jogos, textos, imagens, áudio ou arquivos de Suikoden. O projeto é independente e não é afiliado nem endossado pela Konami.
