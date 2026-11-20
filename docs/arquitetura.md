# Arquitetura do cluster

| Nós | Função |
| --- | --- |
| `server` | Administração do cluster e execução de processos MPI |
| `node1` a `node7` | Execução de processos MPI |
| `nfs` | Armazenamento compartilhado via NFSv3, fora da execução dos benchmarks |

Um switch Ethernet interliga os nove dispositivos em `10.0.0.0/24`. O `server` fornece DHCP e DNS local e faz o encaminhamento da rede cabeada para o Wi-Fi no roteiro de instalação. O Open MPI coordena a execução distribuída entre os oito nós computacionais, com lançamento remoto via OpenSSH e programas disponíveis no compartilhamento NFSv3.

O [manual 5.0](configurando-o-cluster-5.0.md) inclui o diagrama da montagem. Os endereços observados na campanha e a montagem NFS estão no [resumo da configuração](configuracao-cluster.md). As velocidades negociadas constam do [inventário de hardware](hardware.md).
