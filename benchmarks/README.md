# Proveniência do NPB

A pesquisa utilizou o NAS Parallel Benchmarks 3.4.4, implementação MPI, classe A. O SHA-256 do tarball recuperado, do `make.def` e dos oito binários da campanha coincide com o valor declarado em cada snapshot correspondente. A comparação com o tarball mostrou que os nove Makefiles recuperados são idênticos aos distribuídos pela NASA. [Manifesto de proveniência](../metadata/proveniencia-npb.md)

## Pacote-fonte verificado

O download oficial da NASA contém 446.013 bytes. O SHA-256 calculado coincide com o valor declarado nas oito coletas.

```text
1ae219398e02a0a79ad51b7460fcffbf7b5df83a69d5d3d3a9dc2d8acf523549  NPB3.4.4.tar.gz
```

Os avisos nos arquivos principais de EP, IS, CG, MG, FT, LU, BT e SP da implementação MPI permitem uso, cópia, modificação e redistribuição, com ou sem cobrança. Também pedem que trabalhos derivados referenciem o NAS Parallel Benchmarks 3.4 e registram a ausência de garantia. Consulte os cabeçalhos originais do tarball para os termos de cada componente. [Distribuição oficial do NPB](https://www.nas.nasa.gov/software/npb.html)

O pacote, os Makefiles da distribuição e os binários ARM ficam no acervo restrito. O [`make.def` recuperado](../config/npb/make.def) preserva a configuração local de compilação. A conferência do pacote e das entradas recuperadas verifica a proveniência dos arquivos disponíveis.

## Compilação da classe A

Use uma árvore NPB 3.4.4 MPI obtida da NASA e um ambiente AArch64 com os wrappers `mpicc` e `mpif90` do Open MPI 4.1.0 associados a GCC e GNU Fortran 10.2.1. A configuração original usa `-O3` e adiciona `-fallow-argument-mismatch` às flags de Fortran. Registre as versões dos compiladores, os caminhos efetivos dos wrappers e os hashes dos binários gerados. [Configuração original](../config/README.md)

A partir da raiz do repositório, ajuste o caminho para o pacote já obtido. Os comandos verificam o arquivo e compilam em uma árvore separada.

```sh
(
    set -eu
    repo_tcc=$(pwd -P)
    pacote_npb=/caminho/para/NPB3.4.4.tar.gz
    printf '%s  %s\n' '1ae219398e02a0a79ad51b7460fcffbf7b5df83a69d5d3d3a9dc2d8acf523549' "$pacote_npb" |
        sha256sum --check --strict
    build_npb=$(mktemp -d)
    tar -xzf "$pacote_npb" -C "$build_npb"
    cd "$build_npb/NPB3.4.4/NPB3.4-MPI"
    cp -- "$repo_tcc/config/npb/make.def" config/make.def
    for benchmark in ep is cg mg ft lu bt sp; do
        make "$benchmark" CLASS=A
    done
    sha256sum -- bin/*.A.x
)
```

O acervo contém as amostras de `suite.def` no tarball. O uso de um `suite.def` pela compilação histórica permanece indeterminado. Os alvos individuais acima dispensam esse arquivo. O hash final de um binário também depende das bibliotecas, do ambiente e das condições da compilação. Compare com os hashes históricos e registre eventuais diferenças. [Binários da campanha](../metadata/proveniencia-npb.md#binários-por-campanha)

Para reproduzir a análise dos CSVs arquivados, use o guia da auditoria. Para repetir as medições no cluster, siga a matriz e as condições do protocolo experimental. [Guia da auditoria](../scripts/analise/auditoria-npb/README.md) · [Protocolo](../docs/protocolo-experimental.md) · [Plano de publicação](../docs/publicacao.md)
