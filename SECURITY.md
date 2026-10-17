# Política de segurança

## Escopo

Este repositório é uma ferramenta local de análise de arquivos e localização. Atualmente, a inspeção de bundles é somente de leitura e não extrai nem reconstrói os assets do jogo.

## Como relatar uma vulnerabilidade

Não publique detalhes exploráveis de uma vulnerabilidade ainda não corrigida em uma Issue pública. Entre em contato com o mantenedor pelos meios privados disponibilizados no perfil do GitHub e inclua:

- versão/commit afetado;
- ambiente e versão do Python;
- passos mínimos para reproduzir;
- impacto observado e logs sanitizados.

Não envie bundles proprietários nem dados pessoais nos relatórios. Se não houver um canal privado disponível, abra uma Issue com descrição não sensível solicitando um meio de contato.

## Práticas recomendadas

- Execute ferramentas de terceiros somente de fontes oficiais e revise os arquivos antes de executá-los.
- Faça cópias de segurança e não teste em seus únicos arquivos originais.
- Trate arquivos de entrada como não confiáveis; parsers futuros devem validar tamanhos, offsets e limites.
- Não inclua credenciais, caminhos pessoais, arquivos do jogo ou dumps integrais em commits.
