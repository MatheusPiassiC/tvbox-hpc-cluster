# Política de frequência da CPU

Os snapshots de abertura das oito coletas registraram o driver `cpufreq-dt`, o governador `ondemand` e os limites de escala de 1.000 e 1.500 MHz. O driver reportou 2.100 MHz em `cpuinfo_max_freq`. Esse campo é o teto informado pelo driver, enquanto `scaling_max_freq` registra o limite de operação configurado.

As frequências nos snapshots são leituras pontuais de abertura. O monitoramento durante a execução estava desativado, por isso o conjunto deixa indeterminada a frequência ao longo de cada execução. A forma de aplicar e persistir a política ainda precisa ser documentada. Consulte [os registros por nó](../../results/processed/auditoria/tabelas/nos_ambiente.csv).
