# Registro de engenharia reversa

Este documento registra observações reproduzíveis da investigação local. Atualize-o quando novos resultados forem obtidos. Não confunda observação com hipótese.

## Ambiente observado

- Jogo: Suikoden I & II HD Remaster para Windows.
- Pasta de dados observada: `Suikoden I and II HD Remaster_Data`.
- Diretório observado de bundles: `StreamingAssets\aa\StandaloneWindows64`.
- Ferramenta usada na extração do objeto registrado abaixo: UnityDataTool 2.4.0.
- Os caminhos completos do jogo são específicos da máquina e não devem ser codificados no toolkit.

## Bundle de teste

Arquivo sob `Backup_Translation`:

- Nome: `700bf7ec8ded4a20613b92988e3f8142.bundle`
- Tamanho: 28.478 bytes.
- SHA-256: `dfcd2baaadabbd9d352eae756b522773c0f6806e1c916165099db630ac8419a2`
- UnityFS: assinatura identificada.
- Format version: 8.
- Unity version informada: `5.x.x`.
- Revision: `0.0.0`.
- Declared size: corresponde ao tamanho do arquivo observado.
- Flags: 579.

Esses valores descrevem o arquivo específico examinado; não devem ser generalizados a todos os bundles.

## Objetos listados

Comando usado:

```powershell
.\tools\UnityDataTools\UnityDataTool.exe archive list $TestBundle
.\tools\UnityDataTools\UnityDataTool.exe serialized-file objectlist $TestBundle
```

O resultado listou o contêiner `CAB-6ef7fc2f739cb602e2a2a6bb1dd699fc`, com um objeto `AssetBundle` (ClassID 142) e um `TextAsset` (ClassID 49). O TextAsset tinha ID `5394828719103633905`, nome `text_add_en` e tamanho de dados informado de 77.304 bytes.

Dump local gerado em `work/bundle_analysis/CAB-6ef7fc2f739cb602e2a2a6bb1dd699fc.txt`. Esse dump não é necessário para instalar o toolkit e não deve ser versionado.

## Conteúdo JSON observado

O campo `m_Script` do TextAsset continha JSON com raiz `textList`. A lista foi extraída para `work/bundle_analysis/text_add_en.json` e contém 1.443 entradas, cada uma com `id` e `text`.

Resultados do diagnóstico local:

- IDs ausentes: 0.
- IDs duplicados: 0.
- Textos ausentes: 0.
- Textos vazios: 3.
- Entradas com o marcador literal `∠`: 27.
- Entradas com quebra de linha LF ou CR: 1.

Exemplos observados incluem frases narrativas, mensagens de menu, descrições de itens e mensagens do sistema. Isso demonstra que a tabela tem usos variados. Não comprova que contenha todos os diálogos de Suikoden I ou II.

O caractere `∠` foi preservado na exportação. Seu significado exato, se é marcador de quebra de linha, controle de layout ou outro separador, precisa ser validado em contexto no jogo. Não o remover nem substituí-lo automaticamente.

## Catálogo traduzível

Foi criado localmente `work/bundle_analysis/catalogo_pt_br.json` com o comando:

```powershell
suikoden-tool text export `
    --input work/bundle_analysis/text_add_en.json `
    --output work/bundle_analysis/catalogo_pt_br.json `
    --target-language pt-BR
```

Resultado observado pelo usuário:

- 1.443 entradas exportadas.
- Textos originais preservados na comparação com a fonte.
- Campos de saída: `id`, `original`, `translation`, `status`.
- Valores iniciais de tradução vazios e status `pending`.

**Estado atual do toolkit:** `text export` implementa mesclagem segura: preserva tradução/status quando ID e original coincidem, marca texto de origem alterado como `needs_review` e mantém IDs removidos como `orphaned`. A extração automatizada via `text extract` é experimental e ainda precisa ser validada localmente com UnityDataTool 2.4.0 e bundles reais. Faça backup antes de alterações importantes.

## Hashes de outros bundles examinados

| Nome | Tamanho (bytes) | SHA-256 |
|---|---:|---|
| `03cf0288ba3ecaca0776d7fadf1f0bb6.bundle` | 193.557 | `8ae73a8bff7dff65ce1ba8f164276542e5af85f6a1a51e0a702a2d5a0074db21` |
| `0573e2f60d0cda7892d60f38dfd7282c.bundle` | 680.918 | `560b8b2c883e3dae824ef9d23891e4ad7527ed55681f051cbbf35b2dd378d0ab` |
| `49d65af6f8fea7a9e8008c6b2c688fc3.bundle` | 1.410.565 | `e5827394bd44fd83d87a53ecee65f6e34f06272e6efa46d8cbf3082b3b5af23d` |
| `700bf7ec8ded4a20613b92988e3f8142.bundle` | 28.478 | `dfcd2baaadabbd9d352eae756b522773c0f6806e1c916165099db630ac8419a2` |

Os quatro foram relatados como UnityFS format version 8, Unity version `5.x.x`, revision `0.0.0`, flags 579, com tamanho declarado correspondente ao observado. O objeto `text_add_en` foi identificado especificamente no bundle de 28.478 bytes; não presumir que os outros três contenham o mesmo tipo de texto.

## Perguntas em aberto

1. Que bundles contêm diálogos principais, textos de batalha, nomes, menus e créditos de cada jogo?
2. O esquema `textList` aparece em outros recursos/idiomas?
3. Qual é o significado exato dos marcadores `∠` e outros caracteres especiais?
4. Como o jogo associa IDs aos textos em tempo de execução?
5. Quais são as restrições de encoding, tamanho, fonte e layout?
6. É possível reconstruir o asset sem alterar metadados, alinhamento, compressão ou referências?
7. Como fazer round-trip de extração e reinserção e provar que dados não editados permanecem intactos?

## Critério para novas entradas neste registro

Cada experimento novo deve registrar: data, arquivo e SHA-256, ferramenta/versão, comando, resultado, artefatos de saída, limitações e se houve teste no jogo. Evite copiar dumps integrais ou texto proprietário para este arquivo.
