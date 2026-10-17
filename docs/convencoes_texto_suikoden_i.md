# Convenções de texto e símbolos — Suikoden I e II HD Remaster

Este documento registra observações fornecidas durante a inspeção dos dumps e a observação do jogo. O objetivo é orientar a extração, edição, validação e futura reinserção das strings sem modificar conteúdo que já funciona.

## Princípios de preservação

- Tratar os dumps originais como referência.
- Preservar caracteres Unicode, espaços, pontuação, sequências de símbolos e escapes.
- Não normalizar caracteres visualmente semelhantes nem converter caracteres de largura completa para ASCII.
- Não atribuir significado definitivo a um símbolo sem evidência suficiente.
- Quando a função for desconhecida, preservar o elemento exatamente como encontrado.
- Manter regras específicas por jogo; não transferir automaticamente convenções de Suikoden I para Suikoden II ou vice-versa.

## Suikoden I

| Elemento no dump/JSON | Interpretação registrada | Regra para a ferramenta |
|---|---|---|
| `\\"` | Escape usado para que aspas apareçam literalmente como texto visível no jogo. | Preservar a semântica do escape. Não remover nem duplicar barras indiscriminadamente. |
| `ＬＶ３` | Texto literal que aparece visivelmente como “Level 3”, conforme observado. Os caracteres do dump são de largura completa. | Preservar exatamente `ＬＶ３`; não converter para `LV3` nem substituir automaticamente. |
| `★☆` | Sequência de símbolos visíveis. | Preservar a sequência e a ordem. |
| `★★☆☆` | Sequência de símbolos visíveis. | Preservar a sequência e a ordem. |
| `★★★☆☆☆` | Sequência de símbolos visíveis. | Preservar a sequência e a ordem. |
| `\\` | Barra invertida associada a texto visível, conforme a observação fornecida. | Preservar. Não inferir que toda barra invertida isolada tem a mesma função sem examinar o contexto. |
| `▲`, `▼` | Não foram encontrados no texto de Suikoden I examinado. | Não tratá-los como tokens confirmados de Suikoden I. Isso não prova ausência em todos os recursos do jogo. |
| `■` | Significado não confirmado. | Preservar sem alteração. |
| `�` (U+FFFD) | Função não confirmada. | Preservar sem substituição ou remoção automática. |
| `∠` | Indicador de quebra de linha, segundo a observação registrada. Uma janela de diálogo comporta no máximo quatro linhas. | Preservar o marcador e validar quebras de linha conforme o contexto do diálogo. |
| `∨` | Indicador de transição/quebra de janela de diálogo, segundo a observação registrada; deve ocorrer a cada quatro linhas. | Preservar e validar conforme o contexto. Não substituir por `▲` ou `▼`. |
| `♂㈱` | Token combinado usado para o nome do protagonista em Suikoden I. A combinação deve ser considerada integral, não apenas `♂` isolado. | Preservar a sequência exata; verificar ocorrências de `♂` em outros contextos antes de aplicar validação automática. |
| `♂①` | Token relacionado ao nome do castelo em Suikoden I, conforme a observação inicial. | Preservar a sequência exata. Confirmar a associação por jogo ao manter o catálogo de regras. |
| `∨☆` | Marcador especial de transição. Foi sugerido que possa representar uma pausa mais longa, mas isso não foi confirmado de forma independente. | Preservar a sequência exata; não codificar duração ou semântica definitiva sem evidência adicional. |
| `ＬＶ２`, `ＬＶ４` | Texto literal de nível em largura completa, conforme a informação fornecida. | Preservar cada caractere e a largura original. |
| `♂⑩` | Relatado como referência ao protagonista de Suikoden I em diálogos de Suikoden II que recontam eventos ou tratam de dados carregados. | Preservar a sequência; manter a regra específica de Suikoden II e validar em contexto no jogo. |

## Suikoden II

Os itens abaixo são observações preliminares. **A busca posterior nos arquivos disponíveis não encontrou ocorrências de `♂▼n`**. Portanto, as referências a esse padrão não são evidência de que ele esteja presente nos dumps examinados e não devem ser tratadas como tokens existentes até que um exemplo concreto seja localizado.

| Elemento | Estado da evidência | Regra para a ferramenta |
|---|---|---|
| `♂▼0` até `♂▼7` | Não encontrado em nenhum arquivo examinado. A hipótese anterior de que apareceria no início de frases em diálogos de batalha não está confirmada pelos arquivos. | Não adicionar à lista de tokens encontrados nem implementar regra de parsing específica sem evidência. |
| `♂▼1` até `♂▼7` em tutorial de pesca | Não encontrado em nenhum arquivo examinado. A hipótese anterior sobre diálogos de tutorial de pesca também não está confirmada pelos arquivos. | Não registrar como ocorrência real; reavaliar apenas se for fornecido um exemplo verificável. |
| `♂㈱` | Token do nome do protagonista de Suikoden II, conforme a observação fornecida. | Preservar a sequência exata, sem separar ou substituir caracteres. |
| `♂②` | Token do nome do exército em Suikoden II, conforme a observação fornecida. | Preservar a sequência exata. |
| `♂①` | Token do nome do castelo em Suikoden II, conforme a observação fornecida. | Preservar a sequência exata. |
| `◎1`, `◎2`, `◎5` etc. | Relatados como indicadores ordinais/estruturados usados em contextos como escolhas e minijogos. A interpretação exata pode depender do recurso. | Preservar o símbolo e o número. Não substituir por números ordinais localizados sem confirmar como o jogo interpreta esses marcadores. |

### Nota de auditoria

Não documentar um token como presente apenas com base numa hipótese de interpretação ou numa lembrança do contexto. Para adicionar um padrão à lista de ocorrências verificadas, registrar pelo menos o arquivo de origem e a string exata (idealmente também o ID). Ausência nos arquivos examinados significa apenas que a busca não encontrou correspondência nesses arquivos; não prova que o padrão seja impossível em outros recursos do jogo.

## Marcadores adicionais relatados para Suikoden I e II

As interpretações desta seção foram fornecidas durante o trabalho de tradução e ainda devem ser verificadas contra ocorrências concretas e comportamento no jogo. Elas orientam a preservação, não autorizam substituição automática.

| Elemento | Interpretação relatada | Regra para a ferramenta |
|---|---|---|
| `♂㈱` | Nome escolhido para o protagonista. | Tratar a sequência combinada como token indivisível; não substituir `♂` isoladamente. |
| `♂①` | Nome do castelo/quartel-general. | Preservar a sequência exata. |
| `♂②` | Nome do exército, relatado especificamente para Suikoden II. | Preservar a sequência exata e restringir a interpretação ao contexto do jogo correspondente. |
| `♂⑩` | Referência ao herói de Suikoden I em determinados textos de Suikoden II. | Preservar a sequência exata; confirmar o contexto antes de aplicar validação semântica. |
| `∠` | Quebra de linha dentro da mesma janela de diálogo. | Preservar o marcador no dump; qualquer visualização como nova linha deve ser reversível. |
| `∨` | Transição para outra janela/bloco de diálogo. | Preservar; não converter em quebra de linha comum durante exportação/importação. |
| `∨☆` | Marcador de transição com pausa/espera automática relatada. | Preservar sem inferir temporização. |
| `ＬＶ２`, `ＬＶ３`, `ＬＶ４` | Rótulos de nível em caracteres de largura completa. | Não converter para ASCII (`LV2`, `LV3`, `LV4`). |
| `★☆`, `★★☆☆`, `★★★☆☆☆` | Sequências visuais de estrelas. | Preservar símbolos, quantidade e ordem. |

## Cuidado com escapes JSON

Em JSON, uma aspa dupla dentro de uma string precisa ser escapada como `\\"`. Isso pertence à sintaxe de serialização: ao interpretar o JSON, a barra de escape não necessariamente faz parte do texto entregue ao jogo. A ferramenta deve distinguir:

1. **Representação JSON:** os caracteres necessários para que o arquivo seja JSON válido.
2. **Valor da string:** o texto após o parser JSON interpretar os escapes.
3. **Conteúdo do jogo:** a forma efetivamente consumida/exibida pelo jogo após a importação.

Não comparar apenas a aparência bruta do arquivo JSON para decidir se a string final está correta. Validar o valor decodificado e, quando possível, comparar o resultado exportado/reinserido com o conteúdo original.

## Regras recomendadas para implementação

1. **Extração sem alteração:** extrair o campo `text` ou conteúdo correspondente sem normalizar Unicode, traduzir símbolos, remover espaços ou reinterpretar marcadores.
2. **JSON inválido:** se o dump não for JSON válido, registrar o erro e interromper o processamento daquele arquivo. Não corrigir silenciosamente caracteres de controle ou escapes ambíguos.
3. **Round-trip:** testar que ler e serializar o JSON preserva o valor decodificado de cada string. A formatação do arquivo pode mudar, mas o conteúdo da string não deve mudar.
4. **Tokens por jogo:** manter listas separadas para Suikoden I e II, distinguindo tokens confirmados de símbolos com função desconhecida.
5. **Validação contextual:** validar sequências conhecidas sem alterá-las automaticamente. Não exigir que um símbolo tenha apenas uma função em todos os contextos.
6. **Relatório de diferenças:** ao detectar alterações em símbolos, espaços, escapes ou caracteres Unicode, informar o ID e os valores antes/depois. Não aplicar reparos automáticos.
7. **Evidências:** registrar exemplos com arquivo, ID, string original, contexto (batalha, pesca, menu etc.) e captura de tela ou teste no jogo, quando disponíveis.

## Nível de certeza

As interpretações refletem observações fornecidas durante a análise dos dumps e testes visuais. Onde a função está marcada como desconhecida ou preliminar, a ferramenta deve preservar o dado e não inventar uma explicação. Novas regras devem incluir a evidência observada.