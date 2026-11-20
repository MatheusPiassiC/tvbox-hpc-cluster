# Resultados experimentais

A série NPB 3.4.4 MPI, classe A, de 16 e 17 de novembro de 2026 contém oito conjuntos de coleta. Os 32 arquivos em [`raw/`](raw/) conservam os nomes e a organização da origem. Os planos somam 460 posições, e os CSVs de medições somam 460 tentativas. Há dez posições e dez tentativas por configuração em 46 configurações.

## Registros originais

| Arquivo original por benchmark | Conteúdo |
| --- | --- |
| `npb_<id>_<benchmark>_A-plano.csv` | Bloco, ordem no bloco e número de processos MPI |
| `npb_<id>_<benchmark>_A.csv` | Identificador da tentativa, configuração, tempo, estado do coletor e referência ao TXT |
| `npb_<id>_<benchmark>_A_saidas.txt` | Blocos de execução, stdout e stderr, mapeamento, afinidade e resumo do NPB |
| `npb_<id>_<benchmark>_A_ambiente.txt` | Snapshot da plataforma, dos parâmetros e do estado inicial da coleta |

Os oito snapshots originais de ambiente contêm identificadores de interfaces e ficam excluídos do versionamento. As ligações que apontam para suas linhas funcionam na cópia local com o conjunto completo.

Os originais usam UTF-8 e quebras LF. Os CSVs usam vírgula como delimitador, ponto decimal e campos vazios para valores ausentes. Os horários do coletor usam ISO 8601 com deslocamento `-03:00`. Nos CSVs de medições, `np` é a quantidade de processos solicitada, `tempo_s` copia o tempo do NPB em segundos e `tempo_parede_s` guarda a duração externa de `mpirun`. [Dicionário dos arquivos brutos](processed/auditoria/relatorios/01_exploracao_dos_arquivos.md#formatos-e-campos)

## Da tentativa ao resultado

Use `(campanha, exec_id)` para identificar a tentativa e `(campanha, bloco, np)` para identificar a posição no plano. Na base consolidada, `id_auditoria` reúne campanha e identidade da tentativa. `id_repeticao_logica` reúne campanha, bloco e processos. Os campos `arquivo_csv` e `arquivo_txt` usam caminhos relativos a `results/`, com linhas físicas contadas a partir de 1.

A tentativa `EP/npb_1_EP_A/1-0001`, por exemplo, corresponde ao bloco 1 de EP com 16 processos e registra 1,81 s no NPB. A base consolidada aponta para a linha 2 do CSV e a linha 7 do TXT. [Linha do CSV](raw/EP/npb_1_EP_A.csv#L2) · [Bloco da saída NPB](raw/EP/npb_1_EP_A_saidas.txt#L7)

| Para consultar | Arquivo e campos |
| --- | --- |
| Evidências de uma tentativa | A [base consolidada](processed/auditoria/tabelas/execucoes_consolidadas.csv) conserva os campos originais e os recuperados dos logs. |
| Validação | A [tabela de decisões](processed/auditoria/tabelas/auditoria_execucoes.csv) registra `estado_coleta`, `estado_auditoria` e `inclusao_estatistica_principal`. |
| Mapeamento efetivo | A [tabela de ranks MPI](processed/auditoria/tabelas/ranks_mpi.csv) vincula ranks, hosts e núcleos à tentativa. |
| Comparação entre configurações | As [estatísticas descritivas](processed/auditoria/tabelas/estatisticas_descritivas.csv) e a [tabela de escala](processed/auditoria/tabelas/speedup_eficiencia.csv) usam campanha, benchmark, classe e processos como chave. |

Os relatórios arquivados preservam os comandos e hashes da disposição original. Para trabalhar nesta árvore, consulte o [guia da auditoria](../scripts/analise/auditoria-npb/README.md), os [metadados](../metadata/README.md) e as [figuras do TCC](../reports/README.md).
