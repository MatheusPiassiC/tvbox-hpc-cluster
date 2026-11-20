# Scripts da pesquisa

| Diretório | Material |
| --- | --- |
| [execucao](execucao/) | Destino do código original de execução. A campanha registra o coletor v5.4 nos snapshots. |
| [coleta](coleta/) | Destino dos scripts originais de coleta e sondagem, ainda pendentes. |
| [analise/auditoria-npb](analise/auditoria-npb/README.md) | Reconciliação de CSV, plano, TXT e ambiente. Inclui código, testes sintéticos e dependências fixadas. |
| [analise/visualizacoes](analise/visualizacoes/) | Geração do catálogo e das peças candidatas a partir das tabelas auditadas. |
| [analise/verificar_integridade.py](analise/verificar_integridade.py) | Conferência dos hashes declarados da entrada, dos artefatos da auditoria e do código. |

O pacote da auditoria mantém a disposição original de código, testes e dependências para conservar os hashes declarados no [manifesto de reprodução](../results/processed/auditoria/manifestos/reproducibilidade.json). O [guia de reprodução computacional](analise/auditoria-npb/README.md) indica como fornecer a entrada e um destino separado.

## Gerar as visualizações

Após preparar o ambiente da auditoria, use os comandos abaixo na raiz do repositório. Eles leem as tabelas arquivadas em `results/processed/auditoria/tabelas/`. O catálogo escreve em `.local/reproducao/visualizacoes/`, e as peças candidatas escrevem em `.local/reproducao/candidatas-tcc/`.

```sh
.venv/bin/python scripts/analise/visualizacoes/gerar_visualizacoes.py
.venv/bin/python scripts/analise/visualizacoes/gerar_candidatas.py
```

Para gerar o catálogo e as peças candidatas a partir de uma nova auditoria, aponte `--entrada` para as tabelas produzidas e escolha um diretório de saída próprio para cada gerador.

```sh
.venv/bin/python scripts/analise/visualizacoes/gerar_visualizacoes.py \
  --entrada .local/reproducao/auditoria/tabelas \
  --saida .local/reproducao/visualizacoes-reprocessadas
.venv/bin/python scripts/analise/visualizacoes/gerar_candidatas.py \
  --entrada .local/reproducao/auditoria/tabelas \
  --saida .local/reproducao/candidatas-reprocessadas
```

Para reproduzir as tabelas em PDF e as provas de impressão, use pdfLaTeX com `booktabs`, `lmodern`, `geometry`, `graphicx` e `babel` em português, além de `pdftoppm` e `pdfinfo` do Poppler. O catálogo registra quando precisou usar a renderização alternativa. [Catálogo arquivado](../reports/figures/visualizacoes_experimentais/CATALOGO_VISUALIZACOES.md)
