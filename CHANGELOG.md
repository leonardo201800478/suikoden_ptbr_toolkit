# Changelog

As mudanças relevantes do projeto serão registradas aqui.

## [Não lançado]

### Documentação e manutenção
- Documentada a instalação local das ferramentas externas AssetRipper, UABEA e UnityDataTools.
- Esclarecido que as distribuições executáveis não são dependências do toolkit nem devem ser versionadas neste repositório.
- Documentados os limites do `.gitignore`: ele evita novas inclusões, mas não remove arquivos grandes do histórico Git existente.

## [0.1.0] - 2026-10-17

### Adicionado
- Inspeção básica e não destrutiva de cabeçalho UnityFS.
- Cálculo SHA-256 e inventário de bundles em JSON.
- Interface CLI com os comandos `inspect`, `inventory` e `template`.
- Esquema inicial para entradas de tradução.
- Teste unitário inicial e configuração de desenvolvimento com pytest/Ruff.
- Documentação inicial do projeto, arquitetura, formato de tradução, contribuição, segurança e licença.

### Limitações conhecidas
- Extração de textos ainda não implementada.
- Reconstrução ou reinserção de bundles ainda não implementada.
- Limites de diálogo, tokens e variáveis ainda precisam ser confirmados com assets reais.
