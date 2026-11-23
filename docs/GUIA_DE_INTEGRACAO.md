# Guia de integração

O conjunto de 16 e 17 de novembro de 2026 reúne os registros originais, a auditoria, o coletor v5.4, o `make.def` e o hostfile verificados. O inventário de serviços foi complementado com as observações de 23/11/2026 fornecidas pelo pesquisador. [Resultados integrados](../results/README.md) · [Proveniência da campanha](../metadata/proveniencia-npb.md) · [Configuração do cluster](configuracao-cluster.md)

## Materiais integrados e pendências

| Prioridade | Material e provável localização | Informação e finalidade | Destino | Conferência antes de publicar |
| --- | --- | --- | --- | --- |
| Integrado | Coletor v5.4 e sondagens embutidas | Procedimento e parâmetros da campanha | [scripts/coleta](../scripts/README.md#coletor-v54) | Hash integral verificado contra as oito coletas |
| Integrado | CSVs e TXTs originais da campanha | Evidência por tentativa e origem dos agregados | [results/raw](../results/raw/) | 24 originais versionados e oito snapshots restritos, com SHA-256 conferido |
| Essencial | Caderno experimental e registros complementares | Relacionar a série integrada às demais coletas e esclarecer decisões de método | [protocolo](protocolo-experimental.md) e [metadata](../metadata/) | Conciliar com scripts, logs e identificadores |
| Integrado e conferido | `make.def`, hostfile e hashes de pacote e binários | Relacionar a compilação e o lançamento aos executáveis usados | [config](../config/README.md) e [benchmarks](../benchmarks/README.md) | Tarball, binários ARM e Makefiles da distribuição permanecem no acervo restrito |
| Essencial | Arquivos efetivos dos serviços e manuais complementares, na pasta do cluster | Complementar o manual 5.0 com a configuração observada | [docs](./) | Confirmar revisão, nós e campanhas aplicáveis, consistência e exposição de informações sensíveis |
| Pendente | Registro da intervenção de acesso a DRM | Relacionar o sintoma e a correção às versões e aos nós | [nota sobre hwloc e DRM](investigacoes/correcao-hwloc-drm.md) | Confirmar permissões, intervenção e verificação |
| Essencial para publicação | Nomes de autoria e orientação, referência do TCC e decisões de licença, nos registros acadêmicos e com os titulares | Crédito, citação e permissões de distribuição | [guia de publicação](publicacao.md), futuros `CITATION.cff` e `LICENSE` | Confirmar nomes, escopo das licenças e créditos |
| Documentado | Inventário de hardware e valores referenciais do TCC | Composição e base da análise econômica | [hardware](hardware.md) e [custos](custos.md) | Recuperar as fichas bibliográficas originais das consultas de preço |
| Pendente | Identificação integral da imagem instalada | Relacionar a imagem-base H7 às adaptações no cluster | [ambiente de software](ambiente-software.md) | Registrar hash, componentes e condições de redistribuição da imagem efetiva |
| Recomendado | Versão final das tabelas e figuras efetivamente incorporadas ao TCC | Comparar com as peças candidatas já integradas | [reports](../reports/) | Conferir vínculo com a campanha e versão da análise |

## Informações a extrair do ambiente

Usar primeiro os registros contemporâneos às execuções. Para uma coleta posterior, registrar nó, data e campanha associada, se conhecida. Os comandos abaixo são opções de leitura para executar localmente no nó pertinente, conforme a disponibilidade das ferramentas. Conferir o conteúdo antes de compartilhá-lo.

| Prioridade | Onde coletar | O que fornecer e por quê | Destino | Conferência |
| --- | --- | --- | --- | --- |
| Essencial | Diretório de lançamento e configuração do Open MPI no `server` | Hostfile, parâmetros MCA, opções de mapeamento e binding e logs de distribuição, para identificar a alocação efetiva | [config/mpi](../config/mpi/) e [metadata](../metadata/) | Confrontar com scripts e logs. Revisar nomes e endereços sensíveis |
| Conforme a evidência disponível | Árvore efetiva de compilação do NPB | Confirmar se houve uso de `suite.def` e registrar dependências do rebuild | [config/npb](../config/npb/) | Vincular o registro à compilação e à campanha |
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
