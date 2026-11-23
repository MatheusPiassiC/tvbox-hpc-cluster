# Hardware

O cluster utiliza **nove TV Boxes H7** reaproveitadas, disponibilizadas pelo CRC-Lavras. Cada equipamento tem SoC Amlogic S905X3 e quatro núcleos ARM Cortex-A55. Os snapshots registram `MemTotal` de 1.868.128 kB por dispositivo. O `server` e `node1` a `node7` oferecem 32 slots MPI, quatro por nó. O nono equipamento, `nfs`, fornece armazenamento compartilhado. [Arquitetura](arquitetura.md) · [Hostfile](../config/mpi/cluster)

H7 é o nome comercial. O device tree usado na inicialização registra a plataforma de firmware como `SEI Robotics SEI610`, com identificadores de compatibilidade `seirobotics,sei610` e `amlogic,sm1`. [Origem da imagem e versões](ambiente-software.md)

| Componente | Inventário |
| --- | --- |
| Switch | Intelbras SG 2400 QR, 24 portas Gigabit |
| Cabeamento | Nove cabos CAT6 de aproximadamente 1 m, totalizando 9 m de cabo e 18 conectores RJ45 |
| Alimentação | Nove fontes originais de 5 V e 2 A nominais e dois protetores bivolt de seis tomadas |
| Refrigeração e armazenamento | Equipamentos usados sem refrigeração adicional e sem mídia de armazenamento externa |

Os snapshots de abertura da campanha registram enlaces de 100 Mb/s em full-duplex nos nove equipamentos. Na inspeção de 23/11/2026, os oito nós MPI negociaram 100 Mb/s em full-duplex. A especificação Gigabit corresponde às portas do switch. Os valores das fontes são nominais e a avaliação não mediu o consumo elétrico. [Ambiente por nó](../results/processed/auditoria/tabelas/nos_ambiente.csv) · [Análise de custos](custos.md)
