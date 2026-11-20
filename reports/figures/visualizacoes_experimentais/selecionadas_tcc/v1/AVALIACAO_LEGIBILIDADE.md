# Avaliação de legibilidade das peças candidatas v1

A prova foi compilada em LaTeX e inspecionada a 150 dpi nas dimensões de inserção. Como o modelo do TCC não está no repositório, a prova adota papel A4 com largura útil de 15,6 cm e margens laterais de 2,7 cm. A01, C03 e D03 medem 15,6 × 10,2 cm. Os PDFs são vetoriais e os PNGs das figuras têm 600 dpi. [Prova A4](PROVA_INSERCAO_TCC.pdf) · [Fonte LaTeX](PROVA_INSERCAO_TCC.tex)

## Peças e prévias

| Peça | Arquivos | Página da prova |
| --- | --- | --- |
| A01 · Tempo médio | [PDF](A01_tempo_medio_8paineis_4x2.pdf) · [PNG](A01_tempo_medio_8paineis_4x2.png) | [1](previas_impressao/01_A01.png) |
| C03 · Speedup | [PDF](C03_speedup_8paineis_4x2.pdf) · [PNG](C03_speedup_8paineis_4x2.png) | [2](previas_impressao/02_C03.png) |
| D03 · Eficiência | [PDF](D03_eficiencia_8paineis_4x2.pdf) · [PNG](D03_eficiencia_8paineis_4x2.png) | [3](previas_impressao/03_D03.png) |
| T01 · Síntese | [LaTeX](T01_sintese_desempenho_completa.tex) · [PDF](T01_sintese_desempenho_completa.pdf) · [Exemplo de inclusão](exemplo_inclusao_T01.tex) | [4](previas_impressao/04_T01.png) |
| D03 · Comparação 2×4 | [PDF](D03_eficiencia_8paineis_alternativa_2x4.pdf) · [PNG](D03_eficiencia_8paineis_alternativa_2x4.png) | [5](previas_impressao/05_D03-2x4.png) |

## Leitura em largura de página

- **A01 · Legível em 4×2.** As escalas independentes mostram as tendências em segundos, da faixa de IS à de SP. A barra de FT com 32 processos está completa e mede cerca de 9,3 mm na página. O tempo médio nesse ponto é 19,033 s e o IC vai de 15,028 a 23,038 s. ICs muito estreitos, como os de EP, aparecem como traços próximos aos marcadores. Para ler seus limites exatos, consulte a tabela descritiva. [ICs auditados](../../../../../results/processed/auditoria/tabelas/estatisticas_descritivas.csv)
- **C03 · Legível em 4×2.** A referência ideal cinza tracejada se distingue das séries com marcadores. A escala y comum facilita comparar a distância para o ideal. Valores baixos de speedup ficam próximos da base e, em EP, a série acompanha de perto o ideal. Use os marcadores para identificar as configurações avaliadas. [Speedup auditado](../../../../../results/processed/auditoria/tabelas/speedup_eficiencia.csv)
- **D03 · Legível em 4×2 para tendências e valores superlineares.** CG e LU atingem, respectivamente, 125,02% e 107,58% em dois processos. Os pontos baixos de IS e FT aparecem inteiros, e seus marcadores estão separados em x. Em IS, 1,83% e 1,60% ficam a cerca de 0,06 mm de distância vertical. A variante 2×4 dá mais espaço horizontal aos rótulos e marcadores. Ela mede 15,6 × 20,0 cm e mantém a escala percentual. A diferença vertical em IS continua sutil, portanto a leitura exata depende dos dados tabulados. [Eficiência auditada](../../../../../results/processed/auditoria/tabelas/speedup_eficiencia.csv)
- **T01 · Legível em 15,6 cm.** O fragmento `booktabs` usa corpo de 10 pt no documento de prova e alinha os campos numéricos à direita. Tempo, IC e speedup usam três casas decimais. Eficiência usa duas. A distinção entre as duas colunas de eficiência aparece, por exemplo, em IS, com 72,94% no melhor p e 1,60% no maior p. O exemplo LaTeX foi compilado com a tabela e sua nota. [Exemplo de inclusão](exemplo_inclusao_T01.tex)

As grades 4×2 usam EP, IS, CG e MG na primeira linha e FT, LU, BT e SP na segunda. Os números dos eixos têm 8,5 pt em x e 9 pt em y, com títulos em negrito de 9,3 pt. Há um rótulo comum por eixo e uma legenda por figura. A inspeção confirmou o espaçamento entre painéis, sem recortes nem sobreposições. Os rótulos 16 e 25 de BT e SP são os mais próximos, com pelo menos 0,5 mm de folga nas três grades 4×2.

## Conferência e reprodução

O gerador confronta as 46 configurações com as 460 execuções auditadas. Os gráficos registram os processos 1, 4, 9, 16 e 25 para BT e SP e 1, 2, 4, 8, 16 e 32 para os demais, em escala log₂ no eixo x. Os marcadores indicam observações e os traços que os unem guiam a leitura. A linha ideal de C03 representa a função teórica `S(p) = p`. A01 usa os ICs bilaterais auditados. C03 e D03 mostram estimativas pontuais.

Execute na raiz do repositório com a `.venv` preparada conforme o [guia da auditoria](../../../../../scripts/analise/auditoria-npb/README.md), pdfLaTeX e os utilitários Poppler `pdftoppm` e `pdfinfo`.

```sh
.venv/bin/python scripts/analise/visualizacoes/gerar_candidatas.py
```
