# Configurando o cluster 5.0

> Manual de montagem do cluster fornecido pelo pesquisador. Esta cópia usa campos de preenchimento nas reservas DHCP e solicita a credencial do Wi-Fi de forma interativa. Preencha os campos com os dados da rede e dos equipamentos de sua instalação. Consulte a [configuração documentada](configuracao-cluster.md) para relacionar o procedimento às condições registradas na campanha.

# Visão Geral

A ideia é criar um cluster de processamento paralelo composto por TV Boxes. O sistema operacional utilizado é uma versão customizada do Armbian feita pelo CRC-LAVRAS, sem interface gráfica, sem pacotes desnecessários que possam atrapalhar o desempenho e com os sistemas de áudio e Bluetooth desabilitados.

O cluster será composto por:

- uma TV Box atuando como **HEAD**, responsável pelo gerenciamento da rede, DHCP, DNS, NAT e execução do MPI;
    
- uma TV Box dedicada ao **NFS**, responsável exclusivamente pelo armazenamento compartilhado;
    
- outras TV Boxes funcionando como **NODEs**, responsáveis pelo processamento paralelo;
    
- um switch de rede conectando todas as máquinas.
    

A arquitetura de rede utilizada neste manual é:

|Função|Nome|Endereço|
|---|---|---|
|HEAD|`server`|`10.0.0.100`|
|Servidor NFS|`nfs`|`10.0.0.99`|
|NODEs|`node1`, `node2`, ...|`10.0.0.101+`|
|Rede|—|`10.0.0.0/24`|
|Faixa DHCP|—|`10.0.0.150–200`|

O HEAD possui IP estático. Os NODEs e o servidor NFS utilizam DHCP, mas recebem endereços fixos por meio de reservas no `dnsmasq`, associadas ao endereço MAC de cada equipamento.

O servidor NFS possui um endereço reservado (`10.0.0.99`) fora da faixa dinâmica utilizada pelos NODEs.

A pasta compartilhada utilizada pelo cluster será:

```text
/home/minipc/nfs
```

Essa pasta estará fisicamente armazenada no servidor `nfs`, mas será montada pelos demais computadores no mesmo caminho `/home/minipc/nfs`. Dessa maneira, programas, arquivos de configuração, códigos e o hostfile do MPI podem ser acessados a partir de qualquer máquina.

Uma distinção importante:

> O servidor `nfs` **não é um NODE de processamento** e não deve ser adicionado ao arquivo `cluster` utilizado pelo MPI.

A partir desta versão, a configuração foi organizada para que um leitor consiga montar cada máquina **sem possuir uma Golden Image previamente preparada**. Durante o processo, alguns pontos serão identificados como possíveis pontos de criação de uma Golden Image.

---

# FASE 1 — Configurando o HEAD

O HEAD será responsável por:

- conexão do cluster à internet;
    
- DHCP;
    
- DNS local;
    
- NAT;
    
- encaminhamento IP;
    
- acesso SSH;
    
- execução do MPI.
    

Ele **não será mais o servidor NFS**.

---

## 1.1 — Atualização do sistema

No HEAD:

```bash
sudo apt update
sudo apt upgrade
```

---

## 1.2 — Instalação dos pacotes necessários

Instalar o cliente NFS. O HEAD utilizará o NFS apenas para acessar a pasta compartilhada localizada no servidor `nfs`:

```bash
sudo apt-get install nfs-common
```

Instalar o OpenSSH Server:

```bash
sudo apt-get install openssh-server
```

Instalar o Open MPI:

```bash
sudo apt-get install openmpi-bin
sudo apt-get install libopenmpi-dev
```

Instalar o `ntpdate` para sincronização de horário:

```bash
sudo apt-get install ntpdate
```

Reiniciar:

```bash
sudo reboot
```

---

## 1.3 — Configuração da interface de rede — eth0

O HEAD será a única máquina do cluster com IP definido manualmente.

Instalar o `net-tools`, caso necessário:

```bash
sudo apt-get install net-tools
```

Editar:

```bash
sudo nano /etc/network/interfaces
```

Inserir:

```text
auto eth0
allow-hotplug eth0
iface eth0 inet static
    address 10.0.0.100
    netmask 255.255.255.0
    network 10.0.0.0
```

Reiniciar a rede:

```bash
sudo /etc/init.d/networking restart
```

Confirmar:

```bash
ip addr show eth0
```

O endereço `10.0.0.100` deve estar atribuído à interface.

---

## 1.4 — Configuração do Wi-Fi

> **Atenção:** O Armbian com interface gráfica utiliza o NetworkManager para administrar o Wi-Fi. Não configure `wpa_supplicant` manualmente e não adicione `wlan0` ao `/etc/network/interfaces`.

Verificar:

```bash
systemctl status NetworkManager
```

Listar redes:

```bash
nmcli device wifi list
```

Conectar:

```bash
sudo nmcli --ask device wifi connect "NOME_DA_REDE"
```

Verificar:

```bash
ip addr show wlan0
```

O NetworkManager armazenará a configuração e reconectará automaticamente após reinicializações.

Se houver conflito com processos `wpa_supplicant`:

```bash
sudo killall wpa_supplicant
sudo systemctl restart NetworkManager
```

---

## 1.5 — Configuração do IP Forwarding

O HEAD precisa encaminhar pacotes entre a rede cabeada do cluster e a rede Wi-Fi.

Adicionar:

```bash
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
```

Aplicar:

```bash
sudo sysctl -p
```

Confirmar:

```bash
cat /proc/sys/net/ipv4/ip_forward
```

O resultado deve ser:

```text
1
```

---

## 1.6 — Configuração do NAT com iptables

Como os NODEs utilizam endereços privados, o HEAD precisa realizar NAT para que eles consigam acessar a internet através do Wi-Fi.

Aplicar:

```bash
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
```

Permitir saída do cluster:

```bash
sudo iptables -A FORWARD -i eth0 -o wlan0 -j ACCEPT
```

Permitir respostas:

```bash
sudo iptables -A FORWARD -i wlan0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

> **Atenção:** Execute cada regra uma única vez. Para verificar as regras existentes:

```bash
sudo iptables -t nat -L -n -v
sudo iptables -L FORWARD -n -v
```

Instalar o mecanismo de persistência:

```bash
sudo apt-get install iptables-persistent
```

Salvar:

```bash
sudo netfilter-persistent save
```

---

## 1.7 — Configuração do hostname

Editar:

```bash
sudo nano /etc/hostname
```

Definir:

```text
server
```

Também é recomendável garantir que o hostname seja aplicado:

```bash
sudo hostnamectl set-hostname server
```

---

## 1.8 — DHCP + DNS com dnsmasq

O `dnsmasq` será responsável por atribuir endereços aos equipamentos e resolver os nomes dentro do cluster.

Antes de instalar, verificar se existe outro serviço ocupando a porta 53:

```bash
sudo ss -lntup | grep :53
```

Instalar:

```bash
sudo apt-get install dnsmasq
```

Editar:

```bash
sudo nano /etc/dnsmasq.conf
```

Configurar:

```text
# --- Interface ---
interface=eth0
bind-interfaces
except-interface=wlan0

# --- DHCP ---
dhcp-range=10.0.0.150,10.0.0.200,12h
dhcp-option=option:router,10.0.0.100
dhcp-option=option:dns-server,10.0.0.100

# --- DNS local ---
domain=cluster.local
expand-hosts
local=/cluster.local/

# --- DNS externo ---
server=8.8.8.8
no-resolv

# --- Logs ---
log-dhcp
log-queries
```

As três linhas relacionadas ao DHCP são importantes:

```text
dhcp-range=10.0.0.150,10.0.0.200,12h
dhcp-option=option:router,10.0.0.100
dhcp-option=option:dns-server,10.0.0.100
```

A primeira define a faixa de endereços disponíveis.

A segunda informa aos clientes que `10.0.0.100` é o gateway.

A terceira informa que o próprio HEAD deve ser utilizado como servidor DNS.

O `dnsmasq` receberá posteriormente as reservas individuais dos equipamentos.

Iniciar:

```bash
sudo systemctl restart dnsmasq
sudo systemctl enable dnsmasq
```

Verificar:

```bash
sudo systemctl status dnsmasq
```

Se houver problemas:

```bash
sudo journalctl -u dnsmasq -n 50 --no-pager
```

### Observação sobre o próprio HEAD

Os NODEs receberão automaticamente `10.0.0.100` como servidor DNS através do DHCP.

O HEAD, entretanto, possui IP estático e não recebe essa configuração automaticamente.

Por isso, para nomes importantes como `nfs`, pode ser conveniente manter entradas locais no `/etc/hosts`.

Por enquanto, adicionar:

```bash
sudo nano /etc/hosts
```

Posteriormente será adicionada:

```text
10.0.0.99 nfs
```

As entradas dos NODEs poderão ser adicionadas conforme forem cadastrados.

---

## 1.9 — Configuração do SSH

Verificar se o servidor SSH está ativo:

```bash
sudo systemctl status ssh
```

Gerar uma chave:

```bash
ssh-keygen -t rsa -P ""
```

Autorizar a própria chave:

```bash
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

Autorizar acesso ao próprio HEAD:

```bash
ssh-copy-id minipc@server
```

Substitua `minipc` pelo usuário utilizado no sistema, se necessário.

Verificar:

```bash
whoami
```

---

## 1.10 — Estado do HEAD

Neste ponto, o HEAD já possui:

- IP estático `10.0.0.100`;
    
- acesso à internet via Wi-Fi;
    
- NAT;
    
- IP forwarding;
    
- DHCP;
    
- DNS;
    
- SSH;
    
- Open MPI.
    

O NFS ainda não foi montado porque o servidor `nfs` ainda será configurado.

---

# FASE 2 — Configurando o servidor NFS

Agora será configurada uma TV Box exclusivamente para armazenamento compartilhado.

> **IMPORTANTE:** Esta TV Box será configurada manualmente neste momento. Não é necessário possuir uma Golden Image.

O servidor será:

```text
hostname: nfs
IP:       10.0.0.99
```

O endereço será fornecido pelo DHCP do HEAD através de uma reserva baseada no MAC address.

---

## 2.1 — Atualização do sistema

Na TV Box que será utilizada como servidor NFS:

```bash
sudo apt update
sudo apt upgrade
```

---

## 2.2 — Configuração da rede

Editar:

```bash
sudo nano /etc/network/interfaces
```

Configurar a interface Ethernet como DHCP:

```text
auto eth0
allow-hotplug eth0
iface eth0 inet dhcp
```

Reiniciar:

```bash
sudo /etc/init.d/networking restart
```

Verificar:

```bash
ip addr show eth0
```

Neste momento, a máquina deverá receber algum endereço da faixa:

```text
10.0.0.150–200
```

Isso é temporário. O endereço `10.0.0.99` será reservado posteriormente no HEAD.

---

## 2.3 — Definir o hostname

Definir:

```bash
sudo hostnamectl set-hostname nfs
```

Ou editar:

```bash
sudo nano /etc/hostname
```

Conteúdo:

```text
nfs
```

Verificar:

```bash
hostname
```

O resultado deve ser:

```text
nfs
```

---

## 2.4 — Instalar o servidor NFS

Instalar:

```bash
sudo apt-get install nfs-kernel-server
```

Instalar também o `rsync`, que será útil para copiar os arquivos do cluster:

```bash
sudo apt-get install rsync
```

Verificar o serviço:

```bash
sudo systemctl status nfs-kernel-server
```

---

## 2.5 — Criar a pasta compartilhada

A pasta utilizada pelo cluster será:

```text
/home/minipc/nfs
```

Criar:

```bash
sudo mkdir -p /home/minipc/nfs
```

Alterar o proprietário:

```bash
sudo chown minipc:minipc /home/minipc/nfs
```

Confirmar:

```bash
ls -ld /home/minipc/nfs
```

---

## 2.6 — Configurar a exportação NFS

Editar:

```bash
sudo nano /etc/exports
```

Adicionar:

```text
/home/minipc/nfs 10.0.0.0/24(rw,sync,no_subtree_check)
```

Essa configuração permite que máquinas da rede `10.0.0.0/24` montem a pasta.

Os principais parâmetros são:

- `rw`: permite leitura e escrita;
    
- `sync`: confirma operações após serem efetivamente processadas pelo servidor;
    
- `no_subtree_check`: evita verificações desnecessárias da árvore de diretórios.
    

Aplicar:

```bash
sudo exportfs -ra
```

Verificar:

```bash
sudo exportfs -v
```

Também é possível verificar os serviços RPC:

```bash
sudo rpcinfo -p localhost
```

---

## 2.7 — Registrar o servidor NFS no DHCP

Agora é necessário voltar ao HEAD.

No HEAD, descobrir o MAC address da TV Box `nfs`:

```bash
sudo arp-scan --interface=eth0 --localnet
```

Se necessário:

```bash
sudo apt-get install arp-scan
```

Também é possível verificar os leases do `dnsmasq`:

```bash
cat /var/lib/misc/dnsmasq.leases
```

Identificar o MAC correspondente ao equipamento `nfs`.

No HEAD, editar:

```bash
sudo nano /etc/dnsmasq.conf
```

Adicionar:

```text
dhcp-host=MAC_NFS,nfs,10.0.0.99
```

Substitua `MAC_NFS` pelo MAC real da TV Box.

Reiniciar:

```bash
sudo systemctl restart dnsmasq
```

---

## 2.8 — Renovar o endereço do servidor NFS

Voltar ao equipamento `nfs`.

Renovar o DHCP:

```bash
sudo dhclient -r eth0
sudo dhclient eth0
```

Ou simplesmente reiniciar:

```bash
sudo reboot
```

Após o reboot:

```bash
ip addr show eth0
```

O endereço deverá ser:

```text
10.0.0.99
```

No HEAD, testar:

```bash
ping nfs
```

E:

```bash
ping 10.0.0.99
```

---

## 2.9 — Registrar o NFS no `/etc/hosts` do HEAD

Como o HEAD possui endereço estático e não recebe sua própria configuração DNS via DHCP, adicionar:

```bash
sudo nano /etc/hosts
```

Linha:

```text
10.0.0.99 nfs
```

Testar:

```bash
ping nfs
```

---

## 2.10 — Testar o NFS a partir do HEAD

Antes de configurar qualquer NODE, é importante verificar se o servidor NFS está funcionando.

No HEAD:

```bash
sudo mkdir -p /mnt/nfs-teste
```

Montar temporariamente:

```bash
sudo mount -t nfs -o vers=3 10.0.0.99:/home/minipc/nfs /mnt/nfs-teste
```

Verificar:

```bash
df -h
```

Criar um arquivo de teste:

```bash
sudo touch /mnt/nfs-teste/teste-nfs
```

No servidor `nfs`, verificar:

```bash
ls -l /home/minipc/nfs
```

O arquivo `teste-nfs` deverá aparecer.

Depois, no HEAD:

```bash
sudo rm /mnt/nfs-teste/teste-nfs
sudo umount /mnt/nfs-teste
```

Neste momento, o servidor NFS está funcional.

---

# FASE 3 — Configurando o HEAD como cliente NFS

Agora que o servidor `nfs` existe, o próprio HEAD poderá montar a pasta compartilhada.

No HEAD:

```bash
sudo mkdir -p /home/minipc/nfs
```

Editar:

```bash
sudo nano /etc/fstab
```

Adicionar:

```text
10.0.0.99:/home/minipc/nfs /home/minipc/nfs nfs rw,sync,hard,vers=3 0 0
```

Montar:

```bash
sudo mount -a
```

Verificar:

```bash
df -h
```

A pasta deverá aparecer como algo semelhante a:

```text
10.0.0.99:/home/minipc/nfs
```

Testar:

```bash
touch /home/minipc/nfs/teste-head
```

No servidor `nfs`:

```bash
ls /home/minipc/nfs
```

O arquivo deve estar presente.

Remover o teste:

```bash
rm /home/minipc/nfs/teste-head
```

> **Nota:** O HEAD agora é cliente NFS. Ele não deve possuir `nfs-kernel-server` nem exportar a pasta compartilhada.

---

# FASE 4 — Configurando os NODEs

> **Repita esta fase para cada NODE.**

Cada NODE será configurado manualmente na primeira vez. Não é necessário possuir uma Golden Image.

A configuração será praticamente idêntica entre eles.

---

## 4.1 — Atualização

No NODE:

```bash
sudo apt update
sudo apt upgrade
```

---

## 4.2 — Instalação dos pacotes

Instalar o cliente NFS:

```bash
sudo apt-get install nfs-common
```

Instalar SSH:

```bash
sudo apt-get install openssh-server
```

Instalar Open MPI:

```bash
sudo apt-get install openmpi-bin
sudo apt-get install libopenmpi-dev
```

Instalar sincronização de horário:

```bash
sudo apt-get install ntpdate
```

Reiniciar:

```bash
sudo reboot
```

---

## 4.3 — Configuração da rede

Editar:

```bash
sudo nano /etc/network/interfaces
```

Configurar:

```text
auto eth0
allow-hotplug eth0
iface eth0 inet dhcp
```

Reiniciar:

```bash
sudo /etc/init.d/networking restart
```

Verificar:

```bash
ip addr show eth0
```

O NODE deverá receber temporariamente um endereço da faixa:

```text
10.0.0.150–200
```

---

## 4.4 — Configuração do hostname

Cada NODE precisa possuir um nome próprio.

Para o primeiro:

```bash
sudo hostnamectl set-hostname node1
```

Para o segundo:

```bash
sudo hostnamectl set-hostname node2
```

E assim por diante.

Verificar:

```bash
hostname
```

> O hostname é a principal informação que precisa ser individualizada em cada NODE. O IP será determinado posteriormente pelo HEAD através da reserva DHCP.

---

## 4.5 — Configuração do NFS

Criar o ponto de montagem:

```bash
sudo mkdir -p /home/minipc/nfs
```

Editar:

```bash
sudo nano /etc/fstab
```

Adicionar:

```text
10.0.0.99:/home/minipc/nfs /home/minipc/nfs nfs rw,sync,hard,vers=3 0 0
```

A opção `vers=3` determina o uso do NFSv3.

Montar:

```bash
sudo mount -a
```

Verificar:

```bash
df -h
```

A saída deverá indicar:

```text
10.0.0.99:/home/minipc/nfs
```

Testar:

```bash
touch /home/minipc/nfs/teste-node
```

No servidor `nfs`, verificar se o arquivo apareceu:

```bash
ls /home/minipc/nfs
```

Depois removê-lo:

```bash
rm /home/minipc/nfs/teste-node
```

---

## 4.6 — Teste da rede

No NODE:

```bash
ping 10.0.0.100
```

O HEAD deve responder.

Testar acesso à internet:

```bash
ping 8.8.8.8
```

Testar DNS:

```bash
ping google.com
```

Testar o servidor NFS:

```bash
ping nfs
```

Se todos funcionarem, a comunicação básica está correta.

---

## 4.7 — Estado em que uma Golden Image poderia ser criada

Neste ponto, o NODE já possui:

- sistema atualizado;
    
- rede Ethernet configurada como DHCP;
    
- `nfs-common`;
    
- `openssh-server`;
    
- Open MPI;
    
- `ntpdate`;
    
- ponto de montagem `/home/minipc/nfs`;
    
- entrada correspondente no `/etc/fstab`;
    
- conectividade com o HEAD;
    
- acesso ao servidor NFS.
    

**Este é um excelente ponto para criar uma Golden Image de NODE.**

A imagem, entretanto, ainda não deve conter:

- hostname definitivo (`node1`, `node2`, etc.);
    
- configuração específica de DHCP por MAC;
    
- identidade SSH de host compartilhada;
    
- `machine-id` compartilhado.
    

Esses elementos precisam ser individualizados após a clonagem.

Se não houver interesse em utilizar Golden Image, simplesmente continue o manual.

---

# FASE 5 — Registrando o NODE no HEAD

Agora o NODE já está funcional, mas ainda utiliza um endereço DHCP genérico.

O objetivo desta fase é transformar esse endereço em uma reserva permanente.

> **Execute esta fase no HEAD.**

---

## 5.1 — Descobrir o MAC do NODE

No HEAD:

```bash
sudo arp-scan --interface=eth0 --localnet
```

Também é possível consultar:

```bash
cat /var/lib/misc/dnsmasq.leases
```

Identificar o MAC correspondente ao NODE.

---

## 5.2 — Criar a reserva DHCP

Editar:

```bash
sudo nano /etc/dnsmasq.conf
```

Para `node1`:

```text
dhcp-host=MAC_NODE1,node1,10.0.0.101
```

Para `node2`:

```text
dhcp-host=MAC_NODE2,node2,10.0.0.102
```

E assim sucessivamente.

A faixa de IPs reservados pode seguir:

```text
server → 10.0.0.100
nfs    → 10.0.0.99
node1  → 10.0.0.101
node2  → 10.0.0.102
node3  → 10.0.0.103
...
```

Reiniciar:

```bash
sudo systemctl restart dnsmasq
```

---

## 5.3 — Renovar o DHCP no NODE

Voltar ao NODE:

```bash
sudo dhclient -r eth0
sudo dhclient eth0
```

Ou reiniciar:

```bash
sudo reboot
```

Verificar:

```bash
ip addr show eth0
```

O `node1`, por exemplo, deverá agora possuir:

```text
10.0.0.101
```

---

## 5.4 — Testar DNS

No HEAD:

```bash
ping node1
```

E:

```bash
nslookup node1
```

O DNS fornecido pelo `dnsmasq` deverá resolver o hostname para o endereço reservado.

Isso também permite que os outros computadores do cluster utilizem:

```bash
ssh node1
```

em vez de:

```bash
ssh 10.0.0.101
```

---

# FASE 6 — Configurando o acesso SSH entre as máquinas

O MPI utiliza SSH para iniciar processos remotamente. Por isso, o HEAD precisa conseguir acessar os NODEs sem solicitar senha.

No HEAD, gerar a chave caso ainda não exista:

```bash
ssh-keygen -t rsa -P ""
```

Copiar a chave para o NODE:

```bash
ssh-copy-id minipc@node1
```

Testar:

```bash
ssh node1
```

O acesso deverá ocorrer sem solicitar a senha do usuário.

Repetir para cada NODE:

```bash
ssh-copy-id minipc@node2
ssh-copy-id minipc@node3
```

etc.

Também é possível autorizar o próprio HEAD:

```bash
ssh-copy-id minipc@server
```

---

# FASE 7 — Preparando o ambiente MPI

Como `/home/minipc/nfs` é compartilhado pelo NFS, arquivos criados nessa pasta podem ser acessados por todas as máquinas.

Isso permite manter o hostfile e os programas MPI em um único local.

No HEAD:

```bash
cd /home/minipc/nfs
```

---

## 7.1 — Criar o arquivo de hosts

Criar:

```bash
nano cluster
```

Exemplo:

```text
server
node1
node2
```

Com indicação de slots:

```text
server slots=4
node1 slots=4
node2 slots=4
```

O arquivo deve conter somente as máquinas que participarão do processamento.

**Não adicionar:**

```text
nfs
```

O servidor NFS fornece armazenamento compartilhado, mas não participa automaticamente do processamento paralelo.

---

# FASE 8 — Testando o MPI

## 8.1 — Criar o programa de teste

Na pasta compartilhada:

```bash
cd /home/minipc/nfs
nano hello.c
```

Conteúdo:

```c
#include "mpi.h"
#include <stdio.h>

int main(int argc, char *argv[]) {
    int processo;
    int n_Processos;
    int tamanho_nome;
    char nome_computador[MPI_MAX_PROCESSOR_NAME];

    MPI_Init(&argc, &argv);

    MPI_Comm_size(MPI_COMM_WORLD, &n_Processos);
    MPI_Comm_rank(MPI_COMM_WORLD, &processo);
    MPI_Get_processor_name(nome_computador, &tamanho_nome);

    fprintf(
        stderr,
        "Olá mundo! Eu sou o processo %d no computador %s\n",
        processo,
        nome_computador
    );

    MPI_Finalize();

    return 0;
}
```

---

## 8.2 — Compilar

```bash
mpicc hello.c -o hello
```

Como o arquivo está no NFS, o executável deverá estar disponível no mesmo caminho em todos os NODEs.

---

## 8.3 — Executar

```bash
mpirun -np 8 --hostfile cluster ./hello
```

O MPI deverá distribuir os oito processos entre as máquinas listadas.

A saída deverá indicar o rank de cada processo e o computador responsável por executá-lo.

Por exemplo:

```text
Olá mundo! Eu sou o processo 0 no computador server
Olá mundo! Eu sou o processo 1 no computador node1
Olá mundo! Eu sou o processo 2 no computador node1
Olá mundo! Eu sou o processo 3 no computador node2
...
```

A distribuição exata depende do número de slots disponíveis e da configuração do hostfile.

---

# FASE 9 — Adicionando novos NODEs

Depois que o primeiro NODE tiver sido configurado manualmente, existem duas possibilidades.

## 9.1 — Sem Golden Image

Um novo NODE pode ser configurado seguindo:

1. Fase 4 — configuração do NODE;
    
2. Fase 5 — registro no DHCP;
    
3. Fase 6 — configuração do SSH;
    
4. Fase 7 — adicionar o NODE ao hostfile;
    
5. Fase 8 — testar o MPI.
    

Esse procedimento não depende de nenhum arquivo previamente preparado.

---

## 9.2 — Com Golden Image

Depois que a Fase 4.7 for concluída e todos os componentes comuns estiverem funcionando, o estado do NODE pode ser transformado em uma Golden Image.

A partir daí, para adicionar um novo NODE:

1. Gravar a Golden Image no novo equipamento;
    
2. inicializar o equipamento;
    
3. gerar uma nova identidade SSH de host;
    
4. gerar um novo `machine-id`;
    
5. definir o hostname (`nodeX`);
    
6. conectar ao switch;
    
7. descobrir o MAC pelo HEAD;
    
8. criar a reserva DHCP;
    
9. testar o acesso SSH;
    
10. adicionar o NODE ao arquivo `cluster`.
    

---

# FASE 10 — Preparação da Golden Image

A Golden Image não é necessária para montar o cluster. Ela é apenas uma forma de transformar a configuração repetitiva de um NODE em uma imagem reutilizável.

Antes de gerar a imagem, o NODE de referência deve possuir toda a configuração comum:

- Armbian configurado;
    
- sistema atualizado;
    
- Ethernet em DHCP;
    
- `nfs-common`;
    
- `openssh-server`;
    
- Open MPI;
    
- `ntpdate`;
    
- `/home/minipc/nfs` criado;
    
- `/etc/fstab` apontando para `10.0.0.99:/home/minipc/nfs`;
    
- conectividade com o servidor NFS;
    
- ferramentas necessárias ao funcionamento do cluster.
    

Antes de clonar, entretanto, devem ser removidas as identidades específicas daquela máquina.

### Regenerar as chaves SSH

Remover as chaves de host:

```bash
sudo rm /etc/ssh/ssh_host_*
```

Reconfigurar o OpenSSH:

```bash
sudo dpkg-reconfigure openssh-server
```

Ou reiniciar o serviço depois que as novas chaves forem geradas:

```bash
sudo systemctl restart ssh
```

### Regenerar o machine-id

Remover:

```bash
sudo rm /etc/machine-id
```

Gerar novamente:

```bash
sudo systemd-machine-id-setup
```

### Não gravar informações específicas do NODE

A Golden Image não deve conter:

- `node1` como hostname definitivo;
    
- uma reserva DHCP específica;
    
- um IP estático de NODE;
    
- chaves SSH de host específicas;
    
- um `machine-id` específico.
    

O arquivo `/etc/fstab`, por outro lado, **pode permanecer configurado**, pois todos os NODEs utilizarão o mesmo servidor:

```text
10.0.0.99:/home/minipc/nfs /home/minipc/nfs nfs rw,sync,hard,vers=3 0 0
```

Isso é justamente uma das vantagens da arquitetura: o armazenamento compartilhado não depende do endereço individual do NODE.

---

# Observação — por que o NFS possui configuração própria

O servidor NFS não deve simplesmente receber a mesma configuração utilizada pelos NODEs.

Um NODE é cliente NFS e, portanto, precisa de:

```bash
nfs-common
```

e de uma montagem como:

```text
10.0.0.99:/home/minipc/nfs /home/minipc/nfs nfs rw,sync,hard,vers=3 0 0
```

Já o servidor NFS precisa de:

```bash
nfs-kernel-server
```

e deve exportar:

```text
/home/minipc/nfs 10.0.0.0/24(rw,sync,no_subtree_check)
```

Consequentemente, uma Golden Image preparada para NODEs **não deve ser utilizada diretamente como servidor NFS** sem antes remover a configuração de cliente NFS e instalar/configurar o servidor.

O servidor `nfs` deve ser tratado como uma função independente do cluster de processamento.

---

# Observação — arquitetura final

Ao final da configuração, a arquitetura será aproximadamente:

```text
                         INTERNET
                             │
                           Wi-Fi
                             │
                    ┌─────────────────┐
                    │      server     │
                    │      HEAD       │
                    │  10.0.0.100    │
                    │                 │
                    │ DHCP / DNS      │
                    │ NAT / Routing   │
                    │ SSH / MPI       │
                    └────────┬────────┘
                             │
                         Ethernet
                             │
                    ┌────────┴────────┐
                    │     SWITCH      │
                    └─┬────┬────┬────┘
                      │    │    │
              ┌───────┘    │    └────────┐
              │            │             │
       ┌──────▼─────┐ ┌────▼─────┐ ┌────▼─────┐
       │    nfs     │ │  node1   │ │  node2   │
       │ 10.0.0.99  │ │10.0.0.101│ │10.0.0.102│
       │            │ │          │ │          │
       │ NFS Server │ │ MPI      │ │ MPI      │
       └────────────┘ └──────────┘ └──────────┘
```

O fluxo de funcionamento é:

```text
NODE
  │
  ├── DHCP ────────────────► HEAD
  │                           │
  │                           └── fornece IP + DNS + gateway
  │
  ├── DNS ──────────────────► HEAD
  │
  ├── Internet ─────────────► HEAD ───► NAT ───► Wi-Fi
  │
  ├── NFS ──────────────────► nfs
  │                            │
  │                            └── /home/minipc/nfs
  │
  └── MPI/SSH ◄───────────── HEAD
```

O `HEAD` administra o cluster, mas o armazenamento compartilhado foi separado dele. Isso evita que a máquina responsável pelo controle da rede e pelo lançamento dos processos MPI também precise assumir a carga do servidor NFS.

---

# Fluxo resumido de instalação

Para uma instalação completamente nova, a ordem recomendada é:

```text
1. Configurar HEAD
       │
       ├── IP estático
       ├── Wi-Fi
       ├── NAT
       ├── IP forwarding
       ├── DHCP
       ├── DNS
       └── SSH
       │
       ▼
2. Configurar servidor NFS
       │
       ├── DHCP
       ├── hostname nfs
       ├── nfs-kernel-server
       ├── /home/minipc/nfs
       └── /etc/exports
       │
       ▼
3. Montar NFS no HEAD
       │
       ▼
4. Configurar NODE
       │
       ├── DHCP
       ├── hostname
       ├── Open MPI
       ├── SSH
       └── cliente NFS
       │
       ▼
5. Registrar NODE no HEAD
       │
       ├── MAC
       ├── reserva DHCP
       └── DNS
       │
       ▼
6. Configurar SSH
       │
       ▼
7. Adicionar NODE ao hostfile
       │
       ▼
8. Testar MPI
       │
       ▼
9. Opcionalmente criar Golden Image
       │
       ▼
10. Novos NODEs podem ser clonados
```

A Golden Image, portanto, não é uma dependência da instalação. Ela é uma **otimização posterior**: primeiro o procedimento manual deve funcionar de forma independente; somente depois faz sentido transformá-lo em uma imagem para acelerar a expansão do cluster.