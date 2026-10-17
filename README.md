# Suikoden I & II HD Remaster — Toolkit PT-BR

Projeto inicial em Python para analisar recursos da versão Windows e desenvolver o fluxo de localização.

## Estado atual
- Inspeção não destrutiva de cabeçalho UnityFS e SHA-256.
- Inventário recursivo de `.bundle` em JSON.
- Esquema JSON com campos para texto, tokens, ponteiros e limites.
- Teste unitário do cabeçalho.

**Ainda não extrai textos nem reconstrói bundles.** Precisamos identificar os tipos de assets e a estrutura dos objetos serializados. Limites e ponteiros serão preenchidos com evidências reais, não estimativas.

## Configuração Windows / VS Code
Recomendação inicial: Python 3.12 ou 3.13.
```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Comandos
```powershell
suikoden-tool inspect "C:\\caminho\\arquivo.bundle"
suikoden-tool inventory "C:\\caminho\\StandaloneWindows64" -o output\\bundle_inventory.json
suikoden-tool template --game suikoden_i -o data\\translations_template.json
pytest
ruff check .
```

## Ferramentas para avaliar
- **AssetRipper** para extração em lote e análise de assets Unity suportados.
- **UABEA** para inspeção/edição direcionada de assets e bundles.
- **UnityDataTools** para dump e análise de conteúdo serializado.

Links: https://github.com/AssetRipper/AssetRipper · https://github.com/nesrak1/UABEA · https://github.com/Unity-Technologies/UnityDataTools

Os arquivos fornecidos apresentam assinatura `UnityFS` e estão em `StreamingAssets/aa/StandaloneWindows64`, estrutura típica de Unity Addressables. Isso identifica o contêiner, não ainda o recurso que contém cada texto.

## Guia de tradução PT-BR (Suikoden I e II)

A nomenclatura aprovada deve ser compartilhada pelos dois jogos. Consulte **[Guia de tradução e glossário PT-BR](docs/GLOSSARIO_TRADUCAO_PTBR.md)** antes de traduzir ou revisar textos. A forma aprovada de um termo deve ser reutilizada sempre que o mesmo conceito aparecer; não criar variantes sem registrar e revisar a decisão. O guia também define os marcadores que precisam ser preservados.

## Carregar arquivos JSON já preparados para tradução

Na interface gráfica, use **Carregar JSON preparado** e selecione um ou mais arquivos `.json` que contenham
`textList` com objetos `id` e `text`. Exemplos de nomes incluem
`text_gsd1_en-....json`, `text_gsd2_en-....json` e `text_add_en-....json`.

O editor cria catálogos independentes em `output/catalogos/<nome>.catalog.json`. Se o catálogo já existir,
as traduções existentes são mescladas por ID: traduções não são descartadas, textos de origem alterados
ficam marcados para revisão e IDs que desapareceram são mantidos como órfãos. Se for selecionado apenas um
arquivo e a carga terminar sem erros, o catálogo resultante é aberto automaticamente.

O carregamento não traduz nem reescreve os JSONs de origem. Os campos `text` são copiados para `original`
sem substituir marcadores como `∠`, `∨`, `♂㈱`, `◎1` ou o caractere `?`.
Os JSONs preparados não são arquivos para importar diretamente no UABEA; são fontes para o catálogo de edição.

## Divisão de arquivos em lotes

A guia **Lotes de tradução** divide JSONs `textList` em arquivos menores, preservando os IDs originais. O padrão é 100 entradas por lote, configurável entre 1 e 200. Os lotes ficam em `lotes_traducao/<nome-integral-do-arquivo-de-origem>/`, separados dos catálogos completos. Consulte [Fluxo de lotes e prompts de tradução](docs/FLUXO_LOTES_E_PROMPTS_TRADUCAO.md) para os procedimentos, prompts de tradução e auditoria por ID. A interface também oferece o botão **Unificar lotes traduzidos…**, que confere os IDs, bloqueia lotes incompletos ou duplicados e reconstrói o JSON na ordem original substituindo apenas `text`.

## Limite de caracteres nas caixas de diálogo

A interface valida o texto digitado antes de salvar. **Cada linha exibida deve ter no máximo 66 caracteres**; se alguma linha ultrapassar o limite, o salvamento é interrompido e a ferramenta informa o número da linha e a contagem encontrada.

Regras de contagem implementadas:
- `∠` indica quebra de linha e `∨` indica mudança de caixa de diálogo; esses marcadores não entram na contagem.
- Os marcadores de nome `♂㈱`, `♂①`, `♂②` e `♂⑩` reservam **10 caracteres cada**, pois serão substituídos dinamicamente pelo nome correspondente.
- O padrão `/"texto"/` é contado como o conteúdo exibido, incluindo as aspas: `"texto"`.
- Outros caracteres e marcadores são contados literalmente, um caractere Unicode por posição, até que seu comportamento no jogo seja confirmado.

A contagem é uma proteção conservadora baseada nas regras conhecidas, não uma medição automática da largura visual da fonte. Novos tokens que tenham comportamento especial devem ser documentados e acrescentados explicitamente ao contador. A validação não altera o texto original; ela apenas impede salvar uma tradução que exceda o limite calculado.

## Fluxo fiel de TextAsset com UABEA

O fluxo de referência para testar exportação/importação é o UABEA:

1. **FILE** → carregar o bundle para a memória (não usar *Load File*).
2. **INFO** → confirmar **Version Select** apenas com **OK**.
3. Selecionar o objeto **TextAsset** → **Plugin → Export** para gerar o `.txt`.
4. Para importar, repetir a abertura e seleção do mesmo TextAsset; escolher **Plugin → Import**,
   selecionar o `.txt` com o mesmo nome e salvar o bundle modificado.

O módulo `suikoden_tool.uabea_textasset_workflow` trata o `.txt` como bytes opacos: não
decodifica, não converte para JSON e não normaliza quebras de linha nem caracteres de controle.
Pode preparar uma cópia com o mesmo nome para importação e comparar SHA-256/bytes entre arquivos.
Ele **não automatiza a interface do UABEA nem grava bundles**.

```python
from pathlib import Path
from suikoden_tool.uabea_textasset_workflow import (
    compare_uabea_textassets,
    prepare_uabea_import,
)

result = prepare_uabea_import(
    Path(r"C:\\traducao\\text_gsd1_en.txt"),
    Path(r"C:\\traducao\\pronto_para_importar"),
)
print(result)

# Em teste de round-trip sem edição, o arquivo reexportado deve ser idêntico.
print(compare_uabea_textassets(
    Path(r"C:\\traducao\\text_gsd1_en.txt"),
    Path(r"C:\\traducao\\reexportado.txt"),
))
```

O conversor JSON existente é auxiliar para análise/edição, **não** é o arquivo a ser entregue
ao comando **Plugin → Import** do UABEA. Teste primeiro um round-trip sem edição e depois
experimente com textos traduzidos.

## Próximas etapas
1. Inventariar os bundles originais do jogo e registrar hashes.
2. Identificar `MonoBehaviour`, `TextAsset`, tabelas e fontes via ferramentas externas.
3. Mapear formato de strings, IDs, tokens e referências.
4. Implementar extração/importação JSON preservando dados técnicos.
5. Criar validador de tokens, comprimento e quebra de linha.
6. Criar editor visual de diálogos e menus.
7. Implementar reconstrução/patch e testes no jogo.

Trabalhe em cópias e mantenha os arquivos originais preservados.

## Extração automática de textos (UnityDataTool)

O comando `extract-texts` processa os quatro bundles conhecidos, considera somente entradas `SerializedFile`, identifica objetos `TextAsset` e procura pares JSON `id`/`text`. A extração é somente leitura: não reconstrói nem sobrescreve os bundles originais.

```powershell
suikoden-tool extract-texts "G:\\SteamLibrary\\steamapps\\common\\Suikoden I and II HD Remaster\\Suikoden I and II HD Remaster_Data\\StreamingAssets\\aa\\StandaloneWindows64" --unity-data-tool ".\\tools\\UnityDataTools\\UnityDataTool.exe" -o output\\catalogo_textos.json --csv output\\catalogo_textos.csv
```

O JSON é o catálogo principal; o CSV UTF-8 com BOM facilita a revisão no Excel. Cada entrada conserva o ID de origem, o bundle, o caminho do SerializedFile, o ID do objeto e o texto original. O marcador `?` observado nos dumps é preservado literalmente e listado em `control_tokens`; **não é convertido automaticamente em quebra de linha**, pois seu significado ainda precisa ser confirmado. Os diagnósticos do catálogo registram contagens por bundle e eventuais erros.

Testes automatizados:

```powershell
python -m pytest -q
```

A validação executada no ambiente de desenvolvimento cobre a extração de pares `id`/`text`, deduplicação, preservação dos marcadores e exportação CSV. A execução integrada contra os bundles reais ainda deve ser feita no Windows onde o `UnityDataTool.exe` está disponível.
