# Metadados e integridade

## Série NPB classe A

Os manifestos originais identificam os 32 arquivos de entrada, os artefatos da auditoria e a versão do código. Em `dados_entrada.json`, os caminhos que começam em `raw/` são relativos a `results/` nesta árvore. Em `artefatos.json`, os caminhos são relativos a `results/processed/auditoria/`. Em `reproducibilidade.json`, os caminhos do código são relativos a `scripts/analise/auditoria-npb/`. [Manifestos arquivados](../results/processed/auditoria/manifestos/)

Os oito conjuntos de coleta estão identificados pelo benchmark e pelo identificador `experimento_id`. As datas, as assinaturas declaradas do coletor, dos binários e da compilação e as opções registradas constam de `ambientes.csv`. O manifesto de proveniência registra a conferência dos arquivos recuperados contra essas assinaturas. [Ambiente por campanha](../results/processed/auditoria/tabelas/ambientes.csv) · [Proveniência da campanha](proveniencia-npb.md)

Use `estado_entrada_sha256` para identificar o conjunto de dados e `codigo_sha256` para identificar a versão do código da auditoria. O manifesto de reprodução também registra o Python e as versões das dependências. [Manifesto de reprodução](../results/processed/auditoria/manifestos/reproducibilidade.json)

## Verificação da cópia pública

O manifesto na raiz registra os hashes dos arquivos distribuídos com esta versão, com caminhos relativos à raiz. Execute a conferência na raiz da cópia obtida no GitHub. [Manifesto SHA-256](../SHA256SUMS)

```sh
sha256sum --check --strict SHA256SUMS
```

## Verificação local

Na raiz do repositório, execute o verificador com Python 3.12. Ele usa a biblioteca padrão, lê os três manifestos existentes e retorna código de saída diferente de zero se detectar arquivos ausentes, inacessíveis ou com SHA-256 divergente.

```sh
python3 scripts/analise/verificar_integridade.py
```

O verificador confere 32 arquivos brutos, 37 artefatos da auditoria e 15 arquivos de código e dependências. A verificação dos 32 originais requer a cópia local completa, incluindo os oito snapshots de ambiente excluídos do versionamento.

## Resultado da reprodução

A auditoria foi reprocessada em um destino separado com Python 3.12.3 e as 12 versões registradas no manifesto. As novas tabelas alimentaram os dois geradores. A compilação das provas e das tabelas usou pdfTeX 1.40.29 do TeX Live 2026 e Poppler 24.02.0. O reprocessamento preservou a amostra de 460 tentativas em 46 configurações e os identificadores de tentativa e posição lógica. [Comandos de análise](../scripts/analise/auditoria-npb/README.md#reproduzir-a-análise) · [Comandos de visualização](../scripts/README.md#gerar-as-visualizações)

| Conjunto comparado | Resultado |
| --- | --- |
| Auditoria | As 18 tabelas CSV, os 12 arquivos de gráficos e os manifestos de entrada e de código coincidiram byte a byte. Os cinco relatórios coincidiram após ajustar os links relativos para a comparação. O manifesto de artefatos registra os hashes dos relatórios nos respectivos destinos. |
| Catálogo | Os 121 arquivos PDF, PNG e LaTeX coincidiram byte a byte. O Markdown varia nos links para as tabelas, o script e o guia. |
| Peças candidatas ao TCC | Os 18 arquivos PDF, PNG e LaTeX coincidiram byte a byte. |

Os SHA-256 dos registros originais e das saídas arquivadas foram conferidos antes e depois. Os manifestos atuais registram a edição consolidada dos relatórios e a versão do código que os gera. As tabelas e os gráficos tiveram seus hashes novamente conferidos após essa revisão.

Para comparar novas saídas, use os diretórios documentados nos comandos acima. A partir da raiz, compare as tabelas e os gráficos da auditoria com:

```sh
diff -qr results/processed/auditoria/tabelas .local/reproducao/auditoria/tabelas
diff -qr results/processed/auditoria/graficos .local/reproducao/auditoria/graficos
```

## Metadados de novas coletas

Para uma nova coleta, use um arquivo JSON por campanha. Copie o [modelo de campanha](campanha.example.json) para `metadata/<id-da-campanha>.json`, preencha com evidências e registre os valores indisponíveis. Use caminhos relativos à raiz e identifique os artefatos por commit, versão de origem ou SHA-256. Registre horários em ISO 8601 com fuso. Preserve os originais em [`results/raw/`](../results/raw/).

O inventário de tentativas pode ser mantido em um arquivo JSON separado por campanha, referenciado pelo modelo. Cada tentativa deve indicar identificador, benchmark, classe, número de processos, horário, configuração, binário, arquivos originais e chave ou linha quando aplicável, estado de validação, critério e justificativa de exclusão. Ajustar o formato do inventário após examinar a coleta original.

## Manifesto SHA-256

Gere `SHA256SUMS` a partir da raiz do conjunto. Para a seleção da integração de 23/11/2026, combine os caminhos versionados com os quatro destinos novos explicitamente selecionados. O comando ordena os caminhos por byte, remove duplicatas e exclui o próprio manifesto. A lista explícita permite conferir os novos arquivos antes do stage.

```bash
(
    set -euo pipefail
    manifesto=$(mktemp .SHA256SUMS.XXXXXXXX)
    trap 'rm -f -- "$manifesto"' EXIT
    {
        git ls-files -z -- . ':(exclude,top)SHA256SUMS'
        printf '%s\0' \
            config/npb/make.def \
            docs/custos.md \
            metadata/proveniencia-npb.md \
            scripts/coleta/npb-experimento-v5.4.sh
    } | LC_ALL=C sort -zu | xargs -0 -r sha256sum -- > "$manifesto"
    sha256sum --check --strict --quiet "$manifesto"
    chmod --reference=SHA256SUMS "$manifesto"
    mv -- "$manifesto" SHA256SUMS
)
sha256sum --check --strict SHA256SUMS
```

Para uma seleção futura, ajuste a lista de destinos novos à versão aprovada. Se a distribuição tiver layouts diferentes, gere um manifesto por conjunto e registre o diretório de referência nas notas da Release.
