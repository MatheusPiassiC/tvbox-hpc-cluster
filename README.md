# Análise de Desempenho e Custo de um Cluster de Baixo Custo Baseado em TV Boxes Reaproveitadas

Material complementar ao Trabalho de Conclusão de Curso em Ciência da Computação da Universidade Federal de Lavras (UFLA), orientado pelo Prof. Dr. Luiz Henrique Andrade Correia. A pesquisa avalia o desempenho e o custo de um cluster de baixo custo construído com TV Boxes reaproveitadas para computação paralela e distribuída.

## Resultados

Na campanha NPB 3.4.4 MPI, classe A, a tabela mostra a configuração com o menor tempo médio observado em cada benchmark.

| Benchmark | Processos MPI | Tempo médio (s) | Speedup |
| --- | ---: | ---: | ---: |
| EP | 32 | 0,936 | 30,19× |
| IS | 4 | 0,826 | 2,92× |
| CG | 8 | 3,670 | 4,48× |
| MG | 32 | 2,444 | 5,19× |
| FT | 4 | 8,509 | 2,53× |
| LU | 32 | 28,857 | 6,56× |
| BT | 25 | 62,725 | 4,73× |
| SP | 25 | 113,178 | 3,95× |

EP chegou a 94,35% de eficiência com 32 processos. IS, CG e FT tiveram as menores médias em configurações intermediárias. Os valores descrevem esta campanha de classe A. [Resumo numérico](results/processed/auditoria/tabelas/resumo_benchmarks.csv) · [Análise estatística e intervalos](results/processed/auditoria/relatorios/03_analise_estatistica.md)

### Figuras e tabela selecionadas para o TCC

[Tempo médio (PDF)](reports/figures/visualizacoes_experimentais/selecionadas_tcc/v1/A01_tempo_medio_8paineis_4x2.pdf) · [Speedup (PDF)](reports/figures/visualizacoes_experimentais/selecionadas_tcc/v1/C03_speedup_8paineis_4x2.pdf) · [Eficiência (PDF)](reports/figures/visualizacoes_experimentais/selecionadas_tcc/v1/D03_eficiencia_8paineis_4x2.pdf) · [Síntese de desempenho (PDF)](reports/figures/visualizacoes_experimentais/selecionadas_tcc/v1/T01_sintese_desempenho_completa.pdf)

[Prévias e avaliação de legibilidade](reports/figures/visualizacoes_experimentais/selecionadas_tcc/v1/AVALIACAO_LEGIBILIDADE.md) · [Catálogo de alternativas exploratórias](reports/figures/visualizacoes_experimentais/CATALOGO_VISUALIZACOES.md)

## Custo de aquisição

O desembolso do projeto foi de **R$ 0,00**, pois o CRC-Lavras disponibilizou os componentes. A estimativa referencial registrada no TCC é de **R$ 8.369,79**. [Composição e fontes do custo](docs/custos.md)

## Infraestrutura

O cluster reúne nove TV Boxes H7 disponibilizadas pelo CRC-Lavras. Cada unidade tem SoC Amlogic S905X3, quatro núcleos ARM Cortex-A55 (AArch64) e cerca de 2 GB de RAM. O `server` coordena o cluster e executa MPI com `node1` a `node7`, totalizando 32 slots. O equipamento `nfs` fornece armazenamento via NFSv3. O switch Intelbras SG 2400 QR tem portas Gigabit, e os oito nós MPI negociaram 100 Mb/s em full-duplex na inspeção de 23/11/2026. [Arquitetura](docs/arquitetura.md) · [Hardware](docs/hardware.md)

Os nós de cálculo usaram kernel `6.1.11-meson64`, Open MPI 4.1.0 e lançamento remoto via OpenSSH. A compilação usou GCC e GNU Fortran 10.2.1 no coordenador. Os snapshots registraram o governador `ondemand` e o limite de escala de 1.500 MHz. A documentação identifica a imagem-base H7 do CRC-Lavras e registra separadamente os identificadores do sistema e do build instalado. [Ambiente de software](docs/ambiente-software.md) · [Política de frequência](docs/investigacoes/politica-frequencia-cpu.md)

## Campanha experimental

Em 16 e 17 de novembro de 2026, a campanha avaliou escalabilidade forte com o NAS Parallel Benchmarks 3.4.4 MPI, mantendo a classe A em cada benchmark. EP, IS, CG, MG, FT e LU usaram 1, 2, 4, 8, 16 e 32 processos. BT e SP usaram 1, 4, 9, 16 e 25. O MPI preencheu até quatro slots por nó, na ordem do hostfile, com afinidade por núcleo.

A auditoria conciliou plano, CSV do coletor e saída TXT do NPB. Foram confirmadas **460 tentativas válidas em 46 configurações**, com dez repetições por configuração. Em SP, a base usa as 50 tentativas de `npb_9_SP_A`. A métrica principal é `Time in seconds` do NPB. A análise registra média, mediana, desvio-padrão amostral, IC bilateral de 95% para a média, speedup e eficiência em relação a um processo da mesma série. [Protocolo experimental](docs/protocolo-experimental.md) · [Auditoria experimental](results/processed/auditoria/relatorios/02_auditoria_experimental.md)

## Consulta e reprodução

- **Consultar as evidências.** A base consolidada liga cada tentativa às linhas do CSV e do TXT. As tabelas de estatísticas e de escala agrupam as tentativas por campanha, benchmark, classe e número de processos. [Guia dos dados](results/README.md) · [Base consolidada](results/processed/auditoria/tabelas/execucoes_consolidadas.csv) · [Catálogo de figuras e tabelas](reports/README.md)
- **Compreender a montagem.** O manual 5.0 cobre preparação dos nós, rede, NFSv3, SSH e teste MPI. O resumo da configuração registra o que foi observado nas coletas. [Manual de instalação](docs/configurando-o-cluster-5.0.md) · [Configuração registrada](docs/configuracao-cluster.md)
- **Reproduzir a análise.** Em Linux, use Python 3.12 com as dependências fixadas e a cópia local completa de `results/raw/` para reprocessar a auditoria. Os oito snapshots de ambiente contêm identificadores de interfaces e estão excluídos do versionamento. As tabelas processadas permitem regenerar as figuras e as peças candidatas ao TCC. [Guia da auditoria](scripts/analise/auditoria-npb/README.md) · [Geração de visualizações](scripts/README.md)
- **Repetir os experimentos.** A seleção inclui o coletor v5.4, o `make.def` original e o hostfile, com SHA-256 conferido. O guia do NPB indica como obter e compilar o pacote oficial. O protocolo registra a matriz, o lançamento MPI e as condições prévias. [Reprodução experimental](docs/protocolo-experimental.md#reprodução-experimental) · [Compilação](benchmarks/README.md#compilação-da-classe-a) · [Manifesto de proveniência](metadata/proveniencia-npb.md)

## Organização do material

| Diretório | Conteúdo |
| --- | --- |
| [docs](docs/) | [Arquitetura](docs/arquitetura.md), [hardware](docs/hardware.md), [software](docs/ambiente-software.md), [configuração](docs/configuracao-cluster.md) e [protocolo](docs/protocolo-experimental.md) |
| [config](config/README.md) | Hostfile e `make.def` originais verificados |
| [benchmarks](benchmarks/README.md) | Proveniência do NPB e eventuais patches |
| [scripts](scripts/README.md) | Coletor original e código da auditoria, análise e geração de visualizações |
| [results](results/README.md) | Registros brutos, tabelas de auditoria, estatísticas e manifestos |
| [reports](reports/README.md) | Catálogo de figuras, tabelas e peças selecionadas para o TCC |
| [metadata](metadata/README.md) | Metadados de campanha e manifestos de integridade |

## Referência acadêmica

Use a referência bibliográfica oficial do TCC quando estiver disponível. Ao reutilizar os dados, identifique a campanha, o arquivo consultado e o commit ou o manifesto de entrada da versão consultada. A autoria bibliográfica e o ano de defesa aguardam confirmação. [Orientações de citação](docs/publicacao.md#referência-acadêmica) · [Repositório público](https://github.com/MatheusPiassiC/tvbox-hpc-cluster)

O apêndice do TCC apresenta o acervo técnico, a documentação experimental e as condições de reprodução. [Apêndice em LaTeX](docs/apendice-repositorio.tex)
