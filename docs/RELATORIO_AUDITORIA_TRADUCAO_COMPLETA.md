# Relatório de auditoria --- catálogo PT-BR de Suikoden I & II HD Remaster

**Data:** 17/10/2026\
**Arquivo auditado:** `text_add_en_ptbr_auditado.json`

## Resultado estrutural

-   JSON lido e validado sintaticamente.
-   Entradas traduzidas: **1443**.
-   IDs únicos: **1443**.
-   IDs da origem cobertos: **1443**.
-   Faixa de IDs: **1--1448**.
-   Lacunas existentes na origem: **97, 126, 129, 155 e 201**. Não são
    entradas perdidas: a origem tem 1.443 IDs e não exige sequência
    contínua.
-   Textos vazios preservados: **312, 314 e 642**.
-   Diferenças entre catálogo completo e 15 lotes traduzidos: **0**.
-   Divergências detectadas na sequência de marcadores reconhecidos ou
    nas quebras de linha: **0**.
-   Divergências de espaços iniciais/finais: **0**.

## Correções feitas nesta auditoria

1.  Corrigida a quantidade/posição de `∠` nos IDs **957, 959, 962, 965,
    967, 969, 970, 973, 974, 975, 976, 979, 986, 987 e 988**.
2.  Corrigida a posição relativa entre marcador e placeholder dinâmico
    nos IDs **1109 e 1151**.
3.  Padronizados rótulos de `LCK` para **SOR** nos IDs **929 e 1045**,
    conforme o glossário do projeto.
4.  Padronizados alcances compactos para **C/M/L** nos IDs **788--790**
    e no rótulo descritivo do ID **1047**.
5.  Ajustada a redação dos efeitos de estado nos IDs **1233**
    (`Remove o estado Veneno`) e **1235** (`Remove o estado Balão`);
    "Balão" ainda requer confirmação terminológica.
6.  Restaurado o espaço final significativo do ID **290**.
7.  Atualizados os lotes afetados para que cada lote corresponda ao
    catálogo completo auditado.
8.  Padronizadas **85 ocorrências** de consistência entre textos de
    origem idênticos: rótulos de estrelas (IDs 706--755), títulos
    repetidos, opções de interface e descrições de efeitos de
    batalha/cura.
9.  Uniformizados `Event Viewer`, `Message Speed`, `The Last Battle`,
    `The Battle at Pannu Yakuta`, descrições de dano (`2x/3x/1,5x`) e
    mensagens repetidas, sem alterar IDs ou marcadores.

## O que foi efetivamente verificado

-   Sintaxe JSON.
-   Correspondência dos IDs de origem com o catálogo completo e ausência
    de IDs duplicados.
-   Igualdade entre os textos do catálogo completo e os 15 lotes
    traduzidos.
-   Sequência/quantidade dos marcadores reconhecidos (`∠`, `∨`, `∨☆`,
    `♂㈱`, `♂①`, `♂②`, `♂⑩`, placeholders `〓n`, tokens `ＬＶ２/３/４`,
    sequências de estrelas, indicadores `◎n` e `?`).
-   Quantidade de quebras de linha e padrão de espaços iniciais/finais.
-   Preservação dos três textos vazios.

A validação não prova a semântica de todos os símbolos desconhecidos nem
a renderização visual dentro do jogo.

## Pontos semânticos que ainda precisam de revisão humana/contextual

-   **Alta --- ID 762, `Bag` → `Bolsa`:** confirmar se a interface
    significa bolsa, inventário ou recipiente.
-   **Alta --- IDs 815, 832 e 865:** `Blinking Rune` →
    `Runa do Teletransporte`, `Gadget Rune` → `Runa do Dispositivo` e
    `Skunk Rune` → `Runa do Cangambá`; confirmar a terminologia no
    contexto do jogo.
-   **Alta --- ID 1235, `Cures Balloon` → `Remove o estado Balão`:**
    confirmar o nome PT-BR do estado no jogo.
-   **Média --- `Dragon Knights` → `Cavaleiros Dragões`:** forma
    consistente nos lotes, mas a construção em português precisa de
    aprovação.
-   **Média --- ID 1147, `Log` → `Registro`:** pode significar registro
    ou histórico, dependendo da função da interface.
-   **Média --- faixas musicais e subtítulos:** há títulos traduzidos e
    títulos em inglês; padronizar por mapeamento exato, sem tradução
    parcial inconsistente.

## Conclusão

O catálogo completo e os 15 lotes estão estruturalmente alinhados; as
verificações automáticas de JSON, IDs, marcadores reconhecidos e espaços
passaram. **Isso não equivale a aprovação linguística absoluta nem à
validação visual no jogo.** Os itens semânticos acima devem ser
resolvidos e registrados no glossário antes de serem tratados como
nomenclatura oficial.
