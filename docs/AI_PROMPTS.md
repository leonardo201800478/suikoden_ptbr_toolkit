# Prompts reutilizáveis para assistentes de IA

Use um prompt por tarefa. Antes de começar, forneça ao assistente `docs/AI_CONTEXT.md` e peça que consulte o código real do branch atual. Os prompts não substituem os testes nem autorizam suposições sobre os formatos internos do jogo.

## 1. Entender o projeto antes de alterar

> Leia primeiro `README.md`, `docs/AI_CONTEXT.md`, `docs/ARCHITECTURE.md`, `docs/TRANSLATION_FORMAT.md`, `docs/REVERSE_ENGINEERING_LOG.md`, `pyproject.toml`, o código de `src/suikoden_tool/` e os testes. Resuma a arquitetura atual, comandos implementados, limitações confirmadas, riscos de perda de dados e próximos passos. Diferencie explicitamente funcionalidades existentes de propostas. Não altere arquivos ainda.

## 2. Implementar uma funcionalidade de forma segura

> Implemente [DESCREVER FUNCIONALIDADE] no toolkit Suikoden PT-BR. Antes de codificar, inspecione o código e os testes atuais e identifique os módulos que devem mudar. Mantenha compatibilidade com Python 3.11+, dependências de runtime mínimas e mensagens de erro úteis. Preserve IDs, texto original, Unicode, tokens e quebras de linha. Adicione testes para sucesso, entradas inválidas e casos-limite. Não altere bundles do jogo nem inclua dumps proprietários. Ao terminar, informe arquivos alterados, comandos executados, resultados reais dos testes e limitações remanescentes.

## 3. Revisar um pull request ou branch

> Faça revisão técnica da branch [BRANCH/PR] contra a base indicada. Priorize bugs, perda de tradução, regressões, segurança de arquivos, validação de formatos, portabilidade Windows e testes ausentes. Para cada achado, informe severidade, arquivo/linha, cenário de reprodução e correção sugerida. Não invente falhas nem aprove uma alteração sem verificar o diff e os testes disponíveis.

## 4. Projetar mesclagem segura de catálogos

> Projete e implemente atualização segura de um catálogo existente a partir de uma nova extração. Preserve traduções e status quando ID e texto original forem compatíveis. Detecte IDs removidos, novos IDs, IDs duplicados e texto de origem alterado. Não associe traduções automaticamente quando a origem tiver mudado sem registrar conflito. A operação deve ser não destrutiva, ter backup ou saída separada, produzir relatório de mesclagem e ter testes cobrindo preservação e conflitos. Documente a política de resolução.

## 5. Validar catálogos de tradução

> Implemente `suikoden-tool text validate` e/ou estatísticas sem alterar o catálogo. Verifique estrutura, versão de esquema, IDs únicos, tipos de campo, estados permitidos, traduções pendentes e preservação de marcadores/variáveis. Não presuma que o marcador `∠` significa quebra de linha até haver evidência. Diferencie erro bloqueante de aviso heurístico. Adicione testes e documente códigos de saída.

## 6. Investigar um novo bundle Unity

> Analise o bundle [CAMINHO] de forma somente leitura. Registre SHA-256, tamanho, assinatura, ferramenta e versão, comandos exatos, objetos encontrados e resultados. Use cópias de trabalho para qualquer extração. Não conclua que um bundle pode ser reconstruído só porque foi aberto ou extraído. Não publique o conteúdo integral dos textos do jogo. Entregue um resumo técnico reproduzível e atualize `docs/REVERSE_ENGINEERING_LOG.md` com fatos, hipóteses e perguntas em aberto.

## 7. Planejar a extração automatizada de TextAssets

> Proponha uma camada Python que invoque/configure uma ferramenta externa para extrair TextAssets, sem acoplar a lógica de catálogo a uma ferramenta específica. Inspecione as versões e opções reais da ferramenta antes de escrever comandos. Considere caminhos com espaços no Windows, timeout, mensagens de erro, arquivos temporários, hashes, idempotência e preservação de originais. Primeiro entregue plano, interfaces e testes; não implemente reconstrução de bundles.

## 8. Traduzir entradas para PT-BR

> Traduza as entradas fornecidas para português brasileiro natural, mantendo tom, intenção, terminologia consistente e limites explicitamente informados. Preserve exatamente IDs, placeholders, variáveis, marcadores de controle e quebras de linha exigidas. Não traduza nomes próprios ou termos de lore sem consultar o glossário/contexto. Não invente contexto ausente. Retorne apenas o formato estruturado solicitado e marque dúvidas em notas, sem modificar o texto original.

## 9. Criar ou atualizar documentação

> Revise a documentação para refletir somente o comportamento comprovado no código e nos testes. Atualize README, arquitetura, formato, registro de experimentos e contexto de IA conforme necessário. Marque claramente o que está implementado, planejado, testado ou ainda desconhecido. Inclua exemplos de comandos que funcionem na branch atual e não exponha dumps integrais ou conteúdo proprietário. Verifique links internos e consistência entre os documentos.

## 10. Diagnosticar falha no Windows/PowerShell

> Diagnostique o erro abaixo no contexto do toolkit. Primeiro identifique a pasta de execução, ambiente Python ativo, branch e versão instalada. Peça ou use o comando mínimo para reproduzir. Separe problemas de shell, instalação do pacote, código e arquivos de entrada. Forneça correção reversível e comandos PowerShell exatos. Não recomende apagar arquivos, reescrever histórico Git ou substituir catálogos sem backup e confirmação.
>
> Erro/log: [COLAR AQUI]

## 11. Planejar importação/reconstrução

> Investigue os requisitos de importação e reconstrução apenas depois de identificar a estrutura binária real do asset. Liste evidências necessárias, campos que devem ser preservados, estratégias de round-trip, validação por hash e teste em cópia. Não implemente escrita no bundle com base apenas no cabeçalho UnityFS ou no JSON extraído. Comece por um plano de prova de conceito e critérios de aceitação.

## 13. Atualizar ou validar um catálogo sem perda de dados

> Use `suikoden-tool text export` para mesclar uma nova extração com o catálogo existente. Antes de recomendar a operação, confirme que o recurso e o idioma de destino coincidem. Verifique que traduções compatíveis sejam preservadas, mudanças de origem recebam `needs_review` e `previous_original`, e IDs ausentes sejam mantidos como `orphaned`. Depois execute `text validate` com `--source` e `text stats`. Nunca sobrescreva manualmente um catálogo malformado sem backup.

## 12. Fazer uma sessão curta de continuidade

> Continue o projeto a partir de `docs/AI_CONTEXT.md` e `docs/REVERSE_ENGINEERING_LOG.md`. Confira o estado atual do Git e o código real antes de assumir qualquer coisa. Identifique a próxima tarefa prioritária que não esteja concluída, proponha uma alteração pequena com testes e pare para reportar resultados verificáveis. Não repita tarefas já concluídas e não trate arquivos locais em `work/` como parte do repositório.
