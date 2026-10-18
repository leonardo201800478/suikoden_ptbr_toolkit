# Ferramentas externas (Windows)

## Objetivo

AssetRipper, UABEA e UnityDataTools são ferramentas auxiliares para investigar assets Unity. São ferramentas independentes, não fazem parte do código Python do toolkit e ainda estão em avaliação quanto à compatibilidade com os bundles de Suikoden I & II HD Remaster.

## Instalação local

Baixe cada ferramenta apenas de sua fonte oficial ou de uma publicação mantida pelo projeto original:

- [AssetRipper — Releases](https://github.com/AssetRipper/AssetRipper/releases)
- [UABEA — Releases](https://github.com/nesrak1/UABEA/releases)
- [UnityDataTools — Releases](https://github.com/Unity-Technologies/UnityDataTools/releases)

Extraia cada distribuição na pasta local do repositório, se desejar usar a estrutura abaixo:

```text
tools/
├── AssetRipper/
├── UABEA/
└── UnityDataTools/
```

Os nomes de pastas são convenções locais; os executáveis podem variar entre versões. Registre a versão usada nos relatórios de teste. Não presuma que uma ferramenta é compatível apenas porque consegue abrir o arquivo.

## Integração com o toolkit

O comando `suikoden-tool text extract` chama a CLI do UnityDataTool sem shell, usando argumentos separados. O executável é resolvido nesta ordem:

1. caminho passado em `--tool`;
2. variável de ambiente `UNITY_DATA_TOOL`;
3. executável `UnityDataTool.exe`/`UnityDataTool` disponível no `PATH`;
4. `tools/UnityDataTools/UnityDataTool.exe` relativo ao diretório de trabalho.

A extração usa `serialized-file objectlist --format json` para localizar objetos `TextAsset` e `dump --objectid ... --stdout` para ler `m_Name` e `m_Script`. Só grava a saída se `m_Script` for JSON com uma lista `textList`; quando houver vários recursos compatíveis, é obrigatório indicar `--asset-name`. Para bundles com mais de um SerializedFile, informe `--entry`.

Exemplo:

```powershell
suikoden-tool text extract --bundle "C:\\jogo\\arquivo.bundle" --output work\\text.json --asset-name text_add_en
```

A integração ainda precisa de validação local contra a versão 2.4.0 e os bundles reais do projeto. O formato textual do dump pode variar entre versões; se a extração falhar, não edite nem substitua o bundle original. A extração não implementa reinserção.

Referência da CLI: [documentação oficial do UnityDataTool](https://github.com/Unity-Technologies/UnityDataTools/blob/main/Documentation/command-dump.md).

## Versionamento e arquivos grandes

As pastas locais acima são ignoradas pelo `.gitignore`. Isso é intencional:

- não armazenar executáveis, DLLs ou distribuições de terceiros no histórico Git;
- não depender dessas ferramentas para instalar ou executar a CLI do toolkit;
- não distribuir bundles, dumps ou outros dados proprietários do jogo;
- evitar limites de tamanho de arquivo do GitHub e manter o clone leve.

O `.gitignore` impede novas inclusões, mas **não remove arquivos que já estejam em commits anteriores**. Se o GitHub rejeitar um push por arquivos grandes, não basta alterar o `.gitignore` nem criar outro commit: é necessário remover os arquivos do índice e, quando já estiverem em commits locais, limpar o histórico não publicado. Faça backup da branch antes de reescrever histórico.

Para conferir se uma ferramenta está sendo ignorada:

```powershell
git check-ignore tools/AssetRipper/AssetRipper.GUI.Free.exe
git check-ignore tools/UnityDataTools/UnityDataTool.exe
```

Para verificar se algum caminho continua rastreado:

```powershell
git ls-files tools/AssetRipper tools/UABEA tools/UnityDataTools
```

Se o segundo comando listar arquivos, eles ainda estão no índice do Git. Não use comandos destrutivos de limpeza sem conferir antes `git status` e o histórico local.

## Registro de experimentos

Para cada teste, documente:

- ferramenta e versão;
- hash SHA-256 e caminho do arquivo de entrada;
- comando/opções utilizados;
- resultado e mensagens de erro;
- arquivos gerados e hash de saída, quando aplicável;
- se os metadados e a estrutura foram preservados;
- se o resultado foi testado no jogo.

Trabalhe sempre com cópias dos arquivos do jogo. Não sobrescreva os originais. A inspeção bem-sucedida não comprova que a reconstrução seja segura ou sem perdas.
