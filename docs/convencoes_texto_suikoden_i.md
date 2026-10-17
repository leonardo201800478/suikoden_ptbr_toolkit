# Convenções de texto e símbolos — Suikoden I HD Remaster

Este documento registra observações confirmadas durante a inspeção do dump de texto de **Suikoden I**. O objetivo é orientar a extração, edição, validação e futura reinserção das strings sem modificar conteúdo que já funciona no jogo.

## Princípio de preservação

- Tratar o texto extraído como fonte de referência.
- Preservar caracteres Unicode, espaços, pontuação, sequências de símbolos e escapes.
- Não normalizar caracteres visualmente semelhantes nem converter caracteres de largura completa para ASCII.
- Não atribuir significado a um símbolo sem evidência suficiente.
- Quando o significado de um elemento for desconhecido, preservá-lo exatamente como encontrado.
- Não aplicar automaticamente as convenções de Suikoden I a Suikoden II, nem o contrário.

## Elementos observados

| Elemento no dump/JSON | Interpretação registrada | Regra para a ferramenta |
|---|---|---|
| `\\"` | Escape usado para que aspas apareçam literalmente como texto visível no jogo. | Preservar a semântica do escape. Não remover nem duplicar barras indiscriminadamente. |
| `ＬＶ３` | Texto literal que aparece visivelmente como “Level 3” no jogo, conforme observado. Os caracteres do dump são de largura completa. | Preservar exatamente `ＬＶ３`; não converter para `LV3` nem substituir por uma tradução automática. |
| `★☆` | Sequência de símbolos visíveis. | Preservar a sequência e a ordem. |
| `★★☆☆` | Sequência de símbolos visíveis. | Preservar a sequência e a ordem. |
| `★★★☆☆☆` | Sequência de símbolos visíveis. | Preservar a sequência e a ordem. |
| `\\` | Barra invertida associada a texto visível, conforme a observação fornecida. | Preservar. Não inferir que toda barra invertida isolada tem a mesma função sem examinar o contexto e a representação JSON. |
| `▲`, `▼` | Não foram encontrados no texto de Suikoden I examinado. | Não tratá-los como tokens confirmados de Suikoden I. A ausência nessa amostra não prova que nunca apareçam em outros recursos. |
| `■` | Significado não confirmado. | Preservar sem alteração. |
| `�` (U+FFFD) | Função não confirmada. | Preservar sem substituição ou remoção automática. |
| `∠` | Indicador de quebra de linha, segundo a observação registrada. Uma janela de diálogo comporta no máximo quatro linhas. | Preservar o marcador e validar as quebras de linha com base no contexto do diálogo. |
| `∨` | Indicador de transição/quebra de janela de diálogo, segundo a observação registrada; deve ocorrer a cada quatro linhas. | Preservar e validar conforme o contexto. Não substituir por `▲` ou `▼`. |
| `♂㈱` | Token combinado usado para o nome do protagonista em Suikoden I. A combinação deve ser considerada integral, não apenas `♂` isolado. | Preservar a sequência exata `♂㈱`; não separar, reordenar ou substituir seus caracteres. Verificar ocorrências de `♂` em outros contextos antes de aplicar validação automática. |
| `♂①` | Token relacionado ao nome do castelo em Suikoden I. | Preservar a sequência exata `♂①`. |
| `∨☆` | Marcador especial de transição. Foi sugerido que possa representar uma pausa mais longa, mas essa interpretação não foi confirmada de forma independente. | Preservar a sequência exata e não codificar uma duração ou semântica definitiva sem evidência adicional. |

## Cuidado com escapes JSON

Em JSON, uma aspa dupla dentro de uma string precisa ser escapada como `\\"`. Isso é parte da sintaxe de serialização: ao interpretar o JSON, a barra de escape não necessariamente faz parte do texto entregue ao jogo. Por isso, a ferramenta deve distinguir:

1. **Representação JSON:** os caracteres necessários para que o arquivo seja JSON válido.
2. **Valor da string:** o texto que resulta após o parser JSON interpretar os escapes.
3. **Conteúdo do jogo:** a forma efetivamente consumida/exibida pelo jogo após a importação.

Não se deve comparar apenas a aparência bruta do arquivo JSON para decidir se a string final está correta. A validação deve comparar o valor decodificado e, quando possível, o resultado exportado/reinserido com o conteúdo original.

## Regras recomendadas para implementação

1. **Extração sem alteração:** extrair o campo `text` ou o conteúdo correspondente sem normalizar Unicode, traduzir símbolos, remover espaços ou reinterpretar marcadores.
2. **JSON inválido:** se o dump não for JSON válido, registrar o erro e interromper o processamento daquele arquivo. Não corrigir silenciosamente caracteres de controle ou escapes ambíguos.
3. **Round-trip:** testar que ler e serializar o JSON preserva o valor decodificado de cada string. A representação textual pode mudar por formatação, mas o conteúdo da string não deve mudar.
4. **Tokens protegidos:** manter uma lista por jogo de tokens confirmados, sem presumir que todos os símbolos especiais sejam tokens de controle.
5. **Validação contextual:** validar sequências como `♂㈱`, `♂①`, `∠`, `∨` e `∨☆` sem alterar automaticamente as strings.
6. **Relatório de diferenças:** ao detectar alterações em símbolos, espaços, escapes ou caracteres Unicode, informar o ID do texto e os valores antes/depois. Não aplicar reparos automáticos.
7. **Regras separadas por jogo:** manter as observações de Suikoden I separadas das de Suikoden II até que cada convenção seja verificada no respectivo dump.

## Nível de certeza

As interpretações deste documento refletem observações fornecidas durante a análise do dump e testes visuais no jogo. Quando o significado está marcado como não confirmado, a ferramenta deve preservar o dado, não inventar uma interpretação. Novas regras devem incluir a evidência observada (ID do texto, trecho original e, se disponível, captura de tela ou teste no jogo).

