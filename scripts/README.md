# Scripts da pesquisa

| Diretório | Material |
| --- | --- |
| [execucao](execucao/) | Reservado para outros scripts de execução. |
| [coleta](coleta/) | Coletor original v5.4 com as sondagens integradas e SHA-256 conferido nas oito coletas. |
| [analise/auditoria-npb](analise/auditoria-npb/README.md) | Reconciliação de CSV, plano, TXT e ambiente. Inclui código, testes sintéticos e dependências fixadas. |
| [analise/visualizacoes](analise/visualizacoes/) | Geração do catálogo e das peças candidatas a partir das tabelas auditadas. |
| [analise/verificar_integridade.py](analise/verificar_integridade.py) | Conferência dos hashes declarados da entrada, dos artefatos da auditoria e do código. |

O pacote da auditoria mantém a disposição original de código, testes e dependências para conservar os hashes declarados no [manifesto de reprodução](../results/processed/auditoria/manifestos/reproducibilidade.json). O `exploracao.md` junto ao código é o modelo do relatório, com referências relativas ao diretório de saída `relatorios/`. Para consulta, use o relatório arquivado. [Guia de reprodução computacional](analise/auditoria-npb/README.md) · [Relatório de exploração](../results/processed/auditoria/relatorios/01_exploracao_dos_arquivos.md)

## Coletor v5.4

O comando histórico segue a forma `bash npb-experimento-v5.4.sh <BENCHMARK> <CLASSE> ["lista de np"]`. A lista é opcional e deve ser passada como um argumento. Para a classe A, os valores padrão são `1 2 4 8 16 32` em EP, IS, CG, MG, FT e LU e `1 4 9 16 25` em BT e SP. O hash da cópia é `efa570e5d040626e7580071208f0f4df5a604242a700a072eb32b06a4ce7a38b`. [Coletor original](coleta/npb-experimento-v5.4.sh) · [Protocolo](../docs/protocolo-experimental.md)

| Parâmetros | Uso |
| --- | --- |
| `PROJ`, `NPB_DIR`, `BIN_DIR`, `NPB_TARBALL` | Raiz de trabalho, árvore NPB MPI, binários executáveis e pacote-fonte usado na comparação. |
| `HOSTFILE`, `NFS_HOST`, `NFS_DIR`, `IFACE`, `MPI_EXTRA` | Hostfile, servidor e caminho NFS, interface TCP e opções adicionais de lançamento. A campanha usou `eth0`. |
| `REPS`, `SEMENTE`, `TIMEOUT` | Dez blocos, semente `20261114` e limite de 3.600 s por tentativa nas oito coletas. |
| `LIMITE_CPU`, `TEMP_LIMITE_MC`, `ESPERA_OCIOSO`, `PAUSA` | Sondagens antes de cada tentativa, com limite de 10% de CPU e 80 °C (85 °C em SP). O limite térmico é passado em milésimos de grau Celsius. O script adota 60 s de espera e 5 s de pausa por padrão. |
| `RESULTADOS`, `CONFIG_DIR`, `MANUAL`, `NOTAS` | Destinos próprios para registros e configurações e campos de documentação de uma nova coleta. |

O lançamento pressupõe Bash, Python 3, Open MPI, utilitários GNU, SSH por chave entre o coordenador e os nós e os binários disponíveis no NFS. O coletor usa `random.Random` para permutar os valores de `np` em cada bloco, salva o plano antes da primeira tentativa e verifica a política CPUFreq nas sondagens prévias. Uma falha de pré-condição pode interromper a coleta. As tentativas executadas são registradas, sem aquecimento, reposição automática ou monitoramento durante o kernel. O diretório `RESULTADOS/raw/<BENCHMARK>/` recebe plano, CSV, saídas TXT e snapshot de ambiente. O snapshot requer triagem de privacidade antes do compartilhamento. [Formatos dos registros](../results/README.md) · [Parâmetros das oito coletas](../results/processed/auditoria/tabelas/ambientes.csv)

Uma futura repetição deve apontar para um diretório de saída separado e conferir a matriz, as pré-condições e os binários antes do lançamento. A análise dos CSVs arquivados é executada pelo código de auditoria em uma máquina de análise. [Compilação](../benchmarks/README.md#compilação-da-classe-a) · [Reprodução da análise](analise/auditoria-npb/README.md)

## Gerar as visualizações

Após preparar o ambiente da auditoria, use os comandos abaixo na raiz do repositório. Eles leem as tabelas arquivadas em `results/processed/auditoria/tabelas/`. O catálogo escreve em `.local/reproducao/visualizacoes/`, e as peças candidatas escrevem em `.local/reproducao/candidatas-tcc/`.

```sh
.venv/bin/python scripts/analise/visualizacoes/gerar_visualizacoes.py
.venv/bin/python scripts/analise/visualizacoes/gerar_candidatas.py
```

Para gerar o catálogo e as peças candidatas a partir de uma nova auditoria, aponte `--entrada` para as tabelas produzidas e escolha um diretório de saída próprio para cada gerador.

```sh
.venv/bin/python scripts/analise/visualizacoes/gerar_visualizacoes.py \
  --entrada .local/reproducao/auditoria/tabelas \
  --saida .local/reproducao/visualizacoes-reprocessadas
.venv/bin/python scripts/analise/visualizacoes/gerar_candidatas.py \
  --entrada .local/reproducao/auditoria/tabelas \
  --saida .local/reproducao/candidatas-reprocessadas
```

Para reproduzir as tabelas em PDF e as provas de impressão, use pdfLaTeX com `booktabs`, `lmodern`, `geometry`, `graphicx` e `babel` em português, além de `pdftoppm` e `pdfinfo` do Poppler. O catálogo registra quando precisou usar a renderização alternativa. [Catálogo arquivado](../reports/figures/visualizacoes_experimentais/CATALOGO_VISUALIZACOES.md)
