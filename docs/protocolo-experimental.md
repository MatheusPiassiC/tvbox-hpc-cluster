# Protocolo experimental

A campanha de 16 e 17 de novembro de 2026 mediu escalabilidade forte, mantendo a classe A do NPB 3.4.4 MPI fixa dentro de cada benchmark.

## Desenho da campanha

| Benchmarks | Processos MPI |
| --- | --- |
| EP (Embarrassingly Parallel), IS (Integer Sort), CG (Conjugate Gradient), MG (Multi-Grid), FT (Fast Fourier Transform) e LU (Lower-Upper Gauss-Seidel) | 1, 2, 4, 8, 16 e 32 |
| BT (Block Tri-diagonal) e SP (Scalar Penta-diagonal) | 1, 4, 9, 16 e 25, sujeitos às restrições da implementação |

Cada benchmark tem dez blocos, com uma passagem por cada quantidade de processos em cada bloco. A ordem foi permutada com a semente declarada `20261114`. Os planos foram preservados em CSV. Os snapshots do coletor v5.4 documentam a ausência de aquecimento deliberado, de reposição e de monitoramento durante a execução. [Planos e chaves de execução](../results/README.md) · [Parâmetros das coletas](../results/processed/auditoria/tabelas/ambientes.csv)

Os snapshots registram o modelo de lançamento a seguir. A auditoria recuperou a alocação de ranks por host e núcleo e confirmou a ocupação de até quatro processos por nó na ordem do hostfile.

```text
mpirun -np <np> --hostfile /home/minipc/nfs/cluster --map-by slot --rank-by slot --bind-to core --mca btl_tcp_if_include eth0 --mca oob_tcp_if_include eth0 --display-map --report-bindings <binário>
```

Os registros por rank estão em [`ranks_mpi.csv`](../results/processed/auditoria/tabelas/ranks_mpi.csv). O [hostfile recuperado](../config/mpi/cluster) contém quatro slots por nó de cálculo. Consulte a [política de frequência](investigacoes/politica-frequencia-cpu.md).

## Registro e validação

O coletor gravou `exec_id`, `status`, `exit_code` e a referência ao bloco TXT por tentativa. As condições prévias documentadas incluíam até 10% de CPU ocupada e o limite de temperatura de 80 °C, com 85 °C em SP. O timeout declarado foi de 3.600 s.

A auditoria reconcilia plano, CSV e TXT. A confirmação exige tempo positivo no resumo do NPB, código de saída zero, `Verification = SUCCESSFUL`, consistência de classe e processos e evidência do mapeamento e da afinidade individual. A amostra principal usa as tentativas confirmadas e elegíveis da grade, com uma por posição lógica. O estado do coletor fica em coluna própria, junto do resultado da auditoria e dos motivos de inclusão. [Tabela de decisões](../results/processed/auditoria/tabelas/auditoria_execucoes.csv)

Na auditoria arquivada, as 46 configurações têm dez tentativas confirmadas cada. O coletor v5.4 é identificado nos snapshots por caminho e SHA-256. Seu código ainda precisa ser localizado para verificar independentemente a implementação das sondagens e do protocolo de execução. [Auditoria experimental](../results/processed/auditoria/relatorios/02_auditoria_experimental.md)

## Análise estatística

A análise principal usa o campo `Time in seconds` do NPB nas tentativas confirmadas e elegíveis. Para cada configuração, os resultados registram a amostra `n`, média, mediana, desvio-padrão amostral `s` e outras estatísticas descritivas. O IC bilateral de 95% da média, quando `n > 1`, usa a média mais ou menos `t × s/√n`, com o quantil de 97,5% da distribuição t de Student com `n−1` graus de liberdade.

O speedup com `p` processos é `T₁/Tₚ`, usando os tempos médios da mesma campanha, benchmark e classe e uma referência comparável de um processo. A eficiência em porcentagem é `100 × (T₁/Tₚ)/p`. Sem uma referência comparável, as razões ficam indisponíveis. Speedup e eficiência são estimativas pontuais. Os intervalos publicados se referem aos tempos médios, e a análise preserva as observações atípicas confirmadas.

O tempo externo de `mpirun` está em uma tabela própria. Consulte o [relatório estatístico](../results/processed/auditoria/relatorios/03_analise_estatistica.md), o [código da análise](../scripts/README.md) e os [metadados de proveniência](../metadata/README.md).

## Reprodução experimental

1. Reconstrua a infraestrutura a partir do manual 5.0 e confira a montagem NFSv3, a versão do MPI, o acesso SSH, a política de frequência e a alocação dos nós de cálculo. [Configuração do cluster](configuracao-cluster.md)
2. Recupere o coletor v5.4, o pacote NPB 3.4.4, o `make.def` integral e os registros de compilação. Compare as cópias recuperadas com as assinaturas declaradas nos snapshots. Para uma nova série, registre os compiladores, as opções, a classe e o hash de cada binário. [Proveniência do NPB](../benchmarks/README.md) · [Configuração de compilação](../config/README.md)
3. Use o plano correspondente a cada benchmark para a ordem das tentativas, com a matriz e os limites prévios documentados. Arquive plano, CSV, TXT e snapshot de ambiente sob identificadores próprios da nova série. Preserve todas as tentativas e vincule os desvios e decisões de validação aos registros correspondentes. [Dados e formatos](../results/README.md)
4. Audite as saídas da nova série em um diretório próprio e compare as configurações com a campanha arquivada. Registre diferenças de ambiente e de protocolo junto com os resultados. [Reprodução da análise](../scripts/analise/auditoria-npb/README.md)

O acervo atual permite reconstruir a matriz, o lançamento MPI e os critérios documentados. Para repetir integralmente o procedimento, faltam a identificação exata da imagem usada, os arquivos integrais de compilação e o código do coletor com suas sondagens e regras de execução. Os snapshots registram as condições de abertura e as sondagens prévias. As condições de rede, frequência, temperatura e memória durante os benchmarks permanecem indeterminadas. [Pendências de integração](GUIA_DE_INTEGRACAO.md)
