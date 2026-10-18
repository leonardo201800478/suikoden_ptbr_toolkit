# Contexto canônico do projeto --- Suikoden I & II HD Remaster PT-BR

**Versão revisada:** 17/10/2026. Este documento consolida o contexto do
toolkit e as decisões terminológicas já aplicadas aos 15 lotes
traduzidos. Em caso de divergência, o código e os testes atuais
prevalecem para o comportamento do toolkit; o glossário aprovado
prevalece para a terminologia.

## Missão

Construir em Python uma ferramenta prática, eficiente e segura para
investigar, extrair, organizar, traduzir, validar e, futuramente,
reinserir textos de Suikoden I & II HD Remaster para português
brasileiro.

## Ambiente e tecnologias

-   Windows e PowerShell; Python \>= 3.11.
-   Pacote `suikoden-ptbr-toolkit`; CLI `suikoden-tool`.
-   Código-fonte em `src/suikoden_tool/`; testes em `tests/`.
-   Ferramentas Unity opcionais em `tools/`, ignoradas pelo Git.
-   Dados locais de investigação em `work/`; não presumir que existam em
    outro clone.

## Funcionalidades conhecidas

-   `inspect`: inspeção não destrutiva de cabeçalho UnityFS e SHA-256.
-   `inventory`: inventário recursivo de bundles.
-   `template`: criação de JSON inicial de tradução.
-   `text extract`: integração experimental com UnityDataTool; localiza
    `TextAsset`, lê `m_Script` e grava JSON com `textList`. Requer
    `--asset-name` quando há múltiplos recursos compatíveis e não
    sobrescreve saída sem `--force`.
-   `text export`: cria/mescla catálogo JSON; preserva traduções
    compatíveis, marca mudanças de origem para revisão e mantém IDs
    removidos como `orphaned`.
-   `text validate`: verifica estrutura, IDs duplicados, campos, status
    e traduções pendentes; avisa sobre divergência de `∠`/quebras de
    linha; com `--source`, compara IDs e textos com uma extração atual.
-   `text stats`: conta entradas por status e percentual concluído sem
    alterar o catálogo.
-   `text batch-export`: exporta entradas `pending` e, por padrão,
    `needs_review` para CSV UTF-8 com BOM, compatível com Excel; limite
    padrão 100.
-   `text batch-import`: valida IDs, tipos e igualdade exata do original
    antes de gravar. Células vazias não apagam traduções; `needs_review`
    continua exigindo revisão.

A integração `text extract` ainda precisa ser testada localmente com
UnityDataTool 2.4.0 e bundles reais. Não afirmar que a extração está
validada sem resultado de teste fornecido. Quando a origem muda, a
tradução é mantida, `previous_original` é preservado, `source_changed`
fica verdadeiro e o status passa a `needs_review`. IDs removidos são
mantidos como `orphaned`.

## Evidência de engenharia reversa

-   Um bundle local de `Backup_Translation`,
    `700bf7ec8ded4a20613b92988e3f8142.bundle`, foi analisado.
-   UnityDataTool 2.4.0 listou um `AssetBundle` e um `TextAsset` chamado
    `text_add_en`.
-   O objeto continha JSON `textList` com 1.443 entradas, cada uma com
    `id` e `text`.
-   O catálogo de origem tem 1.443 IDs únicos no intervalo 1--1448. Os
    IDs 97, 126, 129, 155 e 201 não existem na origem; não são entradas
    perdidas e não devem ser inventados.
-   Três textos vazios foram preservados: IDs 312, 314 e 642.
-   `∠` é quebra na mesma janela; `∨` inicia a próxima caixa/janela;
    `∨☆` indica transição com pausa/espera. Preserve-os literalmente.
-   A tabela observada inclui menus, descrições, itens e textos
    narrativos; não há prova de que contenha todos os diálogos ou todos
    os recursos dos dois jogos.
-   Detalhes, hashes e limitações: `docs/REVERSE_ENGINEERING_LOG.md`.

## Regras obrigatórias de engenharia

1.  Inspecionar código e testes atuais antes de propor alterações.
2.  Não tratar planos/exemplos de CLI como funcionalidade existente sem
    conferir `--help` e implementação.
3.  Preservar o original byte a byte quando possível; nunca sobrescrever
    arquivos originais do jogo.
4.  Manter original e tradução em campos separados.
5.  Preservar IDs, ordem, tokens, marcadores, variáveis, espaços
    significativos e quebras de linha até que as regras sejam
    confirmadas.
6.  Não inventar limites de caracteres, semântica de tokens, mapeamento
    de IDs ou estrutura de reconstrução.
7.  Preferir funções pequenas, tipadas e testáveis; manter dependências
    de runtime em zero quando possível.
8.  Adicionar testes para caminho válido, dados inválidos, Unicode,
    strings vazias, marcadores, IDs duplicados, preservação de
    traduções, mudanças de origem e IDs órfãos.
9.  Não incluir bundles, executáveis de ferramentas, dumps integrais ou
    textos proprietários do jogo no Git.
10. Documentar hipóteses, comandos exatos, versão da ferramenta, hash de
    entrada e resultados.
11. Para comandos destrutivos ou que possam substituir traduções,
    alertar e implementar proteção/backup.
12. Não declarar testes aprovados sem executá-los ou sem citar resultado
    fornecido pelo usuário.

## Referências obrigatórias de tradução

-   Fluxo e prompt principal, seção 5:
    https://github.com/leonardo201800478/suikoden_ptbr_toolkit/blob/feature/translation-gui/docs/FLUXO_LOTES_E_PROMPTS_TRADUCAO.md
-   Glossário aprovado:
    https://github.com/leonardo201800478/suikoden_ptbr_toolkit/blob/feature/translation-gui/docs/GLOSSARIO_TRADUCAO_PTBR.md

## Regras obrigatórias para traduzir lotes

1.  Alterar somente `text`. Preservar estrutura JSON, IDs, tipo dos IDs,
    ordem, quantidade e propriedades de nível superior.
2.  Não traduzir nomes de personagens, localidades, facções, obras ou
    itens específicos de modo livre. Se houver mapeamento aprovado
    abaixo, usar exatamente essa forma; se não houver, manter o nome
    original e registrar dúvida.
3.  Não alternar sinônimos por preferência estilística. Reutilizar as
    formas aprovadas nos dois jogos.
4.  Preservar literalmente e na mesma sequência os marcadores técnicos:
    `♂㈱`, `♂①`, `♂②`, `♂⑩`, `∠`, `∨`, `∨☆`, `ＬＶ２`, `ＬＶ３`,
    `ＬＶ４`, `★☆`, `★★☆☆`, indicadores `◎1`, `◎2`, `◎5`, placeholders
    como `〓1`/`〓2`, símbolos desconhecidos e `?` literal.
5.  `∠` não é pontuação comum: é quebra na mesma janela. `∨` e `∨☆` têm
    função própria. Não remover, substituir por quebra real nem mover
    placeholders em relação aos marcadores sem motivo estrutural.
6.  Preservar espaços significativos, espaços finais, aspas, pontuação
    estrutural, caracteres fullwidth, escapes e quebras de linha.
7.  Traduzir texto comum em PT-BR natural, fiel ao sentido, tom e voz.
    Não inventar contexto, gênero, relação ou intenção não sustentados
    pelo texto.
8.  Não omitir, resumir, truncar ou reordenar entradas. Se necessário,
    trabalhar em partes contíguas por ID sem lacunas ou sobreposição.
9.  Em caso de ambiguidade, usar a tradução conservadora e registrar
    fora do JSON o ID, trecho original e motivo. Não adicionar notas ou
    campos ao JSON.
10. Validar sintaxe JSON, IDs e tipos, duplicados, sequência de
    marcadores por ID, espaços iniciais/finais, textos vazios e
    consistência com o glossário.
11. Não afirmar que o texto está "sem ambiguidades" se restar questão
    semântica. Separar validação estrutural de revisão
    linguística/contextual.
12. Para títulos de faixas musicais/obras, usar apenas mapeamento já
    registrado. Sem mapeamento exato, manter o título original e
    sinalizar a dúvida; não traduzir parte do título e deixar outra
    parte em inglês sem justificativa.

## Glossário canônico de atributos e interface

  ------------------------------------------------------------------------------------
  Origem                     PT-BR canônico                    Regra
  -------------------------- --------------------------------- -----------------------
  `STR`                      `FOR`                             Rótulo compacto de
                                                               Força.

  `DEX`                      `DES`                             Rótulo compacto de
                                                               Destreza.

  `PROT`                     `PROT`                            Não substituir por
                                                               `DEF`; são rótulos
                                                               distintos na origem.

  `SPD`                      `VEL`                             Rótulo compacto de
                                                               Velocidade.

  `MAG`                      `MAG`                             Manter.

  `LCK`                      `SOR`                             Usar `SOR`, não
                                                               `SORTE`, em rótulos
                                                               compactos.

  `ATK`                      `ATQ`                             Rótulo compacto de
                                                               ataque.

  `DEF`                      `DEF`                             Manter distinto de
                                                               `PROT`.

  `MDEF`                     `MDEF`                            Manter.

  `HP`                       `PV`                              Pontos de vida.

  `MP`                       `PM`                              Pontos de magia.

  `EXP`                      `EXP`                             Manter.

  `LV`                       `NV`                              Rótulo de nível
                                                               localizado; preservar
                                                               tokens fullwidth como
                                                               `ＬＶ２`.

  `S (Short Range)`          `C (Alcance curto)`               Categorias compactas:
                                                               `C/M/L`.

  `M (Medium Range)`         `M (Alcance médio)`               Manter `M`.

  `L (Long Range)`           `L (Alcance longo)`               Manter `L`, não
                                                               converter em `G`.

  `Add to party.`            `Adicionar ao grupo.`             Preservar ponto final
                                                               quando existir.

  `Don't add to party.`      `Não adicionar ao grupo.`         Preservar ponto final
                                                               quando existir.

  `potch`                    `potch`                           Moeda do jogo; não
                                                               traduzir nem
                                                               capitalizar como
                                                               `Potch`.

  `True Runes`               `Runas Verdadeiras`               Forma já aplicada.

  `Dragon Rune`              `Runa do Dragão`                  Forma já aplicada.

  `Fortune Orb`              `Orbe da Fortuna`                 Não confundir com
                                                               `Fortune Rune`.

  `Prosperity Orb`           `Orbe da Prosperidade`            Não confundir com
                                                               `Prosperity Rune`.

  `Fortune Rune`             `Runa da Fortuna`                 Distinta de Orbe da
                                                               Fortuna.

  `Prosperity Rune`          `Runa da Prosperidade`            Distinta de Orbe da
                                                               Prosperidade.

  `Soul Eater`               `Devorador de Almas`              Nome específico já
                                                               traduzido.

  `The Rune of Beginning`    `A Runa do Início`                Forma já aplicada.

  `Rune of Life and Death`   `Runa da Vida e da Morte`         Forma já aplicada.

  `City-States Army`         `Exército das Cidades-Estado`     Usar sempre.

  `City-States of Jowston`   `Cidades-Estado de Jowston`       Manter `Jowston`.

  `Highland Army`            `Exército das Terras Altas`       Usar sempre.

  `Matilda Knights`          `Cavaleiros de Matilda`           Manter `Matilda`.

  `Dragon Knights`           `Cavaleiros Dragões`              Forma usada nos lotes;
                                                               revisar antes de
                                                               substituir globalmente.

  `Mercenary Fortress`       `Fortaleza dos Mercenários`       Forma já aplicada.

  `Northern Checkpoint`      `Posto de Controle do Norte`      Forma já aplicada.

  `Floating Fortress`        `Fortaleza Flutuante`             Forma já aplicada.

  `Garan Fortress`           `Fortaleza de Garan`              Preservar `Garan`.

  `Viktor's Fortress`        `Fortaleza de Viktor`             Preservar `Viktor`.

  `Qlon Temple`              `Templo de Qlon`                  Preservar `Qlon`.

  `Lake Toran`               `Lago Toran`                      Preservar `Toran`.

  `The Gate Rune War`        `A Guerra da Runa do Portão`      Forma já aplicada.

  `Dunan Unification War`    `Guerra de Unificação de Dunan`   Forma já aplicada.

  `Log`                      `Registro`                        Forma atual; confirmar
                                                               se o contexto for
                                                               histórico de eventos.

  `Runes`                    `Runas`                           Rótulo de interface.

  `Rune Pieces`              `Fragmentos de runa`              Forma aplicada.

  `Rune orb`                 `Orbe de runa`                    Não confundir com
                                                               Fortune/Prosperity Orb.
  ------------------------------------------------------------------------------------

## Glossário de nomes de runas já traduzidos

Usar exatamente as formas abaixo quando o nome original corresponder.
São decisões registradas nos lotes existentes, não confirmação de
nomenclatura oficial. Se a revisão contextual indicar problema, marcar
para aprovação em vez de inventar uma variante silenciosamente.

  Nome original          PT-BR aplicado
  ---------------------- -----------------------------
  `Fire Rune`            `Runa do Fogo`
  `Rage Rune`            `Runa da Fúria`
  `Water Rune`           `Runa da Água`
  `Flowing Rune`         `Runa Fluente`
  `Wind Rune`            `Runa do Vento`
  `Cyclone Rune`         `Runa do Ciclone`
  `Earth Rune`           `Runa da Terra`
  `Mother Earth Rune`    `Runa da Mãe Terra`
  `Lightning Rune`       `Runa do Relâmpago`
  `Thunder Rune`         `Runa do Trovão`
  `Resurrection Rune`    `Runa da Ressurreição`
  `Bright Shield Rune`   `Runa do Escudo Brilhante`
  `Black Sword Rune`     `Runa da Espada Negra`
  `Blinking Rune`        `Runa do Teletransporte`
  `Darkness Rune`        `Runa das Trevas`
  `Pale Gate Rune`       `Runa do Portão Pálido`
  `White Saint Rune`     `Runa do Santo Branco`
  `Titan Rune`           `Runa do Titã`
  `Viper Rune`           `Runa da Víbora`
  `Great Hawk Rune`      `Runa do Grande Falcão`
  `Lion Rune`            `Runa do Leão`
  `Kite Rune`            `Runa do Milhafre`
  `Unicorn Rune`         `Runa do Unicórnio`
  `Gozu Rune`            `Runa Gozu`
  `Pixie Rune`           `Runa da Fada`
  `Banshee Rune`         `Runa da Banshee`
  `Sylph Rune`           `Runa do Silfo`
  `Chimera Rune`         `Runa da Quimera`
  `Nymph Rune`           `Runa da Ninfa`
  `Dryad Rune`           `Runa da Dríade`
  `Gadget Rune`          `Runa do Dispositivo`
  `Shrike Rune`          `Runa do Picanço`
  `Falcon Rune`          `Runa do Falcão`
  `Mayfly Rune`          `Runa da Efêmera`
  `Swallow Rune`         `Runa da Andorinha`
  `Fire Breath Rune`     `Runa do Sopro de Fogo`
  `Groundhog Rune`       `Runa da Marmota`
  `Fire Dragon Rune`     `Runa do Dragão de Fogo`
  `Shining Wind Rune`    `Runa do Vento Brilhante`
  `Blue Drop Rune`       `Runa da Gota Azul`
  `White Tiger Rune`     `Runa do Tigre Branco`
  `Howling Rune`         `Runa do Uivo`
  `Spider Slay Rune`     `Runa Matadora de Aranhas`
  `Angry Dragon Rune`    `Runa do Dragão Furioso`
  `Twin Ring Rune`       `Runa do Anel Duplo`
  `Rabid Fang Rune`      `Runa da Presa Raivosa`
  `Fortune Rune`         `Runa da Fortuna`
  `Prosperity Rune`      `Runa da Prosperidade`
  `Champion's Rune`      `Runa do Campeão`
  `Double-Jab Rune`      `Runa do Golpe Duplo`
  `Killer Rune`          `Runa Assassina`
  `Counter Rune`         `Runa do Contra-ataque`
  `Spark Rune`           `Runa da Centelha`
  `Gale Rune`            `Runa da Rajada`
  `Sunbeam Rune`         `Runa do Raio de Sol`
  `Phero Rune`           `Runa Phero`
  `Knight Rune`          `Runa do Cavaleiro`
  `Wall Rune`            `Runa da Muralha`
  `Haziness Rune`        `Runa da Nebulosidade`
  `Drain Rune`           `Runa da Drenagem`
  `Barrier Rune`         `Runa da Barreira`
  `Balance Rune`         `Runa do Equilíbrio`
  `Fire Sealing Rune`    `Runa do Selamento do Fogo`
  `Skunk Rune`           `Runa do Cangambá`
  `Firefly Rune`         `Runa do Vaga-lume`
  `Medicine Rune`        `Runa da Medicina`
  `Double-Edged Rune`    `Runa de Dois Gumes`
  `Wizard Rune`          `Runa do Mago`
  `Warrior Rune`         `Runa do Guerreiro`
  `Waking Rune`          `Runa do Despertar`
  `Alertness Rune`       `Runa da Vigilância`
  `Fury Rune`            `Runa da Fúria`
  `Violence Rune`        `Runa da Violência`
  `High-Speed Rune`      `Runa da Alta Velocidade`
  `Fire Lizard Rune`     `Runa do Lagarto de Fogo`
  `Magic Drain Rune`     `Runa de Drenagem Mágica`
  `Hunter Rune`          `Runa do Caçador`
  `Technique Rune`       `Runa da Técnica`
  `Silence Rune`         `Runa do Silêncio`
  `Poison Rune`          `Runa do Veneno`
  `Knockdown Rune`       `Runa da Derrubada`
  `Sleep Rune`           `Runa do Sono`
  `Friendship Rune`      `Runa da Amizade`
  `Solitude Rune`        `Runa da Solidão`
  `Kindness Rune`        `Runa da Bondade`
  `Exertion Rune`        `Runa do Esforço`

| `The Rune of Beginning` \| `A Runa do Início` \|
| `Rune of Life and Death` \| `Runa da Vida e da Morte` \|

## Outros itens e objetos nomeados já traduzidos

  Nome original          PT-BR aplicado
  ---------------------- --------------------------
  `Defective Urn`        `Urna Defeituosa`
  `Octopus Pot`          `Pote de Polvo`
  `Flower Vase`          `Vaso de Flores`
  `Black Urn`            `Urna Negra`
  `Fine China`           `Porcelana Fina`
  `Hex Doll`             `Boneco Amaldiçoado`
  `Japanese Dish`        `Prato Japonês`
  `Chinese Dish`         `Prato Chinês`
  `Peeing Boy`           `Menino Fazendo Xixi`
  `Bonsai Tree`          `Bonsai`
  `Knight Statue`        `Estátua de Cavaleiro`
  `Goddess Statue`       `Estátua de Deusa`
  `Graffiti`             `Grafite`
  `Flower Painting`      `Pintura de Flores`
  `Lovers' Garden`       `Jardim dos Amantes`
  `Landscape Scroll`     `Pergaminho de Paisagem`
  `Beauties of Nature`   `Belezas da Natureza`

## Nomes próprios que devem manter a grafia original

A lista é exemplificativa, baseada nos textos processados; não é
exaustiva. Não transliterar, traduzir nem adaptar nomes pessoais,
topônimos e nomes inventados. Traduzir apenas o termo genérico ao redor
quando houver mapeamento consistente.

-   **Personagens e nomes próprios:** Crowley, Joshua Levenheit, Gremio,
    Pahn, Kai, Clive, Gen, Templeton, Mace, Tesla, Kimberly, Sergei,
    Antonio, Lester, Hugo, Kasios, Milich, Jabba, Kamandol, Anji, Tai
    Ho, Rubi, Fuma, Fu Su Lu, Pesmerga, Kreutz, Geil Rugner, Humphrey
    Mintz, Yuber, Neclord, Lady Windy, Barbarossa, Leon Silverberg, Lord
    Oulan, Viktor, Flik, Luca Blight, Teo McDohl, McDohl, Odessa,
    Leknaat, Viki, Shu, Hai Yo, Jowy, Lepant, Richmond, Miklotov, Camus,
    Tengaar, Futch, Sonya, Kraze, Ridley, Teresa, Zorak e Hirotaka.
-   **Topônimos e nomes de regiões/cidades a preservar:** Teien, Antei,
    Kaku, Seika, Kirov, Qlon, Jowston, Kalekka, Premier L'Amour, Rikon,
    Toran, Dunan, Gregminster, Greenhill, Muse, South Window, North
    Window, Two Rivers, Lakewest, Radat, Kuskus, Tinto, Crom, Rockaxe,
    L'Renouille, Pannu Yakuta, Garan, Moravia, Scarleticia, Ryube,
    Kyaro, Sarady, Toto, Lake Toran e Rokkaku.
-   **Títulos/expressões próprios não mapeados:** manter no original até
    haver decisão explícita. Exemplos: `PENPE`, `Nahala Yam Koong`,
    `Asian Dub Mix`, `Orizzonte` e `Due Fiumi`.
-   Não traduzir o núcleo de nomes como `Jowston`, `Kalekka`, `Teien`,
    `Kaku`, `Kirov`, `Qlon`, `Toran`, `Dunan` ou `L'Renouille`. Para
    termos genéricos (`Lake`, `Village`, `Castle`, `Temple`,
    `Fortress`), seguir o mapeamento existente quando houver; caso
    contrário, manter o original e registrar a dúvida.

## Ambiguidades semânticas já identificadas --- não resolver por inferência

-   `Bag` → `Bolsa` (ID 762): confirmar se o menu significa
    bolsa/inventário ou outro recipiente.
-   `Blinking Rune` → `Runa do Teletransporte` (ID 815), `Gadget Rune` →
    `Runa do Dispositivo` (ID 832) e `Skunk Rune` → `Runa do Cangambá`
    (ID 865): traduções aplicadas, mas precisam de confirmação
    terminológica contextual.
-   `Dragon Knights` → `Cavaleiros Dragões`: forma consistente nos
    lotes, mas a naturalidade em PT-BR precisa de decisão terminológica
    antes de alteração global.
-   `Cures Balloon` → `Remove o estado Balão` (ID 1235): confirmar o
    nome do estado no jogo.
-   Títulos de faixas musicais e subtítulos: há títulos traduzidos e
    outros em inglês. Usar mapeamento exato já aprovado; sem
    correspondência, manter o original e registrar dúvida.
-   `Log` → `Registro` (ID 1147): confirmar se a função é registro ou
    histórico de eventos.
-   Alcances curtos/médios/longos: manter `C/M/L`; não voltar para
    `P/M/G`.

## Validação final obrigatória

1.  Comparar original e tradução por ID, incluindo tipos e ordem.
2.  Confirmar que nenhum ID foi acrescentado, removido, duplicado ou
    reordenado.
3.  Comparar sequência exata dos marcadores e placeholders por ID, não
    só a contagem total.
4.  Comparar quebras de linha e espaços iniciais/finais.
5.  Conferir nomes próprios, lugares, itens, runas, `potch` e
    abreviações com este glossário.
6.  Procurar texto comum deixado em inglês sem motivo.
7.  Validar JSON sintaticamente.
8.  Listar ambiguidades separadamente, com ID, original, tradução atual
    e motivo.
9.  Não declarar ausência total de ambiguidades se restar questão
    semântica; separar validação estrutural de revisão contextual.

## Linha de base e comandos

A branch é de desenvolvimento e não deve ser confundida com `main`.
Antes do fluxo CSV, o usuário executou `python -m pytest -q` com 16
testes aprovados e `ruff check .` sem erros. A implementação CSV
acrescenta 7 casos de teste; precisam ser executados localmente antes de
declarar a nova etapa validada.

Executar na raiz do repositório, em PowerShell:

``` powershell
python -m pytest -q
ruff check .
suikoden-tool text export --help
suikoden-tool text validate --help
suikoden-tool text stats --help
suikoden-tool text batch-export --help
suikoden-tool text batch-import --help
```

## Como responder

-   Usar português brasileiro, ser direto e técnico.
-   Separar fatos comprovados, inferências e próximos passos.
-   Fornecer comandos PowerShell copiáveis e indicar a pasta de
    execução.
-   Pedir apenas logs relevantes quando houver erro; evitar repetir
    etapas já concluídas.
-   Para mudanças grandes, indicar arquivos afetados, riscos, testes e
    forma de validar.
