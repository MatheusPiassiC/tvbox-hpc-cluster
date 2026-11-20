# Configurações do ambiente

| Diretório | Configurações |
| --- | --- |
| [mpi](mpi/) | O [hostfile `cluster`](mpi/cluster) foi recuperado das oito cópias textuais nos snapshots. Seu SHA-256 coincide com o declarado em todas as coletas. O protocolo registra os parâmetros MPI observados. |
| [npb](npb/) | Os snapshots transcrevem as atribuições ativas de `make.def` e informam seu SHA-256. O arquivo integral e a confirmação de uso de `suite.def` ainda estão pendentes. |
| [sistema](sistema/) | O [manual 5.0](../docs/configurando-o-cluster-5.0.md) descreve rede, DHCP/DNS, NAT, SSH e NFSv3. O [resumo da configuração registrada](../docs/configuracao-cluster.md) identifica os valores confirmados pelos snapshots e as pendências. |

O `make.def` observado indica `MPICC=mpicc`, `MPIFC=mpif90`, `CFLAGS=-O3`, `FFLAGS=-O3 -fallow-argument-mismatch`, `CONVERTFLAG=-DFORTRAN_REC_SIZE=0` e `RAND=randi8`. Os demais campos transcritos e as assinaturas constam de [`ambientes.csv`](../results/processed/auditoria/tabelas/ambientes.csv). As linhas ativas registram as opções sem restituir todos os bytes do arquivo original.

Preservar os originais dos serviços no acervo da pesquisa e registrar caminho de origem, nó, data e coleta ao incorporá-los. A cópia do manual disponível em `docs/` usa campos de preenchimento para os identificadores de interfaces e solicita a senha do Wi-Fi de forma interativa.
