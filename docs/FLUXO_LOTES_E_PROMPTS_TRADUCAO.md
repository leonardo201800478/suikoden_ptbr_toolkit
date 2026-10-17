# Fluxo de lotes de tradução — Suikoden I & II HD Remaster

Este documento define como dividir arquivos JSON em lotes, traduzir os lotes em conversas separadas e conferir o resultado por ID. O glossário aprovado em [GLOSSARIO_TRADUCAO_PTBR.md](GLOSSARIO_TRADUCAO_PTBR.md) continua sendo a referência terminológica.

## 1. Formato de entrada

A guia **Lotes de tradução** aceita um JSON que tenha uma propriedade `textList` contendo uma lista de objetos com pelo menos os campos `id` e `text`. Exemplo:

```json
{
  "textList": [
    { "id": 1, "text": "Power?" },
    { "id": 2, "text": "Is it power that we seek?" }
  ]
}
```

O arquivo de origem não é modificado. Os IDs devem ser únicos e cada ID deve ser um número inteiro ou uma string. A ferramenta rejeita estrutura inválida, IDs duplicados ou tipos de ID não aceitos. Não presume que os IDs sejam sequenciais.

## 2. Tamanho dos lotes

- **Padrão recomendado: 100 entradas por lote.**
- A interface permite escolher 50, 100, 150 ou 200, e aceita qualquer inteiro entre 1 e 200.
- Comece com 100. Para textos especialmente longos ou cheios de marcadores, reduza para 50–80. Lotes com textos curtos podem usar 150–200.
- O número de entradas é apenas um limite de quantidade; o tamanho textual também importa. Se o conteúdo ficar grande demais para uma resposta segura, trabalhe em subconjuntos identificados por ID e nunca omita entradas silenciosamente.

## 3. Organização dos arquivos

Ao dividir, selecione como destino a pasta que conterá os lotes. A ferramenta cria uma subpasta própria para lotes, identificada pelo nome integral do arquivo de origem, incluindo a extensão:

```text
<pasta-de-destino>/
└── lotes_traducao/
    ├── text_gsd1_en.json/
    │   ├── lote_001.json
    │   ├── lote_002.json
    │   └── manifest_lotes.json
    └── text_gsd2_en.json/
        ├── lote_001.json
        ├── lote_002.json
        └── manifest_lotes.json
```

Catálogos completos permanecem separados dos arquivos de lote. Não renomeie os diretórios de origem nem misture lotes de arquivos de origem diferentes. Se o diretório de um arquivo já contiver conteúdo, a ferramenta pede confirmação antes de substituir arquivos com nomes coincidentes; faça backup antes de confirmar.

Cada arquivo `lote_NNN.json` conserva as propriedades de nível superior do JSON de origem e substitui somente `textList` pelo subconjunto correspondente. As entradas são copiadas na ordem de origem e os IDs não são renumerados. O manifesto registra o arquivo de origem, tamanho configurado, IDs de cada lote, primeiro/último ID, quantidade e estado inicial.

**Importante:** o manifesto gerado registra o estado inicial como `pending`; a interface atual não atualiza automaticamente esse estado conforme uma conversa de tradução progride.

## 4. Regras obrigatórias de tradução

1. Traduza somente o valor de `text`. Não altere IDs, nomes de propriedades, a estrutura do JSON, nem acrescente/remova entradas.
2. Preserve exatamente todos os marcadores e tokens técnicos, inclusive os que ainda não estejam documentados. Exemplos: `♂㈱`, `♂①`, `♂②`, `♂⑩`, `∠`, `∨`, `∨☆`, `ＬＶ２`, `ＬＶ３`, `ＬＶ４`, `★☆`, `★★☆☆`, `◎1`, `◎2`, `◎5` e o caractere literal `?`.
3. Não converta JSON em outro formato para devolver o lote. Entregue JSON válido com a mesma estrutura.
4. Preserve a ordem das entradas e o tipo/valor de cada ID.
5. Não invente contexto de história. Se uma linha for ambígua, traduza de modo conservador e registre a dúvida separadamente pelo ID.
6. Use o glossário aprovado para os dois jogos. Atualmente: STR → FOR; DEX → DES; PROT → PROT; SPD → VEL; MAG → MAG; LCK → SOR; “Add to party.” → “Adicionar ao grupo.”; “Don't add to party.” → “Não adicionar ao grupo.”
7. Preserve os marcadores de quebra de linha e caixa. `∠` é uma quebra na mesma janela; `∨` inicia a próxima caixa/janela; `∨☆` indica transição com pausa/espera. Não os substitua por quebras de linha JSON nem os remova.
8. Não normalize espaços internos, pontuação, escapes ou caracteres especiais sem necessidade de tradução. O arquivo .txt exportado pelo UABEA é um fluxo separado e não deve ser convertido para JSON para importação no UABEA.

## 5. Prompt principal para traduzir um lote

Copie este prompt no chat que receberá o lote. Anexe o JSON do lote e, quando possível, o glossário do projeto. Este prompt é a referência principal para tradução assistida por IA.

```text
Vamos continuar o projeto de tradução PT-BR de Suikoden I & II HD Remaster.

REFERÊNCIAS OBRIGATÓRIAS
- Consulte e aplique o glossário aprovado:
  https://github.com/leonardo201800478/suikoden_ptbr_toolkit/blob/feature/translation-gui/docs/GLOSSARIO_TRADUCAO_PTBR.md
- Siga o fluxo e as regras do projeto:
  https://github.com/leonardo201800478/suikoden_ptbr_toolkit/blob/feature/translation-gui/docs/FLUXO_LOTES_E_PROMPTS_TRADUCAO.md

Vou enviar um arquivo JSON de um lote. Cada entrada possui um id e um campo text.

OBJETIVO
Produzir uma tradução brasileira natural, consistente e fiel ao sentido, ao tom e à intenção do texto original, adequada a um RPG clássico. Priorize a voz dos personagens, a clareza em jogo e a fidelidade ao autor, sem traduções mecânicas palavra por palavra quando uma adaptação natural preservar melhor o sentido.

REGRAS OBRIGATÓRIAS

1. Altere somente o valor do campo "text". Não modifique IDs, tipos dos IDs, ordem, quantidade de entradas, nomes de propriedades ou qualquer outra parte da estrutura JSON.

2. Preserve literalmente todos os marcadores técnicos, na mesma ordem, quantidade e posição lógica. Incluem, sem se limitar a:
   ♂㈱, ♂①, ♂②, ♂⑩, ∠, ∨, ∨☆, ＬＶ２, ＬＶ３, ＬＶ４, sequências de estrelas, indicadores ◎ como ◎1, ◎2, ◎5, símbolos desconhecidos, pontuação estrutural e o caractere literal ?.
   Não invente marcadores; não remova nem substitua símbolos por parecerem estranhos.

3. Preserve as quebras e os controles de diálogo. Não transforme marcadores técnicos em quebras reais nem remova marcadores para melhorar a leitura. O caractere de controle pertence ao texto e deve permanecer exatamente preservado.

4. Não traduza nem adapte nomes próprios, nomes de personagens, lugares, localidades, itens/equipamentos, nomes de inimigos/monstros ou outros nomes específicos do universo do jogo. Mantenha a grafia original desses nomes. Traduza o texto comum ao redor deles. Se não for possível distinguir com segurança um nome próprio de um termo descritivo, mantenha o original e registre a dúvida separadamente por ID.

5. Consulte o glossário obrigatório e reutilize as formas aprovadas nos dois jogos sempre que o conceito for equivalente. Não crie sinônimos por preferência estilística nem altere uma decisão aprovada sem apontar a ocorrência para revisão.

6. Não use gírias contemporâneas, memes ou expressões passageiras. Prefira português brasileiro natural e atemporal, compatível com o cenário de fantasia e aventura.

7. Adapte ditados, trocadilhos e piadas ao português brasileiro quando a tradução literal perder o efeito original. Preserve a intenção, o humor, a informação e a personalidade da fala; não invente uma piada nova que altere o sentido. Registre separadamente adaptações que possam mudar significativamente a referência original.

8. Quando for possível identificar a voz do personagem pelo próprio texto ou pelo contexto disponível, ajuste vocabulário, ritmo, formalidade e emoção a essa voz. Não atribua personalidade, gênero, relação entre personagens ou contexto narrativo que não esteja sustentado pelas informações disponíveis.

9. Não force formalidade nem linguagem politicamente correta. Preserve o grau de rudeza, humor, ironia, hostilidade, intimidade ou solenidade do original, sem censurar nem intensificar gratuitamente o conteúdo.

10. Busque fidelidade à intenção do autor original, não à ordem literal das palavras. Use frases idiomáticas em português brasileiro, mantendo informações, implicações e tom. Não acrescente explicações narrativas nem elimine elementos do original.

11. Não omita entradas, não resuma e não trunque o lote. Devolva todas as entradas. Se o lote for grande demais para uma resposta segura, trabalhe em partes contíguas identificadas pelos IDs, sem sobreposição, lacunas, duplicações ou alteração da ordem relativa.

12. Em caso de ambiguidade, não invente contexto. Faça a tradução mais conservadora possível e registre a dúvida separadamente por ID. Mantenha nomes e termos incertos na forma original até que haja evidência suficiente.

13. Não acrescente comentários, notas, justificativas ou campos de revisão dentro do JSON. As dúvidas devem aparecer depois do JSON, em uma seção separada intitulada "Ambiguidades para revisão", com ID, trecho original e motivo da dúvida. Se não houver dúvidas relevantes, informe "Nenhuma ambiguidade relevante identificada" fora do JSON.

14. A resposta principal deve ser um JSON válido, sem comentários inseridos no documento. Preserve as propriedades de nível superior existentes no arquivo de entrada. Não use reticências para substituir entradas e não inclua introdução ou explicação antes do JSON.

15. Não declare que realizou validações que não executou. Antes de responder, confira efetivamente, na medida permitida pelo conteúdo disponível:
   - se a quantidade de entradas e a sequência de IDs correspondem ao lote recebido;
   - se os tipos e valores dos IDs foram mantidos;
   - se os marcadores técnicos permaneceram na mesma ordem e quantidade em cada entrada;
   - se nenhuma entrada foi omitida, duplicada ou truncada;
   - se a saída é JSON sintaticamente válido;
   - se nomes próprios foram mantidos e o glossário aplicado;
   - se há textos comuns deixados sem tradução sem motivo aparente.

FORMATO DA RESPOSTA
1. Primeiro, entregue o JSON completo em um único bloco de código json, sem comentários ou notas dentro dele.
2. Depois do bloco JSON, apresente "Ambiguidades para revisão" com os IDs e dúvidas encontradas, ou declare que não foram identificadas ambiguidades relevantes.
3. Resuma as validações somente se elas tiverem sido realmente realizadas. Se alguma checagem não puder ser feita, informe claramente qual ficou pendente.

Comece analisando o arquivo JSON anexado e traduza o lote segundo estas regras.
```

## 6. Prompt de auditoria do lote traduzido

Use após receber a tradução, especialmente se o lote for grande:

```text
Audite o JSON traduzido comparando-o com o JSON original anexado. Não reescreva nem corrija silenciosamente.

Verifique e informe:
- validade sintática dos dois JSONs;
- igualdade da quantidade e sequência de IDs, incluindo tipos;
- IDs duplicados, ausentes, extras ou reordenados;
- entradas sem tradução ou com campo "text" ausente;
- diferenças nos marcadores técnicos, comparando quantidade e ordem de cada marcador por ID;
- alterações fora do campo "text";
- textos aparentemente truncados ou deixados em inglês sem motivo evidente.

Apresente os problemas em uma tabela com ID, tipo do problema e evidência curta. Se tudo passar, declare apenas as verificações efetivamente realizadas. Não trate diferenças legítimas de tradução como erro de estrutura.
```

## 7. Prompt para revisar consistência entre lotes

```text
Revise os lotes traduzidos anexados quanto à consistência terminológica com o glossário PT-BR de Suikoden I & II HD Remaster.

Não altere IDs nem marcadores. Identifique termos equivalentes traduzidos de formas diferentes, variações nas traduções de opções recorrentes, diferenças de capitalização relevantes e possíveis violações do glossário. Informe cada ocorrência com nome do arquivo, ID, forma encontrada e forma recomendada. Não invente equivalências sem contexto suficiente e não substitua automaticamente nomes próprios.
```

## 8. Reconstrução do JSON completo

Depois da tradução:

1. Guarde os arquivos traduzidos separadamente dos lotes originais e do catálogo completo.
2. Audite cada lote contra sua versão original usando o prompt de auditoria.
3. Reúna as entradas usando o ID como chave de correspondência, não apenas o número ou nome do lote.
4. Confira se cada ID de origem aparece exatamente uma vez no conjunto final; entradas ausentes, extras ou duplicadas devem bloquear a reconstrução.
5. Reinsira os textos traduzidos nos objetos de origem, alterando somente `text`, e preserve a ordem e as demais propriedades originais.
6. Valide o JSON final e compare a estrutura antes de usar o arquivo em qualquer ferramenta de modificação.
7. Não trate a geração de lotes como uma funcionalidade de mesclagem automática: a guia atual divide arquivos, mas não reúne automaticamente os lotes traduzidos nem atualiza seus estados.

## 9. Unificar os lotes traduzidos pela interface

A guia **Lotes de tradução** inclui o botão **Unificar lotes traduzidos…**. Use-o depois de traduzir os arquivos:

1. Clique no botão e selecione o **JSON original completo**, não um dos lotes.
2. Selecione a pasta que contém diretamente os arquivos `lote_001.json`, `lote_002.json` etc. Os arquivos devem conter as traduções no campo `text`.
3. A ferramenta confere os lotes pelo ID e bloqueia a operação se houver IDs ausentes, extras, duplicados, campos inválidos ou JSON malformado.
4. Se a validação passar, escolha o nome e o destino do JSON completo traduzido.
5. O resultado conserva a ordem e as propriedades do arquivo original e substitui somente o campo `text` correspondente a cada ID.

O arquivo original e os lotes não são modificados. Recomenda-se salvar o resultado com um nome distinto, por exemplo `text_gsd1_en_ptbr.json`.

**Atenção:** selecione apenas os lotes pertencentes ao mesmo arquivo original. Não coloque lotes de origens diferentes na mesma pasta. A ferramenta não usa apenas o número do lote para associar textos: a associação é feita pelo ID de cada entrada. Se a tradução de um lote estiver incompleta, a unificação é bloqueada para evitar produzir um catálogo parcial.

## 10. Checklist por lote

- [ ] O lote foi traduzido integralmente.
- [ ] IDs e ordem conferidos com o original.
- [ ] Marcadores preservados.
- [ ] Glossário aplicado.
- [ ] JSON validado sintaticamente.
- [ ] Auditoria estrutural concluída.
- [ ] Dúvidas semânticas registradas por ID.
- [ ] Arquivo traduzido salvo com referência clara ao lote e à origem.
