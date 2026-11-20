# 01 — Exploração dos arquivos brutos

A auditoria examinou 32 arquivos de quatro tipos nos oito benchmarks. Os registros de SP correspondem à campanha 9. Os arquivos `_ambiente.txt` descrevem os parâmetros da coleta e registram as assinaturas do coletor v5.4, dos executáveis e das configurações de compilação. A conferência direta dessas assinaturas depende da recuperação dos arquivos correspondentes.

## Inventário de entrada

| Arquivo | Tipo | Bytes | Linhas | Codificação | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| [raw/BT/npb_10_BT_A-plano.csv](../../../raw/BT/npb_10_BT_A-plano.csv) | plano | 349 | 51 | UTF-8 | `c7662a74154c724725e42208bbbb187ace8e2c213e282ed715b2c5312a7988b4` |
| [raw/BT/npb_10_BT_A.csv](../../../raw/BT/npb_10_BT_A.csv) | resultados | 30566 | 51 | UTF-8 | `8b2f0b34e8f43d66194cc866087e17e98d2c463bdb84f000b3ede4803543a5aa` |
| [raw/BT/npb_10_BT_A_ambiente.txt](../../../raw/BT/npb_10_BT_A_ambiente.txt) | ambiente | 59279 | 1218 | UTF-8 | `818ddbb1e8410411340ab11c84d851e037e00eba42bf3cfbc8f99ac240403011` |
| [raw/BT/npb_10_BT_A_saidas.txt](../../../raw/BT/npb_10_BT_A_saidas.txt) | saidas | 638487 | 13175 | UTF-8 | `bbde2a9c03d98973a8fe0c457b4ece4063e89f3791e31f06087c24fa440b598f` |
| [raw/CG/npb_3_CG_A-plano.csv](../../../raw/CG/npb_3_CG_A-plano.csv) | plano | 410 | 61 | UTF-8 | `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` |
| [raw/CG/npb_3_CG_A.csv](../../../raw/CG/npb_3_CG_A.csv) | resultados | 35965 | 61 | UTF-8 | `29747cdf3ffc9c45a820d21259abcf64368cbf03338ce20a8aa0a701c8aae7de` |
| [raw/CG/npb_3_CG_A_ambiente.txt](../../../raw/CG/npb_3_CG_A_ambiente.txt) | ambiente | 59331 | 1219 | UTF-8 | `50f7abb41c2ceab873dccbc86706c54020835a8ea595a605fa8cdffa49170b2b` |
| [raw/CG/npb_3_CG_A_saidas.txt](../../../raw/CG/npb_3_CG_A_saidas.txt) | saidas | 693136 | 14226 | UTF-8 | `7be45715d189dbb970612da05b6e39e7d2e93ee96a892d64126a84e7b8040658` |
| [raw/EP/npb_1_EP_A-plano.csv](../../../raw/EP/npb_1_EP_A-plano.csv) | plano | 410 | 61 | UTF-8 | `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` |
| [raw/EP/npb_1_EP_A.csv](../../../raw/EP/npb_1_EP_A.csv) | resultados | 35966 | 61 | UTF-8 | `23ff6f667aff0dce0c8c58408991b056035916e22f8925d83bfaf8de448d9730` |
| [raw/EP/npb_1_EP_A_ambiente.txt](../../../raw/EP/npb_1_EP_A_ambiente.txt) | ambiente | 59329 | 1219 | UTF-8 | `0fcb6ea0e077dabe65475b510016ca7531f61cd58fae524b307ab79919ed4460` |
| [raw/EP/npb_1_EP_A_saidas.txt](../../../raw/EP/npb_1_EP_A_saidas.txt) | saidas | 693476 | 14466 | UTF-8 | `f0f911229e6c20874e0ac9031f28063fff49e0da77a26b1785a8b1e8361cb0ae` |
| [raw/FT/npb_5_FT_A-plano.csv](../../../raw/FT/npb_5_FT_A-plano.csv) | plano | 410 | 61 | UTF-8 | `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` |
| [raw/FT/npb_5_FT_A.csv](../../../raw/FT/npb_5_FT_A.csv) | resultados | 36094 | 61 | UTF-8 | `87b1543deff193c8ed949dd93bb0c3f26229e45d041d49eab3179b05a381a0f4` |
| [raw/FT/npb_5_FT_A_ambiente.txt](../../../raw/FT/npb_5_FT_A_ambiente.txt) | ambiente | 59403 | 1219 | UTF-8 | `3de6a21862c8c871377fc296c92f9499633a2bbc2f3040a51844b6dfde75852b` |
| [raw/FT/npb_5_FT_A_saidas.txt](../../../raw/FT/npb_5_FT_A_saidas.txt) | saidas | 710401 | 14286 | UTF-8 | `bc4819b15ea45ac8c180ef84015f1d07fb399fa3ec4f169b9b9c96a490a58590` |
| [raw/IS/npb_2_IS_A-plano.csv](../../../raw/IS/npb_2_IS_A-plano.csv) | plano | 410 | 61 | UTF-8 | `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` |
| [raw/IS/npb_2_IS_A.csv](../../../raw/IS/npb_2_IS_A.csv) | resultados | 35891 | 61 | UTF-8 | `3478d7040274edac1de779e3910821e8611b7f4bf89e1fc057da48d35b358674` |
| [raw/IS/npb_2_IS_A_ambiente.txt](../../../raw/IS/npb_2_IS_A_ambiente.txt) | ambiente | 59139 | 1216 | UTF-8 | `4085810a0a0b629bc3679bd78637835bb2f81e2b9ecf195db606c72337ea90b5` |
| [raw/IS/npb_2_IS_A_saidas.txt](../../../raw/IS/npb_2_IS_A_saidas.txt) | saidas | 671608 | 14166 | UTF-8 | `b70b96f46289e421240fc4f9b17543079a16755bd968dd673f1bc3868cc3017d` |
| [raw/LU/npb_6_LU_A-plano.csv](../../../raw/LU/npb_6_LU_A-plano.csv) | plano | 410 | 61 | UTF-8 | `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` |
| [raw/LU/npb_6_LU_A.csv](../../../raw/LU/npb_6_LU_A.csv) | resultados | 36209 | 61 | UTF-8 | `002e4d194fe43a5627a1370a6e85dfc0d055f4afa744c9b13e3651a88cdd6f8f` |
| [raw/LU/npb_6_LU_A_ambiente.txt](../../../raw/LU/npb_6_LU_A_ambiente.txt) | ambiente | 59413 | 1219 | UTF-8 | `7479225fcd483fb41c7b0241bb8ebef614612848227ad70f833c78d9ab623dab` |
| [raw/LU/npb_6_LU_A_saidas.txt](../../../raw/LU/npb_6_LU_A_saidas.txt) | saidas | 748453 | 15487 | UTF-8 | `db47119bda1b24d80e635787b0a271a900d667e8377365dc35094b42dcff63df` |
| [raw/MG/npb_4_MG_A-plano.csv](../../../raw/MG/npb_4_MG_A-plano.csv) | plano | 410 | 61 | UTF-8 | `4e3c352bf4782dd03ea3ffd47c76c3503a0a9e29176f9a01c691d5f0a3a8f442` |
| [raw/MG/npb_4_MG_A.csv](../../../raw/MG/npb_4_MG_A.csv) | resultados | 36050 | 61 | UTF-8 | `b73542861b966e6689a3830596f9520949d2edca800c685a378fbada6bde2de8` |
| [raw/MG/npb_4_MG_A_ambiente.txt](../../../raw/MG/npb_4_MG_A_ambiente.txt) | ambiente | 59403 | 1219 | UTF-8 | `f51384c1460496ef2abd4d7e7b62a9c24384971b89c6a861b7ba87849b6462dc` |
| [raw/MG/npb_4_MG_A_saidas.txt](../../../raw/MG/npb_4_MG_A_saidas.txt) | saidas | 684412 | 14226 | UTF-8 | `7883342db940548fdbd1c0ed5027b36070ef74b5095773afee3b5876f6b72f2c` |
| [raw/SP/npb_9_SP_A-plano.csv](../../../raw/SP/npb_9_SP_A-plano.csv) | plano | 349 | 51 | UTF-8 | `c7662a74154c724725e42208bbbb187ace8e2c213e282ed715b2c5312a7988b4` |
| [raw/SP/npb_9_SP_A.csv](../../../raw/SP/npb_9_SP_A.csv) | resultados | 30419 | 51 | UTF-8 | `f2971b345f91ec6e1a574ad157fc6b653b94fede8042fc641acb2a8f59d5664f` |
| [raw/SP/npb_9_SP_A_ambiente.txt](../../../raw/SP/npb_9_SP_A_ambiente.txt) | ambiente | 59186 | 1218 | UTF-8 | `8b2215341de7fd9eddb12b416553f3ee66e93fdc8097a8b4b53349980a15bf82` |
| [raw/SP/npb_9_SP_A_saidas.txt](../../../raw/SP/npb_9_SP_A_saidas.txt) | saidas | 651128 | 13675 | UTF-8 | `0bd57207907115812df7182789ee6be63be6e26bc734b6fd806368e4164f564c` |

O SHA-256 nesta tabela é calculado sobre os bytes de cada arquivo. Os hashes de plataforma e de binário registrados pelo coletor têm outra origem e aparecem em [ambientes.csv](../tabelas/ambientes.csv). O [manifesto de entrada](../manifestos/dados_entrada.json) fornece o inventário em formato legível por máquina.

## Formatos e campos

Todos os 32 arquivos da inspeção inicial decodificaram em UTF-8 sem BOM e com quebras LF. Os oito CSVs de resultados usam a mesma ordem de 36 colunas, vírgula como delimitador, ponto decimal e campo vazio para ausência de valor. Na inspeção linha a linha, a quantidade de campos bateu com o cabeçalho. Os horários usam ISO 8601 com segundos inteiros e deslocamento `-03:00`. O arquivo de ambiente documenta a maior parte da semântica nas seções 7 e 9. [Dicionário e controles de SP, linhas 1172–1218](../../../raw/SP/npb_9_SP_A_ambiente.txt#L1172-L1218)

| Campo(s) do CSV principal | Tipo e significado |
| --- | --- |
| `experimento_id`, `exec_id` | Identificador inteiro da campanha e identificador textual da tentativa. O sufixo de `exec_id` registra a sequência global na campanha. |
| `benchmark`, `classe`, `np` | Nome do benchmark, classe e quantidade MPI solicitada. A quantidade reportada no resumo NPB é recuperada separadamente. |
| `n_nos`, `distribuicao` | Quantidade de hosts com ranks, segundo o coletor, e contagem textual por host no formato `server=4;node1=4`. |
| `tentativa`, `repeticao_valida` | Contador de tentativas por `np` e ordinal de aceitação por `np`. O segundo é vazio quando a tentativa é recusada conforme o dicionário. |
| `inicio`, `fim` | Horários da tentativa, com fuso e resolução de 1 s. |
| `tempo_s` | Cópia de `Time in seconds` do resumo NPB, em segundos, com duas casas decimais nos arquivos auditados. |
| `mops_total`, `mops_por_processo` | Cópias de `Mop/s total` e `Mop/s/process`, conforme a operação específica da carga. |
| `processos_ativos`, `verificacao` | Cópias de `Active processes` e `Verification`. O dicionário admite campo vazio para processos e `NAO_ENCONTRADA` para verificação ausente. |
| `exit_code`, `status`, `motivo` | Código de saída e decisão do coletor, com motivo textual. O dicionário lista `VALIDA`, `TIMEOUT`, `FALHA_EXECUCAO`, `FALHA_VERIFICACAO` e `INVALIDA`. Ocorreram apenas `0`, `VALIDA` e `OK` na inspeção inicial. |
| `tempo_parede_s` | Duração externa do mpirun medida pelo coletor, incluindo a inicialização MPI. Mantida em série própria. |
| `cpu_ocupada_max_antes_pct` | Maior ocupação entre os oito nós MPI na sondagem prévia de 1 s, em porcentagem. |
| `mem_disp_min_antes_mb`, `temp_max_antes_c` | Mínimo de RAM disponível e máxima temperatura na sondagem anterior, nas unidades MB e °C registradas. |
| `temp_max_durante_c`, `freq_min_durante_mhz`, `mem_disp_min_durante_mb` | Campos reservados ao monitoramento durante a execução. Estavam vazios em todas as tentativas, de acordo com o monitoramento desativado. |
| `binario_sha256`, `ambiente_sha256` | Identificadores declarados do binário e da plataforma. O hash de plataforma é descrito como derivado das seções 2 e 3, excluindo dados voláteis. |
| `comando`, `saida_arquivo`, `saida_linha_inicial` | Comando registrado, nome do TXT e linha física do marcador de abertura, com contagem a partir de 1. |
| `fase`, `bloco` | Fase textual e bloco do plano. A fase `MEDICAO` foi documentada para todas as linhas do protocolo v5.4. |
| `governor_antes`, `freq_max_permitida_antes_mhz` | Política registrada antes da tentativa e limite de frequência em MHz. O TXT registra o mesmo limite em kHz. |
| `swap_livre_min_antes_mb` | Campo numérico com unidade MB indicada no nome e mínimo anterior à execução inferido pelo nome. O dicionário omite sua definição operacional. |

O código de amostragem e as regras exatas de agregação dos sensores, conversão de RAM e swap e arredondamento do tempo de parede ficam indeterminados sem o script referenciado. Os horários de começo e fim oferecem um controle de plausibilidade de resolução inferior à duração externa de duas casas decimais.

## Chaves e planejamento

O plano usa `bloco,ordem_no_bloco,np`. A chave `(campanha, bloco, np)` identifica uma posição lógica da medição. A chave `(campanha, exec_id)` identifica uma tentativa física. Os números de tentativa, de bloco e de repetição válida coincidem nesta cópia porque houve uma tentativa aceita em cada posição. São campos distintos por definição. O coletor v5.4 documenta dez blocos, uma medição por configuração por bloco, sem aquecimento e sem reposição. A meta de dez repetições válidas por configuração é confrontada com o plano e com os resultados observados, incluindo possíveis lacunas. [EM v5.4, EP, linhas 24–42 e 1208–1217](../../../raw/EP/npb_1_EP_A_ambiente.txt#L24-L42)

```csv
bloco,ordem_no_bloco,np
1,1,16
1,2,32
```

Todos os planos trazem a semente declarada `20261114`. Os seis benchmarks com níveis 1, 2, 4, 8, 16 e 32 compartilham um plano byte a byte. BT e SP compartilham outro. A ordem muda entre blocos e se repete entre campanhas com o mesmo conjunto de níveis. Cada hash de plano declarado coincide com o SHA-256 do CSV correspondente. A inspeção inicial encontrou 460 posições, 460 linhas de resultados e 460 blocos de saída com pares unívocos. [Plano de EP](../../../raw/EP/npb_1_EP_A-plano.csv#L1-L13) · [Plano de SP](../../../raw/SP/npb_9_SP_A-plano.csv#L1-L11)

## Delimitação e resumo do NPB

O preâmbulo do TXT identifica a campanha e os arquivos associados. Cada bloco começa por `##### EXEC`, contém comando e pré-condições, abre a captura combinada de stdout e stderr e termina por `----- fim EXEC`. O TXT, a linha indicada no CSV e o identificador permitem cruzar a mesma tentativa sem usar a posição relativa como chave.

```text
##### EXEC 1-0001 | EP.A | np=16 | fase=MEDICAO | bloco=1 | tentativa=1 | inicio=2026-11-16T16:22:10-03:00
 EP Benchmark Completed.
 Time in seconds =                     1.81
 Verification    =               SUCCESSFUL
```

A pontuação de `IS Benchmark Completed` difere dos demais, que imprimem ponto no final. O cabeçalho do programa apresenta a série `3.4` e o resumo imprime `3.4.4`. O tempo, o resultado numérico e os processos são extraídos do resumo após a marca de conclusão. CG, MG, FT, LU, BT e SP também imprimem uma mensagem de verificação durante a saída. EP e IS têm a confirmação no resumo. EP imprime adicionalmente `CPU Time` com três casas decimais. FT e MG imprimem duração de inicialização. A série principal usa exclusivamente `Time in seconds` para os oito benchmarks. [Saída EP, linhas 7–10 e 260–314](../../../raw/EP/npb_1_EP_A_saidas.txt#L260-L314) · [Saída IS, linhas 280–297](../../../raw/IS/npb_2_IS_A_saidas.txt#L280-L297)

## Mapa MPI e afinidade

Em cada bloco da cópia inicial, um job aparece com oito representações do mapa, com os mesmos hosts e ranks. `Total slots allocated 32` é a capacidade da alocação MPI. A cardinalidade do conjunto de ranks e `Total processes` do NPB informam quantos processos ocorreram. `Data for node` introduz um host, `Num procs` declara sua contagem e `Process rank` identifica ranks sob esse host. Ranks são reconciliados pelo identificador de job, rank e host. Uma representação pode trazer `Bound: N/A` e as demais podem mostrar afinidade para o mesmo rank. Os registros `[host:pid] MCW rank … bound to socket …[core …]` oferecem uma segunda representação host–rank–núcleo. A auditoria exige evidência individual, coerência e núcleos distintos por host conforme o protocolo local. [Primeiro mapa de EP, linhas 11–91](../../../raw/EP/npb_1_EP_A_saidas.txt#L11-L91) · [Manpage do Open MPI 4.1](https://www.open-mpi.org/doc/v4.1/man1/mpirun.1.php)

## Ambiente e pontos de atenção

- Os arquivos de ambiente exibem o mesmo SHA-256 declarado de plataforma. As seções 2 e 3 também têm conteúdo textual idêntico nos oito arquivos da inspeção. Os horários, a seção volátil, os hashes de executáveis e as opções impressas por cargas distintas variam. O SHA-256 derivado do trecho das seções 2 e 3 é reproduzível a partir do TXT. O procedimento de derivação do fingerprint declarado pelo coletor depende do script.
- Os nove equipamentos imprimem device tree `SEI Robotics SEI610`. A seção manual registra H7 como modelo comercial informado, com fabricante comercial indeterminado. A alegação de modelo comercial SEI6 deve ser conferida. Os registros corroboram AArch64, quatro núcleos Cortex-A55, `MemTotal` de 1.868.128 kB, os oito hosts do hostfile e NFS dedicado. A seção manual informa identificação direta SM1 no coordenador. [SP, seções 2.1–2.6](../../../raw/SP/npb_9_SP_A_ambiente.txt#L47-L190)
- Os snapshots mostram Open MPI 4.1.0, Armbian 25.2.3 bullseye, kernel 6.1.11-meson64, links de 100 Mbit/s full-duplex e política `ondemand` com limite de 1.500 MHz. Os 2.100 MHz reportados pelo driver correspondem a `cpuinfo_max_freq`. A seção 5 tem amostras pontuais de frequência, temperatura, memória, ping e contadores acumulados na abertura da campanha. A taxa durante as execuções, o pico de memória e a temperatura durante o kernel permanecem indeterminados. [SP, seções 2–5](../../../raw/SP/npb_9_SP_A_ambiente.txt#L143-L1000)
- O limite de temperatura prévia da campanha SP 9 foi 85 °C. O protocolo das outras sete campanhas registra 80 °C. A diferença consta nos controles da seção 9, fora das seções usadas pelo identificador de plataforma. [SP, linha 1213](../../../raw/SP/npb_9_SP_A_ambiente.txt#L1213) · [BT, linha 1213](../../../raw/BT/npb_10_BT_A_ambiente.txt#L1213)
- A única linha de aviso identificada na inspeção pertence a LU, `6-0017`, e menciona `setpgid` com `Permission denied(13)`. O restante do bloco contém a conclusão e a verificação do NPB. Rótulos como `Comparison of RMS-norms of solution error` e `Error is …` pertencem aos diagnósticos numéricos e requerem interpretação no contexto de verificação. [LU 6-0017, linha 3966](../../../raw/LU/npb_6_LU_A_saidas.txt#L3966)

## Regras de leitura adotadas

A leitura preserva os textos originais do CSV e intervalos de linhas físicas. A auditoria cruza o identificador e a referência de linha dentro da mesma campanha, verifica o plano por bloco e por ordem e retém registros sem par ou com chaves ambíguas. Campos numéricos são validados antes de normalizar e diferenças de resolução são avaliadas pela precisão registrada. Resumos, mapas e rodapés têm escopo dentro do mesmo bloco, para que uma saída truncada preserve sua proveniência. Lacunas de evidência e contradições recebem registros próprios. A constância da carga é verificada por classe, tamanho e iterações, usando os parâmetros publicados para NPB classe A e a representação observada nos resumos. [Tamanhos de problemas do NPB, NASA](https://nas.nasa.gov/software/npb_problem_sizes.html)
