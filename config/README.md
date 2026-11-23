# Configurações do ambiente

| Diretório | Configurações |
| --- | --- |
| [mpi](mpi/) | O [hostfile `cluster`](mpi/cluster) já versionado coincide byte a byte com o original recuperado. Lista `server` e `node1` a `node7`, com quatro slots por nó, nessa ordem. |
| [npb](npb/) | O [`make.def` original](npb/make.def) foi recuperado integralmente e confere com os oito snapshots. O resgate não contém um `suite.def` efetivo. |
| [sistema](sistema/) | O [manual 5.0](../docs/configurando-o-cluster-5.0.md) descreve rede, DHCP/DNS, NAT, SSH e NFSv3. O [registro da configuração](../docs/configuracao-cluster.md) identifica os valores da campanha e as observações de 23/11/2026. |

O `make.def` original define `MPICC=mpicc`, `MPIFC=mpif90`, `CFLAGS=-O3`, `FFLAGS=-O3 -fallow-argument-mismatch`, `CONVERTFLAG=-DFORTRAN_REC_SIZE=0` e `RAND=randi8`. Os snapshots relacionam os wrappers aos compiladores GCC e GNU Fortran 10.2.1 e ao Open MPI 4.1.0. [Proveniência e hashes](../metadata/proveniencia-npb.md) · [Compilação do NPB](../benchmarks/README.md#compilação-da-classe-a)

Preservar os originais dos serviços no acervo da pesquisa e registrar caminho de origem, nó, data e coleta ao incorporá-los. A cópia do manual disponível em `docs/` usa campos de preenchimento para os identificadores de interfaces e solicita a senha do Wi-Fi de forma interativa.
