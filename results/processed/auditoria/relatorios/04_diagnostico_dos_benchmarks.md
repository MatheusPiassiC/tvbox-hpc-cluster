# 04 — Diagnóstico dos benchmarks

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

A comparação usa tempo relativo ao baseline de cada carga. As transições mostram os nós efetivamente mapeados. Mudanças em p e número de nós também mudam a decomposição do trabalho. A atribuição causal exige medir fases, comunicação e condições dos nós durante a execução.

## EP

### Observações

A menor média foi **0,936 s em 32 processos**, redução de **96,69%** frente a 28,261 s em um processo. O maior speedup foi **30,193×** em 32 processos. A eficiência foi 94,35% no ponto de menor média e 94,35% no maior np (32). A maior dispersão relativa foi CV de 2,15% em 32 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 28,261 | 0,11 | 1,000 | 100,00 | — | — |
| 2 | 1 | 14,129 | 0,32 | 2,000 | 100,01 | 50,01 | intranó · melhora |
| 4 | 1 | 7,083 | 0,31 | 3,990 | 99,75 | 49,87 | intranó · melhora |
| 8 | 2 | 3,581 | 0,92 | 7,892 | 98,65 | 49,44 | mudança de nós · melhora |
| 16 | 4 | 1,814 | 0,87 | 15,579 | 97,37 | 49,34 | mudança de nós · melhora |
| 32 | 8 | 0,936 | 2,15 | 30,193 | 94,35 | 48,40 | mudança de nós · melhora |

As médias comparáveis diminuem nas transições observadas, com ganhos relativos de magnitude variada. O ponto mais influente entre os sinalizados, `1-0018`, tem 0,990 s em 32 processos. Mantido na análise, ele produz uma diferença de -0,64% na média se omitido apenas na sensibilidade individual. [raw/EP/npb_1_EP_A_saidas.txt:4314](../../../raw/EP/npb_1_EP_A_saidas.txt#L4314)

### Hipótese para investigação

A separação das amostras do gerador em trabalho predominantemente local é compatível com a escalabilidade observada e com o ganho contínuo ao adicionar nós. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Tempos de computação, inicialização e reduções em separado, além de contadores de CPU e registros de frequência sob carga.


## IS

### Observações

A menor média foi **0,826 s em 4 processos**, redução de **65,73%** frente a 2,410 s em um processo. O maior speedup foi **2,918×** em 4 processos. A eficiência foi 72,94% no ponto de menor média e 1,60% no maior np (32). A maior dispersão relativa foi CV de 2,72% em 8 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2,410 | 1,05 | 1,000 | 100,00 | — | — |
| 2 | 1 | 1,311 | 1,11 | 1,838 | 91,91 | 45,60 | intranó · melhora |
| 4 | 1 | 0,826 | 1,17 | 2,918 | 72,94 | 36,99 | intranó · melhora |
| 8 | 2 | 8,180 | 2,72 | 0,295 | 3,68 | -890,31 | mudança de nós · piora |
| 16 | 4 | 8,251 | 2,21 | 0,292 | 1,83 | -0,87 | mudança de nós · piora |
| 32 | 8 | 4,698 | 1,59 | 0,513 | 1,60 | 43,06 | mudança de nós · melhora |

As médias aumentam nas transições 4→8 p (890,31% de aumento no tempo), 8→16 p (0,87% de aumento no tempo). O ponto mais influente entre os sinalizados, `2-0005`, tem 1,350 s em 2 processos. Mantido na análise, ele produz uma diferença de -0,33% na média se omitido apenas na sensibilidade individual. [raw/IS/npb_2_IS_A_saidas.txt:1274](../../../raw/IS/npb_2_IS_A_saidas.txt#L1274)

### Hipótese para investigação

A ordenação de inteiros envolve redistribuição de chaves. A mudança de domínio de memória e de comunicação pode contribuir para a elevação do tempo em múltiplos nós. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Perfil das chamadas MPI por fase, volumes e tempos de troca de chaves, desempenho por enlace e medições no mesmo número de processos com arranjos diferentes.


## CG

### Observações

A menor média foi **3,670 s em 8 processos**, redução de **77,66%** frente a 16,425 s em um processo. O maior speedup foi **4,475×** em 8 processos. A eficiência foi 55,94% no ponto de menor média e 10,20% no maior np (32). A maior dispersão relativa foi CV de 1,08% em 16 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 16,425 | 0,42 | 1,000 | 100,00 | — | — |
| 2 | 1 | 6,569 | 0,42 | 2,500 | 125,02 | 60,01 | intranó · melhora |
| 4 | 1 | 3,853 | 0,49 | 4,263 | 106,57 | 41,35 | intranó · melhora |
| 8 | 2 | 3,670 | 0,83 | 4,475 | 55,94 | 4,75 | mudança de nós · melhora |
| 16 | 4 | 4,566 | 1,08 | 3,597 | 22,48 | -24,41 | mudança de nós · piora |
| 32 | 8 | 5,031 | 0,98 | 3,265 | 10,20 | -10,18 | mudança de nós · piora |

As médias aumentam nas transições 8→16 p (24,41% de aumento no tempo), 16→32 p (10,18% de aumento no tempo). O ponto mais influente entre os sinalizados, `3-0046`, tem 6,630 s em 2 processos. Mantido na análise, ele produz uma diferença de -0,10% na média se omitido apenas na sensibilidade individual. [raw/CG/npb_3_CG_A_saidas.txt:10633](../../../raw/CG/npb_3_CG_A_saidas.txt#L10633)

### Hipótese para investigação

Localidade de cache e memória pode contribuir para ganhos intranó. Os acessos irregulares e as reduções podem limitar ganhos quando a distribuição abrange mais nós. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Contadores de cache, ciclos, banda de memória e tempos de computação esparsa e de reduções MPI, com frequência sob carga.


## MG

### Observações

A menor média foi **2,444 s em 32 processos**, redução de **80,73%** frente a 12,681 s em um processo. O maior speedup foi **5,189×** em 32 processos. A eficiência foi 16,21% no ponto de menor média e 16,21% no maior np (32). A maior dispersão relativa foi CV de 4,04% em 8 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 12,681 | 1,07 | 1,000 | 100,00 | — | — |
| 2 | 1 | 9,274 | 1,41 | 1,367 | 68,37 | 26,87 | intranó · melhora |
| 4 | 1 | 4,700 | 0,82 | 2,698 | 67,45 | 49,32 | intranó · melhora |
| 8 | 2 | 4,297 | 4,04 | 2,951 | 36,89 | 8,57 | mudança de nós · melhora |
| 16 | 4 | 3,587 | 2,53 | 3,535 | 22,10 | 16,52 | mudança de nós · melhora |
| 32 | 8 | 2,444 | 1,33 | 5,189 | 16,21 | 31,87 | mudança de nós · melhora |

As médias comparáveis diminuem nas transições observadas, com ganhos relativos de magnitude variada. O ponto mais influente entre os sinalizados, `4-0047`, tem 3,900 s em 8 processos. Mantido na análise, ele produz uma diferença de 1,03% na média se omitido apenas na sensibilidade individual. [raw/MG/npb_4_MG_A_saidas.txt:10834](../../../raw/MG/npb_4_MG_A_saidas.txt#L10834)

### Hipótese para investigação

A hierarquia de malhas combina transferências de memória e mensagens de curto e longo alcance. A relação entre computação local e comunicação pode variar por nível e decomposição. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Tempos por nível do multigrid, tráfego de halo, contadores de memória e origem das diferenças dentro de um bloco.


## FT

### Observações

A menor média foi **8,509 s em 4 processos**, redução de **60,41%** frente a 21,494 s em um processo. O maior speedup foi **2,526×** em 4 processos. A eficiência foi 63,15% no ponto de menor média e 3,53% no maior np (32). A maior dispersão relativa foi CV de 29,42% em 32 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 21,494 | 0,49 | 1,000 | 100,00 | — | — |
| 2 | 1 | 11,794 | 0,60 | 1,822 | 91,12 | 45,13 | intranó · melhora |
| 4 | 1 | 8,509 | 0,47 | 2,526 | 63,15 | 27,85 | intranó · melhora |
| 8 | 2 | 25,196 | 3,40 | 0,853 | 10,66 | -196,11 | mudança de nós · piora |
| 16 | 4 | 24,493 | 9,37 | 0,878 | 5,48 | 2,79 | mudança de nós · melhora |
| 32 | 8 | 19,033 | 29,42 | 1,129 | 3,53 | 22,29 | mudança de nós · melhora |

As médias aumentam nas transições 4→8 p (196,11% de aumento no tempo). O ponto mais influente entre os sinalizados, `5-0028`, tem 34,870 s em 32 processos. Mantido na análise, ele produz uma diferença de -9,25% na média se omitido apenas na sensibilidade individual. [raw/FT/npb_5_FT_A_saidas.txt:6676](../../../raw/FT/npb_5_FT_A_saidas.txt#L6676)

### Hipótese para investigação

As transposições da FFT 3D envolvem redistribuições coletivas. Custos de comunicação, sincronização e diferenças na decomposição são compatíveis com o salto de 4 para 8 processos e com a recuperação parcial em 32. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Tempos por fase da FFT, duração e volume de coletivas, contadores de rede sincronizados à execução e repetição instrumentada da configuração de 32 processos.


## LU

### Observações

A menor média foi **28,857 s em 32 processos**, redução de **84,75%** frente a 189,196 s em um processo. O maior speedup foi **6,556×** em 32 processos. A eficiência foi 20,49% no ponto de menor média e 20,49% no maior np (32). A maior dispersão relativa foi CV de 2,67% em 16 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 189,196 | 0,77 | 1,000 | 100,00 | — | — |
| 2 | 1 | 87,929 | 0,66 | 2,152 | 107,58 | 53,52 | intranó · melhora |
| 4 | 1 | 54,280 | 0,54 | 3,486 | 87,14 | 38,27 | intranó · melhora |
| 8 | 2 | 47,144 | 2,54 | 4,013 | 50,16 | 13,15 | mudança de nós · melhora |
| 16 | 4 | 42,486 | 2,67 | 4,453 | 27,83 | 9,88 | mudança de nós · melhora |
| 32 | 8 | 28,857 | 0,48 | 6,556 | 20,49 | 32,08 | mudança de nós · melhora |

As médias comparáveis diminuem nas transições observadas, com ganhos relativos de magnitude variada. O ponto mais influente entre os sinalizados, `6-0008`, tem 89,360 s em 2 processos. Mantido na análise, ele produz uma diferença de -0,18% na média se omitido apenas na sensibilidade individual. [raw/LU/npb_6_LU_A_saidas.txt:1848](../../../raw/LU/npb_6_LU_A_saidas.txt#L1848)

### Hipótese para investigação

O solver Gauss–Seidel inferior–superior envolve dependências entre subdomínios. Localidade intranó pode contribuir para a eficiência em dois processos. Os ganhos distribuídos podem depender da granularidade e da troca entre fronteiras. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Contadores de memória/cache, tempos por fase do solver, comunicação de fronteira e frequência por núcleo em execuções repetidas.


## BT

### Observações

A menor média foi **62,725 s em 25 processos**, redução de **78,88%** frente a 296,976 s em um processo. O maior speedup foi **4,735×** em 25 processos. A eficiência foi 18,94% no ponto de menor média e 18,94% no maior np (25). A maior dispersão relativa foi CV de 1,45% em 4 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 296,976 | 0,31 | 1,000 | 100,00 | — | — |
| 4 | 1 | 81,642 | 1,45 | 3,638 | 90,94 | 72,51 | intranó · melhora |
| 9 | 3 | 96,211 | 0,97 | 3,087 | 34,30 | -17,84 | mudança de nós · piora |
| 16 | 4 | 81,392 | 0,79 | 3,649 | 22,80 | 15,40 | mudança de nós · melhora |
| 25 | 7 | 62,725 | 0,51 | 4,735 | 18,94 | 22,93 | mudança de nós · melhora |

As médias aumentam nas transições 4→9 p (17,84% de aumento no tempo). O ponto mais influente entre os sinalizados, `10-0036`, tem 84,480 s em 4 processos. Mantido na análise, ele produz uma diferença de -0,39% na média se omitido apenas na sensibilidade individual. [raw/BT/npb_10_BT_A_saidas.txt:9356](../../../raw/BT/npb_10_BT_A_saidas.txt#L9356)

### Hipótese para investigação

A decomposição do solver por blocos e a troca de fronteiras podem contribuir para a regressão ao passar a três nós. A retomada em mais nós é compatível com um novo equilíbrio entre redução do trabalho local e comunicação. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Tamanho das partições, ociosidade por rank, temporização de fases e mensagens e, se o desenho permitir, comparações controladas de mapeamento para o mesmo np.


## SP

### Observações

A menor média foi **113,178 s em 25 processos**, redução de **74,65%** frente a 446,548 s em um processo. O maior speedup foi **3,946×** em 25 processos. A eficiência foi 15,78% no ponto de menor média e 15,78% no maior np (25). A maior dispersão relativa foi CV de 5,31% em 25 processos.

| p | Nós | Média (s) | CV (%) | S | E (%) | Ganho vs. anterior (%) | Transição |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 446,548 | 2,63 | 1,000 | 100,00 | — | — |
| 4 | 1 | 168,466 | 2,96 | 2,651 | 66,27 | 62,27 | intranó · melhora |
| 9 | 3 | 160,404 | 0,43 | 2,784 | 30,93 | 4,79 | mudança de nós · melhora |
| 16 | 4 | 118,102 | 1,94 | 3,781 | 23,63 | 26,37 | mudança de nós · melhora |
| 25 | 7 | 113,178 | 5,31 | 3,946 | 15,78 | 4,17 | mudança de nós · melhora |

As médias comparáveis diminuem nas transições observadas, com ganhos relativos de magnitude variada. O ponto mais influente entre os sinalizados, `9-0046`, tem 130,160 s em 25 processos. Mantido na análise, ele produz uma diferença de -1,67% na média se omitido apenas na sensibilidade individual. [raw/SP/npb_9_SP_A_saidas.txt:12733](../../../raw/SP/npb_9_SP_A_saidas.txt#L12733)

### Hipótese para investigação

O solver pentadiagonal escalar tem troca de dados entre partições. Diferenças de decomposição e condições térmicas durante a carga são hipóteses para testar diante da dispersão nas maiores configurações. [Especificação dos NAS Parallel Benchmarks, NASA](https://nas.nasa.gov/software/npb.html)

### Evidência adicional necessária

Temperatura por sensor e frequência por núcleo durante o kernel, tempos por fase e repetições em blocos com a mesma condição térmica inicial.


## Casos prioritários com rastreabilidade

- **FT com 32 processos.** `5-0028` no bloco 5 registrou 34,87 s no NPB e 40,64 s de parede. A inicialização registrada pelo próprio FT foi 1,9084 s. A temperatura prévia máxima foi 76,6 °C, ante mediana de 75,8 °C nas demais repetições do grupo. [raw/FT/npb_5_FT_A.csv:29](../../../raw/FT/npb_5_FT_A.csv#L29) · [raw/FT/npb_5_FT_A_saidas.txt:6676](../../../raw/FT/npb_5_FT_A_saidas.txt#L6676)
- **SP com 16 processos.** `9-0041` no bloco 9 registrou 124,38 s no NPB e 128,74 s de parede. A temperatura prévia máxima foi 84,7 °C, ante mediana de 80,9 °C nas demais repetições do grupo. [raw/SP/npb_9_SP_A.csv:42](../../../raw/SP/npb_9_SP_A.csv#L42) · [raw/SP/npb_9_SP_A_saidas.txt:11238](../../../raw/SP/npb_9_SP_A_saidas.txt#L11238)
- **SP com 25 processos.** `9-0046` no bloco 10 registrou 130,16 s no NPB e 134,49 s de parede. A temperatura prévia máxima foi 84,0 °C, ante mediana de 80,9 °C nas demais repetições do grupo. [raw/SP/npb_9_SP_A.csv:47](../../../raw/SP/npb_9_SP_A.csv#L47) · [raw/SP/npb_9_SP_A_saidas.txt:12733](../../../raw/SP/npb_9_SP_A_saidas.txt#L12733)

FT em 32 processos apresenta uma observação lenta no meio da campanha. SP tem pontos mais lentos nos blocos finais e uma condição prévia mais permissiva. Esses padrões orientam investigação, com as leituras prévias e a posição dos blocos como evidência descritiva. As temperaturas durante esses kernels são desconhecidas.

[Speedup por configuração](../tabelas/speedup_eficiencia.csv) · [Dispersão e IC](../tabelas/estatisticas_descritivas.csv) · [Posição temporal](../tabelas/comportamento_temporal.csv)
