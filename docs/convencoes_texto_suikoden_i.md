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

## Suikoden II

Os itens abaixo são observações preliminares. Os símbolos aparecem em contextos específicos, mas a sua função interna ainda não foi identificada. **Não os traduzir, remover ou reinterpretar automaticamente.**

| Elemento no dump/JSON | Contexto observado / hipótese | Regra para a ferramenta |
|---|---|---|
| `♂▼0`, `♂▼1`, `♂▼2` … até `♂▼7` | Aparecem no início de frases em diálogos de batalha. A função é desconhecida. | Preservar o token completo, incluindo o número. Tratar a lista de 0 a 7 como observação, não como significado decodificado. |
| `♂▼1` … até `♂▼7` | Também aparecem em diálogos do tutorial de pesca. A função exata não está confirmada. | Preservar a sequência integral e o número; não assumir que a função é igual à dos diálogos de batalha apenas por compartilhar o prefixo. |
| `♂㈱` | Token do nome do protagonista de Suikoden II. | Preservar a sequência exata, sem separar ou substituir caracteres. |
| `♂②` | Token do nome do exército em Suikoden II. | Preservar a sequência exata. |
| `♂①` | Token do nome do castelo em Suikoden II. | Preservar a sequência exata. |
| `◎2`, `◎1` etc. | Indicadores ordinais: primeiro, segundo e assim por diante, conforme a observação fornecida. | Preservar o símbolo e o número. Não substituir por números ordinais localizados sem confirmar como o jogo interpreta esses marcadores. |

### Nota sobre `♂▼n`

O prefixo `♂▼` acompanhado de um algarismo foi observado em pelo menos dois contextos: falas de batalha e tutorial de pesca. Como a função não é conhecida, não se deve concluir que sejam códigos de personagem, animação, voz, velocidade, seleção de linha ou qualquer outra coisa sem evidência. Para investigar, registrar exemplos concretos com ID, texto anterior/posterior e captura de tela do jogo quando possível.

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
7. **Evidências:** registrar exemplos com ID, string original, contexto (batalha, pesca, menu etc.) e captura de tela ou teste no jogo, quando disponíveis.

## Nível de certeza

As interpretações refletem observações fornecidas durante a análise dos dumps e testes visuais. Onde a função está marcada como desconhecida ou preliminar, a ferramenta deve preservar o dado e não inventar uma explicação. Novas regras devem incluir a evidência observada.