# Ambiente de software

As versões abaixo vêm dos snapshots de 16 e 17 de novembro de 2026. A imagem personalizada para os nós de cálculo é atribuída ao CRC-Lavras no [manual 5.0](configurando-o-cluster-5.0.md).

| Componente | Versão ou configuração registrada |
| --- | --- |
| `server` e `node1` a `node7` | Armbian 25.2.3, Debian bullseye 11.11 |
| `nfs` | Debian GNU/Linux 11 (bullseye), versão 11.10 registrada |
| Kernel e arquitetura | `6.1.11-meson64`, AArch64, nos nove equipamentos |
| Execução MPI | Open MPI 4.1.0 nos nós de cálculo |
| Compilação | GCC e GNU Fortran 10.2.1 no coordenador, wrappers `mpicc` e `mpif90` |
| Benchmark | NAS Parallel Benchmarks 3.4.4 MPI, classe A |
| Serviços | OpenSSH para lançamento remoto e NFSv3 para compartilhamento entre os nós |

A identificação da imagem, a versão de hwloc e as versões dos pacotes OpenSSH e NFS ainda precisam ser confirmadas. As opções de compilação registradas estão em [configurações do ambiente](../config/README.md). Consulte as tabelas [`ambientes.csv`](../results/processed/auditoria/tabelas/ambientes.csv) e [`nos_ambiente.csv`](../results/processed/auditoria/tabelas/nos_ambiente.csv) para a proveniência por coleta e por nó.
