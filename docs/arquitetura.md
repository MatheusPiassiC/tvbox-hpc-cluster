# Arquitetura do cluster

| Nós | Função |
| --- | --- |
| `server` | Administração do cluster e execução de processos MPI |
| `node1` a `node7` | Execução de processos MPI |
| `nfs` | Armazenamento compartilhado via NFSv3 |

O switch Intelbras SG 2400 QR interliga as nove TV Boxes H7 na rede `10.0.0.0/24`. O `server` fornece DHCP e DNS via `dnsmasq`, com encaminhamento IPv4 e conexão externa em `wlan0`. O Open MPI usa 32 slots no `server` e em `node1` a `node7`, com lançamento remoto via OpenSSH e programas disponíveis no compartilhamento NFSv3. O `nfs` fica fora do hostfile e da execução MPI.

O [manual 5.0](configurando-o-cluster-5.0.md) inclui o diagrama da montagem. Os endereços observados na campanha e a montagem NFS estão no [resumo da configuração](configuracao-cluster.md). As velocidades negociadas constam do [inventário de hardware](hardware.md).
