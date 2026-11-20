# 05 — Síntese experimental

A auditoria abrange a campanha de novembro de 2026 com o NAS Parallel Benchmarks 3.4.4 MPI, classe A. O cluster tem oito nós H7 de cálculo, com quatro núcleos Cortex-A55 cada, e um servidor NFS dedicado. O problema de cada benchmark permanece fixo ao variar o número de processos. BT e SP usam 1, 4, 9, 16 e 25 processos. EP, IS, CG, MG, FT e LU usam 1, 2, 4, 8, 16 e 32. [Parâmetros de classe A, NASA](https://nas.nasa.gov/software/npb_problem_sizes.html)

## Dados e decisão de validade

Cada campanha tem CSV de resultados, CSV de plano, TXT com mapa/saída e registro de ambiente. O plano tem dez blocos com cada np uma vez por bloco. A ordem foi permutada com semente 20261114, com repetição de arquivo de plano para os mesmos conjuntos de níveis. O coletor v5.4 documenta ausência de aquecimento deliberado e ausência de reposição. `exec_id` identifica a tentativa dentro da campanha. `tentativa` conta lançamentos por np. `repeticao_valida` é o ordinal aceito pelo coletor. `(campanha, bloco, np)` identifica a posição planejada. As tabelas retêm nomes de arquivo, linhas físicas e intervalos correspondentes.

A classificação independente exige conclusão do NPB, verificação numérica `SUCCESSFUL` no resumo, tempo interno positivo, código de saída zero, consistência do problema classe A e dos processos, associação ao plano e mapeamento completo com afinidade individual e exclusiva por núcleo. O timeout e os limites prévios são avaliados pelos valores e controles documentados em cada campanha. O número de slots representa capacidade de alocação. O número de ranks distintos e os processos totais e ativos do resumo verificam o paralelismo. Os ranks devem preencher a ordem dos oito hosts computacionais, até quatro por nó, com o NFS dedicado.

- **Válida confirmada** requer evidência suficiente nos registros e ausência de contradição material.
- **Inválida confirmada** registra falha inequívoca da execução, da verificação numérica ou de critério obrigatório.
- **Inconclusiva** registra uma lacuna que impede confirmar a execução. Ausência de mapa, afinidade ou rodapé pode ter essa consequência.
- **Conflitante** indica valores materiais incompatíveis ou identidade ambígua. O conflito tem precedência quando coexistem sinais de falha ou lacunas. O catálogo preserva todos os motivos.

Para a amostra principal, uma tentativa confirmada precisa ocupar uma posição única na grade de referência, entre os blocos 1 e 10, com tempo do NPB e condições comparáveis dentro da configuração. Campanhas distintas permanecem como séries independentes. O status original do coletor é mantido em coluna própria. Avisos identificados têm registros e referências individuais.

Foram examinados **32 arquivos** em 8 campanhas. Das **46 configurações** de referência, 46 foram observadas e 46 têm dez posições lógicas confirmadas em alguma campanha. A meta documentada é 460 repetições válidas. Há 460 registros nos planos, 460 registros de resultados e 460 blocos TXT. Foram agrupadas **460 tentativas**, das quais 460 aceitas pelo coletor (460 linhas CSV com `VALIDA`). A auditoria confirmou **460 válidas**, **0 inválidas**, **0 inconclusivas** e **0 conflitantes**. A amostra principal contém **460 tempos**.

Todas as configurações da grade têm dez posições confirmadas. Há 0 rejeições explícitas de quantidade MPI no stdout/stderr e 0 tentativas sem np unívoco.

A duração usada nas estatísticas é `Time in seconds` do resumo do NPB. `tempo_parede_s` tem série própria e inclui o lançamento MPI. Médias, DP com `ddof=1`, quartis tipo 7 e IC de 95% t bilateral usam o n observado. Uma medida isolada não gera IC. O speedup usa a razão de médias com um processo na mesma campanha e `E% = 100 × S(p)/p`. Os intervalos da tabela são de tempo médio. As amostras têm pouca resolução para inferir distribuição e as campanhas com medidas ordenadas podem ter dependência temporal. [Intervalo t para a média, NIST/SEMATECH](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)

## Melhor configuração e estimativas por nível

| NPB | Campanha | Média 1 p (s) | Melhor p | Melhor média (s) | Redução (%) | Maior S | Maior p com tempos | E no maior p (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP | EP/npb_1_EP_A | 28,261 | 32 | 0,936 | 96,69 | 30,193 | 32 | 94,35 |
| IS | IS/npb_2_IS_A | 2,410 | 4 | 0,826 | 65,73 | 2,918 | 32 | 1,60 |
| CG | CG/npb_3_CG_A | 16,425 | 8 | 3,670 | 77,66 | 4,475 | 32 | 10,20 |
| MG | MG/npb_4_MG_A | 12,681 | 32 | 2,444 | 80,73 | 5,189 | 32 | 16,21 |
| FT | FT/npb_5_FT_A | 21,494 | 4 | 8,509 | 60,41 | 2,526 | 32 | 3,53 |
| LU | LU/npb_6_LU_A | 189,196 | 32 | 28,857 | 84,75 | 6,556 | 32 | 20,49 |
| BT | BT/npb_10_BT_A | 296,976 | 25 | 62,725 | 78,88 | 4,735 | 25 | 18,94 |
| SP | SP/npb_9_SP_A | 446,548 | 25 | 113,178 | 74,65 | 3,946 | 25 | 15,78 |

| NPB | Camp. | p | n | Nós | Média (s) | IC 95% (s) | CV (%) | S(p) | E(p) (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP | 1 | 1 | 10 | 1 | 28,261 | [28,239 a 28,283] | 0,11 | 1,000 | 100,00 |
| EP | 1 | 2 | 10 | 1 | 14,129 | [14,097 a 14,161] | 0,32 | 2,000 | 100,01 |
| EP | 1 | 4 | 10 | 1 | 7,083 | [7,067 a 7,099] | 0,31 | 3,990 | 99,75 |
| EP | 1 | 8 | 10 | 2 | 3,581 | [3,558 a 3,604] | 0,92 | 7,892 | 98,65 |
| EP | 1 | 16 | 10 | 4 | 1,814 | [1,803 a 1,825] | 0,87 | 15,579 | 97,37 |
| EP | 1 | 32 | 10 | 8 | 0,936 | [0,922 a 0,950] | 2,15 | 30,193 | 94,35 |
| IS | 2 | 1 | 10 | 1 | 2,410 | [2,392 a 2,428] | 1,05 | 1,000 | 100,00 |
| IS | 2 | 2 | 10 | 1 | 1,311 | [1,301 a 1,321] | 1,11 | 1,838 | 91,91 |
| IS | 2 | 4 | 10 | 1 | 0,826 | [0,819 a 0,833] | 1,17 | 2,918 | 72,94 |
| IS | 2 | 8 | 10 | 2 | 8,180 | [8,021 a 8,339] | 2,72 | 0,295 | 3,68 |
| IS | 2 | 16 | 10 | 4 | 8,251 | [8,121 a 8,381] | 2,21 | 0,292 | 1,83 |
| IS | 2 | 32 | 10 | 8 | 4,698 | [4,645 a 4,751] | 1,59 | 0,513 | 1,60 |
| CG | 3 | 1 | 10 | 1 | 16,425 | [16,376 a 16,474] | 0,42 | 1,000 | 100,00 |
| CG | 3 | 2 | 10 | 1 | 6,569 | [6,549 a 6,589] | 0,42 | 2,500 | 125,02 |
| CG | 3 | 4 | 10 | 1 | 3,853 | [3,839 a 3,867] | 0,49 | 4,263 | 106,57 |
| CG | 3 | 8 | 10 | 2 | 3,670 | [3,648 a 3,692] | 0,83 | 4,475 | 55,94 |
| CG | 3 | 16 | 10 | 4 | 4,566 | [4,531 a 4,601] | 1,08 | 3,597 | 22,48 |
| CG | 3 | 32 | 10 | 8 | 5,031 | [4,996 a 5,066] | 0,98 | 3,265 | 10,20 |
| MG | 4 | 1 | 10 | 1 | 12,681 | [12,584 a 12,778] | 1,07 | 1,000 | 100,00 |
| MG | 4 | 2 | 10 | 1 | 9,274 | [9,180 a 9,368] | 1,41 | 1,367 | 68,37 |
| MG | 4 | 4 | 10 | 1 | 4,700 | [4,672 a 4,728] | 0,82 | 2,698 | 67,45 |
| MG | 4 | 8 | 10 | 2 | 4,297 | [4,173 a 4,421] | 4,04 | 2,951 | 36,89 |
| MG | 4 | 16 | 10 | 4 | 3,587 | [3,522 a 3,652] | 2,53 | 3,535 | 22,10 |
| MG | 4 | 32 | 10 | 8 | 2,444 | [2,421 a 2,467] | 1,33 | 5,189 | 16,21 |
| FT | 5 | 1 | 10 | 1 | 21,494 | [21,419 a 21,569] | 0,49 | 1,000 | 100,00 |
| FT | 5 | 2 | 10 | 1 | 11,794 | [11,743 a 11,845] | 0,60 | 1,822 | 91,12 |
| FT | 5 | 4 | 10 | 1 | 8,509 | [8,480 a 8,538] | 0,47 | 2,526 | 63,15 |
| FT | 5 | 8 | 10 | 2 | 25,196 | [24,583 a 25,809] | 3,40 | 0,853 | 10,66 |
| FT | 5 | 16 | 10 | 4 | 24,493 | [22,852 a 26,134] | 9,37 | 0,878 | 5,48 |
| FT | 5 | 32 | 10 | 8 | 19,033 | [15,028 a 23,038] | 29,42 | 1,129 | 3,53 |
| LU | 6 | 1 | 10 | 1 | 189,196 | [188,149 a 190,243] | 0,77 | 1,000 | 100,00 |
| LU | 6 | 2 | 10 | 1 | 87,929 | [87,515 a 88,343] | 0,66 | 2,152 | 107,58 |
| LU | 6 | 4 | 10 | 1 | 54,280 | [54,070 a 54,490] | 0,54 | 3,486 | 87,14 |
| LU | 6 | 8 | 10 | 2 | 47,144 | [46,288 a 48,000] | 2,54 | 4,013 | 50,16 |
| LU | 6 | 16 | 10 | 4 | 42,486 | [41,674 a 43,298] | 2,67 | 4,453 | 27,83 |
| LU | 6 | 32 | 10 | 8 | 28,857 | [28,757 a 28,957] | 0,48 | 6,556 | 20,49 |
| BT | 10 | 1 | 10 | 1 | 296,976 | [296,321 a 297,631] | 0,31 | 1,000 | 100,00 |
| BT | 10 | 4 | 10 | 1 | 81,642 | [80,796 a 82,488] | 1,45 | 3,638 | 90,94 |
| BT | 10 | 9 | 10 | 3 | 96,211 | [95,546 a 96,876] | 0,97 | 3,087 | 34,30 |
| BT | 10 | 16 | 10 | 4 | 81,392 | [80,930 a 81,854] | 0,79 | 3,649 | 22,80 |
| BT | 10 | 25 | 10 | 7 | 62,725 | [62,496 a 62,954] | 0,51 | 4,735 | 18,94 |
| SP | 9 | 1 | 10 | 1 | 446,548 | [438,160 a 454,936] | 2,63 | 1,000 | 100,00 |
| SP | 9 | 4 | 10 | 1 | 168,466 | [164,904 a 172,028] | 2,96 | 2,651 | 66,27 |
| SP | 9 | 9 | 10 | 3 | 160,404 | [159,912 a 160,896] | 0,43 | 2,784 | 30,93 |
| SP | 9 | 16 | 10 | 4 | 118,102 | [116,462 a 119,742] | 1,94 | 3,781 | 23,63 |
| SP | 9 | 25 | 10 | 7 | 113,178 | [108,876 a 117,480] | 5,31 | 3,946 | 15,78 |

EP preserva boa escalabilidade até 32 processos, com speedup de cerca de 30. IS e FT têm as menores médias com quatro processos em um nó e regressão na transição para oito processos em dois nós. IS permanece mais lento que a referência de um processo em todos os níveis distribuídos. FT recupera parte do desempenho com 32 processos, com dispersão elevada. CG tem mínimo com oito processos e regressão com 16 e 32. MG e LU atingem seus menores tempos com 32 processos, com eficiência inferior à de EP. BT regride de quatro para nove processos e melhora até 25. SP melhora ao longo da grade, com ganho menor entre 16 e 25 processos. As razões usam a referência de um processo de cada benchmark. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

As médias incluem valores de eficiência acima de 100% neste snapshot. Os casos são EP em 2 p (100,011%), CG em 2 p (125,019%), CG em 4 p (106,573%), LU em 2 p (107,585%). O ponto de EP muito próximo de 100% é sensível à resolução do cronômetro exibido. Em CG e LU, localidade e comportamento de memória são hipóteses que exigem contadores e perfil por fase.

## Ambiente, anomalias e limites de interpretação

Os snapshots documentam Armbian bullseye em AArch64 nos nós de cálculo, kernel 6.1.11-meson64, Open MPI 4.1.0, GCC/GFortran 10.2.1 e NPB 3.4.4. H7 é o nome comercial, e `SEI Robotics SEI610` é o modelo registrado no device tree. A plataforma SM1 consta do registro do coordenador. As contagens por velocidade de enlace e modo duplex são {(100, 'full'): 72} nos registros por equipamento e coleta. A identificação do switch consta das informações manuais. [Ambiente SP, seções 2.1–3.3](../../../raw/SP/npb_9_SP_A_ambiente.txt#L46-L916)

A capacidade é de quatro slots por host e 32 na alocação. O número de nós observado segue `ceil(p/4)` nas tentativas confirmadas. O layout é recuperado por rank, host e núcleo a partir das representações de job e das linhas individuais de binding. A trilha por rank está em [ranks_mpi.csv](../tabelas/ranks_mpi.csv).

O teto CPUFreq documentado é 1.500 MHz com `ondemand`. O máximo informado pelo driver é 2.100 MHz. As frequências pontuais nos snapshots dos nós de cálculo incluem 1000, 1200, 1500 MHz. A RAM disponível mínima antes dos lançamentos varia entre 1519–1540 MB. A temperatura máxima prévia varia entre 72,3–84,7 °C. Os campos contemporâneos ao kernel ficam vazios com monitoramento desativado. As sondagens são agregados dos nós antes da execução, incluindo nós que podem estar ociosos para aquele np. A rede tem ping e contadores acumulados de abertura, sem vazão de cada tentativa no conjunto disponível. [Snapshot inicial de SP](../../../raw/SP/npb_9_SP_A_ambiente.txt#L950-L1165)

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

O protocolo tem um limite térmico prévio de 85 °C em SP e 80 °C nas outras campanhas desta auditoria. A validação usa o limite documentado de cada série.

O cenário com temperatura prévia de até **80 °C** usa o menor limite documentado e recalcula as médias e a referência de um processo sobre os registros abaixo ou no limite.

| NPB | p | n principal | n no cenário | Média principal (s) | Média no cenário (s) | S principal | S no cenário |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SP | 1 | 10 | 1 | 446,548 | 451,800 | 1,000 | 1,000 |
| SP | 4 | 10 | 1 | 168,466 | 174,600 | 2,651 | 2,588 |
| SP | 9 | 10 | 5 | 160,404 | 160,386 | 2,784 | 2,817 |
| SP | 16 | 10 | 1 | 118,102 | 117,540 | 3,781 | 3,844 |
| SP | 25 | 10 | 4 | 113,178 | 110,805 | 3,946 | 4,077 |

O recorte é posterior à coleta, desbalanceia os blocos e reduz a precisão. A associação com temperatura prévia fica confundida com posição temporal e outras condições da campanha.

A detecção por intervalo interquartil preserva todos os tempos válidos na amostra principal. Os casos de FT e SP abaixo ilustram a ocorrência de observações atípicas em diferentes posições das séries.

- **FT com 32 processos.** `5-0028` no bloco 5 registrou 34,87 s no NPB e 40,64 s de parede. A inicialização registrada pelo próprio FT foi 1,9084 s. A temperatura prévia máxima foi 76,6 °C, ante mediana de 75,8 °C nas demais repetições do grupo. [raw/FT/npb_5_FT_A.csv:29](../../../raw/FT/npb_5_FT_A.csv#L29) · [raw/FT/npb_5_FT_A_saidas.txt:6676](../../../raw/FT/npb_5_FT_A_saidas.txt#L6676)
- **SP com 16 processos.** `9-0041` no bloco 9 registrou 124,38 s no NPB e 128,74 s de parede. A temperatura prévia máxima foi 84,7 °C, ante mediana de 80,9 °C nas demais repetições do grupo. [raw/SP/npb_9_SP_A.csv:42](../../../raw/SP/npb_9_SP_A.csv#L42) · [raw/SP/npb_9_SP_A_saidas.txt:11238](../../../raw/SP/npb_9_SP_A_saidas.txt#L11238)
- **SP com 25 processos.** `9-0046` no bloco 10 registrou 130,16 s no NPB e 134,49 s de parede. A temperatura prévia máxima foi 84,0 °C, ante mediana de 80,9 °C nas demais repetições do grupo. [raw/SP/npb_9_SP_A.csv:47](../../../raw/SP/npb_9_SP_A.csv#L47) · [raw/SP/npb_9_SP_A_saidas.txt:12733](../../../raw/SP/npb_9_SP_A_saidas.txt#L12733)

As assinaturas de ambiente e os trechos estáveis documentados são compatíveis entre campanhas no snapshot inspecionado. Isso sustenta comparação de configuração dentro de cada série, sob as condições arquivadas. A amostragem disponível deixa indeterminados o pico de memória, a frequência efetiva, a temperatura durante o NPB, a saturação de enlace e o comportamento de cada rank sob carga. Também ficam indeterminados efeitos causais de aquecimento, contenção e diferenças da vazão, mecanismos de superlinearidade, desempenho de outros problemas e viabilidade econômica. Custo, energia e resfriamento requerem dados próprios.

Custos de redistribuição e sincronização são hipóteses para as regressões de IS e FT. Localidade, comunicação e mudanças de decomposição podem contribuir para o comportamento de CG, LU, BT e SP. Na campanha, a transição entre nós também altera o número de processos. Isolar o efeito de rede exige observar alocações distintas com o mesmo número de processos e medir fases, comunicação e condições dos nós sob carga.

## Limites de reprodução experimental

Os registros identificam o coletor v5.4, os binários e as configurações por seus hashes declarados. A reprodução da coleta depende da obtenção do código do coletor, da imagem usada e dos arquivos integrais de compilação. A explicação causal das anomalias requer medições por fase e observações de temperatura, frequência, memória e comunicação durante a execução.

## Artefatos da auditoria

- [Exploração e dicionário dos dados](01_exploracao_dos_arquivos.md) · [Auditoria experimental](02_auditoria_experimental.md)
- [Análise estatística e sensibilidade](03_analise_estatistica.md) · [Diagnóstico por benchmark](04_diagnostico_dos_benchmarks.md)
- [Execuções consolidadas](../tabelas/execucoes_consolidadas.csv) · [Cobertura](../tabelas/cobertura_experimental.csv) · [Ocorrências com fontes](../tabelas/inconsistencias.csv)
- [Estatísticas](../tabelas/estatisticas_descritivas.csv) · [Speedup e eficiência](../tabelas/speedup_eficiencia.csv) · [Cenários de sensibilidade](../tabelas/sensibilidade.csv)
- [Ambientes](../tabelas/ambientes.csv) · [Snapshots por nó](../tabelas/nos_ambiente.csv) · [Observações atípicas](../tabelas/observacoes_atipicas.csv)
- [Hashes da entrada](../manifestos/dados_entrada.json) · [Versão do código e dependências](../manifestos/reproducibilidade.json) · [Guia da auditoria](../../../../scripts/analise/auditoria-npb/README.md)

- Tempo médio e intervalo t de 95% · [PDF](../graficos/tempo_medio_npb.pdf) · [PNG](../graficos/tempo_medio_npb.png)
- Speedup e referência ideal · [PDF](../graficos/speedup.pdf) · [PNG](../graficos/speedup.png)
- Eficiência paralela · [PDF](../graficos/eficiencia_paralela.pdf) · [PNG](../graficos/eficiencia_paralela.png)
- Distribuição dos tempos · [PDF](../graficos/distribuicao_tempos.pdf) · [PNG](../graficos/distribuicao_tempos.png)
- Completude experimental · [PDF](../graficos/completude_experimental.pdf) · [PNG](../graficos/completude_experimental.png)
- Variação dos tempos por bloco · [PDF](../graficos/comportamento_temporal.pdf) · [PNG](../graficos/comportamento_temporal.png)
