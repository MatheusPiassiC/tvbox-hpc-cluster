# Proveniência da campanha NPB classe A

A conferência compara os arquivos recuperados do acervo do cluster com os registros de abertura das oito coletas de 16 e 17 de novembro de 2026. Os quatro artefatos abaixo têm o mesmo SHA-256 declarado em cada linha de `ambientes.csv`. Os 32 originais de entrada também coincidem com o manifesto arquivado na árvore local e no resgate. [Ambiente por campanha](../results/processed/auditoria/tabelas/ambientes.csv) · [Manifesto dos dados de entrada](../results/processed/auditoria/manifestos/dados_entrada.json)

## Artefatos comuns

| Artefato | SHA-256 | Origem e acesso |
| --- | --- | --- |
| [Coletor v5.4](../scripts/coleta/npb-experimento-v5.4.sh) | `efa570e5d040626e7580071208f0f4df5a604242a700a072eb32b06a4ce7a38b` | Cópia arquivada pelo coletor em `config/execucoes` no NFS, recuperada e integrada byte a byte. |
| [`make.def`](../config/npb/make.def) | `a069d8fdbcef2dd658e4aa053d61e185468201fe10dd502f919dcc34edf6b07e` | Configuração da árvore NPB MPI, recuperada em duas cópias idênticas e integrada uma vez. |
| [Hostfile `cluster`](../config/mpi/cluster) | `7b935f49effa7f81b391c1ca99b8c5af2ec9d285404eba772d3ecc4d28dc2d1c` | Hostfile do NFS. A cópia já versionada coincide com a cópia recuperada. |
| `NPB3.4.4.tar.gz` | `1ae219398e02a0a79ad51b7460fcffbf7b5df83a69d5d3d3a9dc2d8acf523549` | Cópia recuperada de 446.013 bytes, mantida no acervo local. [Distribuição oficial](https://www.nas.nasa.gov/software/npb.html) |

## Binários por campanha

Cada campanha abaixo usa os quatro artefatos comuns. O SHA-256 e o tamanho de cada executável AArch64 em `NPB3.4-MPI/bin` no acervo recuperado coincidem com a linha correspondente de `ambientes.csv`. A seleção distribui os registros da auditoria e mantém os executáveis no acervo restrito.

| Campanha | Binário | Tamanho (bytes) | SHA-256 |
| --- | --- | ---: | --- |
| EP/`npb_1_EP_A` | `ep.A.x` | 25.240 | `973a0abb56b4ffd1493421b866c98c3bb692874144e6f9888cc9594e5851fec5` |
| IS/`npb_2_IS_A` | `is.A.x` | 26.152 | `da5ee757f6a3f0882fe15556336c3287319d64d2a03f467c5c7d67a47d3fad7a` |
| CG/`npb_3_CG_A` | `cg.A.x` | 48.768 | `22bba3c8bfbcb0602bcc9c1f6a5af5a96e9bbc4ed20766e5c29993b0ea5d0144` |
| MG/`npb_4_MG_A` | `mg.A.x` | 86.128 | `94536d47703918c2b63d6ed58024594db00e400a77510457f768ccdde1247dcd` |
| FT/`npb_5_FT_A` | `ft.A.x` | 61.680 | `107a580b2e38807a3f36fd184ed6e8d0cd9aa0be2d95bc17cb4612cb7dbf6a27` |
| LU/`npb_6_LU_A` | `lu.A.x` | 132.328 | `b7325e0911987c549164a4972ee0bb216673d6d01e2c48025e384030ed488baa` |
| BT/`npb_10_BT_A` | `bt.A.x` | 173.776 | `00d20967fb3c528a6dc79903a0c0f88577b75a4cfe6fd02c8e2019fbe7272929` |
| SP/`npb_9_SP_A` | `sp.A.x` | 200.424 | `0d1f72d1bd099ce916a28c2ee22d99d4a2200c5df004f40cd0c81b360b174b08` |

## Outros materiais do acervo

Três versões históricas do coletor ficaram no acervo. O identificador interno 5.4 aparece em dois arquivos com hashes diferentes. A correspondência da versão da campanha é pelo hash completo.

| Versão interna | SHA-256 da variante fora da campanha |
| --- | --- |
| 3.1 | `d005f4ec11b728b33024b79ab7c4fb85acf4bdb7d2b39d2eb0514437aaaa8723` |
| 5.3 | `bfb91ccb252006b61cef9c6684be6b4e7fe78de8b5f83ef34ccb1cdbeb1dd858` |
| 5.4 | `de03b3f14824d1e912818b519786590a5893e7ff20d006a27703bd54d67e8faa` |

Os nove Makefiles recuperados coincidiram com os membros correspondentes do tarball. O acervo também preserva executáveis de classes B e S, as notas manuais originais e os snapshots `_ambiente.txt`. A série `npb_8_SP_A` fica fora do conjunto principal. [Seleção dos materiais](../docs/publicacao.md) · [Seleção da série SP](../results/README.md#seleção-da-série-sp)
