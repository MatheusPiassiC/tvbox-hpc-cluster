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

## Inspeção de 23/11/2026

No registro do pesquisador, o `server` tinha `eth0=10.0.0.100/24`, rota da rede interna por `eth0` e rota padrão via `192.168.1.1` em `wlan0`. O valor de `net.ipv4.ip_forward` era `1`. A leitura das regras efetivas de NAT exigiu privilégio e ficou pendente. Os oito nós MPI negociaram 100 Mb/s em full-duplex. [Arquitetura](arquitetura.md) · [Hardware](hardware.md)

Em `nfs` (`10.0.0.99`), o arquivo `/etc/exports` registrava a exportação abaixo.

```text
/home/minipc/nfs 10.0.0.0/24(rw,sync,no_subtree_check)
```

As montagens observadas nos clientes usavam NFSv3 sobre TCP, opção `hard` e `rsize=wsize=262144` bytes. O `/etc/fstab` do `server` tinha uma entrada antiga comentada e a entrada ativa abaixo, com automontagem.

```text
10.0.0.99:/home/minipc/nfs /home/minipc/nfs nfs rw,sync,hard,vers=3,_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30 0 0
```

A consulta `exportfs -v` encontrou uma restrição de permissão. O diretório `/usr/sbin` estava fora do `PATH` do usuário e `showmount` ficou sem execução. O registro das montagens remotas sustenta a identificação do protocolo e das opções dos clientes.

## Conferência da instalação

| Verificação | Evidência esperada |
| --- | --- |
| Rede do cluster | O `server` resolve os sete nós de cálculo e o `nfs` na rede cabeada. As interfaces negociam a velocidade registrada no [inventário](hardware.md). |
| Armazenamento | No `nfs`, a exportação está limitada à rede privada. No `server` e nos sete nós, `findmnt -t nfs,nfs4` mostra a montagem no caminho comum com `vers=3`. |
| SSH e MPI | O coordenador acessa os nós de cálculo por chave. O teste em C do manual deve imprimir o rank e o host. Compare os hosts com o hostfile, que contém quatro slots por nó de cálculo. |
| Ambiente de execução | Os nós de cálculo registram Open MPI 4.1.0, `ondemand` e limite de escala de 1.500 MHz. Confirme as versões e a política de frequência antes de iniciar uma nova série. |

O [guia de integração](GUIA_DE_INTEGRACAO.md#informações-a-extrair-do-ambiente) reúne as consultas de leitura para registrar essas condições por nó.

O acervo reúne o hostfile original e os trechos de configuração registrados. A identificação por hash da imagem usada, o conjunto integral de arquivos dos serviços e o registro da intervenção em hwloc/DRM ainda estão pendentes. [Configurações preservadas](../config/README.md) · [Inventário de software](ambiente-software.md) · [Frequência da CPU](investigacoes/politica-frequencia-cpu.md) · [hwloc e DRM](investigacoes/correcao-hwloc-drm.md)
