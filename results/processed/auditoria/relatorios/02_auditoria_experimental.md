# 02 — Auditoria experimental

Foram examinados **32 arquivos** em 8 campanhas. Das **46 configurações** de referência, 46 foram observadas e 46 têm dez posições lógicas confirmadas em alguma campanha. A meta documentada é 460 repetições válidas. Há 460 registros nos planos, 460 registros de resultados e 460 blocos TXT. Foram agrupadas **460 tentativas**, das quais 460 aceitas pelo coletor (460 linhas CSV com `VALIDA`). A auditoria confirmou **460 válidas**, **0 inválidas**, **0 inconclusivas** e **0 conflitantes**. A amostra principal contém **460 tempos**.

## Validação e rastreabilidade

O vínculo usa `exec_id` no mesmo conjunto, conferido pela referência `saida_arquivo` e linha de abertura. O identificador de auditoria inclui a campanha. Na ausência de um ID, um ponteiro inequívoco permite associação ou é registrada a chave derivada da linha. Blocos e registros ambíguos ficam preservados em tabelas próprias. Cada posição lógica do plano usa campanha, bloco e np. O total de tentativas agrupadas inclui candidatos cuja identidade física ainda precise de revisão.

A classificação independente exige conclusão do NPB, verificação numérica `SUCCESSFUL` no resumo, tempo interno positivo, código de saída zero, consistência do problema classe A e dos processos, associação ao plano e mapeamento completo com afinidade individual e exclusiva por núcleo. O timeout e os limites prévios são avaliados pelos valores e controles documentados em cada campanha. O número de slots representa capacidade de alocação. O número de ranks distintos e os processos totais e ativos do resumo verificam o paralelismo. Os ranks devem preencher a ordem dos oito hosts computacionais, até quatro por nó, com o NFS dedicado.

- **Válida confirmada** requer evidência suficiente nos registros e ausência de contradição material.
- **Inválida confirmada** registra falha inequívoca da execução, da verificação numérica ou de critério obrigatório.
- **Inconclusiva** registra uma lacuna que impede confirmar a execução. Ausência de mapa, afinidade ou rodapé pode ter essa consequência.
- **Conflitante** indica valores materiais incompatíveis ou identidade ambígua. O conflito tem precedência quando coexistem sinais de falha ou lacunas. O catálogo preserva todos os motivos.

Para a amostra principal, uma tentativa confirmada precisa ocupar uma posição única na grade de referência, entre os blocos 1 e 10, com tempo do NPB e condições comparáveis dentro da configuração. Campanhas distintas permanecem como séries independentes. O status original do coletor é mantido em coluna própria. Avisos identificados têm registros e referências individuais.

Código 124 documenta timeout. Código 137 documenta encerramento por SIGKILL, com timeout confirmado quando há duração externa pelo menos igual ao limite da campanha. Outros códigos diferentes de zero evidenciam falha de execução. O diagnóstico de causa usa mensagens específicas e sua linha de origem. A declaração `VALIDA` em um envelope não decide a classificação.

## Cobertura por configuração

Todas as configurações da grade têm dez posições confirmadas. Há 0 rejeições explícitas de quantidade MPI no stdout/stderr e 0 tentativas sem np unívoco.

| NPB | Camp. | p | Plano | Tent. | Ord. válidos | Aceitas | Confirmadas | Inválidas | Inconc. | Confl. | Cobertura |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP | 1 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| EP | 1 | 2 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| EP | 1 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| EP | 1 | 8 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| EP | 1 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| EP | 1 | 32 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| IS | 2 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| IS | 2 | 2 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| IS | 2 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| IS | 2 | 8 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| IS | 2 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| IS | 2 | 32 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| CG | 3 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| CG | 3 | 2 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| CG | 3 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| CG | 3 | 8 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| CG | 3 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| CG | 3 | 32 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| MG | 4 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| MG | 4 | 2 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| MG | 4 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| MG | 4 | 8 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| MG | 4 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| MG | 4 | 32 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| FT | 5 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| FT | 5 | 2 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| FT | 5 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| FT | 5 | 8 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| FT | 5 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| FT | 5 | 32 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| LU | 6 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| LU | 6 | 2 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| LU | 6 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| LU | 6 | 8 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| LU | 6 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| LU | 6 | 32 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| BT | 10 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| BT | 10 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| BT | 10 | 9 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| BT | 10 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| BT | 10 | 25 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| SP | 9 | 1 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| SP | 9 | 4 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| SP | 9 | 9 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| SP | 9 | 16 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |
| SP | 9 | 25 | 10 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | completa |

Os planos documentam uma medida por configuração e bloco, sem reposição. A auditoria identifica a ordem pelo sufixo de `exec_id`, confrontando posições do TXT, linhas do CSV, horários e plano. A mesma semente pode gerar as mesmas permutações entre campanhas. Os hashes abaixo indicam repetição de arquivo de plano, enquanto cada conjunto de resultado tem suas próprias tentativas.

| SHA-256 do plano | Campanhas com bytes iguais |
| --- | --- |
| `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` | 6 |
| `c7662a74154c724725e42208bbbb187ace8e2c213e282ed715b2c5312a7988b4` | 2 |

## Mapeamento e tempos

Verificações de mapa completo e afinidade confirmada por tentativa totalizam 460 e 460, respectivamente. As frequências de número de representações do mapa por bloco são {8: 460}. O arquivo [ranks_mpi.csv](../tabelas/ranks_mpi.csv) traz host, socket, núcleo e linhas de evidência por rank e tentativa.

Nas 460 tentativas com ambas as métricas, a diferença parede − NPB vai de 1,690 a 20,490 s. A maior diferença absoluta entre parede e fim − início foi 0,97 s, a confrontar com a resolução de um segundo dos horários. Em 460 dos 460 pares CSV–TXT, os tempos internos têm valores idênticos. O valor principal é o campo `Time in seconds` emitido pelo NPB, inclusive quando o CSV apresenta precisão diferente compatível com arredondamento. No confronto entre números copiados, representações de igual precisão devem ter o mesmo valor. Em precisões distintas, as faixas implícitas de arredondamento precisam se sobrepor no interior. O relatório de ambiente define tempo do NPB como resposta. O tempo de parede inclui a inicialização MPI e tem tabela própria.

## Ambiente documentado

| Campo | Valor e número de campanhas | Exemplo de fonte |
| --- | --- | --- |
| plataforma_declarada_sha256 | `01cb4dfcb38e1f7fd8899a14a3fa1843a2fe1b1cb04be327709844f4bb562305` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:914](../../../raw/BT/npb_10_BT_A_ambiente.txt#L914) |
| secoes_2_3_sha256 | `2799a151c8075ef014da221b8527833ecb6930ed02ccf74ceb503cd9fc7c03a1` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:45](../../../raw/BT/npb_10_BT_A_ambiente.txt#L45) |
| script_sha256 | `efa570e5d040626e7580071208f0f4df5a604242a700a072eb32b06a4ce7a38b` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:7](../../../raw/BT/npb_10_BT_A_ambiente.txt#L7) |
| hostfile_declarado_sha256 | `7b935f49effa7f81b391c1ca99b8c5af2ec9d285404eba772d3ecc4d28dc2d1c` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:55](../../../raw/BT/npb_10_BT_A_ambiente.txt#L55) |
| make_def_declarado_sha256 | `a069d8fdbcef2dd658e4aa053d61e185468201fe10dd502f919dcc34edf6b07e` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:894](../../../raw/BT/npb_10_BT_A_ambiente.txt#L894) |
| npb_pacote | `3.4.4` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:888](../../../raw/BT/npb_10_BT_A_ambiente.txt#L888) |
| open_mpi_coordenador | `4.1.0` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:875](../../../raw/BT/npb_10_BT_A_ambiente.txt#L875) |
| compilador_binario | `GCC: (Debian 10.2.1-6) 10.2.1 20210110` (8) | [raw/BT/npb_10_BT_A_ambiente.txt:924](../../../raw/BT/npb_10_BT_A_ambiente.txt#L924) |

| Benchmark | Campanha | Início | Fim | Pré-temp. (°C) | Limite (°C) | Pré-RAM (MB) | Fonte do limite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BT | 10 | 2026-11-17T20:19:47-03:00 | 2026-11-17T22:21:44-03:00 | 77,4–80,0 | 80 | 1524,0–1533,0 | [raw/BT/npb_10_BT_A_ambiente.txt:1213](../../../raw/BT/npb_10_BT_A_ambiente.txt#L1213) |
| CG | 3 | 2026-11-16T17:06:29-03:00 | 2026-11-16T17:23:08-03:00 | 72,8–74,4 | 80 | 1527,0–1539,0 | [raw/CG/npb_3_CG_A_ambiente.txt:1214](../../../raw/CG/npb_3_CG_A_ambiente.txt#L1214) |
| EP | 1 | 2026-11-16T16:22:10-03:00 | 2026-11-16T16:40:38-03:00 | 72,6–73,7 | 80 | 1519,0–1534,0 | [raw/EP/npb_1_EP_A_ambiente.txt:1214](../../../raw/EP/npb_1_EP_A_ambiente.txt#L1214) |
| FT | 5 | 2026-11-16T17:52:31-03:00 | 2026-11-16T18:22:43-03:00 | 73,2–78,3 | 80 | 1529,0–1540,0 | [raw/FT/npb_5_FT_A_ambiente.txt:1214](../../../raw/FT/npb_5_FT_A_ambiente.txt#L1214) |
| IS | 2 | 2026-11-16T16:46:19-03:00 | 2026-11-16T17:00:48-03:00 | 72,3–74,6 | 80 | 1523,0–1538,0 | [raw/IS/npb_2_IS_A_ambiente.txt:1211](../../../raw/IS/npb_2_IS_A_ambiente.txt#L1211) |
| LU | 6 | 2026-11-16T18:28:25-03:00 | 2026-11-16T19:54:02-03:00 | 75,1–80,0 | 80 | 1529,0–1538,0 | [raw/LU/npb_6_LU_A_ambiente.txt:1214](../../../raw/LU/npb_6_LU_A_ambiente.txt#L1214) |
| MG | 4 | 2026-11-16T17:28:49-03:00 | 2026-11-16T17:46:49-03:00 | 72,8–75,0 | 80 | 1529,0–1539,0 | [raw/MG/npb_4_MG_A_ambiente.txt:1214](../../../raw/MG/npb_4_MG_A_ambiente.txt#L1214) |
| SP | 9 | 2026-11-17T17:04:54-03:00 | 2026-11-17T20:02:45-03:00 | 77,1–84,7 | 85 | 1523,0–1534,0 | [raw/SP/npb_9_SP_A_ambiente.txt:1213](../../../raw/SP/npb_9_SP_A_ambiente.txt#L1213) |

O hash calculado do trecho 2/3 permite comparar o texto observado. O hash declarado do coletor tem procedimento próprio. Os snapshots e a sondagem anterior delimitam a evidência ambiental. Hashes distintos entre executáveis de benchmarks diferentes são esperados. A auditoria compara as opções de compilação comuns com o `make.def` documentado e preserva o `RAND` específico de cada carga. Tamanho e iterações são verificados pelos parâmetros de classe A. Os resumos NPB reportam a versão completa 3.4.4. [Tamanhos de problema, NASA](https://nas.nasa.gov/software/npb_problem_sizes.html)

O nome comercial das TV Boxes é H7. O device tree usado na inicialização registra o modelo `SEI Robotics SEI610`. [Informações manuais de SP](../../../raw/SP/npb_9_SP_A_ambiente.txt#L114-L127)

## Ocorrências com fontes

| Nível | Ocorrência | Registros | Primeiro exemplo | Fontes do exemplo |
| --- | --- | --- | --- | --- |
| alerta | aviso_stdout_stderr | 1 | [server:109059] plm:rsh: Warning: setpgid(109081,109081) failed in parent with errno=Permission denied(13) | [raw/LU/npb_6_LU_A_saidas.txt:3966](../../../raw/LU/npb_6_LU_A_saidas.txt#L3966) |
| alerta | metadados_ambiente_divergentes | 1 | temp_max_c varia entre campanhas: [80, 85]. | [raw/BT/npb_10_BT_A_ambiente.txt:1213](../../../raw/BT/npb_10_BT_A_ambiente.txt#L1213) · [raw/CG/npb_3_CG_A_ambiente.txt:1214](../../../raw/CG/npb_3_CG_A_ambiente.txt#L1214) · [raw/EP/npb_1_EP_A_ambiente.txt:1214](../../../raw/EP/npb_1_EP_A_ambiente.txt#L1214) · [raw/FT/npb_5_FT_A_ambiente.txt:1214](../../../raw/FT/npb_5_FT_A_ambiente.txt#L1214) · [raw/IS/npb_2_IS_A_ambiente.txt:1211](../../../raw/IS/npb_2_IS_A_ambiente.txt#L1211) · [raw/LU/npb_6_LU_A_ambiente.txt:1214](../../../raw/LU/npb_6_LU_A_ambiente.txt#L1214) · [raw/MG/npb_4_MG_A_ambiente.txt:1214](../../../raw/MG/npb_4_MG_A_ambiente.txt#L1214) · [raw/SP/npb_9_SP_A_ambiente.txt:1213](../../../raw/SP/npb_9_SP_A_ambiente.txt#L1213) |

As referências usam linhas físicas contadas a partir de 1. A tabela [inconsistencias.csv](../tabelas/inconsistencias.csv) traz todos os casos, inclusive os exemplos acima e as listas de fontes. [Base consolidada](../tabelas/execucoes_consolidadas.csv) · [Classificação por tentativa](../tabelas/auditoria_execucoes.csv) · [Cobertura completa](../tabelas/cobertura_experimental.csv)
