# Política de frequência da CPU

Os snapshots de abertura das oito coletas registraram o driver `cpufreq-dt`, o governador `ondemand` e os limites de escala de 1.000.000 a 1.500.000 kHz. [Registros por nó](../../results/processed/auditoria/tabelas/nos_ambiente.csv)

Na inspeção de 23/11/2026, o pesquisador registrou a solicitação de persistência em `/etc/default/cpufrequtils` e os valores expostos pelo kernel.

| Campo | Valor | Significado |
| --- | ---: | --- |
| `cpuinfo_max_freq` | 2.100.000 kHz | Teto informado pelo driver |
| `MAX_SPEED` | 1.536.000 kHz | Teto solicitado no arquivo de configuração do `cpufrequtils` |
| `scaling_max_freq` | 1.500.000 kHz | Teto efetivo observado com o governador `ondemand` |

O coletor verificava a uniformidade da política nas sondagens anteriores aos lançamentos. As frequências instantâneas dos snapshots são leituras pontuais. Como o monitoramento durante os kernels estava desativado, o acervo não fornece uma série temporal de frequência durante as medições. [Protocolo experimental](../protocolo-experimental.md) · [Coletor original](../../scripts/coleta/npb-experimento-v5.4.sh)
