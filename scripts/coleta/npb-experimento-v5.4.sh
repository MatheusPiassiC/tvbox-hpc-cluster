#!/bin/bash
# =============================================================================
# npb-experimento.sh
#
# Coleta experimental do NAS Parallel Benchmarks (NPB-MPI) com documentação
# voltada à reprodutibilidade.
#
# Uso:
#   ./npb-experimento-v5.4.sh <BENCHMARK> <CLASSE> ["lista de np"]
#
# Exemplos:
#   ./npb-experimento-v5.4.sh EP A
#   ./npb-experimento-v5.4.sh BT A
#   ./npb-experimento-v5.4.sh CG A "1 2 4"      # sobrescreve a lista padrão de np
#
# Para cada configuração de processos MPI, executa REPS (10) medições, uma
# por bloco em ordem aleatorizada, sem execuções de aquecimento nem reposição
# automática de falhas. Tentativas inválidas permanecem no CSV.
#
# Saídas (results/raw/<BENCHMARK>/), unidas por um ID numérico único:
#   npb_<ID>_<BENCH>_<CLASSE>.csv            uma linha por tentativa
#   npb_<ID>_<BENCH>_<CLASSE>_saidas.txt     saída original de cada execução
#   npb_<ID>_<BENCH>_<CLASSE>_ambiente.txt   documentação do ambiente
#
# As estatísticas (média, IC 95%, speedup, eficiência) NÃO são calculadas aqui:
# devem ser obtidas a partir do CSV por um script de análise separado.
#
# Variáveis de ambiente (todas opcionais):
#   PROJ=/home/minipc/nfs/benchmarks   raiz do projeto
#   NPB_DIR=$PROJ/NPB3.4.4/NPB3.4-MPI  diretório do NPB-MPI
#   HOSTFILE=/home/minipc/nfs/cluster  hostfile do MPI
#   RESULTADOS=$PROJ/results           raiz dos resultados
#   CONFIG_DIR=$PROJ/config            snapshots de compilação e configuração
#   MANUAL=$CONFIG_DIR/informacoes_manuais.txt
#   NPB_TARBALL=$PROJ/NPB3.4.4.tar.gz  tarball original (verifica modificações)
#   NFS_HOST=nfs   NFS_DIR=/home/minipc/nfs   IFACE=eth0
#   REPS=10 TIMEOUT=3600 TIMEOUT_KILL_AFTER=10 PAUSA=5
#   SEMENTE=20261114 TEMP_LIMITE_MC=75000
#   LIMITE_CPU=10   ESPERA_OCIOSO=60           (preparação antes de cada execução)
#   Não há monitoramento ativo durante o kernel: evita interferência na medição.
#   MPI_EXTRA="..."   NOTAS="..."
# =============================================================================

VERSAO_SCRIPT="5.4"
# v5.4: isola leitura do plano em FD 8; protege stdin do MPI; normaliza governor.
# v5.3: remove integralmente aquecimento; versão interna acompanha nome do arquivo.
# v5.2: correção da colisão entre script de sondagem e snapshot do arquivo principal.
# v3.0: afinidade explícita; blocos randomizados;
# validação estrita de ranks, hosts e binding; pré-condições rígidas;
# registro de política cpufreq e plano de execução.
#   3.1  comparação de políticas entre nós mantém estado de divergência de forma irreversível.
# Histórico:
#   2.1  monitoramento durante o kernel removido; --map-by/--rank-by slot explícitos;
#        validação do mapa de processos (compacto); timeout com --kill-after.
#   2.2  exit_code 137 só é TIMEOUT se o tempo de parede atingiu o limite (antes, um rank
#        morto por SIGKILL, ex.: falta de memória, era rotulado como TIMEOUT);
#        mapa de processos ausente grava n_nos/distribuicao como vazio/n-d (antes: 0).
#   2.3  corrige a contagem do mapa de processos: em execuções com vários nós o Open MPI
#        imprime o mapa uma vez por daemon, e a v2.1/2.2 contava tudo em duplicata
#        (ex.: np=1 -> 8 processos/8 nós) e marcava TODAS as execuções como INVALIDA.
export LC_ALL=C

PROJ=${PROJ:-/home/minipc/nfs/benchmarks}
NPB_DIR=${NPB_DIR:-$PROJ/NPB3.4.4/NPB3.4-MPI}
BIN_DIR=${BIN_DIR:-$NPB_DIR/bin}
HOSTFILE=${HOSTFILE:-/home/minipc/nfs/cluster}
RESULTADOS=${RESULTADOS:-$PROJ/results}
CONFIG_DIR=${CONFIG_DIR:-$PROJ/config}
MANUAL=${MANUAL:-$CONFIG_DIR/informacoes_manuais.txt}
NPB_TARBALL=${NPB_TARBALL:-$PROJ/NPB3.4.4.tar.gz}
NFS_HOST=${NFS_HOST:-nfs}
NFS_DIR=${NFS_DIR:-/home/minipc/nfs}
IFACE=${IFACE:-eth0}
REPS=${REPS:-10}
MAX_TENT=${MAX_TENT:-$((REPS * 2))}
TIMEOUT=${TIMEOUT:-3600}
TIMEOUT_KILL_AFTER=${TIMEOUT_KILL_AFTER:-10}
PAUSA=${PAUSA:-5}
SEMENTE=${SEMENTE:-20261114}
TEMP_LIMITE_MC=${TEMP_LIMITE_MC:-80000}
LIMITE_CPU=${LIMITE_CPU:-10}
ESPERA_OCIOSO=${ESPERA_OCIOSO:-60}
MPI_EXTRA=${MPI_EXTRA:-}
NOTAS=${NOTAS:-}

# ------------------------------------------------------------------ argumentos
uso() {
  echo "Uso: $0 <BENCHMARK> <CLASSE> [\"lista de np\"]"
  echo "  BENCHMARK: EP IS CG MG FT LU BT SP"
  echo "  CLASSE   : S W A B C D E"
  exit 1
}
BENCH_IN=${1:-}; CLASSE=${2:-}; NPS=${3:-}
[ -n "$BENCH_IN" ] && [ -n "$CLASSE" ] || uso
bench=${BENCH_IN,,}; BENCH=${BENCH_IN^^}; CLASSE=${CLASSE^^}
case $bench in ep|is|cg|mg|ft|lu|bt|sp) ;; *) echo "ERRO: benchmark inválido: $BENCH_IN"; uso;; esac
case $CLASSE in S|W|A|B|C|D|E) ;; *) echo "ERRO: classe inválida: $CLASSE"; uso;; esac
[[ $SEMENTE =~ ^[0-9]+$ ]] && [[ $TEMP_LIMITE_MC =~ ^[1-9][0-9]*$ ]] || { echo "ERRO: SEMENTE/TEMP_LIMITE_MC inválidos"; exit 1; }
[[ $REPS =~ ^[1-9][0-9]*$ ]] && [[ $MAX_TENT =~ ^[1-9][0-9]*$ ]] || { echo "ERRO: REPS/MAX_TENT inválidos"; exit 1; }
[[ $TIMEOUT =~ ^[1-9][0-9]*$ ]] && [[ $TIMEOUT_KILL_AFTER =~ ^[1-9][0-9]*$ ]] || { echo "ERRO: TIMEOUT/TIMEOUT_KILL_AFTER devem ser inteiros positivos"; exit 1; }
[[ $PAUSA =~ ^[0-9]+$ ]] && [[ $LIMITE_CPU =~ ^[0-9]+$ ]] && [[ $ESPERA_OCIOSO =~ ^[0-9]+$ ]] || { echo "ERRO: PAUSA/LIMITE_CPU/ESPERA_OCIOSO inválidos"; exit 1; }
[ "$MAX_TENT" -ge "$REPS" ] || { echo "ERRO: MAX_TENT deve ser >= REPS"; exit 1; }

if [ -z "$NPS" ]; then
  case $bench in
    bt|sp) NPS="1 4 9 16 25" ;;            # quadrados perfeitos
    *)     NPS="1 2 4 8 16 32" ;;          # EP: qualquer; demais: potências de 2
  esac
fi

np_valido() {  # EP: qualquer; BT/SP: quadrado perfeito; demais: potência de 2
  local n=$1
  [[ $n =~ ^[1-9][0-9]*$ ]] || return 1
  case $bench in
    ep)    return 0 ;;
    bt|sp) awk -v n="$n" 'BEGIN{r=int(sqrt(n)+0.5); exit !(r*r==n)}' ;;
    *)     (( (n & (n - 1)) == 0 )) ;;
  esac
}
for n in $NPS; do
  np_valido "$n" || { echo "ERRO: np=$n não é válido para $BENCH"; exit 1; }
done
read -ra NPS_ARR <<< "$NPS"
[ "${#NPS_ARR[@]}" -eq "$(printf "%s\n" "${NPS_ARR[@]}" | sort -u | wc -l)" ] || { echo "ERRO: np repetido na lista"; exit 1; }

BIN_FILE="$BIN_DIR/$bench.$CLASSE.x"
MEU_HOST=$(hostname); MEU_HOST_CURTO=$(hostname -s)
read -ra EXTRA <<< "$MPI_EXTRA"
MPI_OPTS=(--hostfile "$HOSTFILE" --map-by slot --rank-by slot --bind-to core --mca btl_tcp_if_include "$IFACE" --mca oob_tcp_if_include "$IFACE" --display-map --report-bindings)

# --------------------------------------------------- pré-requisitos e hostfile
for c in mpirun sha256sum awk flock timeout python3 ssh mktemp; do
  command -v "$c" >/dev/null || { echo "ERRO: comando '$c' não encontrado"; exit 1; }
done
[ -r "$HOSTFILE" ] || { echo "ERRO: hostfile não encontrado: $HOSTFILE"; exit 1; }
[ -x "$BIN_FILE" ] || { echo "ERRO: binário não encontrado/executável: $BIN_FILE"; exit 1; }

mapfile -t HOSTS < <(awk '!/^[[:space:]]*(#|$)/ && !s[$1]++ {print $1}' "$HOSTFILE")
[ "${#HOSTS[@]}" -gt 0 ] || { echo "ERRO: hostfile vazio"; exit 1; }
SLOTS_TOTAL=$(awk '!/^[[:space:]]*(#|$)/ {s=1; for(i=2;i<=NF;i++) if($i ~ /^slots=/){split($i,a,"="); s=a[2]} t+=s} END{print t+0}' "$HOSTFILE")
for n in $NPS; do
  [ "$n" -le "$SLOTS_TOTAL" ] || { echo "ERRO: np=$n excede o total de slots do hostfile ($SLOTS_TOTAL)"; exit 1; }
done
nos_minimos_para_np() {  # conta hosts necessários, preenchendo slots na ordem do hostfile
  awk -v np="$1" '
    BEGIN { restante=np }
    /^[[:space:]]*(#|$)/ { next }
    {
      slots=1
      for (i=2; i<=NF; i++) if ($i ~ /^slots=/) { split($i,a,"="); slots=a[2]+0 }
      if (restante > 0) { usados++; restante -= slots }
    }
    END { if (restante > 0) exit 1; print usados }' "$HOSTFILE"
}

# Execução única por vez (evita medições concorrentes)
exec 9> /tmp/npb-experimento.lock
flock -n 9 || { echo "ERRO: outra coleta está em andamento neste computador"; exit 1; }

# ---------------------------------------------------------- acesso aos nós
CTL_DIR=$(mktemp -d /tmp/npb-ssh.XXXXXX)
SSH_COMUM=(-o BatchMode=yes -o ConnectTimeout=5 -o ControlMaster=auto -o "ControlPath=$CTL_DIR/%C" -o ControlPersist=300)

eh_local() { [ "$1" = "$MEU_HOST" ] || [ "$1" = "$MEU_HOST_CURTO" ] || [ "$1" = "localhost" ]; }
exec_no() {     # exec_no <host> <comando>
  if eh_local "$1"; then bash -c "$2"; else ssh -n "${SSH_COMUM[@]}" "$1" "$2"; fi
}
script_no() {   # script_no <host> <script>  (script enviado por stdin)
  if eh_local "$1"; then printf '%s\n' "$2" | bash -s
  else printf '%s\n' "$2" | ssh "${SSH_COMUM[@]}" "$1" bash -s; fi
}
grava_no() {    # grava_no <host> <caminho>  (conteúdo via stdin)
  if eh_local "$1"; then cat > "$2" && chmod +x "$2"
  else ssh "${SSH_COMUM[@]}" "$1" "cat > '$2' && chmod +x '$2'"; fi
}
coleta() {      # coleta <host> <script>   (injeta IFACE e NFS_DIR)
  script_no "$1" "$(printf 'IFACE=%q\nNFS_DIR=%q\n%s' "$IFACE" "$NFS_DIR" "$2")"
}

LIMITACOES=()
PID=""; TMP=""; SAIDAS=""

# --------------------------------------------- scripts executados nos nós
read -r -d '' COLETA_ESTAVEL <<'EOF_EST'
export LC_ALL=C
sec() { printf '\n    [%s]\n' "$1"; }
ind() { sed 's/^/    /'; }
echo "    Hostname: $(hostname)"

sec "Identificação (autodetectada; fabricante/modelo comercial só por informação manual)"
if [ -r /proc/device-tree/model ]; then echo "    Modelo (device-tree): $(tr -d '\0' < /proc/device-tree/model)"; fi
if [ -r /proc/device-tree/compatible ]; then echo "    Compatible (device-tree): $(tr '\0' ' ' < /proc/device-tree/compatible)"; fi
if [ -r /etc/armbian-release ]; then
  grep -E '^(BOARD|BOARD_NAME|VERSION|BRANCH|LINUXFAMILY|IMAGE_TYPE)=' /etc/armbian-release | ind
fi

sec "Sistema operacional"
. /etc/os-release 2>/dev/null
echo "    Distribuição: ${PRETTY_NAME:-n/d}"
echo "    Debian: $(cat /etc/debian_version 2>/dev/null || echo n/d)"
echo "    Kernel: $(uname -srvm)"

sec "Processador"
lscpu 2>/dev/null | grep -E '^(Architecture|CPU\(s\)|Thread|Core|Socket|Vendor|Model name|Model:|Stepping|CPU max|CPU min|BogoMIPS|L1d|L1i|L2|L3|Flags|Features)' | cut -c1-300 | ind
grep -E '^(CPU implementer|CPU architecture|CPU variant|CPU part|CPU revision)' /proc/cpuinfo 2>/dev/null | sort | uniq -c | ind
cf=/sys/devices/system/cpu/cpu0/cpufreq
if [ -d "$cf" ]; then
  echo "    Driver cpufreq: $(cat $cf/scaling_driver 2>/dev/null)"
  echo "    Governor(es): $(sort -u /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null | tr '\n' ' ')"
  for f in cpuinfo_min_freq cpuinfo_max_freq scaling_min_freq scaling_max_freq; do
    if [ -r "$cf/$f" ]; then echo "    $f: $(( $(cat $cf/$f) / 1000 )) MHz"; fi
  done
else
  echo "    cpufreq: indisponível"
fi

sec "Memória"
grep -E '^(MemTotal|SwapTotal):' /proc/meminfo | ind

sec "Armazenamento"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL 2>/dev/null | ind
df -hT --output=source,fstype,size / 2>/dev/null | ind

sec "Montagem NFS ($NFS_DIR)"
m=$(findmnt -no SOURCE,FSTYPE,OPTIONS "$NFS_DIR" 2>/dev/null)
if [ -n "$m" ]; then echo "    $m"; else echo "    $NFS_DIR sem montagem NFS neste equipamento"; fi

sec "Rede ($IFACE)"
ip -br addr show "$IFACE" 2>/dev/null | ind
for f in address operstate speed duplex mtu; do
  echo "    $f: $(cat /sys/class/net/$IFACE/$f 2>/dev/null || echo n/d)"
done
echo "    (speed = velocidade negociada em Mb/s)"
if command -v ethtool >/dev/null 2>&1; then ethtool -i "$IFACE" 2>/dev/null | grep -E '^(driver|version):' | ind; fi

sec "Software"
echo "    Open MPI: $(mpirun --version 2>/dev/null | head -1)"
for p in openmpi-bin libopenmpi3 libgfortran5 libc6 libhwloc15; do
  v=$(dpkg-query -W -f='${Version}' "$p" 2>/dev/null); echo "    pacote $p: ${v:-não instalado}"
done
echo "    gcc: $(gcc --version 2>/dev/null | head -1)"
echo "    gfortran: $(gfortran --version 2>/dev/null | head -1)"
true
EOF_EST

read -r -d '' COLETA_VOLATIL <<'EOF_VOL'
export LC_ALL=C
echo "    Data/hora: $(date -Iseconds)"
echo "    Uptime: $(uptime -p 2>/dev/null)"
echo "    Load average (1/5/15 min): $(cut -d' ' -f1-3 /proc/loadavg)"
echo "    Kernel cmdline: $(cat /proc/cmdline 2>/dev/null)"
grep -E '^(MemFree|MemAvailable|SwapFree):' /proc/meminfo | sed 's/^/    /'
for z in /sys/class/thermal/thermal_zone*; do
  if [ -r "$z/temp" ]; then echo "    Temperatura $(basename $z) ($(cat $z/type 2>/dev/null)): $(( $(cat $z/temp) / 1000 )) C"; fi
done
for c in /sys/devices/system/cpu/cpu[0-9]*; do
  f=$c/cpufreq
  if [ -r "$f/scaling_cur_freq" ]; then
    echo "    $(basename $c): cur=$(( $(cat $f/scaling_cur_freq) / 1000 )) MHz max_permitida=$(( $(cat $f/scaling_max_freq) / 1000 )) MHz"
  fi
done
echo "    Contadores de rede ($IFACE):"
ip -s link show "$IFACE" 2>/dev/null | sed 's/^/      /'
true
EOF_VOL

read -r -d '' SNAP_PAYLOAD <<'EOF_SNAP'
read -r _ a1 b1 c1 d1 e1 f1 g1 _ < /proc/stat
sleep 1
read -r _ a2 b2 c2 d2 e2 f2 g2 _ < /proc/stat
t1=$((a1+b1+c1+d1+e1+f1+g1)); t2=$((a2+b2+c2+d2+e2+f2+g2))
dt=$((t2-t1)); di=$(( (d2+e2) - (d1+e1) ))
if [ "$dt" -gt 0 ]; then busy=$(( (100*(dt-di))/dt )); else busy=0; fi
mem=0
while read -r k v _; do if [ "$k" = "MemAvailable:" ]; then mem=$v; break; fi; done < /proc/meminfo
tmax=0
for z in /sys/class/thermal/thermal_zone*/temp; do
  if [ -r "$z" ]; then read -r t < "$z"; if [ "${t:-0}" -gt "$tmax" ]; then tmax=$t; fi; fi
done
maxkhz=0
for c in /sys/devices/system/cpu/cpu[0-9]*; do
  f="$c/cpufreq/scaling_max_freq"
  if [ -r "$f" ]; then read -r val < "$f"; [ "$maxkhz" -eq 0 ] && maxkhz=$val; [ "$maxkhz" -eq "$val" ] || maxkhz=-1; fi
done
governors=$(cat /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor 2>/dev/null | sort -u | awk 'NR==1 {g=$0} END {if(NR==0) print "indisponivel"; else if(NR==1) print g; else print "MISTO"}')
swap=$(awk '/^SwapFree:/ {print $2}' /proc/meminfo)
echo "$busy $mem $tmax $maxkhz ${governors:-indisponivel} ${swap:-0}"
EOF_SNAP


# -------------------------------------------------------- limpeza e interrupção
limpa() {
  local h
  for h in "${HOSTS[@]}" "$NFS_HOST"; do
    eh_local "$h" || ssh -O exit -o "ControlPath=$CTL_DIR/%C" "$h" >/dev/null 2>&1
  done
  rm -rf "$CTL_DIR" "$PLAT" "$TMP" 2>/dev/null
}
interrompe() {
  echo; echo "COLETA INTERROMPIDA"
  [ -n "$PID" ] && kill -TERM "$PID" 2>/dev/null
  [ -n "$SAIDAS" ] && echo "!!! COLETA INTERROMPIDA em $(date -Iseconds)" >> "$SAIDAS"
  exit 130
}
trap limpa EXIT
trap interrompe INT TERM

# ------------------------------------------------------------ pré-verificações
echo "Pré-verificações (${#HOSTS[@]} nós de computação + servidor NFS)..."
FALHA=0
for h in "${HOSTS[@]}"; do
  if ! exec_no "$h" "true" 2>/dev/null; then echo "ERRO: sem acesso SSH a $h"; FALHA=1; continue; fi
  if ! exec_no "$h" "test -x '$BIN_FILE'"; then echo "ERRO: $h não executa $BIN_FILE (NFS montado?)"; FALHA=1; fi
done
[ "$FALHA" -eq 0 ] || exit 1
NFS_OK=1
if ! exec_no "$NFS_HOST" "true" 2>/dev/null; then
  NFS_OK=0
  LIMITACOES+=("Servidor NFS '$NFS_HOST' inacessível por SSH: seus dados de hardware/software e /etc/exports NÃO foram coletados.")
fi

DOC_HOSTS=("${HOSTS[@]}")
NFS_NA_LISTA=0; for h in "${HOSTS[@]}"; do [ "$h" = "$NFS_HOST" ] && NFS_NA_LISTA=1; done
[ "$NFS_NA_LISTA" -eq 1 ] || [ "$NFS_OK" -eq 0 ] || DOC_HOSTS+=("$NFS_HOST")

# ------------------------------------------------ informações manuais (modelo)
mkdir -p "$CONFIG_DIR/compilacao" "$CONFIG_DIR/execucoes" || { echo "ERRO: não foi possível criar $CONFIG_DIR"; exit 1; }
if [ ! -e "$MANUAL" ]; then
  cat > "$MANUAL" <<'EOF_MANUAL'
# Informações que NÃO podem ser obtidas automaticamente.
# Preencha uma vez; este arquivo é incluído em toda documentação gerada.
# Formato: "campo: valor". Linhas iniciadas por # são ignoradas.
TV Box - fabricante/modelo (server):
TV Box - fabricante/modelo (node1 a node7):
TV Box - fabricante/modelo (nfs):
SoC (modelo exato) por equipamento:
Memória RAM nominal (capacidade/tipo):
Armazenamento (eMMC/SD, modelo, capacidade nominal) por equipamento:
Velocidade nominal da porta Ethernet das TV Boxes (100 Mb/s ou 1 Gb/s):
Switch (fabricante, modelo, nº de portas, velocidade, gerenciável?):
Cabos de rede (categoria e comprimento):
Fonte de alimentação / refrigeração (dissipador, ventoinha):
Temperatura ambiente aproximada durante as medições:
Modificações no código-fonte do NPB (descrever ou escrever "nenhuma"):
Observações:
EOF_MANUAL
  echo "AVISO: criado modelo de informações manuais em $MANUAL (preencha antes da rodada oficial)."
fi
MANUAL_TOTAL=$(grep -cvE '^[[:space:]]*(#|$)' "$MANUAL")
MANUAL_PREENCH=$(grep -vE '^[[:space:]]*(#|$)' "$MANUAL" | awk '{v=$0; sub(/^[^:]*:/,"",v); if (v ~ /[^[:space:]]/) n++} END{print n+0}')
if [ "$MANUAL_PREENCH" -lt "$MANUAL_TOTAL" ]; then
  LIMITACOES+=("Informações manuais incompletas ($MANUAL_PREENCH de $MANUAL_TOTAL campos preenchidos em $MANUAL): fabricante/modelo, SoC, switch, cabos e modificações no código-fonte podem constar como não informados.")
fi

# --------------------------------------------- snapshots de compilação/configuração
sha8() { sha256sum "$1" 2>/dev/null | cut -c1-8; }
guarda() {  # guarda <arquivo> <prefixo>  -> copia para config/ com sufixo do hash; imprime caminho
  local f=$1 p=$2 d
  [ -r "$f" ] || return 1
  d="$CONFIG_DIR/compilacao/$p.$(sha8 "$f")"
  [ -e "$d" ] || cp "$f" "$d"
  echo "$d"
}
MAKEDEF="$NPB_DIR/config/make.def"
SNAP_MAKEDEF=$(guarda "$MAKEDEF" make.def)
SNAP_MAKETOP=$(guarda "$NPB_DIR/Makefile" Makefile)
SNAP_MAKEBENCH=$(guarda "$NPB_DIR/$BENCH/Makefile" "$BENCH.Makefile")
SNAP_HOSTFILE="$CONFIG_DIR/execucoes/cluster.$(sha8 "$HOSTFILE")"
SNAP_SCRIPT="$CONFIG_DIR/execucoes/npb-script.$(sha8 "$0").sh"
[ -e "$SNAP_SCRIPT" ] || cp -- "$0" "$SNAP_SCRIPT"
[ -e "$SNAP_HOSTFILE" ] || cp "$HOSTFILE" "$SNAP_HOSTFILE"
[ -n "$SNAP_MAKEDEF" ] || LIMITACOES+=("make.def não encontrado em $MAKEDEF: flags de compilação NÃO documentadas (o NPB também as imprime na saída de cada execução).")

# ------------------------------------------------------------------ ID e arquivos
RAW="$RESULTADOS/raw/$BENCH"
mkdir -p "$RAW" || { echo "ERRO: não foi possível criar $RAW"; exit 1; }
proximo_id() {
  local max=0 f n
  for f in "$RESULTADOS"/raw/*/npb_*.csv; do
    [ -e "$f" ] || continue
    n=${f##*/npb_}; n=${n%%_*}
    if [[ $n =~ ^[0-9]+$ ]] && [ "$n" -gt "$max" ]; then max=$n; fi
  done
  echo $((max + 1))
}
ID=$(proximo_id)
while true; do
  BASE="$RAW/npb_${ID}_${BENCH}_${CLASSE}"
  CSV="$BASE.csv"; SAIDAS="${BASE}_saidas.txt"; AMB="${BASE}_ambiente.txt"
  if [ ! -e "$SAIDAS" ] && [ ! -e "$AMB" ] && ( set -o noclobber; : > "$CSV" ) 2>/dev/null; then break; fi
  ID=$((ID + 1))
done
: > "$SAIDAS"

# -------------------------------------- verificação do código-fonte (tarball)
FONTE_TXT=""
if [ -f "$NPB_TARBALL" ] && [[ $NPB_DIR == "$PROJ"/* ]]; then
  MEMBRO=${NPB_DIR#"$PROJ"/}
  DIFF_OUT=$(tar -df "$NPB_TARBALL" -C "$PROJ" --wildcards "$MEMBRO/*" 2>&1)
  DIFF_CONT=$(printf '%s\n' "$DIFF_OUT" | grep -E 'Contents differ|Size differs|Cannot stat|No such file' )
  DIFF_META=$(printf '%s\n' "$DIFF_OUT" | grep -E 'Mod time differs|Mode differs|Uid differs|Gid differs' )
  NC=$(printf '%s' "$DIFF_CONT" | grep -c .); NM=$(printf '%s' "$DIFF_META" | grep -c .)
  if [ "$NC" -eq 0 ]; then
    FONTE_TXT="Código-fonte idêntico ao tarball original ($(basename "$NPB_TARBALL"), sha256 $(sha256sum "$NPB_TARBALL" | cut -d' ' -f1)) quanto ao conteúdo dos arquivos. Diferenças apenas de metadados (data/permissão): $NM."
  else
    FONTE_TXT="ATENÇÃO: $NC arquivo(s) diferem do tarball original (sha256 $(sha256sum "$NPB_TARBALL" | cut -d' ' -f1)):"$'\n'"$(printf '%s\n' "$DIFF_CONT" | head -30 | sed 's/^/      /')"
    LIMITACOES+=("O código-fonte do NPB difere do tarball original em $NC arquivo(s); descrever as modificações (ver seção 3).")
  fi
else
  FONTE_TXT="NÃO VERIFICADO: tarball original não encontrado em $NPB_TARBALL (ou NPB fora de $PROJ). Não é possível afirmar automaticamente que o código-fonte não foi modificado."
  LIMITACOES+=("Modificações no código-fonte do NPB não verificadas automaticamente (tarball original ausente).")
fi

# ------------------------------------------------ documentação: parte da plataforma
PLAT=$(mktemp)
COORD_PARTICIPA="não"; for h in "${HOSTS[@]}"; do eh_local "$h" && COORD_PARTICIPA="sim"; done
NFS_PARTICIPA="não"; [ "$NFS_NA_LISTA" -eq 1 ] && NFS_PARTICIPA="sim"
{
  echo "2. PLATAFORMA EXPERIMENTAL"
  echo
  echo "2.1 Papéis dos equipamentos (derivados do hostfile)"
  echo "  Coordenador (executa o mpirun): $MEU_HOST_CURTO"
  echo "  Coordenador participa do cálculo MPI: $COORD_PARTICIPA"
  echo "  Equipamentos no hostfile (participam do MPI): ${HOSTS[*]}"
  echo "  Total de slots no hostfile: $SLOTS_TOTAL"
  echo "  Servidor NFS: $NFS_HOST (participa do MPI: $NFS_PARTICIPA; função: armazenamento compartilhado)"
  echo
  echo "2.2 Hostfile do MPI ($HOSTFILE)"
  echo "  SHA-256: $(sha256sum "$HOSTFILE" | cut -d' ' -f1)"
  echo "  Cópia preservada em: $SNAP_HOSTFILE"
  sed 's/^/    | /' "$HOSTFILE"
  echo
  echo "2.3 Rede e topologia (visão do coordenador)"
  echo "  Interface do cluster: $IFACE"
  ip -br addr show "$IFACE" 2>/dev/null | sed 's/^/    /'
  echo "  Resolução de nomes (/etc/hosts, linhas ativas):"
  grep -vE '^[[:space:]]*(#|$)' /etc/hosts 2>/dev/null | sed 's/^/    | /'
  echo "  DHCP/DNS (dnsmasq, linhas relevantes):"
  grep -hE '^(interface|bind-interfaces|except-interface|dhcp-range|dhcp-option|dhcp-host|domain|local|expand-hosts|server|no-resolv)' /etc/dnsmasq.conf /etc/dnsmasq.d/* 2>/dev/null | sed 's/^/    | /'
  echo "  Equipamentos intermediários (switch), cabos e velocidade nominal:"
  echo "    consultar a seção de informações manuais (2.5); não são autodetectáveis."
  echo
  echo "2.4 Servidor NFS"
  if [ "$NFS_OK" -eq 1 ]; then
    echo "  /etc/exports em $NFS_HOST (linhas ativas):"
    exec_no "$NFS_HOST" "grep -vE '^[[:space:]]*(#|\$)' /etc/exports 2>/dev/null" | sed 's/^/    | /'
  else
    echo "  (servidor NFS inacessível: não coletado)"
  fi
  echo "  Opções de montagem em cada cliente: ver seção 2.6 (campo 'Montagem NFS')."
  echo
  echo "2.5 Informações manuais ($MANUAL) - campos preenchidos: $MANUAL_PREENCH de $MANUAL_TOTAL"
  grep -vE '^[[:space:]]*(#|$)' "$MANUAL" | sed 's/^/    | /'
  echo
  echo "2.6 Hardware e software de cada equipamento (campos estáveis)"
  for h in "${DOC_HOSTS[@]}"; do
    papel="computação MPI"; [ "$h" = "$NFS_HOST" ] && papel="armazenamento NFS"
    echo
    echo "  ---------- $h  [papel: $papel] ----------"
    if ! coleta "$h" "$COLETA_ESTAVEL"; then
      echo "    (FALHA na coleta deste equipamento)"
      LIMITACOES+=("Falha ao coletar hardware/software de '$h'.")
    fi
  done
  echo
  echo "3. SOFTWARE DE BENCHMARK E COMPILAÇÃO"
  echo
  echo "3.1 Open MPI (no coordenador)"
  echo "  $(mpirun --version 2>/dev/null | head -1)"
  ompi_info 2>/dev/null | grep -E 'Open MPI:|Prefix:|Thread support:|C compiler:|Fortran compiler:' | sed 's/^/    /'
  ompi_info 2>/dev/null | grep -E 'MCA btl:' | sed 's/^/    /'
  echo "  Wrapper Fortran (mpif90 --showme): $(mpif90 --showme 2>/dev/null)"
  echo
  echo "3.2 NAS Parallel Benchmarks"
  echo "  Diretório: $NPB_DIR  (versão pelo caminho: $(basename "$(dirname "$NPB_DIR")"); a versão também consta na saída de cada execução)"
  echo "  Verificação de modificações no código-fonte:"
  printf '%s\n' "$FONTE_TXT" | sed 's/^/    /'
  echo "  Modificações declaradas manualmente: ver campo 'Modificações no código-fonte do NPB' em 2.5."
  echo
  echo "3.3 Configuração de compilação (config/make.def)"
  if [ -n "$SNAP_MAKEDEF" ]; then
    echo "  SHA-256: $(sha256sum "$MAKEDEF" | cut -d' ' -f1)"
    echo "  Cópia preservada em: $SNAP_MAKEDEF"
    echo "  Linhas ativas:"
    grep -vE '^[[:space:]]*(#|$)' "$MAKEDEF" | sed 's/^/    | /'
  else
    echo "  (make.def não encontrado)"
  fi
} > "$PLAT"
AMB_SHA=$(sha256sum "$PLAT" | cut -d' ' -f1)
BIN_SHA=$(sha256sum "$BIN_FILE" | cut -d' ' -f1)

# ---------------------------------------------------------- documentação completa
CMD_TEMPLATE="mpirun -np <np> ${MPI_OPTS[*]}${MPI_EXTRA:+ $MPI_EXTRA} $BIN_FILE"
{
  echo "================================================================================"
  echo " DOCUMENTAÇÃO DO AMBIENTE EXPERIMENTAL - experimento $ID ($BENCH, classe $CLASSE)"
  echo "================================================================================"
  echo "  Gerado em ........: $(date -Iseconds)"
  echo "  Executado por ....: $(whoami)@$MEU_HOST_CURTO"
  echo "  Script ...........: $0 (versão $VERSAO_SCRIPT)"
  echo "  SHA-256 do script : $(sha256sum "$0" | cut -d' ' -f1)"
  echo "  Cópia do script .: $SNAP_SCRIPT"
  echo "  Arquivos associados: $(basename "$CSV") | $(basename "$SAIDAS") | $(basename "$AMB")"
  echo
  echo "1. PROTOCOLO EXPERIMENTAL"
  echo
  echo "  Fatores e níveis desta coleta:"
  echo "    Benchmark ................: $BENCH (NPB-MPI)"
  echo "    Classe do problema .......: $CLASSE (fixa)"
  echo "    Nº de processos MPI (np) .: $NPS"
  echo "    Distribuição dos processos: efetiva, registrada em cada execução (colunas n_nos e distribuicao);"
  echo "                                política explícita por slot (--map-by slot); busca preencher os slots"
  echo "                                de cada host antes de usar o próximo, respeitando a ordem do hostfile"
  echo "    Nº de nós participantes ..: registrado em cada execução (coluna n_nos)"
  [ -n "$NOTAS" ] && echo "  Notas desta rodada (variável NOTAS): $NOTAS"
  echo "  Variáveis de resposta: tempo de execução (s) e Mop/s informados pelo benchmark."
  echo "  Métricas derivadas (speedup, eficiência) e estatísticas: calculadas depois, por script, a partir do CSV."
  echo
  echo "  Repetições: $REPS blocos completos, uma medição por configuração em cada bloco; sem reposição de inválidas."
  echo "  Aquecimento: NÃO realizado. A primeira medição de cada configuração é incluída na análise, se válida."
  echo "  Critérios de validade (todos necessários):"
  echo "    1. mpirun terminou com exit_code 0 dentro do timeout de ${TIMEOUT}s; após o limite, SIGTERM e, ${TIMEOUT_KILL_AFTER}s depois, SIGKILL se necessário;"
  echo "    2. a saída contém o resumo do NPB (Time in seconds);"
  echo "    3. 'Verification = SUCCESSFUL' (verificação numérica do NPB);"
  echo "    4. processos ativos informados pelo NPB = np, classe informada = $CLASSE;"
  echo "    5. mapa de ranks completo, em hosts previstos; bindings individuais em núcleos distintos."
  echo "  Classificação das execuções inválidas (coluna status): TIMEOUT, FALHA_EXECUCAO,"
  echo "    FALHA_VERIFICACAO, INVALIDA. Todas permanecem no CSV; nenhuma é descartada por esta coleta."
  echo "  Não há repetição substitutiva: uma falha é registrada como observação inválida no bloco planejado."
  echo "  Preparação antes de cada execução: amostragem de 1 s da CPU de todos os nós; se a ocupação"
  echo "    máxima exceder ${LIMITE_CPU}%, aguarda até ${ESPERA_OCIOSO}s por ociosidade e ABORTA se não normalizar."
  echo "  Pausa entre execuções: ${PAUSA}s (após cada tentativa; não há monitor ou processo auxiliar iniciado pelo script durante o kernel)."
  echo "  Monitoramento durante a execução: DESATIVADO deliberadamente para evitar interferência."
  echo "  Métricas de temperatura/frequência/RAM durante a execução ficam vazias; não são estimadas por amostras externas."
  echo "  Timeout: ${TIMEOUT}s; após SIGTERM, timeout aguarda ${TIMEOUT_KILL_AFTER}s e envia SIGKILL se necessário."
  echo "  Comando de execução (modelo): $CMD_TEMPLATE"
  echo "  Variáveis de ambiente relevantes no coordenador:"
  env | grep -E '^(OMPI_|OMP_|OPENBLAS_|HWLOC_|PMIX_|MPI)' | sort | sed 's/^/    /'
  echo "    (fim da lista)"
  echo
  cat "$PLAT"
  echo
  echo "  >>> SHA-256 da plataforma (seções 2 e 3, sem dados voláteis): $AMB_SHA"
  echo "  >>> Se este valor for idêntico nas documentações de várias coletas, a plataforma documentada"
  echo "  >>> (hardware, software, rede, compilação) não mudou entre elas. Está registrado na coluna ambiente_sha256."
  echo
  echo "4. EXECUTÁVEL UTILIZADO"
  echo "  Caminho .........: $BIN_FILE"
  echo "  Tamanho .........: $(stat -c %s "$BIN_FILE") bytes"
  echo "  Modificado em ...: $(stat -c %y "$BIN_FILE")"
  echo "  SHA-256 .........: $BIN_SHA"
  if command -v readelf >/dev/null 2>&1; then
    echo "  Compilador (seção .comment do binário):"
    readelf -p .comment "$BIN_FILE" 2>/dev/null | grep -E '\[' | sed 's/^/    /'
  fi
  echo "  Bibliotecas compartilhadas (ldd, sem endereços):"
  ldd "$BIN_FILE" 2>/dev/null | sed -E 's/ \(0x[0-9a-f]+\)//; s/^[[:space:]]*/    /'
  echo "  Makefiles preservados em $CONFIG_DIR/compilacao/:"
  for f in "$SNAP_MAKETOP" "$SNAP_MAKEBENCH"; do
    [ -n "$f" ] && echo "    $(basename "$f")  (sha256 $(sha256sum "$f" | cut -d' ' -f1))"
  done
  echo "  Obs.: as opções de compilação e a data de compilação também são impressas pelo próprio NPB"
  echo "        na saída de cada execução (arquivo _saidas.txt)."
  echo
  echo "5. ESTADO DA PLATAFORMA NO INÍCIO DA COLETA (dados voláteis; não entram no hash)"
  echo
  echo "  Latência de rede do coordenador até cada equipamento (ping, 10 pacotes):"
  for h in "${DOC_HOSTS[@]}"; do
    eh_local "$h" && continue
    echo "    $h: $(ping -c 10 -i 0.2 -q "$h" 2>/dev/null | tail -1 | sed 's/^/ /' )"
  done
  echo "  Rotas do coordenador:"
  ip route 2>/dev/null | sed 's/^/    /'
  for h in "${DOC_HOSTS[@]}"; do
    echo
    echo "  ---------- $h ----------"
    coleta "$h" "$COLETA_VOLATIL" || echo "    (FALHA na coleta)"
  done
  echo
  echo "6. LIMITAÇÕES E INFORMAÇÕES NÃO COLETADAS"
  echo "  - Informações de execuções anteriores a esta coleta não foram reconstruídas."
  echo "  - A sondagem de preparação (amostra de CPU de 1 s) ocorre antes do benchmark; não há monitoramento concorrente durante o kernel."
  echo "  - O ambiente (hash da seção 2/3) foi coletado uma vez, no início desta coleta."
  if [ "${#LIMITACOES[@]}" -eq 0 ]; then
    echo "  - Nenhuma limitação adicional detectada automaticamente."
  else
    for l in "${LIMITACOES[@]}"; do echo "  - $l"; done
  fi
  echo
  echo "7. DICIONÁRIO DO CSV ($(basename "$CSV"))"
  cat <<'EOF_DIC'
  experimento_id ........ ID desta coleta (mesmo número nos três arquivos)
  exec_id ............... identificador único da tentativa: <experimento_id>-<sequência>; aparece no _saidas.txt
  benchmark, classe ..... benchmark NPB e classe do problema
  np .................... número de processos MPI
  n_nos ................. nº de equipamentos que receberam processos (segundo --display-map)
  distribuicao .......... processos por equipamento, ex.: server=4;node1=4
  tentativa ............. nº da tentativa para este np (inclui as inválidas)
  repeticao_valida ...... 1..REPS se a tentativa foi válida; vazio caso contrário
  inicio, fim ........... data/hora ISO 8601 da tentativa
  tempo_s ............... "Time in seconds" informado pelo NPB
  mops_total ............ "Mop/s total" informado pelo NPB
  mops_por_processo ..... "Mop/s/process" informado pelo NPB
  processos_ativos ...... "Active processes" informado pelo NPB (vazio se não impresso)
  verificacao ........... "Verification" informado pelo NPB (NAO_ENCONTRADA se ausente)
  exit_code ............. código de saída do mpirun (124 = timeout; 137 = SIGKILL, tratado como timeout só se tempo_parede_s >= timeout)
  status ................ VALIDA | TIMEOUT | FALHA_EXECUCAO | FALHA_VERIFICACAO | INVALIDA
  motivo ................ justificativa quando status != VALIDA
  tempo_parede_s ........ tempo total do mpirun medido pelo script (inclui inicialização do MPI)
  cpu_ocupada_max_antes_pct  maior ocupação de CPU (%) entre os nós, amostra de 1 s antes da execução
  mem_disp_min_antes_mb ..... menor RAM disponível (MB) entre os nós antes da execução
  temp_max_antes_c ...... maior temperatura (C) entre os nós antes da execução
  temp_max_durante_c .... não coletada: monitoramento durante o kernel desativado
  freq_min_durante_mhz .. não coletada: monitoramento durante o kernel desativado
  mem_disp_min_durante_mb  não coletada: monitoramento durante o kernel desativado
  binario_sha256 ........ SHA-256 do executável usado
  ambiente_sha256 ....... SHA-256 da plataforma documentada (seções 2 e 3)
  comando ............... comando mpirun efetivamente executado
  saida_arquivo ......... arquivo com a saída original
  saida_linha_inicial ... linha do arquivo de saída em que começa esta execução
EOF_DIC
  echo
  echo "8. CHECKLIST PARA AUDITORIA (a ser conferido pelo pesquisador; não é declaração automática de validade)"
  echo "  [ ] Informações manuais preenchidas (2.5)        [ ] Código-fonte NPB verificado/declarado (3.2)"
  echo "  [ ] Hash da plataforma igual em todas as coletas  [ ] Distribuição dos processos conferida no CSV"
  echo "  [ ] Execuções inválidas analisadas (status)       [ ] Estatísticas geradas por script a partir do CSV"
} > "$AMB"

# --------------------------------------------------------- preparação/ociosidade
# Nenhum monitor é iniciado durante o benchmark: processos de amostragem
# concorrentes poderiam interferir no kernel e contaminar os tempos medidos.
# A preparação abaixo ocorre integralmente antes de cada tentativa.
snapshot_antes() {   # imprime: cpu_ocupada_max_pct mem_min_kB temp_max_mC
  local h d p rc falha=0
  local -a pids=()
  d=$(mktemp -d) || return 1
  for h in "${HOSTS[@]}"; do
    ( script_no "$h" "$SNAP_PAYLOAD" > "$d/$h" 2>/dev/null ) &
    pids+=("$!")
  done
  for p in "${pids[@]}"; do
    wait "$p" || falha=1
  done
   for h in "${HOSTS[@]}"; do
     if ! awk 'NF==6 && $1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/ && $3 ~ /^[0-9]+$/ && $4 ~ /^-?[0-9]+$/ && $6 ~ /^[0-9]+$/ {ok=1} END{exit !ok}' "$d/$h" 2>/dev/null; then
       echo "ERRO: amostra de preparação ausente/inválida no nó $h" >&2
       falha=1
     fi
   done
   if [ "$falha" -ne 0 ]; then rm -rf "$d"; return 1; fi
   awk '{
     if ($1+0>b) b=$1+0;
     if (m=="" || $2+0<m) m=$2+0;
     if ($3+0>t) t=$3+0;
     if (NR==1) {f=$4;g=$5} else {if ($4!=f) f=-1; if ($5!=g) g="MISTO"}
     if (sw=="" || $6+0<sw) sw=$6+0
   } END {if(NR==0) exit 1; printf "%d %d %d %d %s %d\n",b,m,t,f,g,sw}' "$d"/*
  rc=$?
  rm -rf "$d"
  return "$rc"
}

# ------------------------------------------------------------ utilidades de parsing
extrai() { grep -m1 -E "$2" "$1" | awk -F= '{gsub(/[[:space:]]/, "", $2); print $2}'; }
nd()  { [ "$1" = "-" ] && echo "" || echo "$1"; }
conv() {  # conv <valor> <divisor> <casas>   (vazio ou 0 -> vazio: sensor indisponível)
  awk -v v="$1" -v d="$2" -v c="$3" 'BEGIN{ if (v=="" || v+0==0) print ""; else printf "%." c "f", v/d }'
}
csvq() {
  local s=$1
  s=${s//\"/\"\"}
  if [[ $s == *,* || $s == *\"* ]]; then s="\"$s\""; fi
  printf '%s' "$s"
}

classifica() {   # usa RC WALL VERIF TEMPO ATIVOS CLASSE_OUT np CLASSE; define STATUS MOTIVO
  STATUS=VALIDA; MOTIVO=OK
  # 124 = timeout (SIGTERM). 137 = SIGKILL: timeout só se o tempo de parede atingiu o limite;
  # caso contrário o processo foi morto por outro motivo (ex.: OOM-killer) e é falha de execução.
  if   [ "$RC" -eq 124 ] || { [ "$RC" -eq 137 ] && awk -v w="$WALL" -v t="$TIMEOUT" 'BEGIN{exit !(w>=t)}'; }; then
       STATUS=TIMEOUT; MOTIVO="excedeu ${TIMEOUT}s; encerramento forçado após ${TIMEOUT_KILL_AFTER}s se necessário (exit_code=$RC)"
  elif [ "$RC" -eq 137 ]; then STATUS=FALHA_EXECUCAO; MOTIVO="exit_code=137 (SIGKILL antes do limite de ${TIMEOUT}s; ex.: falta de memória)"
  elif [ "$RC" -ne 0 ];   then STATUS=FALHA_EXECUCAO; MOTIVO="exit_code=$RC"
  elif [ "$VERIF" = "NAO_ENCONTRADA" ] || ! [[ $TEMPO =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
       STATUS=FALHA_EXECUCAO; MOTIVO="saida sem resumo do NPB"
  elif [ "$VERIF" != "SUCCESSFUL" ]; then STATUS=FALHA_VERIFICACAO; MOTIVO="Verification=$VERIF"
  elif [ -n "$ATIVOS" ] && [ "$ATIVOS" != "$np" ]; then STATUS=INVALIDA; MOTIVO="processos ativos=$ATIVOS diferente de np=$np"
  elif [ -n "$CLASSE_OUT" ] && [ "$CLASSE_OUT" != "$CLASSE" ]; then STATUS=INVALIDA; MOTIVO="classe na saida=$CLASSE_OUT"
  fi
}

# O parser usa o primeiro bloco completo do mapa como referência e confere
# todos os blocos repetidos contra ele. Mensagens de binding são independentes.
valida_mapa_e_binding() {  # <log> <np> -> status; define DISTRIB NNOS PROCESSOS_MAPA
  local log="$1" n="$2" saida
  saida=$(python3 - "$log" "$HOSTFILE" "$n" 2>&1 <<'PYMAP'
import sys,re
from collections import OrderedDict
log,hostfile,np=sys.argv[1],sys.argv[2],int(sys.argv[3])
slots=OrderedDict()
for line in open(hostfile):
    line=line.split('#',1)[0].strip()
    if not line: continue
    parts=line.split(); host=parts[0]
    if host in slots: raise SystemExit('ERRO host duplicado no hostfile')
    spec=[int(x.split('=',1)[1]) for x in parts[1:] if x.startswith('slots=')]
    slots[host]=spec[0] if spec else 1
expected={}; left=np
for host,count in slots.items():
    for _ in range(min(left,count)):
        expected[len(expected)]=host
    left-=min(left,count)
if left or len(expected)!=np: raise SystemExit('ERRO slots insuficientes')
lines=open(log,errors='replace').read().splitlines()
blocks=[]; active=None; host=None
bindings={}; malformed=False
for line in lines:
    if '========================   JOB MAP' in line:
        if active is not None and active: blocks.append(active)
        active={};host=None
    m=re.search(r'Data for node:\s*(\S+)',line)
    if m: host=m.group(1)
    m=re.search(r'Process OMPI jobid:.*?Process rank:\s*(\d+)\s+Bound:\s*(.*)',line)
    if m and active is not None:
        rank=int(m.group(1))
        if rank in active and active[rank]!=host: malformed=True
        active[rank]=host
    m=re.search(r'^\[([^]:]+):\d+\]\s+MCW rank\s+(\d+)\s+bound to socket\s+\d+\[core\s+(\d+)\[hwt\s+\d+\]\]',line)
    if m:
        h,r,c=m.group(1),int(m.group(2)),int(m.group(3))
        if r in bindings and bindings[r]!=(h,c): malformed=True
        bindings[r]=(h,c)
if active: blocks.append(active)
if not blocks: raise SystemExit('ERRO nenhum mapa MPI legível')
if malformed or not any(b==expected for b in blocks):
    raise SystemExit('ERRO mapa MPI diferente da distribuição esperada')
if any(any(r not in expected or expected[r]!=h for r,h in b.items()) for b in blocks):
    raise SystemExit('ERRO ranks incompatíveis em mapa repetido')
if len(bindings)!=np: raise SystemExit('ERRO binding ausente em um ou mais ranks')
cores={}
for rank in range(np):
    if rank not in bindings: raise SystemExit('ERRO binding incompleto')
    h,c=bindings[rank]
    if h!=expected[rank] or (h,c) in cores:
        raise SystemExit('ERRO afinidade incorreta ou núcleo duplicado')
    cores[(h,c)]=rank
counts=OrderedDict()
for h in expected.values(): counts[h]=counts.get(h,0)+1
print(';'.join(f'{h}={n}' for h,n in counts.items()),len(counts),np)
PYMAP
  ) || { MAPA_ERRO="$saida"; DISTRIB="n/d"; NNOS=""; PROCESSOS_MAPA=""; return 1; }
  read -r DISTRIB NNOS PROCESSOS_MAPA <<< "$saida"
  MAPA_ERRO=""
}

# -------------------------------------------------------------------- execução
CSV_HEADER="experimento_id,exec_id,benchmark,classe,np,n_nos,distribuicao,tentativa,repeticao_valida,inicio,fim,tempo_s,mops_total,mops_por_processo,processos_ativos,verificacao,exit_code,status,motivo,tempo_parede_s,cpu_ocupada_max_antes_pct,mem_disp_min_antes_mb,temp_max_antes_c,temp_max_durante_c,freq_min_durante_mhz,mem_disp_min_durante_mb,binario_sha256,ambiente_sha256,comando,saida_arquivo,saida_linha_inicial,fase,bloco,governor_antes,freq_max_permitida_antes_mhz,swap_livre_min_antes_mb"
printf '%s\n' "$CSV_HEADER" > "$CSV"
{
  echo "================================================================================"
  echo " SAÍDAS ORIGINAIS DO NPB - experimento $ID ($BENCH, classe $CLASSE)"
  echo " Documentação do ambiente: $(basename "$AMB") | CSV: $(basename "$CSV")"
  echo " Cada bloco começa com '##### EXEC <exec_id>' (coluna exec_id do CSV)."
  echo "================================================================================"
} >> "$SAIDAS"

# Plano de aleatorização reprodutível, obtido por gerador local com semente.
# Sua ordem é salva ANTES da medição e não sofre reordenação após falhas.
PLANO="$BASE-plano.csv"
python3 - "$REPS" "$SEMENTE" "${NPS_ARR[@]}" > "$PLANO" <<'PYPLANO'
import csv,random,sys
reps=int(sys.argv[1]); rng=random.Random(int(sys.argv[2])); nps=list(map(int,sys.argv[3:]))
w=csv.writer(sys.stdout,lineterminator='\n');w.writerow(['bloco','ordem_no_bloco','np'])
for block in range(1,reps+1):
    order=nps.copy();rng.shuffle(order)
    for i,n in enumerate(order,1):w.writerow([block,i,n])
PYPLANO
PLANO_SHA=$(sha256sum "$PLANO" | cut -d' ' -f1)
{
 echo
 echo "9. CONTROLES ADICIONAIS DO PROTOCOLO V5.4"
 echo "  Planejamento: blocos completos com ordem aleatória de np dentro de cada bloco."
 echo "  Semente aleatória: $SEMENTE; plano: $(basename "$PLANO"); SHA-256: $PLANO_SHA"
 echo "  Aquecimento: nenhum. Cada configuração possui uma medição planejada por bloco."
 echo "  Afinidade: --bind-to core; requer registro de binding individual para cada rank MPI."
 echo "  Distribuição: cada rank deve ocupar o nó esperado por preenchimento consecutivo de slots."
 echo "  Condição prévia: CPU <= $LIMITE_CPU%, temperatura <= $((TEMP_LIMITE_MC/1000)) C, frequência máxima/governor uniformes nos nós e constantes na coleta."
 echo "  Se condições falharem após espera, aborta a coleta (não mede fora dos limites)."
 echo "  Sem monitoramento durante o kernel: não há prova de estabilidade térmica/frequência interna; requer diagnóstico separado."
 echo "  Execuções inválidas são preservadas; o plano não é modificado para substituir observações."
 echo "  A coluna fase permanece MEDICAO em todas as linhas para compatibilidade dos CSVs; somente status VALIDA entra nas estatísticas."
 echo "  Observação: configuração de frequência ONDEMAND não foi modificada pelo script."
} >> "$AMB"

# Faz uma medição de preparação, verificando condições de todos os nós.
prepara() {
 local espera=0
 while :; do
   SNAP=$(snapshot_antes) || { echo "ERRO: coleta de pré-condições falhou" >&2; return 1; }
   read -r CPU_B MEM_B TEMP_B FREQ_B GOV_B SWAP_B <<< "$SNAP"
   if (( CPU_B <= LIMITE_CPU && TEMP_B <= TEMP_LIMITE_MC && FREQ_B > 0 )) && [ "$GOV_B" != MISTO ] && [ "$GOV_B" != indisponivel ] && [[ "$GOV_B" != *+*+* ]]; then
       if [ -z "${FREQ_REFERENCIA:-}" ]; then
           FREQ_REFERENCIA=$FREQ_B; GOV_REFERENCIA=$GOV_B
       fi
       if [ "$FREQ_B" != "$FREQ_REFERENCIA" ] || [ "$GOV_B" != "$GOV_REFERENCIA" ]; then
           echo "ERRO: política cpufreq alterada: inicial=$FREQ_REFERENCIA/$GOV_REFERENCIA atual=$FREQ_B/$GOV_B" >&2
           return 1
       fi
       return 0
   fi
   if (( espera >= ESPERA_OCIOSO )); then
       echo "ERRO: condições prévias não atendidas: cpu=$CPU_B%, temp=$(conv "$TEMP_B" 1000 1) C, freq_max=$FREQ_B kHz, governor=$GOV_B" >&2
       return 1
   fi
   sleep 5; espera=$((espera+5))
 done
}

SEQ=0; INCOMPLETO=0
executa_tentativa() {  # <np> <fase> <bloco> <tentativa>
 local np="$1" FASE="$2" BLOCO="$3" TENT="$4"
 SEQ=$((SEQ + 1)); EXEC_ID="${ID}-$(printf '%04d' "$SEQ")"
 prepara || return 10
 TMP=$(mktemp) || return 10
 CMD="mpirun -np $np ${MPI_OPTS[*]}${MPI_EXTRA:+ $MPI_EXTRA} $BIN_FILE"
 INICIO=$(date -Iseconds); T0=$(date +%s.%N)
 timeout --signal=TERM --kill-after="${TIMEOUT_KILL_AFTER}s" "$TIMEOUT" mpirun -np "$np" "${MPI_OPTS[@]}" "${EXTRA[@]}" "$BIN_FILE" </dev/null 8<&- > "$TMP" 2>&1 &
 PID=$!; wait "$PID"; RC=$?; PID=""
 T1=$(date +%s.%N); FIM=$(date -Iseconds)
 WALL=$(awk -v a="$T0" -v b="$T1" 'BEGIN{printf "%.2f", b-a}')
 TEMPO=$(extrai "$TMP" 'Time in seconds *='); MOPS=$(extrai "$TMP" 'Mop/s total *=')
 MOPSP=$(extrai "$TMP" 'Mop/s/process *='); ATIVOS=$(extrai "$TMP" 'Active processes *=')
 CLASSE_OUT=$(extrai "$TMP" '^ *Class *='); VERIF=$(extrai "$TMP" 'Verification *=')
 [ -n "$VERIF" ] || VERIF=NAO_ENCONTRADA
 classifica
 if [ "$STATUS" = VALIDA ]; then
     if [ "$ATIVOS" != "$np" ] || [ "$CLASSE_OUT" != "$CLASSE" ]; then
         STATUS=INVALIDA; MOTIVO="resumo NPB incompleto/incompatível: ativos=$ATIVOS classe=$CLASSE_OUT"
     fi
 fi
 if ! valida_mapa_e_binding "$TMP" "$np"; then
     [ "$STATUS" = VALIDA ] && STATUS=INVALIDA && MOTIVO="mapa/afinidade inválidos: $MAPA_ERRO"
 fi
 if [ "$STATUS" != VALIDA ]; then REPV=""; fi
 LINHA=$(( $(wc -l < "$SAIDAS") + 2 ))
 {
   echo
   echo "##### EXEC $EXEC_ID | $BENCH.$CLASSE | np=$np | fase=$FASE | bloco=$BLOCO | tentativa=$TENT | inicio=$INICIO"
   echo "Comando: $CMD"
   echo "Pré-condições: cpu_max=${CPU_B}% mem_min=$(conv "$MEM_B" 1024 0)MB temp_max=$(conv "$TEMP_B" 1000 1)C freq_max=$FREQ_B kHz governor=$GOV_B"
   echo "----- saída original (stdout+stderr) -----"
   cat "$TMP"
   echo "----- fim EXEC $EXEC_ID | exit_code=$RC | status=$STATUS | motivo=$MOTIVO | fim=$FIM -----"
 } >> "$SAIDAS"
 {
   printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,' "$ID" "$EXEC_ID" "$BENCH" "$CLASSE" "$np" "$NNOS" "$DISTRIB" "$TENT" "${REPV:-}" "$INICIO" "$FIM"
   printf '%s,%s,%s,%s,%s,%s,%s,' "$TEMPO" "$MOPS" "$MOPSP" "$ATIVOS" "$VERIF" "$RC" "$STATUS"
   printf '%s,%s,' "$(csvq "$MOTIVO")" "$WALL"
   printf '%s,%s,%s,' "$CPU_B" "$(conv "$MEM_B" 1024 0)" "$(conv "$TEMP_B" 1000 1)"
   printf ',,,'
   printf '%s,%s,%s,%s,%s,' "$BIN_SHA" "$AMB_SHA" "$(csvq "$CMD")" "$(basename "$SAIDAS")" "$LINHA"
   printf '%s,%s,%s,%s,%s\n' "$FASE" "$BLOCO" "$GOV_B" "$(conv "$FREQ_B" 1000 0)" "$(conv "$SWAP_B" 1024 0)"
 } >> "$CSV"
 printf '[np=%s | %s | bloco=%s] %s tempo=%ss verif=%s\n' "$np" "$FASE" "$BLOCO" "$STATUS" "${TEMPO:-?}" "$VERIF"
 rm -f "$TMP"; TMP=""
 sleep "$PAUSA"
 [ "$STATUS" = VALIDA ]
}

# Nenhum aquecimento: todas as execuções planejadas são medições.
echo "Experimento $ID: $BENCH.$CLASSE | np: $NPS | blocos=$REPS | sem aquecimento"

# Cada bloco é uma permutação dos np. Uma falha fica no CSV e não é
# substituída silenciosamente: reduz o n válido do grupo.
# Plano em descritor próprio (FD 8): processos filhos não recebem o CSV como stdin.
exec 8< "$PLANO" || { echo "ERRO: não foi possível abrir plano: $PLANO" >&2; exit 2; }
while IFS=, read -r -u 8 BLOCO ORDEM np; do
 [ "$BLOCO" = bloco ] && continue
 REPV="$BLOCO"
 executa_tentativa "$np" MEDICAO "$BLOCO" "$BLOCO"
 rc=$?
 if [ "$rc" -eq 10 ]; then echo "ERRO: falha de pré-condições; coleta interrompida" >&2; exit 2; fi
 [ "$rc" -eq 0 ] || INCOMPLETO=1
done
exec 8<&-

RESUMO=$(python3 - "$CSV" <<'PYRES'
import csv,sys,collections
rows=list(csv.DictReader(open(sys.argv[1]))); groups=collections.defaultdict(list)
for r in rows:
 if r['fase']=='MEDICAO':groups[int(r['np'])].append(r)
print('np   válidas  inválidas')
for np,rs in sorted(groups.items()):
 n=sum(r['status']=='VALIDA' for r in rs)
 print(f'{np:<4} {n:<8} {len(rs)-n}')
PYRES
)
{
 echo; echo "================================================================================"
 echo " FIM DA COLETA em $(date -Iseconds) | tentativas registradas: $SEQ"
 echo "$RESUMO"
 echo "================================================================================"
} >> "$SAIDAS"
echo "$RESUMO"
echo "CSV: $CSV"
echo "SAIDAS: $SAIDAS"
echo "AMBIENTE: $AMB"
echo "PLANO: $PLANO"
[ "$INCOMPLETO" -eq 0 ] || exit 2
exit 0
