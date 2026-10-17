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
- Testes automatizados para exportação, preservação de texto e validação de entradas.

O comando `text export` **não extrai o TextAsset diretamente do bundle**. A extração do objeto foi feita durante a investigação com UnityDataTool; o comando recebe o JSON já extraído.

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

O exportador valida a estrutura `textList`, exige `id` e `text`, rejeita IDs duplicados e preserva o texto original. Cada execução gera traduções vazias e status `pending`; portanto, **não execute sobre um catálogo já traduzido sem fazer backup**, pois ainda não há mesclagem/atualização segura.

### Testes e ajuda

```powershell
python -m pytest -q
suikoden-tool --help
suikoden-tool text export --help
```

A validação registrada na branch `feature/text-catalog-export` resultou em 4 testes aprovados no ambiente de desenvolvimento do projeto. Execute novamente os testes após qualquer alteração.

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
2. Implementar atualização/mesclagem segura de catálogos sem perder traduções.
3. Criar validação e estatísticas de tradução.
4. Automatizar a extração de TextAssets usando uma ferramenta externa detectada/configurada, mantendo o parser desacoplado.
5. Inventariar outros bundles e localizar recursos de diálogo dos dois jogos.
6. Só então projetar importação/reconstrução, com testes de ida e volta e cópias de segurança.

## Licença e direitos

O código-fonte do toolkit é distribuído sob MIT conforme `LICENSE`. Isso não concede direitos sobre os jogos, textos, imagens, áudio ou arquivos de Suikoden. O projeto é independente e não é afiliado nem endossado pela Konami.
