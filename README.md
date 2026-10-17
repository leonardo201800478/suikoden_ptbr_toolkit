# Suikoden I & II HD Remaster — Toolkit PT-BR

Ferramentas em Python para investigar os recursos da versão Windows de **Suikoden I & II HD Remaster** e construir um fluxo de localização para português brasileiro (PT-BR).

> **Estado do projeto: fase inicial de engenharia reversa.** O toolkit atualmente inspeciona metadados básicos de bundles UnityFS, gera inventários e define um esquema inicial para entradas de tradução. Ainda **não extrai textos do jogo nem reconstrói/modifica bundles**.

- **Idioma da documentação:** português brasileiro.
- **Plataforma-alvo inicial:** Windows.
- **Tecnologia:** Python, CLI, JSON e testes automatizados.
- **Prioridade:** preservar os dados técnicos originais e validar cada hipótese com arquivos reais.

## Funcionalidades atuais

- Inspeção não destrutiva do cabeçalho de arquivos `.bundle` com assinatura UnityFS.
- Cálculo de SHA-256 para identificar e comparar arquivos.
- Inventário recursivo de bundles, exportável em JSON.
- Geração de modelo JSON para organizar futuras traduções.
- Esquema inicial com campos para jogo, asset, IDs, texto original, tradução, tokens de controle, limites e estado de revisão.
- Testes automatizados para a inspeção de cabeçalho.

## Requisitos

- Windows 10/11 (ambiente inicial de desenvolvimento).
- Python **3.11 ou superior**; recomenda-se Python 3.12 ou 3.13.
- Git e Visual Studio Code são recomendados.

## Instalação em ambiente de desenvolvimento

No PowerShell, na pasta clonada do repositório:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Se o Python 3.12 não estiver instalado, substitua `-3.12` por uma versão disponível que seja 3.11 ou superior.

## Uso

### Inspecionar um bundle

```powershell
suikoden-tool inspect "C:\caminho\arquivo.bundle"
```

Para salvar o resultado em JSON:

```powershell
suikoden-tool inspect "C:\caminho\arquivo.bundle" -o output\bundle_info.json
```

### Inventariar bundles de uma pasta

Aponte para a pasta que contém os bundles do jogo:

```powershell
suikoden-tool inventory "C:\caminho\StandaloneWindows64" -o output\bundle_inventory.json
```

### Criar um modelo de tradução

```powershell
suikoden-tool template --game suikoden_i -o data\translations_template.json
suikoden-tool template --game suikoden_ii -o output\suikoden_ii_template.json
```

### Executar testes e verificações

```powershell
pytest
ruff check .
```

O Ruff é usado para análise estática; enquanto o estilo do código estiver sendo padronizado, eventuais avisos devem ser corrigidos antes de tornar a verificação obrigatória no CI.

## Ferramentas externas em avaliação

Estas ferramentas são candidatas para inspecionar assets Unity. Nenhuma delas é ainda uma dependência obrigatória do toolkit:

- [AssetRipper](https://github.com/AssetRipper/AssetRipper) — extração e análise de assets Unity suportados.
- [UABEA](https://github.com/nesrak1/UABEA) — inspeção e edição direcionada de assets Unity.
- [UnityDataTools](https://github.com/Unity-Technologies/UnityDataTools) — ferramentas de análise de dados Unity.

**As distribuições executáveis não são armazenadas no GitHub deste projeto.** Baixe-as das fontes oficiais e, se desejar, mantenha-as localmente em `tools/AssetRipper/`, `tools/UABEA/` e `tools/UnityDataTools/`. Essas pastas são ignoradas pelo Git para evitar binários grandes e dependências de terceiros no histórico. Consulte [configuração das ferramentas externas](docs/EXTERNAL_TOOLS.md).

O cabeçalho `UnityFS` identifica o contêiner, mas **não revela por si só qual objeto contém o texto**, nem garante que um bundle possa ser reconstruído sem perda. A compatibilidade precisa ser testada com a versão real dos arquivos.

## Plano de desenvolvimento

1. **Inventário reproduzível:** registrar caminhos relativos, tamanhos, hashes e metadados dos bundles originais.
2. **Descoberta de assets:** identificar tipos de objetos, tabelas de texto, fontes, IDs e referências.
3. **Extração controlada:** exportar texto sem perder tokens, IDs, ordenação ou metadados necessários.
4. **Formato de tradução:** definir um JSON versionado e documentar campos obrigatórios e opcionais.
5. **Validação:** verificar tokens, variáveis dinâmicas, quebras de linha e limites confirmados por testes.
6. **Editor:** criar uma interface para pesquisar, traduzir, filtrar e revisar diálogos e menus.
7. **Importação/reconstrução:** implementar apenas após identificar o formato e comprovar a preservação dos dados.
8. **Testes no jogo:** validar cópias de trabalho e manter os originais intactos.

Mais detalhes: [arquitetura e etapas](docs/ARCHITECTURE.md), [formato de tradução](docs/TRANSLATION_FORMAT.md) e [ferramentas externas](docs/EXTERNAL_TOOLS.md).

## Princípios de segurança e qualidade

- Nunca sobrescrever os bundles originais; trabalhar com cópias.
- Não inventar limites de caracteres, IDs ou tokens: registrar a origem de cada regra.
- Preservar tokens de controle, variáveis, ponteiros e quebras de linha até que seu significado seja confirmado.
- Usar hashes para documentar os arquivos testados.
- Manter testes para parsers, exportação, validação e reconstrução.
- Não incluir no repositório bundles, executáveis, dumps integrais ou outros arquivos proprietários do jogo.
- Não tratar o projeto como afiliado ou endossado pela Konami.

## Como contribuir

Consulte [CONTRIBUTING.md](CONTRIBUTING.md). Relatos de falhas e propostas podem ser enviados pela aba Issues do GitHub.

## Licença e direitos sobre o jogo

O **código-fonte original deste toolkit** é distribuído sob a licença MIT, conforme o arquivo [LICENSE](LICENSE). Essa licença não concede direitos sobre Suikoden, seus personagens, marcas, textos originais, imagens, áudio ou arquivos do jogo. Esses materiais pertencem aos respectivos titulares e não devem ser enviados a este repositório.

O projeto é uma iniciativa independente, sem afiliação ou endosso oficial. Veja também [SECURITY.md](SECURITY.md).
