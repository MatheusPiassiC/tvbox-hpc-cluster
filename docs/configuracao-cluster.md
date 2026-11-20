# Configuração do cluster

O [manual Configurando o cluster 5.0](configurando-o-cluster-5.0.md) descreve a instalação desde o sistema base até o teste MPI. Os snapshots de 16 e 17 de novembro de 2026 registram a configuração observada no início de cada coleta. A tabela [`nos_ambiente.csv`](../results/processed/auditoria/tabelas/nos_ambiente.csv) reúne as versões, os papéis dos nós, a política de frequência e as condições dos enlaces registrados.

## Ordem de montagem

1. Preparar o `server` com endereço estático em `eth0`. O roteiro usa o `dnsmasq` para DHCP e DNS em `eth0`, com encaminhamento IPv4 e NAT por `wlan0` para o acesso externo. Os comandos de Wi-Fi usam o NetworkManager. O manual descreve a imagem do cluster como sem interface gráfica e cita uma imagem com interface gráfica na seção de Wi-Fi. A forma de implantação do NetworkManager na imagem usada ainda precisa de confirmação.
2. Preparar o `nfs` com `nfs-kernel-server`, reservar o endereço no DHCP do `server` e exportar `/home/minipc/nfs` para a rede privada com `rw,sync,no_subtree_check`. A seção de NFS do manual explica como verificar a exportação e fazer um teste de escrita a partir do `server`.
3. Configurar o `server` e os sete nós de cálculo como clientes do compartilhamento no mesmo caminho. O manual registra a entrada de `/etc/fstab` abaixo. Configurar hostnames e reservas DHCP individuais e autorizar a chave do coordenador no OpenSSH de cada nó de cálculo.
4. Colocar os programas MPI e o [hostfile `cluster`](../config/mpi/cluster) no compartilhamento. O manual inclui um programa curto em C, compilado com `mpicc`, para testar o lançamento por SSH e identificar os ranks por máquina. O roteiro também descreve a preparação opcional de uma imagem reutilizável para os nós.

```text
10.0.0.99:/home/minipc/nfs /home/minipc/nfs nfs rw,sync,hard,vers=3 0 0
```

## Configuração registrada na coleta

A seção 2.3 dos oito snapshots registra a mesma rede `10.0.0.0/24`. O `server` é o gateway e o resolvedor DNS fornecido aos clientes. A faixa dinâmica documentada do `dnsmasq` é `10.0.0.150–200`. As reservas e os nomes usados na campanha foram os seguintes.

| Host | Endereço em `eth0` | Papel |
| --- | --- | --- |
| `server` | `10.0.0.100` | Coordenador, nó MPI e cliente NFS |
| `nfs` | `10.0.0.99` | Servidor NFS dedicado |
| `node1` | `10.0.0.101` | Nó MPI e cliente NFS |
| `node2` | `10.0.0.190` | Nó MPI e cliente NFS |
| `node3` | `10.0.0.183` | Nó MPI e cliente NFS |
| `node4` | `10.0.0.168` | Nó MPI e cliente NFS |
| `node5` | `10.0.0.167` | Nó MPI e cliente NFS |
| `node6` | `10.0.0.170` | Nó MPI e cliente NFS |
| `node7` | `10.0.0.182` | Nó MPI e cliente NFS |

O endereço `10.0.0.102` atribuído a `node2` no diagrama e na reserva de exemplo do manual é ilustrativo. A reserva do snapshot experimental é `10.0.0.190`. Os snapshots originais incluem identificadores de interfaces e têm acesso local. A [auditoria experimental](../results/processed/auditoria/relatorios/02_auditoria_experimental.md) liga os registros de ambiente às tentativas.

O MPI ocupa até quatro slots por nó na ordem do hostfile, com afinidade por núcleo. O exemplo `hello.c` do manual verifica a infraestrutura. Os comandos da campanha e os registros por rank estão descritos no [protocolo experimental](protocolo-experimental.md).

## Conferência da instalação

| Verificação | Evidência esperada |
| --- | --- |
| Rede do cluster | O `server` resolve os sete nós de cálculo e o `nfs` na rede cabeada. As interfaces negociam a velocidade registrada no [inventário](hardware.md). |
| Armazenamento | No `nfs`, a exportação está limitada à rede privada. No `server` e nos sete nós, `findmnt -t nfs,nfs4` mostra a montagem no caminho comum com `vers=3`. |
| SSH e MPI | O coordenador acessa os nós de cálculo por chave. O teste em C do manual deve imprimir o rank e o host. Compare os hosts com o hostfile, que contém quatro slots por nó de cálculo. |
| Ambiente de execução | Os nós de cálculo registram Open MPI 4.1.0, `ondemand` e limite de escala de 1.500 MHz. Confirme as versões e a política de frequência antes de iniciar uma nova série. |

O [guia de integração](GUIA_DE_INTEGRACAO.md#informações-a-extrair-do-ambiente) reúne as consultas de leitura para registrar essas condições por nó.

Consulte as [configurações preservadas](../config/README.md), o [inventário de software](ambiente-software.md) e as notas sobre [hwloc e DRM](investigacoes/correcao-hwloc-drm.md) e [frequência da CPU](investigacoes/politica-frequencia-cpu.md). O acervo disponível ainda carece da imagem usada, dos arquivos completos de serviços e da evidência da intervenção em hwloc/DRM.
