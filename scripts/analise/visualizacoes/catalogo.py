"""Catálogo Markdown vinculado aos arquivos e às dimensões da geração."""

import os
from pathlib import Path

from alternativas import FAMILIAS, FIGURAS, LARGURA_UTIL, TABELAS
from graficos import decimal
from pre_impressao import base, caminho_comparativo, caminho_previa, dimensoes


METRICAS = {
    "tempo": "Tempo médio do NPB (s) e IC bilateral de 95%",
    "relativo": "Tempo normalizado R(p) = T̄(p)/T̄(1)",
    "speedup": "Speedup S(p) = T̄(1)/T̄(p)",
    "eficiencia": "Eficiência paralela E(p) = 100 × S(p)/p (%)",
}


def contagem(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def link(rotulo, caminho):
    return f"[{rotulo}]({Path(caminho).as_posix()})"


def links_alternativa(item):
    nome = base(item)
    formatos = [link(f"`{item.arquivo}.pdf`", nome.with_suffix(".pdf")),
                link("PNG", nome.with_suffix(".png")), link("Prévia", caminho_previa(item))]
    if item.familia == "T":
        formatos.append(link("TeX", nome.with_suffix(".tex")))
    return formatos


def ficha(item, dim):
    if item.familia == "T":
        metrica = "Síntese por benchmark no mínimo de tempo e no maior p avaliado"
        quantidade = f"8 linhas de dados, {len(item.campos)} colunas"
        inclusao = f"`\\input` do fragmento `booktabs`, com largura declarada de {decimal(item.largura, 1)} cm."
    else:
        metrica = " · ".join(METRICAS[m] for m in dict.fromkeys(p.metrica for p in item.paineis))
        n_paineis = len(item.paineis)
        n_curvas = sum(len(p.series) for p in item.paineis)
        n_referencias = sum(p.metrica != "tempo" for p in item.paineis)
        quantidade = " · ".join((contagem(n_paineis, "painel", "painéis"),
                                  contagem(n_curvas, "série observada", "séries observadas"),
                                  contagem(n_referencias, "linha de referência", "linhas de referência")))
        inclusao = f"`\\includegraphics[width={item.dim[0]:.1f}cm]` com altura resultante de {decimal(dim[1], 1)} cm."

    linhas = [
        f"## {item.id}", "",
        " · ".join(links_alternativa(item)), "",
        "| Propriedade | Descrição |", "| --- | --- |",
        f"| Métrica | {metrica} |", f"| Estrutura | {quantidade} |", f"| Disposição | {item.disposicao} |",
        f"| Dimensões do PDF | {dimensoes(dim)} |", f"| Inserção no LaTeX | {inclusao} |",
    ]
    if item.familia != "T":
        eixo_x = "log₂" if item.escala_x == "log" else "linear"
        escala_y = {"linear": "linear", "log": "logarítmica", "local": "linear com limites por benchmark"}
        eixo_y = " e ".join(escala_y[escala] for escala in dict.fromkeys(p.escala_y for p in item.paineis))
        if item.familia == "A" and item.id != "A07":
            eixo_y += " com limites por benchmark"
        local = {"inferior": "faixa inferior", "superior": "faixa superior", "celula": "célula livre"}[item.legenda]
        linhas += [f"| Eixos e legenda | x em escala {eixo_x}, y em escala {eixo_y}, legenda na {local} |"]
    linhas += ["", f"- **Vantagem** — {item.vantagem}", f"- **Limitação** — {item.limitacao}",
               f"- **Leitura em tamanho de inserção** — {item.legibilidade}",
               f"- **Discussão** — {item.discussao}", ""]
    return linhas


def escrever_catalogo(pasta, saida, entrada, script, dados, dim, dpi, dpi_previa, motivo_tabelas, motivo_a4):
    itens = (*FIGURAS, *TABELAS)
    texto = [
        "# Catálogo de visualizações experimentais", "",
        f"Campanha NPB 3.4.4, MPI, classe A. O catálogo reúne {len(FIGURAS)} figuras e {len(TABELAS)} tabelas. "
        f"As {dados.n_configuracoes} configurações usam as {dados.n_execucoes} execuções auditadas, "
        f"incluindo as {dados.n_atipicas} observações atípicas sinalizadas. "
        "As alternativas servem à comparação antes da seleção para o TCC.", "",
        "## Navegação", "", "| ID | Arquivos | Largura × altura |", "| --- | --- | --- |",
    ]
    for item in itens:
        ancora = item.id.lower()
        texto.append(f"| [{item.id}](#{ancora}) | {' · '.join(links_alternativa(item))} | {dimensoes(dim[item.id])} |")
    texto += ["", "## Folhas comparativas e prova A4", "", "| Família | Arquivos |", "| --- | --- |"]
    for familia, (_, _, titulo) in FAMILIAS.items():
        caminho = caminho_comparativo(familia)
        texto.append(f"| {familia} · {titulo} | {link(caminho.name + '.pdf', caminho.with_suffix('.pdf'))} · "
                     f"{link('PNG', caminho.with_suffix('.png'))} |")
    texto += [
        "",
        "Cada folha usa a mesma redução de 52% para todas as miniaturas e para a régua de largura útil. "
        "Use as folhas para comparar a composição e a prova A4 para ler no tamanho de inserção.", "",
        "O modelo LaTeX do TCC não estava disponível neste repositório. A prova usa papel A4, "
        f"{decimal(LARGURA_UTIL, 1)} cm de largura útil, margens laterais de 2,7 cm e margens verticais de 2,5 cm. "
        "Há uma alternativa por página em ordem de catálogo. Avalie a 100% ou imprima em tamanho real.", "",
        f"- {link('Prova A4', 'comparativos/previas_A4.pdf')} · {link('Fonte LaTeX', 'comparativos/previas_A4.tex')}",
    ]
    if motivo_a4:
        texto += [f"- Prova A4 simulada com as mesmas dimensões de inserção. Motivo registrado ` {motivo_a4} `."]
    else:
        texto += [r"- Prova compilada com pdfLaTeX. As figuras foram inseridas com `\includegraphics` e as tabelas com `\input`."]
    if motivo_tabelas:
        texto += [f"- PDFs e PNGs de tabela renderizados com Matplotlib. Motivo registrado ` {motivo_tabelas} `."]
    else:
        texto += ["- Cada PDF de tabela foi compilado a partir do fragmento `.tex`. Os PNGs dessas tabelas são rasterizações dos PDFs."]

    def fonte(nome):
        return link(nome, os.path.relpath(entrada / nome, saida))

    relatorios = entrada.parent / "relatorios"
    estatistica = link("Metodologia estatística", os.path.relpath(relatorios / "03_analise_estatistica.md", saida))
    diagnostico = link("Diagnóstico por benchmark", os.path.relpath(relatorios / "04_diagnostico_dos_benchmarks.md", saida))
    texto += [
        "", "## Dados, eixos e incerteza", "",
        "- **Tempo absoluto** — Média aritmética do tempo interno do NPB em segundos. As barras usam os limites "
        f"do IC bilateral t de 95% auditado para cada média. {fonte('estatisticas_descritivas.csv')} · {estatistica}",
        "- **Tempo normalizado** — R(p) = T̄(p)/T̄(1) na mesma campanha. A linha em R = 1 indica o tempo de referência. "
        "R < 1 indica redução de tempo e R > 1 indica aumento.",
        "- **Speedup e eficiência** — S(p) = T̄(1)/T̄(p) e E(p) = 100 × S(p)/p. Os pontos usam os valores auditados. "
        "A referência de speedup é S = p ao longo da faixa avaliada de cada painel. A referência de eficiência é 100%. "
        f"Tempo normalizado, speedup e eficiência são estimativas pontuais. {fonte('speedup_eficiencia.csv')}",
        "- **Processos MPI** — EP, IS, CG, MG, FT e LU usam 1, 2, 4, 8, 16 e 32. BT e SP usam 1, 4, 9, 16 e 25. "
        "Os eixos x usam log₂, com exceção de A06a e A06b, que usam escala linear. As linhas coloridas unem as "
        "observações marcadas para guiar a leitura. A linha cinza de speedup ideal representa a função teórica.",
        "- **Agrupamento** — EP, MG, LU e SP têm o mínimo de tempo na maior configuração e média decrescente a cada transição. "
        "IS, CG e FT têm mínimos intermediários. BT tem uma regressão de 4 para 9 processos e seu mínimo em 25. "
        f"Os painéis agrupam os benchmarks pela evolução dos tempos médios. {diagnostico}",
        "- **Estilo** — STIXGeneral nos gráficos, com ticks de 8 pt no tamanho de inserção e símbolos e traços próprios "
        "por benchmark. Linhas cinza tracejadas representam as referências. Os eixos y lineares incluem o zero "
        "com uma pequena folga inferior para os marcadores. Os fragmentos de tabela usam `booktabs`.",
        "- **Validação da geração** — As médias, desvios-padrão e ICs foram confrontados com as dez repetições de cada chave. "
        "Foram conferidos o speedup, a eficiência, R × S = 1, a inclusão dos valores atípicos e os números das tabelas. "
        "Também foram verificados os ticks, os dados dos artistas, os limites das barras, as referências e a posição dos textos "
        f"e das legendas. {fonte('execucoes_consolidadas.csv')} · {fonte('observacoes_atipicas.csv')} · {fonte('resumo_benchmarks.csv')}",
        "", "## Comparação em tamanho de inserção", "",
        "- Para o tempo absoluto, A03 mantém as oito séries em uma página e acomoda a chave do IC. A04a/b e A05a/b dão mais "
        "espaço às escalas e à leitura das regressões. A06a/b ocupam a maior parte da altura útil.",
        "- B04 mantém as regressões de IS e FT acima de R = 1 e separa os tempos pequenos. B02 preserva a escala y linear "
        "comum e reduz a quantidade de curvas por painel.",
        "- C06 dá espaço ao speedup abaixo do ideal com escalas indicadas nos eixos. D01 apresenta o excedente superlinear "
        "em pontos percentuais. D05a/b e E05 abrem espaço para os valores baixos com escala logarítmica.",
        "- E03 mantém os grupos na mesma ordem nas duas métricas. E02 oferece mais espaço para seguir curvas individuais. "
        "E05 ocupa meia largura e concentra mais cruzamentos por centímetro.",
        "- T01 conserva os ICs e as eficiências nos dois p de interesse. T02 atende a um resumo que caiba em largura menor.",
        "", "## Reprodução", "",
        "A partir da raiz do repositório, use a `.venv` preparada conforme o guia da auditoria.", "",
        "```sh", ".venv/bin/python scripts/analise/visualizacoes/gerar_visualizacoes.py", "```", "",
        f"O script aceita `--entrada`, `--saida`, `--dpi` e `--dpi-previa`. Esta geração usa PNGs a {dpi} dpi "
        f"e prévias raster a {dpi_previa} dpi nas mesmas dimensões físicas dos originais. "
        "Figuras e tabelas têm PDFs vetoriais. As folhas comparativas usam miniaturas rasterizadas. "
        "A instalação de pdfLaTeX com `booktabs`, `lmodern`, `geometry` e `graphicx`, mais `pdftoppm` e `pdfinfo`, "
        f"permite compilar e rasterizar as provas a partir da fonte LaTeX. {link('Script', os.path.relpath(script, saida))}",
        "", "As fichas abaixo registram a disposição, a escala, o tamanho e as limitações de cada alternativa. "
        "As alturas incluem os rótulos e a legenda interna da própria figura. Reserve espaço adicional para a legenda do TCC.", "",
    ]
    for item in itens:
        texto += ficha(item, dim[item.id])
    (pasta / "CATALOGO_VISUALIZACOES.md").write_text("\n".join(texto), encoding="utf-8")
