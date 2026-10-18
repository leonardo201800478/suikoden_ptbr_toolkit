# Guia de tradução PT-BR — Suikoden I & II HD Remaster

**Status:** convenção inicial aprovada para uso compartilhado nos dois jogos.  
**Escopo:** textos de interface, atributos, menus e demais ocorrências equivalentes em Suikoden I e Suikoden II.  
**Regra principal:** quando um termo deste guia voltar a aparecer em qualquer um dos jogos, reutilize a forma aprovada abaixo. Não crie uma variante apenas porque a ocorrência está em outro jogo, arquivo ou contexto técnico. Se o contexto exigir outra interpretação, registre a ocorrência para revisão em vez de alterar silenciosamente o padrão.

## 1. Nomenclatura aprovada

### Atributos e estatísticas

| Termo de origem | Tradução PT-BR aprovada | Significado de referência | Regra |
|---|---|---|---|
| `STR` | **FOR** | Força | Usar sempre FOR em rótulos compactos de atributos. |
| `DEX` | **DES** | Destreza | Usar sempre DES em rótulos compactos de atributos. |
| `PROT` | **PROT** | Proteção | Manter PROT; não alternar com DEF ou DEFESA nesses rótulos. |
| `SPD` | **VEL** | Velocidade | Usar sempre VEL em rótulos compactos de atributos. |
| `MAG` | **MAG** | Magia | Manter MAG em rótulos compactos de atributos. |
| `LCK` | **SOR** | Sorte | Usar sempre SOR em rótulos compactos de atributos. |

A sequência padronizada para a linha de atributos é:

`FOR DES PROT VEL MAG SOR`

Não expandir esses rótulos quando o espaço da interface exigir abreviações. Em frases corridas ou descrições, usar os nomes completos em português quando isso for natural e compatível com o espaço disponível.

### Opções de entrada/saída de personagem

| Texto de origem | Tradução PT-BR aprovada |
|---|---|
| `Add to party.` | **Adicionar ao grupo.** |
| `Don't add to party.` | **Não adicionar ao grupo.** |

Usar essas formas nas ocorrências equivalentes dos dois jogos. Manter o ponto final quando ele existir na origem, salvo se a revisão do conjunto demonstrar que a interface usa consistentemente outra pontuação.

## 2. Regra de consistência entre os jogos

1. Este guia é compartilhado por **Suikoden I e Suikoden II**.
2. Ao traduzir uma ocorrência, procurar primeiro o termo de origem e a tradução aprovada neste guia.
3. Reutilizar a tradução aprovada em menus, telas de atributos, diálogos e arquivos diferentes quando a função semântica for a mesma.
4. Não alternar sinônimos por preferência estilística. Exemplo: não trocar **FOR** por **FRC**, **VEL** por **SPD**, **PROT** por **DEF** ou **SOR** por **SRT**.
5. Se uma ocorrência tiver sentido realmente diferente, não for equivalente ou não couber na interface, marcar para revisão e registrar o contexto. Não alterar a nomenclatura global com base em uma ocorrência isolada.
6. Ao aprovar um novo termo, atualizar este arquivo antes de aplicá-lo em lote. A documentação é a referência canônica para tradutores humanos e sugestões de IA.

## 3. Preservação de marcadores e estrutura

A consistência terminológica nunca autoriza modificar a estrutura técnica do texto. Preservar exatamente os marcadores e sua posição, a menos que exista uma regra documentada específica para a operação em questão.

| Marcador / padrão | Tratamento |
|---|---|
| `♂㈱` | Marcador de nome do protagonista; não traduzir nem remover. |
| `♂①` | Marcador de nome do castelo/quartel-general; não traduzir nem remover. |
| `♂②` | Marcador de nome do exército em Suikoden II; não traduzir nem remover. |
| `♂⑩` | Referência ao herói de Suikoden I em algumas ocorrências de Suikoden II; não traduzir nem remover. |
| `∠` | Marcador de quebra de linha na mesma janela; preservar. |
| `∨` | Marcador de próxima caixa/janela de diálogo; preservar. |
| `∨☆` | Transição com pausa/espera; preservar integralmente. |
| `ＬＶ２`, `ＬＶ３`, `ＬＶ４` | Texto literal com caracteres fullwidth; preservar como está, salvo decisão de tradução documentada. |
| `★☆`, `★★☆☆`, `★★★☆☆☆` | Sequências de estrelas; preservar a quantidade e a ordem. |
| `◎1`, `◎2`, `◎5` etc. | Indicadores estruturados de escolhas/minijogos; preservar. |
| `?` | Pode ser caractere literal; não converter em placeholder, quebra de linha ou token sem evidência. |

Também preservar espaços significativos, escapes, BOM, finais de linha CR/LF, aspas, pontuação e símbolos desconhecidos. Não inventar marcadores, como `♂▼n`, nem remover caracteres apenas por parecerem estranhos.

## 4. Limite de texto em caixas

A ferramenta de tradução aplica a regra técnica atual de **até 66 caracteres por linha**. Ao revisar uma tradução:

- manter a divisão indicada por `∠`;
- considerar que os marcadores dinâmicos de nome podem ocupar espaço na tela;
- não remover nem mover marcadores para tentar reduzir a contagem;
- reformular a frase traduzida quando a linha exceder o limite;
- confirmar no jogo a legibilidade visual, pois a contagem de caracteres não equivale à largura exata da fonte.

As regras de contagem implementadas pela ferramenta estão documentadas no README do projeto. Este guia define terminologia e preservação; não substitui a validação técnica da ferramenta.

## 5. Exemplo aplicado

Origem:

```text
STR DEX PROT SPD MAG LCK Add to party.∠
Don't add to party.
```

Tradução padronizada:

```text
FOR DES PROT VEL MAG SOR Adicionar ao grupo.∠
Não adicionar ao grupo.
```

O marcador `∠` permanece no mesmo ponto lógico. A sequência de atributos usa exclusivamente as abreviações aprovadas neste documento.

## 6. Termos novos e revisão

Termos que ainda não constam na tabela **não estão automaticamente aprovados**. Para incluir um termo:

1. registrar o original e a tradução proposta;
2. registrar o contexto e o jogo/arquivo em que foi encontrado;
3. verificar se já existe equivalente no outro jogo;
4. avaliar espaço, clareza e consistência com as convenções existentes;
5. após a aprovação, adicionar a entrada a este guia e só então reutilizá-la globalmente.

Não inferir traduções oficiais a partir de abreviações ambíguas. Quando houver dúvida, manter a ocorrência marcada para revisão.

## 7. Instrução obrigatória para tradução assistida por IA

Ao traduzir ou revisar qualquer texto de Suikoden I ou Suikoden II:

- consultar este guia antes de propor a tradução;
- aplicar as formas aprovadas exatamente como estão escritas;
- reutilizar a mesma nomenclatura nos dois jogos;
- preservar marcadores, símbolos, espaços e estrutura técnica;
- não inventar novas abreviações nem alternar sinônimos;
- sinalizar termos desconhecidos ou contextos ambíguos em vez de decidir sem evidência;
- ao identificar uma nova decisão terminológica aprovada, propor a atualização deste documento.

**Referência canônica:** `docs/GLOSSARIO_TRADUCAO_PTBR.md`.
