# Publicação, licenciamento e citação

O acervo público está disponível no GitHub. [Repositório do TCC](https://github.com/MatheusPiassiC/tvbox-hpc-cluster)

## Seleção e armazenamento

| Material | Destino |
| --- | --- |
| 24 originais revisados | Git. Oito CSVs de planos, oito CSVs de medições e oito TXTs de saída MPI/NPB. |
| Código, configurações documentadas, tabelas, gráficos e manifestos | Git. Os arquivos versionados mantêm os caminhos usados para consulta e geração das figuras. |
| Oito snapshots `*_ambiente.txt` e manual original | Acervo local restrito. Os snapshots contêm identificadores de interfaces. O manual inclui parâmetros de rede substituídos por campos de preenchimento na cópia em `docs/`. |
| Ambientes Python, caches, imagem de sistema, binários compilados e saídas de reprocessamento | Fora da seleção inicial. As saídas de verificação e o acervo local ficam sob `.local/`. |
| Pacote NPB de terceiros | Download oficial da NASA, acompanhado do SHA-256 verificado no [guia do NPB](../benchmarks/README.md). |

Os arquivos distribuídos ocupam cerca de 32 MiB. O maior arquivo, `comparativo_A_tempo_absoluto.png`, ocupa 1,91 MiB. O Git convencional comporta os dados e gráficos desta versão. O GitHub emite aviso acima de 50 MiB e bloqueia arquivos acima de 100 MiB no Git convencional. [Limites de arquivos do GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)

O recorte público permite consultar as 460 tentativas e gerar novamente as figuras a partir das tabelas processadas. Reprocessar a auditoria completa a partir dos originais requer acesso ao conjunto local de 32 arquivos. As referências por linha aos snapshots nos relatórios arquivados também requerem acesso à cópia local. [Dados experimentais](../results/README.md) · [Reprodução da análise](../metadata/README.md#resultado-da-reprodução)

O `.gitignore` exclui os originais restritos e os produtos locais. O `.gitattributes` mantém os bytes dos registros e dos artefatos da auditoria e define LF para os demais arquivos de texto. A cópia pública pode ser conferida a partir da raiz com:

```sh
sha256sum --check --strict SHA256SUMS
```

## Licenciamento e materiais de terceiros

- **Scripts e testes autorais.** Recomenda-se MIT, que permite reutilização e modificação com preservação do aviso de direitos autorais e da licença. Confirmar titulares e aprovar o escopo antes de adicionar `LICENSE`. [Licença MIT](https://opensource.org/license/mit)
- **Documentação, figuras e dados de autoria própria.** Recomenda-se CC BY 4.0 para os direitos que os titulares puderem licenciar, com crédito e indicação de adaptações. Preservar as atribuições de terceiros e identificar os materiais abrangidos. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.pt)
- **NPB 3.4.4.** O tarball oficial coincide com o hash das oito coletas. Os avisos da implementação MPI usada autorizam redistribuição e pedem referência ao NPB 3.4. Preservar os avisos pertinentes se uma versão futura redistribuir código, patches ou binários. [Conferência do pacote e dos avisos](../benchmarks/README.md)
- **Imagem personalizada.** O sistema de build do Armbian publica licença GPLv2. As condições da imagem efetiva dependem dos pacotes, do firmware e das alterações presentes nela. A imagem ainda precisa ser recuperada e inventariada para essa avaliação. [Licença do sistema de build do Armbian](https://github.com/armbian/build/blob/main/LICENSE)
- **Fontes e ferramentas.** Os PDFs incorporam STIX General, DejaVu e Latin Modern. Os avisos instalados identificam SIL OFL 1.1, Bitstream Vera/Arev e GUST/LPPL 1.3c ou posterior, respectivamente. Manter os créditos dos componentes incorporados. O repositório indica as versões das ferramentas e das dependências Python e usa as distribuições oficiais para obtê-las. [Aviso STIX](https://github.com/matplotlib/matplotlib/blob/main/lib/matplotlib/mpl-data/fonts/ttf/LICENSE_STIX) · [Licença DejaVu](https://dejavu-fonts.github.io/License.html) · [Latin Modern](https://ctan.org/pkg/lm)

A proposta de licenciamento segue pendente de aprovação dos titulares. Ao aprovar as licenças, registrar o alcance por grupo de arquivos para que os avisos de terceiros sejam preservados.

## Referência acadêmica

O artefato complementa o TCC *Análise de Desempenho e Custo de um Cluster de Baixo Custo Baseado em TV Boxes Reaproveitadas*, do curso de Ciência da Computação da Universidade Federal de Lavras (UFLA), sob orientação do Prof. Dr. Luiz Henrique Andrade Correia.

Para citar o estudo, use o registro bibliográfico oficial do TCC quando estiver disponível. Para citar os dados ou o código, identifique o artefato consultado, a campanha de 16 e 17 de novembro de 2026 quando aplicável e a versão do conjunto. Na cópia local, `estado_entrada_sha256` identifica os dados e `codigo_sha256` identifica a versão do código da auditoria. [Manifesto de reprodução](../results/processed/auditoria/manifestos/reproducibilidade.json)

A autoria bibliográfica, o ano de defesa e a referência oficial do TCC ainda precisam ser confirmados. Com esses dados, preparar e validar o `CITATION.cff` com os nomes das pessoas autoras, ORCID quando disponível, título, versão, data e endereço do artefato. [Arquivos de citação no GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)

## Git e sequência de commits

A primeira publicação em `main` agrupa as alterações na seguinte sequência:

1. `chore: definir exclusões e preservar bytes dos artefatos` para `.gitignore` e `.gitattributes`.
2. `data: preservar registros e resultados da campanha NPB` para os originais da seleção, os resultados processados, os manifestos e as figuras de referência.
3. `feat: incluir auditoria, visualizações e verificação de integridade` para código, testes existentes e dependências fixadas.
4. `docs: documentar o cluster H7 e a reprodução do estudo` para o manual, o hostfile recuperado, o protocolo, a proveniência do NPB e o README.
5. `chore: registrar manifesto SHA-256 da versão pública` para o `SHA256SUMS`.

## Checklist da futura Release

- [x] Simular a seleção do Git e conferir a exclusão do acervo local e dos snapshots restritos.
- [x] Conferir o conjunto local, reproduzir as tabelas e figuras arquivadas e verificar a integridade dos originais.
- [x] Conferir o SHA-256 e os avisos da distribuição oficial do NPB.
- [ ] Confirmar autoria, licenças e dados de citação aplicáveis ao conjunto final.
- [x] Obter autorização para enviar a seleção ao repositório público.
- [x] Gerar e conferir o manifesto SHA-256 dos arquivos distribuídos na publicação inicial.
- [ ] Repetir a triagem quando a Release incluir arquivos adicionais.

## Procedimento futuro

1. Confirmar os dados de citação, os avisos e as licenças da versão para a Release.
2. Marcar a versão aprovada com uma tag anotada. Registrar a campanha, o commit, as versões do ambiente, o recorte de dados distribuído e as lacunas de reprodução.
3. Conferir uma cópia do conjunto final com o manifesto de distribuição e publicar a Release autorizada.
