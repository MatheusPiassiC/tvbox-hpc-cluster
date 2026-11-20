# Auditoria dos NAS Parallel Benchmarks

A auditoria reconcilia os CSVs de resultados e de planejamento, os logs MPI/NPB e os snapshots de ambiente das campanhas do TCC. A [base consolidada](../../../results/processed/auditoria/tabelas/execucoes_consolidadas.csv) tem uma linha por identidade de tentativa, com referências às fontes e código de decisão. A [síntese experimental](../../../results/processed/auditoria/relatorios/05_sintese_experimental.md) reúne cobertura, resultados e limitações de interpretação.

## Reproduzir a análise

A auditoria funciona em uma máquina Linux/POSIX com Python 3.12 e os registros arquivados. O manifesto da entrega registra Python 3.12.3. A lista de dependências fixa NumPy, SciPy, Matplotlib e os demais pacotes do ambiente. [Dependências da auditoria](requirements-auditoria.txt) · [Versões da entrega](../../../results/processed/auditoria/manifestos/reproducibilidade.json)

Na raiz do repositório, prepare o ambiente se ainda precisar das dependências fixadas.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r scripts/analise/auditoria-npb/requirements-auditoria.txt
```

Use `results/raw/` com os 32 originais, incluindo os oito snapshots de ambiente da cópia local. Confira os hashes de entrada antes do processamento. Especifique a entrada com `--raw` e um destino separado das saídas arquivadas com `--out`. [Verificação de integridade](../../../metadata/README.md#verificação-local)

```sh
.venv/bin/python scripts/analise/auditoria-npb/scripts/auditar_npb.py --raw results/raw --out .local/reproducao/auditoria
```

A auditoria grava `tabelas/`, `graficos/`, `relatorios/` e `manifestos/` no destino escolhido. Para comparar com a entrega arquivada, confira primeiro as assinaturas das entradas e as versões do ambiente. Use `id_auditoria` nas tabelas por tentativa e `(campanha, benchmark, classe, np)` nas tabelas por configuração. A mudança de diretório pode alterar os links relativos dos relatórios e seus hashes. As tabelas da nova saída também podem alimentar o catálogo. [Chaves e formatos](../../../results/README.md) · [Geração de visualizações](../../README.md)

Os testes da auditoria usam dados sintéticos em diretórios temporários. A partir da raiz, execute:

```sh
(cd scripts/analise/auditoria-npb && ../../../.venv/bin/python -m unittest discover -s tests -v)
```

## Arquivos produzidos

| Caminho | Conteúdo |
| --- | --- |
| [relatorios/](../../../results/processed/auditoria/relatorios/) | Exploração, auditoria experimental, análise estatística, diagnóstico de cada benchmark e síntese da campanha. |
| [execucoes_consolidadas.csv](../../../results/processed/auditoria/tabelas/execucoes_consolidadas.csv) | Colunas originais do CSV, dados derivados, estado da auditoria, elegibilidade e proveniência. |
| [auditoria_execucoes.csv](../../../results/processed/auditoria/tabelas/auditoria_execucoes.csv) e [inconsistencias.csv](../../../results/processed/auditoria/tabelas/inconsistencias.csv) | Decisões, motivos e fontes com linhas físicas. |
| [registros_csv.csv](../../../results/processed/auditoria/tabelas/registros_csv.csv), [registros_plano.csv](../../../results/processed/auditoria/tabelas/registros_plano.csv), [blocos_txt.csv](../../../results/processed/auditoria/tabelas/blocos_txt.csv) e [ranks_mpi.csv](../../../results/processed/auditoria/tabelas/ranks_mpi.csv) | Registros individuais de fonte e reconstrução dos hosts e núcleos por rank. |
| [cobertura_experimental.csv](../../../results/processed/auditoria/tabelas/cobertura_experimental.csv) | Grade esperada, planos, tentativas, validação e blocos completos. |
| [estatisticas_descritivas.csv](../../../results/processed/auditoria/tabelas/estatisticas_descritivas.csv), [speedup_eficiencia.csv](../../../results/processed/auditoria/tabelas/speedup_eficiencia.csv) e [resumo_benchmarks.csv](../../../results/processed/auditoria/tabelas/resumo_benchmarks.csv) | Distribuição dos tempos internos, intervalos, razões de médias e melhor configuração. |
| [estatisticas_tempo_parede.csv](../../../results/processed/auditoria/tabelas/estatisticas_tempo_parede.csv), [comportamento_temporal.csv](../../../results/processed/auditoria/tabelas/comportamento_temporal.csv), [observacoes_atipicas.csv](../../../results/processed/auditoria/tabelas/observacoes_atipicas.csv) e [sensibilidade.csv](../../../results/processed/auditoria/tabelas/sensibilidade.csv) | Duração externa, ordem, dispersão e efeitos de decisões alternativas. |
| [ambientes.csv](../../../results/processed/auditoria/tabelas/ambientes.csv) e [nos_ambiente.csv](../../../results/processed/auditoria/tabelas/nos_ambiente.csv) | Metadados dos snapshots e comparações de configuração. |
| [graficos/](../../../results/processed/auditoria/graficos/) | Seis figuras exploratórias, em PNG e PDF. |
| [manifestos/](../../../results/processed/auditoria/manifestos/) | Hashes da entrada e dos artefatos, identificação do código e versões de execução. |

Os CSVs de saída usam UTF-8, vírgula como separador, ponto decimal e campo vazio para dado ausente. Colunas com listas ou mapas usam JSON. Os campos `arquivo:linha` e `arquivo:início-fim` apontam para linhas físicas contadas a partir de 1. O campo `id_auditoria` agrega o caminho relativo da campanha e a identidade original ou derivada. O campo `id_repeticao_logica` identifica uma posição por campanha, bloco e np.

## Controle dos dados e atualização

A auditoria verifica novamente os hashes da entrada antes de gravar as saídas. Ela prepara os arquivos em uma área temporária e usa o manifesto dos artefatos para identificar saídas gerenciadas. Quando detecta um arquivo de terceiros ou uma edição manual no destino, preserva o arquivo e sinaliza a colisão. Use outro diretório com `--out` nesse caso. Cada troca de arquivo é atômica e a execução idêntica pode retomar uma gravação interrompida.

Os parsers refletem os envelopes do coletor v5.4 e os formatos Open MPI/NPB observados. Ocorrências de leitura e ambiguidades aparecem com referência à origem. Campanhas adicionais ficam identificadas pelo próprio conjunto de arquivos e suas séries ficam isoladas nas tabelas. O relatório de exploração e as notas de interpretação registram a inspeção inicial deste snapshot.
