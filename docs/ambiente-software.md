# Ambiente de software

## Imagem-base para H7

A imagem-base veio do projeto FênixBook do CRC-Lavras. A tabela oficial identifica a unidade como **HTV H7**, com processador `s905x3`. O manual 5.0 descreve a preparação dessa base para o cluster. A imagem efetivamente instalada ainda carece de um inventário dos componentes e de um SHA-256. [Tabela de imagens do CRC-Lavras](https://github.com/crc-lavras/crc-lavras#tabela) · [Manual 5.0](configurando-o-cluster-5.0.md)

## Campanha de 16 e 17 de novembro de 2026

| Componente | Versão ou configuração registrada |
| --- | --- |
| Identificação exibida do sistema | Os snapshots registram Armbian 25.2.3 bullseye e Debian 11.11 no `server` e no `nfs`. Em `node5`, exibem Debian GNU/Linux 11 (bullseye), versão 11.10. A tabela por nó preserva os valores de cada coleta. |
| Kernel e arquitetura | `6.1.11-meson64`, AArch64, nos nove equipamentos |
| Execução MPI | Open MPI 4.1.0 nos nós de cálculo |
| Compilação | GCC e GNU Fortran 10.2.1 no coordenador, wrappers `mpicc` e `mpif90` |
| Benchmark | NAS Parallel Benchmarks 3.4.4 MPI, classe A |
| Serviços | OpenSSH para lançamento remoto e NFSv3 para compartilhamento entre os nós |

Os snapshots registram `libhwloc15` na versão `2.4.1+dfsg-1`. A confirmação das versões dos pacotes OpenSSH e NFS permanece pendente. [Ambiente por campanha](../results/processed/auditoria/tabelas/ambientes.csv) · [Ambiente por nó](../results/processed/auditoria/tabelas/nos_ambiente.csv) · [Nota sobre hwloc e DRM](investigacoes/correcao-hwloc-drm.md)

## Inspeção de 23/11/2026

O pesquisador registrou os identificadores a seguir em arquivos diferentes do `server`.

| Origem | Valor registrado |
| --- | --- |
| `/etc/os-release` | Armbian 25.2.3 bullseye |
| `/etc/armbian-release` | `VERSION=23.02.2`, `BOARD=aml-s9xx-box`, `LINUXFAMILY=meson64`, `BUILD_REPOSITORY_COMMIT=1a8daf0` |
| Kernel | `6.1.11-meson64`, build `#23.02.2` |

Em `node5`, `/etc/os-release` exibia `PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"`. O `/etc/armbian-release` registrava `VERSION=23.02.2`, `BOARD=aml-s9xx-box` e `BUILD_REPOSITORY_COMMIT=1a8daf0`. O kernel e os elementos operacionais observados coincidiam com os dos demais nós MPI. Os campos descrevem a identificação exibida, o build Armbian e o kernel em uso. [Configuração de rede e NFS](configuracao-cluster.md) · [Política de frequência](investigacoes/politica-frequencia-cpu.md)
