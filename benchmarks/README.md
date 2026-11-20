# Proveniência do NPB

A pesquisa utilizou o NAS Parallel Benchmarks 3.4.4, implementação MPI. Os snapshots registram o SHA-256 declarado do tarball `NPB3.4.4.tar.gz`, do `make.def` e dos binários por benchmark. A comparação relatada nos snapshots identificou o mesmo conteúdo-fonte do tarball. [Metadados de compilação](../results/processed/auditoria/tabelas/ambientes.csv)

## Pacote-fonte verificado

O download oficial da NASA contém 446.013 bytes. O SHA-256 calculado coincide com o valor declarado nas oito coletas.

```text
1ae219398e02a0a79ad51b7460fcffbf7b5df83a69d5d3d3a9dc2d8acf523549  NPB3.4.4.tar.gz
```

Os avisos nos arquivos principais de EP, IS, CG, MG, FT, LU, BT e SP da implementação MPI permitem uso, cópia, modificação e redistribuição, com ou sem cobrança. Também pedem que trabalhos derivados referenciem o NAS Parallel Benchmarks 3.4 e registram a ausência de garantia. Consulte os cabeçalhos originais do tarball para os termos de cada componente. [Distribuição oficial do NPB](https://www.nas.nasa.gov/software/npb.html)

Ao obter o pacote, calcule o SHA-256 com `sha256sum -- caminho/do/pacote` e compare com o valor acima. O `make.def` integral e os binários da campanha ainda precisam ser recuperados para conferência direta.

Guardar em [patches](patches/) as alterações locais efetivamente aplicadas, se existirem, com ordem de aplicação e referência ao pacote-base. Preservar em [config/npb](../config/npb/) as configurações efetivas de compilação. Associar cada binário ao código-fonte, patches, classe, opções de compilação, compiladores, bibliotecas, registro da compilação e SHA-256 disponível. Vincular esse registro às campanhas correspondentes.

A versão proposta do repositório remete ao download da NASA. Se uma futura Release incluir o pacote ou componentes dele, preserve os avisos originais e a atribuição. [Plano de publicação](../docs/publicacao.md)
