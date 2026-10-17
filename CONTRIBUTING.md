# Como contribuir

Obrigado pelo interesse em contribuir com o toolkit de localização PT-BR de Suikoden I & II HD Remaster.

## Antes de abrir uma contribuição

1. Confira as Issues existentes para evitar duplicidade.
2. Para mudanças grandes (formato de dados, arquitetura, reconstrução de bundles), abra uma Issue para discutir a abordagem antes de implementar.
3. Não envie bundles, executáveis, dumps integrais, arquivos extraídos do jogo ou outros materiais proprietários.
4. Não presuma limites de texto ou o significado de tokens sem evidência reproduzível.

## Ambiente local

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Verificações antes de enviar

```powershell
pytest
ruff check .
```

Se o Ruff apontar problemas preexistentes fora do escopo da sua alteração, informe isso na descrição; não esconda erros novos. Toda correção de parser ou formato deve incluir testes, inclusive casos inválidos e dados truncados quando aplicável.

## Diretrizes de implementação

- Mantenha a compatibilidade com as versões de Python declaradas em `pyproject.toml`.
- Prefira funções pequenas, tipadas e com mensagens de erro úteis.
- Use UTF-8 para arquivos de texto e JSON; preserve acentos.
- Não altere os arquivos de entrada durante inspeção.
- Preserve IDs, ordem, tokens, variáveis e metadados necessários para uma futura reinserção.
- Não introduza dependências obrigatórias sem justificar a necessidade.
- Documente qualquer formato binário ou regra inferida e como ela foi confirmada.
- Atualize a documentação e os testes junto com a funcionalidade.

## Pull requests

Descreva o problema, a solução, os testes executados e eventuais limitações. Inclua exemplos pequenos e sintéticos em vez de dados extraídos do jogo. Se a mudança depender de um bundle específico, informe o hash SHA-256 e os passos para reproduzir sem anexar o arquivo proprietário.
