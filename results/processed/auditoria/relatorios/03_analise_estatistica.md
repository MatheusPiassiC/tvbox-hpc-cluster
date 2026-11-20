# 03 — Análise estatística

Foram examinados **32 arquivos** em 8 campanhas. Das **46 configurações** de referência, 46 foram observadas e 46 têm dez posições lógicas confirmadas em alguma campanha. A meta documentada é 460 repetições válidas. Há 460 registros nos planos, 460 registros de resultados e 460 blocos TXT. Foram agrupadas **460 tentativas**, das quais 460 aceitas pelo coletor (460 linhas CSV com `VALIDA`). A auditoria confirmou **460 válidas**, **0 inválidas**, **0 inconclusivas** e **0 conflitantes**. A amostra principal contém **460 tempos**.

A série usa a média aritmética de `Time in seconds` das tentativas confirmadas. Os quartis usam interpolação linear, tipo 7 do NumPy. O desvio-padrão e a variância amostrais usam divisor `n−1`. O coeficiente de variação é `100 × s/média`. O IC de 95% bilateral para a média é `média ± t(0,975; n−1) × s/√n` com n observado, definido a partir de duas medidas. Uma medida isolada sustenta média e mediana descritivas. Um grupo vazio tem métricas ausentes. Amostras da ordem de dez têm pouca resolução para caracterizar a forma da distribuição. A interpretação nominal do IC supõe observações independentes e uma aproximação distributiva adequada. [NIST/SEMATECH](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)

Os intervalos da tabela referem-se ao tempo médio. O speedup usa `S(p) = média(1)/média(p)` e a eficiência é `100 × S(p)/p` em porcentagem. A referência precisa ser comparável em plataforma, binário, tamanho, iterações, versão, compilação e parâmetros MPI na mesma campanha. O cálculo deixa o speedup vazio se essa evidência está ausente. O ideal é `p`, e `desvio_speedup_do_ideal` registra `S(p) − p`. A análise apresenta estimativas pontuais das razões. Os ICs dos tempos e suas sobreposições servem à inspeção descritiva.

## Estatísticas por configuração

| NPB | Camp. | p | n | Média (s) | Mediana (s) | DP (s) | Variância (s²) | Mín.–máx. (s) | Q1–Q3 (s) | IQR (s) | CV (%) | IC 95% (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP | 1 | 1 | 10 | 28,261 | 28,255 | 0,030 | 0,000921 | 28,230–28,320 | 28,240–28,260 | 0,020 | 0,11 | [28,239 a 28,283] |
| EP | 1 | 2 | 10 | 14,129 | 14,115 | 0,045 | 0,002054 | 14,090–14,240 | 14,100–14,130 | 0,030 | 0,32 | [14,097 a 14,161] |
| EP | 1 | 4 | 10 | 7,083 | 7,075 | 0,022 | 0,000490 | 7,070–7,140 | 7,070–7,080 | 0,010 | 0,31 | [7,067 a 7,099] |
| EP | 1 | 8 | 10 | 3,581 | 3,570 | 0,033 | 0,001077 | 3,540–3,640 | 3,570–3,578 | 0,008 | 0,92 | [3,558 a 3,604] |
| EP | 1 | 16 | 10 | 1,814 | 1,815 | 0,016 | 0,000249 | 1,780–1,830 | 1,810–1,828 | 0,018 | 0,87 | [1,803 a 1,825] |
| EP | 1 | 32 | 10 | 0,936 | 0,930 | 0,020 | 0,000404 | 0,920–0,990 | 0,930–0,938 | 0,007 | 2,15 | [0,922 a 0,950] |
| IS | 2 | 1 | 10 | 2,410 | 2,400 | 0,025 | 0,000644 | 2,390–2,480 | 2,400–2,410 | 0,010 | 1,05 | [2,392 a 2,428] |
| IS | 2 | 2 | 10 | 1,311 | 1,310 | 0,014 | 0,000210 | 1,300–1,350 | 1,302–1,310 | 0,008 | 1,11 | [1,301 a 1,321] |
| IS | 2 | 4 | 10 | 0,826 | 0,820 | 0,010 | 0,000093 | 0,820–0,850 | 0,820–0,830 | 0,010 | 1,17 | [0,819 a 0,833] |
| IS | 2 | 8 | 10 | 8,180 | 8,180 | 0,222 | 0,049333 | 7,910–8,600 | 8,000–8,308 | 0,308 | 2,72 | [8,021 a 8,339] |
| IS | 2 | 16 | 10 | 8,251 | 8,295 | 0,182 | 0,033121 | 7,910–8,510 | 8,123–8,328 | 0,205 | 2,21 | [8,121 a 8,381] |
| IS | 2 | 32 | 10 | 4,698 | 4,710 | 0,075 | 0,005551 | 4,580–4,810 | 4,675–4,728 | 0,053 | 1,59 | [4,645 a 4,751] |
| CG | 3 | 1 | 10 | 16,425 | 16,395 | 0,069 | 0,004717 | 16,360–16,550 | 16,380–16,448 | 0,068 | 0,42 | [16,376 a 16,474] |
| CG | 3 | 2 | 10 | 6,569 | 6,560 | 0,028 | 0,000766 | 6,540–6,630 | 6,550–6,578 | 0,028 | 0,42 | [6,549 a 6,589] |
| CG | 3 | 4 | 10 | 3,853 | 3,845 | 0,019 | 0,000357 | 3,830–3,890 | 3,840–3,868 | 0,028 | 0,49 | [3,839 a 3,867] |
| CG | 3 | 8 | 10 | 3,670 | 3,665 | 0,031 | 0,000933 | 3,630–3,720 | 3,650–3,688 | 0,038 | 0,83 | [3,648 a 3,692] |
| CG | 3 | 16 | 10 | 4,566 | 4,545 | 0,049 | 0,002449 | 4,530–4,670 | 4,530–4,595 | 0,065 | 1,08 | [4,531 a 4,601] |
| CG | 3 | 32 | 10 | 5,031 | 5,000 | 0,049 | 0,002432 | 4,980–5,100 | 4,992–5,080 | 0,088 | 0,98 | [4,996 a 5,066] |
| MG | 4 | 1 | 10 | 12,681 | 12,665 | 0,136 | 0,018521 | 12,500–12,920 | 12,582–12,780 | 0,198 | 1,07 | [12,584 a 12,778] |
| MG | 4 | 2 | 10 | 9,274 | 9,310 | 0,131 | 0,017138 | 9,080–9,490 | 9,152–9,360 | 0,207 | 1,41 | [9,180 a 9,368] |
| MG | 4 | 4 | 10 | 4,700 | 4,690 | 0,039 | 0,001489 | 4,630–4,760 | 4,680–4,725 | 0,045 | 0,82 | [4,672 a 4,728] |
| MG | 4 | 8 | 10 | 4,297 | 4,340 | 0,174 | 0,030134 | 3,900–4,460 | 4,235–4,415 | 0,180 | 4,04 | [4,173 a 4,421] |
| MG | 4 | 16 | 10 | 3,587 | 3,555 | 0,091 | 0,008223 | 3,450–3,730 | 3,532–3,655 | 0,123 | 2,53 | [3,522 a 3,652] |
| MG | 4 | 32 | 10 | 2,444 | 2,445 | 0,032 | 0,001049 | 2,400–2,490 | 2,415–2,465 | 0,050 | 1,33 | [2,421 a 2,467] |
| FT | 5 | 1 | 10 | 21,494 | 21,470 | 0,105 | 0,011116 | 21,400–21,750 | 21,418–21,520 | 0,102 | 0,49 | [21,419 a 21,569] |
| FT | 5 | 2 | 10 | 11,794 | 11,815 | 0,071 | 0,005027 | 11,660–11,870 | 11,742–11,850 | 0,107 | 0,60 | [11,743 a 11,845] |
| FT | 5 | 4 | 10 | 8,509 | 8,510 | 0,040 | 0,001588 | 8,450–8,590 | 8,482–8,527 | 0,045 | 0,47 | [8,480 a 8,538] |
| FT | 5 | 8 | 10 | 25,196 | 25,005 | 0,856 | 0,733227 | 24,080–26,900 | 24,582–25,782 | 1,200 | 3,40 | [24,583 a 25,809] |
| FT | 5 | 16 | 10 | 24,493 | 24,300 | 2,294 | 5,264534 | 20,660–29,180 | 23,473–24,915 | 1,442 | 9,37 | [22,852 a 26,134] |
| FT | 5 | 32 | 10 | 19,033 | 17,590 | 5,599 | 31,349246 | 16,320–34,870 | 16,793–17,900 | 1,107 | 29,42 | [15,028 a 23,038] |
| LU | 6 | 1 | 10 | 189,196 | 189,520 | 1,463 | 2,141182 | 187,030–191,270 | 187,823–190,332 | 2,510 | 0,77 | [188,149 a 190,243] |
| LU | 6 | 2 | 10 | 87,929 | 87,935 | 0,579 | 0,334766 | 87,330–89,360 | 87,535–88,032 | 0,498 | 0,66 | [87,515 a 88,343] |
| LU | 6 | 4 | 10 | 54,280 | 54,190 | 0,293 | 0,086022 | 53,940–54,720 | 54,058–54,558 | 0,500 | 0,54 | [54,070 a 54,490] |
| LU | 6 | 8 | 10 | 47,144 | 46,700 | 1,196 | 1,430804 | 45,930–48,860 | 46,175–48,350 | 2,175 | 2,54 | [46,288 a 48,000] |
| LU | 6 | 16 | 10 | 42,486 | 42,380 | 1,135 | 1,288271 | 41,010–44,270 | 41,812–42,973 | 1,160 | 2,67 | [41,674 a 43,298] |
| LU | 6 | 32 | 10 | 28,857 | 28,885 | 0,140 | 0,019579 | 28,620–29,020 | 28,800–28,957 | 0,157 | 0,48 | [28,757 a 28,957] |
| BT | 10 | 1 | 10 | 296,976 | 297,240 | 0,915 | 0,838004 | 295,530–298,210 | 296,230–297,647 | 1,417 | 0,31 | [296,321 a 297,631] |
| BT | 10 | 4 | 10 | 81,642 | 81,685 | 1,183 | 1,400084 | 79,990–84,480 | 81,017–81,790 | 0,772 | 1,45 | [80,796 a 82,488] |
| BT | 10 | 9 | 10 | 96,211 | 96,240 | 0,930 | 0,864988 | 94,720–97,660 | 95,938–96,853 | 0,915 | 0,97 | [95,546 a 96,876] |
| BT | 10 | 16 | 10 | 81,392 | 81,410 | 0,646 | 0,417884 | 80,190–82,290 | 81,198–81,650 | 0,453 | 0,79 | [80,930 a 81,854] |
| BT | 10 | 25 | 10 | 62,725 | 62,695 | 0,320 | 0,102561 | 62,330–63,230 | 62,500–62,888 | 0,388 | 0,51 | [62,496 a 62,954] |
| SP | 9 | 1 | 10 | 446,548 | 451,875 | 11,725 | 137,474729 | 426,080–457,570 | 437,327–453,210 | 15,883 | 2,63 | [438,160 a 454,936] |
| SP | 9 | 4 | 10 | 168,466 | 167,900 | 4,979 | 24,789449 | 162,520–175,550 | 164,183–173,097 | 8,915 | 2,96 | [164,904 a 172,028] |
| SP | 9 | 9 | 10 | 160,404 | 160,375 | 0,688 | 0,473160 | 159,460–161,710 | 160,080–160,695 | 0,615 | 0,43 | [159,912 a 160,896] |
| SP | 9 | 16 | 10 | 118,102 | 117,525 | 2,292 | 5,252684 | 116,620–124,380 | 116,905–117,862 | 0,957 | 1,94 | [116,462 a 119,742] |
| SP | 9 | 25 | 10 | 113,178 | 111,415 | 6,014 | 36,162507 | 110,220–130,160 | 110,925–111,817 | 0,892 | 5,31 | [108,876 a 117,480] |

A tabela [estatisticas_tempo_parede.csv](../tabelas/estatisticas_tempo_parede.csv) conserva a duração externa em uma série própria, sobre o mesmo filtro de elegibilidade e com n de durações efetivamente registradas.

## Escalabilidade

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

O desempenho com eficiência observada acima de 100% aparece na tabela seguinte. Localidade de cache e memória, conduta da frequência e dispersão podem influir em razões de médias. Valores muito próximos de 100% também são sensíveis à resolução de 0,01 s emitida pelo resumo.

| NPB | p | S(p) | E(p) (%) | S(p) − p |
| --- | --- | --- | --- | --- |
| EP | 2 | 2,00021 | 100,011 | 0,00021 |
| CG | 2 | 2,50038 | 125,019 | 0,50038 |
| CG | 4 | 4,26291 | 106,573 | 0,26291 |
| LU | 2 | 2,15169 | 107,585 | 0,15169 |

## Dispersão e observações atípicas

As cercas de Tukey usam `Q1 − 1,5 × IQR` e `Q3 + 1,5 × IQR` quando há pelo menos quatro observações e IQR positivo. O teste exploratório usa desigualdade estrita com tolerância numérica de 10⁻¹⁰ s na fronteira. Os tempos confirmados continuam elegíveis independentemente desse sinalizador. CV de pelo menos 5% aparece em FT/16 p, FT/32 p, SP/25 p. A assimetria de Fisher–Pearson ajustada tem magnitude ≥ 1 em 19 configurações. Pontos muito próximos do centro em segundos podem ser detectados em séries de pequena dispersão ou resolução limitada. Consulte [estatisticas_descritivas.csv](../tabelas/estatisticas_descritivas.csv) e [observacoes_atipicas.csv](../tabelas/observacoes_atipicas.csv).

Foram sinalizadas **29 observações**, preservadas nas médias. A tabela lista as seis de maior impacto absoluto na média ao omitir uma observação por vez.

| NPB | p | Bloco | Execução | NPB (s) | Parede (s) | Média (s) | Média sem ponto (s) | Variação (%) | Temp. prévia (°C) | Mediana prévia das demais (°C) | Fontes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FT | 32 | 5 | 5-0028 | 34,870 | 40,640 | 19,033 | 17,273 | -9,25 | 76,6 | 75,8 | [raw/FT/npb_5_FT_A.csv:29](../../../raw/FT/npb_5_FT_A.csv#L29) · [raw/FT/npb_5_FT_A_saidas.txt:6676](../../../raw/FT/npb_5_FT_A_saidas.txt#L6676) |
| FT | 16 | 8 | 5-0043 | 29,180 | 36,580 | 24,493 | 23,972 | -2,13 | 77,0 | 75,9 | [raw/FT/npb_5_FT_A.csv:44](../../../raw/FT/npb_5_FT_A.csv#L44) · [raw/FT/npb_5_FT_A_saidas.txt:10274](../../../raw/FT/npb_5_FT_A_saidas.txt#L10274) |
| FT | 16 | 4 | 5-0019 | 20,660 | 27,210 | 24,493 | 24,919 | 1,74 | 75,9 | 76,2 | [raw/FT/npb_5_FT_A.csv:20](../../../raw/FT/npb_5_FT_A.csv#L20) · [raw/FT/npb_5_FT_A_saidas.txt:4566](../../../raw/FT/npb_5_FT_A_saidas.txt#L4566) |
| SP | 25 | 10 | 9-0046 | 130,160 | 134,490 | 113,178 | 111,291 | -1,67 | 84,0 | 80,9 | [raw/SP/npb_9_SP_A.csv:47](../../../raw/SP/npb_9_SP_A.csv#L47) · [raw/SP/npb_9_SP_A_saidas.txt:12733](../../../raw/SP/npb_9_SP_A_saidas.txt#L12733) |
| MG | 8 | 8 | 4-0047 | 3,900 | 9,350 | 4,297 | 4,341 | 1,03 | 73,5 | 74,0 | [raw/MG/npb_4_MG_A.csv:48](../../../raw/MG/npb_4_MG_A.csv#L48) · [raw/MG/npb_4_MG_A_saidas.txt:10834](../../../raw/MG/npb_4_MG_A_saidas.txt#L10834) |
| EP | 32 | 3 | 1-0018 | 0,990 | 4,810 | 0,936 | 0,930 | -0,64 | 72,9 | 73,2 | [raw/EP/npb_1_EP_A.csv:19](../../../raw/EP/npb_1_EP_A.csv#L19) · [raw/EP/npb_1_EP_A_saidas.txt:4314](../../../raw/EP/npb_1_EP_A_saidas.txt#L4314) |

## Ordem das execuções

A ordem verificada permite comparar a primeira repetição com as posteriores e metades com o mesmo tamanho, com descarte da medida central apenas nesse contraste descritivo para n ímpar. Usa-se ρ de Spearman entre bloco e tempo e r de Pearson entre tempos adjacentes quando há sequência consecutiva, n ≥ 4 e variação. A tabela mostra casos com |ρ| ≥ 0,55 ou diferença de pelo menos 3% na primeira medida ou entre metades. De 46 configurações com ordem, 22 começam acima da média seguinte e 24 abaixo. Há dependência temporal plausível. A ordem é entrelaçada com outros níveis em cada bloco e as condições mudam ao longo das campanhas. O protocolo documenta ausência de aquecimento específico e de reposição de tentativas. Consulte [comportamento_temporal.csv](../tabelas/comportamento_temporal.csv).

| NPB | p | n | Primeiro vs. seguintes (%) | Última vs. primeira metade (%) | ρ ordinal | r lag 1 |
| --- | --- | --- | --- | --- | --- | --- |
| IS | 1 | 10 | 3,24 | -0,50 | -0,125 | -0,227 |
| IS | 2 | 10 | 3,32 | -0,76 | -0,499 | -0,394 |
| FT | 2 | 10 | 0,25 | 0,58 | 0,573 | 0,218 |
| FT | 16 | 10 | 10,62 | 2,67 | -0,285 | -0,256 |
| FT | 32 | 10 | -11,67 | -16,67 | -0,030 | -0,123 |
| LU | 8 | 10 | -2,85 | 3,92 | 0,855 | 0,442 |
| LU | 16 | 10 | -3,85 | 0,29 | 0,358 | -0,049 |
| BT | 25 | 10 | -0,70 | 0,57 | 0,646 | -0,079 |
| SP | 4 | 10 | -3,29 | 2,44 | 0,576 | 0,402 |
| SP | 25 | 10 | -2,90 | 4,08 | 0,842 | 0,704 |

## Sensibilidade

Conservar as tentativas cujo único impedimento seria evidência incompleta de mapa ou afinidade, com conclusão numérica e posição unívocas, altera o n de 0 configurações. As perdas por conflito ou falha permanecem fora desse cenário. [Tabela de sensibilidade](../tabelas/sensibilidade.csv)

O cenário com temperatura prévia de até **80 °C** usa o menor limite documentado e recalcula as médias e a referência de um processo sobre os registros abaixo ou no limite.

| NPB | p | n principal | n no cenário | Média principal (s) | Média no cenário (s) | S principal | S no cenário |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SP | 1 | 10 | 1 | 446,548 | 451,800 | 1,000 | 1,000 |
| SP | 4 | 10 | 1 | 168,466 | 174,600 | 2,651 | 2,588 |
| SP | 9 | 10 | 5 | 160,404 | 160,386 | 2,784 | 2,817 |
| SP | 16 | 10 | 1 | 118,102 | 117,540 | 3,781 | 3,844 |
| SP | 25 | 10 | 4 | 113,178 | 110,805 | 3,946 | 4,077 |

O recorte é posterior à coleta, desbalanceia os blocos e reduz a precisão. A associação com temperatura prévia fica confundida com posição temporal e outras condições da campanha.

## Figuras exploratórias

Os painéis mantêm a escala de tempo por benchmark. Speedup e eficiência mostram p no eixo horizontal em log₂. A figura temporal usa diferença percentual da mediana do próprio grupo para comparar flutuações relativas. Os ganhos percentuais nas transições referem-se à mudança de médias entre níveis adjacentes.

- Tempo médio e intervalo t de 95% · [PDF](../graficos/tempo_medio_npb.pdf) · [PNG](../graficos/tempo_medio_npb.png)
- Speedup e referência ideal · [PDF](../graficos/speedup.pdf) · [PNG](../graficos/speedup.png)
- Eficiência paralela · [PDF](../graficos/eficiencia_paralela.pdf) · [PNG](../graficos/eficiencia_paralela.png)
- Distribuição dos tempos · [PDF](../graficos/distribuicao_tempos.pdf) · [PNG](../graficos/distribuicao_tempos.png)
- Completude experimental · [PDF](../graficos/completude_experimental.pdf) · [PNG](../graficos/completude_experimental.png)
- Variação dos tempos por bloco · [PDF](../graficos/comportamento_temporal.pdf) · [PNG](../graficos/comportamento_temporal.png)
