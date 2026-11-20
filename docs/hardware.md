# Hardware

O cluster utiliza nove TV Boxes H7 reaproveitadas, disponibilizadas pelo CRC-Lavras segundo o pesquisador. Os oito nós de cálculo oferecem 32 núcleos e o nono equipamento serve o NFS. Os snapshots registram quatro núcleos ARM Cortex-A55 e `MemTotal` de 1.868.128 kB por dispositivo.

O pesquisador confirmou **H7** como nome comercial e associou as unidades à plataforma Amlogic SM1/S905X3. O device tree usado na inicialização registra o modelo `SEI Robotics SEI610`, com identificadores de compatibilidade `seirobotics,sei610` e `amlogic,sm1`.

O campo de inventário manual registra um switch Intelbras SG 2400 QR de 24 portas, com a grafia exata pendente de conferência na etiqueta. Os enlaces dos nove equipamentos foram registrados a 100 Mbit/s em full-duplex nos oito snapshots. A [tabela de ambiente por nó](../results/processed/auditoria/tabelas/nos_ambiente.csv) contém esses registros.

O inventário ainda precisa identificar as mídias de armazenamento, as revisões de placa e os itens, valores, datas e fontes da análise de custos. Consulte também a [política de frequência](investigacoes/politica-frequencia-cpu.md).
