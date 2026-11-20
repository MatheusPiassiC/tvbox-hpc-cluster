# Guia de integração

O conjunto de 16 e 17 de novembro de 2026 já conta com registros originais, scripts de análise, auditoria, figuras e o manual de instalação 5.0. A prioridade agora é localizar o coletor v5.4, os arquivos integrais de compilação e as configurações efetivas dos serviços. [Resultados integrados](../results/README.md) · [Configuração do cluster](configuracao-cluster.md)

## Materiais que podem ser fornecidos diretamente

| Prioridade | Material e provável localização | Informação e finalidade | Destino | Conferência antes de publicar |
| --- | --- | --- | --- | --- |
| Essencial | Coletor v5.4 e auxiliares, na pasta de experimentos ou repositório de desenvolvimento | Método de execução, coleta e verificação em tempo de execução | [scripts](../scripts/README.md) | Comparar com o SHA-256 declarado, registrar argumentos e revisar credenciais |
| Essencial quando houver novas séries | CSVs e TXTs originais, na saída dos scripts ou no armazenamento compartilhado | Evidência por tentativa e origem dos agregados | [results/raw](../results/raw/) | Conferir completude, integridade, referência por tentativa e dados sensíveis |
| Essencial | Caderno experimental e registros complementares | Relacionar a série integrada às demais coletas e esclarecer decisões de método | [protocolo](protocolo-experimental.md) e [metadata](../metadata/) | Conciliar com scripts, logs e identificadores |
| Essencial | Pacote original NPB, fonte usada, alterações, binários e registros disponíveis, na árvore de compilação, no NFS ou no acervo da pesquisa | Relacionar origem, alterações e compilação ao executável | [benchmarks](../benchmarks/README.md) e [config/npb](../config/npb/) | Verificar versão, SHA-256, flags, classe e redistribuição |
| Essencial | Arquivos efetivos dos serviços e manuais complementares, na pasta do cluster | Complementar o manual 5.0 com a configuração observada | [docs](./) | Confirmar revisão, nós e campanhas aplicáveis, consistência e exposição de informações sensíveis |
| Essencial | Registros existentes de DRM e da aplicação da política de frequência | Evidências e procedimentos aplicados a hwloc e à política de CPU | [investigações](investigacoes/) | Relacionar as correções a versões, nós e campanhas |
| Essencial para publicação | Nomes de autoria e orientação, referência do TCC e decisões de licença, nos registros acadêmicos e com os titulares | Crédito, citação e permissões de distribuição | [guia de publicação](publicacao.md), futuros `CITATION.cff` e `LICENSE` | Confirmar nomes, escopo das licenças e créditos |
| Recomendado | Inventário de hardware e registros de custo, em notas, planilhas e comprovantes | Características da infraestrutura e base da análise econômica | [hardware](hardware.md) | Conferir unidades, datas, fontes e dados pessoais |
| Recomendado | Identificação, origem e instruções de preparação da imagem Armbian, no acervo da instalação | Ajudar a recriar a base do sistema | [ambiente de software](ambiente-software.md) | Conferir versão, personalizações e condições de distribuição |
| Opcional | Imagem do sistema, no acervo da instalação | Facilitar a reconstrução quando sua redistribuição for possível | Anexo da futura [Release](publicacao.md) | Verificar SHA-256, licença, tamanho e presença de segredos |
| Recomendado | Versão final das tabelas e figuras efetivamente incorporadas ao TCC | Comparar com as peças candidatas já integradas | [reports](../reports/) | Conferir vínculo com a campanha e versão da análise |

## Informações a extrair do ambiente

Usar primeiro os registros contemporâneos às execuções. Para uma coleta posterior, registrar nó, data e campanha associada, se conhecida. Os comandos abaixo são opções de leitura para executar localmente no nó pertinente, conforme a disponibilidade das ferramentas. Conferir o conteúdo antes de compartilhá-lo.

| Prioridade | Onde coletar | O que fornecer e por quê | Destino | Conferência |
| --- | --- | --- | --- | --- |
| Essencial | Diretório de lançamento e configuração do Open MPI no `server` | Hostfile, parâmetros MCA, opções de mapeamento e binding e logs de distribuição, para identificar a alocação efetiva | [config/mpi](../config/mpi/) e [metadata](../metadata/) | Confrontar com scripts e logs. Revisar nomes e endereços sensíveis |
| Essencial | Árvore efetiva de compilação do NPB | `make.def`, `suite.def` se usada e demais entradas, para reconstruir os binários | [config/npb](../config/npb/) | Conferir vínculo com a compilação e a campanha |
| Essencial | Nós computacionais e nó `nfs` | Inventário de versões, hardware e frequência, para caracterizar o ambiente | [hardware](hardware.md), [software](ambiente-software.md) e [metadata](../metadata/) | Verificar divergências entre nós e distinguir observações atuais das históricas |
| Essencial | Configurações nos nós e no `nfs` | Montagens e exportações NFS, rede, SSH e arquivos de política de frequência e permissões, para reconstruir os serviços | [config/sistema](../config/sistema/) | Conferir protocolo, opções, caminhos e preservar originais em acervo restrito quando sensíveis |

```sh
date -Iseconds
hostname
uname -a
cat /etc/os-release
lscpu
cat /proc/meminfo
lsblk
ip -br link
mpirun --version
ompi_info --all
gcc --version
gfortran --version
ssh -V
findmnt -t nfs,nfs4
```

No servidor NFS, consultar as exportações com `exportfs -v` se houver permissão de leitura. Nos nós computacionais, consultar a política de frequência, quando exposta pelo kernel, com o trecho a seguir.

```sh
for politica in /sys/devices/system/cpu/cpufreq/policy*; do
    [ -d "$politica" ] || continue
    printf '%s\n' "$politica"
    cat "$politica/scaling_governor" "$politica/scaling_max_freq"
done
```

Registrar a unidade da frequência reportada (kHz para `scaling_max_freq`) e associar os valores aos nós. Consultar os manuais existentes para localizar configurações efetivas. Revisar saídas de diagnóstico que possam expor caminhos privados, nome de usuário, endereços ou opções sensíveis.
