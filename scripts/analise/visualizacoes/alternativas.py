"""Composições, dimensões de impressão e notas para o catálogo."""

from dataclasses import dataclass

from npb_auditoria.model import LEVELS


LARGURA_UTIL = 15.6
ALTURA_UTIL = 24.7
FAMILIAS = {
    "A": ("01_tempo_absoluto", "tempo_absoluto", "Tempo absoluto"),
    "B": ("02_tempo_normalizado", "tempo_normalizado", "Tempo normalizado"),
    "C": ("03_speedup", "speedup", "Speedup"),
    "D": ("04_eficiencia", "eficiencia", "Eficiência paralela"),
    "E": ("05_metricas_combinadas", "metricas_combinadas", "Speedup e eficiência"),
    "T": ("06_tabelas", "tabelas", "Tabelas de síntese"),
}

TODOS = tuple(LEVELS)
CONVENCIONAL_1, CONVENCIONAL_2 = TODOS[:4], TODOS[4:]
GRUPO_1, GRUPO_2 = ("EP", "MG", "LU", "SP"), ("IS", "CG", "FT", "BT")


@dataclass(frozen=True)
class Painel:
    metrica: str
    series: tuple[str, ...]
    titulo: str = ""
    escala_y: str = "linear"


@dataclass(frozen=True)
class Figura:
    id: str
    arquivo: str
    grade: tuple[int, int]  # colunas, linhas
    dim: tuple[float, float]
    paineis: tuple[Painel, ...]
    disposicao: str
    vantagem: str
    limitacao: str
    legibilidade: str
    discussao: str
    legenda: str = "inferior"
    escala_x: str = "log"
    eixo_x_comum: bool = False

    @property
    def familia(self) -> str:
        return self.id[0]


@dataclass(frozen=True)
class Tabela:
    id: str
    arquivo: str
    largura: float
    campos: tuple[str, ...]
    disposicao: str
    vantagem: str
    limitacao: str
    legibilidade: str
    discussao: str

    @property
    def familia(self) -> str:
        return "T"


def individuais(metrica, series=TODOS, escala="linear"):
    return tuple(Painel(metrica, (b,), b, escala) for b in series)


def por_grupo(metrica):
    return tuple(
        Painel(metrica, grupo, ", ".join(grupo)) for grupo in (GRUPO_1, GRUPO_2)
    )


FIGURAS = (
    Figura("A01", "A01_tempo_absoluto_8paineis_4x2", (4, 2), (15.6, 8.6),
           individuais("tempo"), "4 colunas × 2 linhas",
           "Reúne os oito benchmarks em uma faixa curta da página.",
           "Os eixos y independentes indicam magnitudes diferentes em cada painel.",
           "O espaço entre marcas de processos é menor. As hastes dos ICs mais estreitos podem se fundir ao marcador.",
           "Permite contrastar curvas decrescentes e regressões locais em um único quadro."),
    Figura("A02", "A02_tempo_absoluto_8paineis_2x4", (2, 4), (15.6, 17.3),
           individuais("tempo"), "2 colunas × 4 linhas",
           "Dá mais espaço horizontal aos processos de cada benchmark.",
           "Ocupa cerca de 70% da altura útil A4 antes da legenda LaTeX.",
           "Os ticks têm maior separação lateral. ICs muito curtos ainda podem aparecer apenas como traços.",
           "Facilita localizar os mínimos e os aumentos de tempo nas transições observadas."),
    Figura("A03", "A03_tempo_absoluto_8paineis_3x3", (3, 3), (15.6, 13.3),
           individuais("tempo"), "3 colunas × 3 linhas com legenda na última célula",
           "O espaço final explica a média e o IC sem consumir uma faixa da página.",
           "Os quatro últimos painéis da ordem de leitura se dividem entre duas linhas.",
           "Os eixos são menos largos que em A02. A legenda e os oito títulos ficam fora das áreas dos dados.",
           "Equilibra a identificação das oito tendências com a leitura de tempos em segundos.", legenda="celula"),
    Figura("A04a", "A04a_tempo_absoluto_EP_IS_CG_MG_2x2", (2, 2), (15.6, 10.0),
           individuais("tempo", CONVENCIONAL_1), "2 colunas × 2 linhas com EP, IS, CG e MG",
           "Painéis largos facilitam a leitura das escalas independentes e dos mínimos.",
           "A04b contém a outra metade dos benchmarks.",
           "A dispersão relativa pode ser pouco aparente nas barras com IC muito estreito.",
           "Confronta EP e MG com as inversões de tendência de IS e CG."),
    Figura("A04b", "A04b_tempo_absoluto_FT_LU_BT_SP_2x2", (2, 2), (15.6, 10.0),
           individuais("tempo", CONVENCIONAL_2), "2 colunas × 2 linhas com FT, LU, BT e SP",
           "Mantém espaço para ticks e ICs em curvas de magnitudes distintas.",
           "A04a contém a outra metade dos benchmarks.",
           "As barras de FT são mais visíveis em p = 32. As de BT em algumas configurações ficam próximas do marcador.",
           "Mostra a dispersão de FT e SP e o aumento local de BT em 9 processos."),
    Figura("A05a", "A05a_tempo_absoluto_melhora_ate_maximo_2x2", (2, 2), (15.6, 10.0),
           individuais("tempo", GRUPO_1), "2 colunas × 2 linhas com EP, MG, LU e SP",
           "Reúne as séries cujo tempo médio diminuiu nas transições observadas.",
           "Os limites independentes dificultam comparar segundos pela inclinação aparente.",
           "Para comparar magnitudes, consulte as marcações de cada eixo y.",
           "Documenta mínimos nas maiores configurações, inclusive SP em 25 processos."),
    Figura("A05b", "A05b_tempo_absoluto_regressoes_intermediarias_2x2", (2, 2), (15.6, 10.0),
           individuais("tempo", GRUPO_2), "2 colunas × 2 linhas com IS, CG, FT e BT",
           "Concentra os casos com aumento de tempo entre configurações consecutivas.",
           "O mínimo de BT ocorre em 25 processos, após a regressão local de 4 para 9.",
           "As barras de FT em 32 processos são visualmente maiores. As amplitudes em segundos exigem ler o eixo de cada painel.",
           "Relaciona mínimos intermediários de IS, CG e FT à recuperação observada em BT."),
    Figura("A06a", "A06_tempo_absoluto_paineis_horizontais_EP_MG_LU_SP", (1, 4), (15.6, 20.5),
           individuais("tempo", GRUPO_1), "1 coluna × 4 linhas com painéis largos",
           "Os painéis largos permitem espaçamento linear entre os processos.",
           "Ocupa cerca de 83% da altura útil A4. A legenda LaTeX ocupa parte da altura restante.",
           "A separação entre os primeiros valores de p é menor na escala linear.",
           "Distingue a fase inicial das transições com mais processos, respeitando os valores de p de SP.",
           escala_x="linear"),
    Figura("A06b", "A06_tempo_absoluto_paineis_horizontais_IS_CG_FT_BT", (1, 4), (15.6, 20.5),
           individuais("tempo", GRUPO_2), "1 coluna × 4 linhas com painéis largos",
           "Distribui os processos no espaço de acordo com os incrementos absolutos.",
           "Ocupa cerca de 83% da altura útil A4. A legenda LaTeX ocupa parte da altura restante.",
           "O uso de uma coluna amplia as transições nos valores altos de p. As iniciais ficam próximas.",
           "Mostra a piora de IS e FT em 8 processos e a regressão de BT em 9.", escala_x="linear"),
    Figura("A07", "A07_tempo_absoluto_8curvas_escala_log", (1, 1), (15.6, 9.6),
           (Painel("tempo", TODOS, escala_y="log"),), "8 curvas sobrepostas com eixo y logarítmico",
           "Compara em segundos amplitudes que vão de menos de 1 s a centenas de segundos.",
           "Distâncias verticais representam razões de tempo. Curvas próximas podem se cruzar.",
           "Os ICs pequenos e as sobreposições de marcadores exigem consultar os painéis individuais ou a tabela.",
           "Explora ordens de grandeza e mostra por que tempos absolutos em escala linear comum ocultariam parte das séries."),
    Figura("B01", "B01_tempo_normalizado_8curvas_sobrepostas", (1, 1), (15.6, 8.8),
           (Painel("relativo", TODOS),), "8 curvas sobrepostas",
           "Uma mesma escala mostra a redução e o aumento relativo à referência.",
           "Os valores de IS ampliam o intervalo e comprimem as curvas abaixo de R = 1.",
           "Todos os benchmarks coincidem em p = 1. Há cruzamentos em outros processos.",
           "IS e FT ultrapassam a referência. As demais séries ficam abaixo dela após p = 1."),
    Figura("B02", "B02_tempo_normalizado_2paineis_por_comportamento", (2, 1), (15.6, 8.4),
           por_grupo("relativo"), "2 painéis lado a lado por comportamento",
           "A escala y comum permite comparação direta entre os grupos com quatro curvas por painel.",
           "O grupo EP, MG, LU e SP ocupa menos de um terço do intervalo y.",
           "As marcas 8 e 9 ficam próximas no grupo com BT ou SP. Os marcadores preservam os processos efetivos.",
           "Contextualiza as regressões em relação ao desempenho no processo de referência."),
    Figura("B03", "B03_tempo_normalizado_8paineis_4x2", (4, 2), (15.6, 8.7),
           individuais("relativo", escala="local"), "4 colunas × 2 linhas com ajuste de y por benchmark",
           "Mostra cada trajetória e a referência R = 1 em painéis independentes.",
           "IS e FT usam tetos verticais próprios, indicados por seus eixos e pelo aviso na figura.",
           "O espaço entre rótulos é menor. Use as marcações numéricas para comparar amplitudes.",
           "Distingue regressão entre configurações de lentidão acima de R = 1."),
    Figura("B04", "B04_tempo_normalizado_sobreposto_escala_log", (1, 1), (15.6, 9.1),
           (Painel("relativo", TODOS, escala_y="log"),), "8 curvas sobrepostas com eixo y logarítmico",
           "Abre espaço para tempos relativos pequenos e para valores maiores que 1.",
           "A leitura de diferenças abaixo e acima da referência depende da escala logarítmica.",
           "A união em p = 1 é inevitável. Traços e marcadores ajudam a seguir as curvas após esse ponto.",
           "Evidencia a redução de EP e as perdas relativas de IS e FT no mesmo eixo."),
    Figura("C01", "C01_speedup_8curvas_sobrepostas_com_ideal", (1, 1), (15.6, 8.9),
           (Painel("speedup", TODOS),), "8 curvas sobrepostas com legenda externa superior",
           "Reúne os oito benchmarks e dá espaço à referência S = p.",
           "EP e a referência ideal dominam a amplitude vertical.",
           "Os outros sete benchmarks se concentram na parte inferior. A legenda externa libera o painel.",
           "Mostra quão próximo EP chega do ideal até 32 processos.", legenda="superior"),
    Figura("C02", "C02_speedup_2paineis_por_comportamento", (2, 1), (15.6, 8.4),
           por_grupo("speedup"), "2 painéis lado a lado por comportamento",
           "Compara os grupos com os mesmos limites lineares e referência ideal em ambos.",
           "Boa parte do painel de IS, CG, FT e BT fica acima de todas as observações.",
           "As curvas baixas continuam próximas em y. As marcas 8 e 9 ficam próximas em x.",
           "Contrasta ganhos sustentados com máximos intermediários e recuperação de BT."),
    Figura("C03", "C03_speedup_8paineis_4x2", (4, 2), (15.6, 8.7),
           individuais("speedup"), "4 colunas × 2 linhas com eixo y comum",
           "Mostra oito comparações com o ideal sem sobreposição de benchmarks.",
           "A escala comum reserva a maior parte da altura para o ideal e para EP.",
           "Pequenas diferenças de S são difíceis de separar perto da base. A grade privilegia a visão geral.",
           "Permite examinar a distância para S = p a partir da mesma escala vertical."),
    Figura("C04", "C04_speedup_8paineis_2x4", (2, 4), (15.6, 17.2),
           individuais("speedup"), "2 colunas × 4 linhas com eixo y comum",
           "Aumenta o espaço entre as configurações e mantém o mesmo referencial entre painéis.",
           "Ocupa cerca de 70% da altura útil. Valores de S pequenos ainda ocupam uma faixa curta em y.",
           "A largura extra melhora a identificação de p e do trecho superlinear próximo da origem.",
           "Facilita a leitura das tendências em cada série usando a mesma escala de speedup."),
    Figura("C05a", "C05a_speedup_EP_IS_CG_MG_2x2", (2, 2), (15.6, 10.2),
           individuais("speedup", CONVENCIONAL_1), "2 colunas × 2 linhas com EP, IS, CG e MG",
           "Mantém a comparação com o ideal em painéis mais altos e largos que em C03.",
           "C05b contém a outra metade das séries na mesma escala vertical.",
           "Os excessos de CG acima de S = p em p pequeno ocupam uma fração curta da altura.",
           "Mostra escalabilidade de EP, máximo intermediário de IS e CG e crescimento de MG."),
    Figura("C05b", "C05b_speedup_FT_LU_BT_SP_2x2", (2, 2), (15.6, 10.2),
           individuais("speedup", CONVENCIONAL_2), "2 colunas × 2 linhas com FT, LU, BT e SP",
           "Facilita ler os processos de BT e SP e a extensão de seu ideal até 25.",
           "A escala vertical se mantém igual à de C05a. As observações usam a parte baixa dos painéis.",
           "Trechos quase planos têm diferenças pequenas na escala comum.",
           "Permite confrontar os ganhos sustentados de LU e SP com a queda de FT e a recuperação de BT."),
    Figura("C06", "C06_speedup_EP_separado_dos_demais", (2, 1), (15.6, 8.8),
           (Painel("speedup", ("EP",), "EP"), Painel("speedup", TODOS[1:], "Demais benchmarks", "log")),
           "EP em escala y linear à esquerda e 7 curvas em escala y logarítmica à direita",
           "Evidencia valores baixos sem cortar a referência S = p em nenhum painel.",
           "A geometria muda com a escala y, indicada em cada eixo. Inclinações entre painéis não são diretamente comparáveis.",
           "Sete curvas compartilham o painel direito e se cruzam perto da unidade e dos máximos.",
           "Mostra a ordem de grandeza que separa EP dos demais nos maiores processos."),
    Figura("D01", "D01_eficiencia_8curvas_sobrepostas", (1, 1), (15.6, 8.9),
           (Painel("eficiencia", TODOS),), "8 curvas sobrepostas com referência em 100%",
           "Compara perdas e valores superlineares em pontos percentuais.",
           "Eficiências de poucos pontos percentuais se concentram abaixo da primeira linha de grade acima de zero.",
           "Os oito marcadores coincidem a 100% em p = 1 e algumas curvas se aproximam em p alto.",
           "Mostra a permanência de EP perto de 100% e o pico superlinear de CG em 2 processos."),
    Figura("D02", "D02_eficiencia_2paineis_por_comportamento", (2, 1), (15.6, 8.4),
           por_grupo("eficiencia"), "2 painéis lado a lado por comportamento",
           "Reduz a sobreposição e preserva o mesmo eixo y linear nos dois grupos.",
           "Os pontos de IS e FT com poucos pontos percentuais continuam na faixa inferior.",
           "Os rótulos 8 e 9 ficam próximos. A linha de 100% mantém a mesma altura nos dois grupos.",
           "Confronta as perdas rápidas em IS e FT com os declínios mais graduais ou a estabilidade de EP."),
    Figura("D03", "D03_eficiencia_8paineis_4x2", (4, 2), (15.6, 8.8),
           individuais("eficiencia"), "4 colunas × 2 linhas com eixo y comum",
           "Mostra a queda de eficiência de cada benchmark sem sobreposição de séries.",
           "A representação compacta limita a separação de valores baixos em um mesmo painel.",
           "Cabe distinguir a tendência geral. Diferenças pequenas nas faixas próximas de 0% e 100% são sutis.",
           "Identifica os painéis com pontos acima de 100% e em que p a perda se intensifica."),
    Figura("D04", "D04_eficiencia_8paineis_2x4", (2, 4), (15.6, 17.4),
           individuais("eficiencia"), "2 colunas × 4 linhas com eixo y comum",
           "Abre espaço para os processos e a referência em cada benchmark.",
           "Usa cerca de 70% da altura útil. O eixo linear ainda comprime diferenças de poucos pontos percentuais.",
           "O espaço horizontal melhora a leitura da sequência de pontos perto do piso do painel.",
           "Permite ler quedas de eficiência com uma escala percentual comparável entre benchmarks."),
    Figura("D05a", "D05a_eficiencia_EP_IS_CG_MG_2x2", (2, 2), (15.6, 10.7),
           individuais("eficiencia", CONVENCIONAL_1, "log"), "2 colunas × 2 linhas em escala y logarítmica",
           "Dá espaço à variação de IS abaixo de 5% e preserva os valores superlineares de CG.",
           "O eixo logarítmico amplia diferenças relativas na base e comprime a região próxima de 100%.",
           "O desvio de EP em relação a 100% fica sutil. As marcas da escala representam porcentagens.",
           "Mostra eficiências de ordens de grandeza diferentes na mesma figura."),
    Figura("D05b", "D05b_eficiencia_FT_LU_BT_SP_2x2", (2, 2), (15.6, 10.7),
           individuais("eficiencia", CONVENCIONAL_2, "log"), "2 colunas × 2 linhas em escala y logarítmica",
           "Distingue os pontos de baixa eficiência de FT e usa a mesma escala de D05a.",
           "O excedente de LU acima de 100% ocupa uma distância curta em y.",
           "Use a escala numérica ao comparar a região alta e a cauda de FT em 16 e 32 processos.",
           "Evidencia a queda de FT e o declínio de BT e SP em suas configurações quadradas."),
    Figura("E01", "E01_speedup_eficiencia_combinados_1x2", (2, 1), (15.6, 8.7),
           (Painel("speedup", TODOS), Painel("eficiencia", TODOS)),
           "2 painéis lado a lado com 8 curvas por métrica",
           "Uma faixa curta da página reúne speedup e eficiência com legenda compartilhada.",
           "As curvas de speedup baixas e as eficiências de poucos pontos percentuais ocupam faixas estreitas.",
           "Oito curvas dividem painéis estreitos. Os cruzamentos precisam de atenção em impressão.",
           "Mostra como ganho de tempo e aproveitamento paralelo variam para o mesmo p."),
    Figura("E02", "E02_speedup_eficiencia_combinados_2x1", (1, 2), (15.6, 14.2),
           (Painel("speedup", TODOS), Painel("eficiencia", TODOS)),
           "2 painéis empilhados com processos alinhados",
           "A largura integral e o alinhamento horizontal ajudam a relacionar as duas métricas.",
           "Tem mais altura que E01 e mantém oito curvas por painel.",
           "A largura ajuda a separar os processos. Nos extremos baixos ainda há curvas próximas.",
           "Relaciona o crescimento de S e o declínio de E em benchmarks como MG e LU.", eixo_x_comum=True),
    Figura("E03", "E03_speedup_eficiencia_4paineis_2x2", (2, 2), (15.6, 13.4),
           (*por_grupo("speedup"), Painel("eficiencia", GRUPO_1), Painel("eficiencia", GRUPO_2)),
           "2 colunas de grupos × 2 linhas de métricas",
           "Mesma ordem de grupos por coluna e escala y comum dentro de cada métrica.",
           "Cada painel mantém a faixa até a referência ideal. Os speedups do segundo grupo ficam baixos.",
           "Os processos se alinham por coluna. Quatro curvas por painel reduzem as colisões.",
           "Permite relacionar regressões de S a quedas de E no mesmo grupo e processo.", eixo_x_comum=True),
    Figura("E04a", "E04a_speedup_eficiencia_grupo_EP_MG_LU_SP", (1, 2), (12.0, 13.2),
           (Painel("speedup", GRUPO_1), Painel("eficiencia", GRUPO_1)),
           "2 painéis empilhados com EP, MG, LU e SP",
           "Mostra só quatro trajetórias por métrica e alinha os mesmos processos.",
           "O segundo grupo requer E04b. A largura é intermediária entre 7,8 e 15,6 cm.",
           "A linha ideal e EP passam perto uma da outra no speedup, sobretudo nos primeiros processos.",
           "Mostra que ganhar speedup até o maior p pode coincidir com perda de eficiência.", eixo_x_comum=True),
    Figura("E04b", "E04b_speedup_eficiencia_grupo_IS_CG_FT_BT", (1, 2), (12.0, 13.2),
           (Painel("speedup", GRUPO_2), Painel("eficiencia", GRUPO_2)),
           "2 painéis empilhados com IS, CG, FT e BT",
           "A composição mantém as escalas lineares de E04a e dá a cada curva mais espaço horizontal.",
           "A linha ideal impõe um intervalo amplo ao speedup. O outro grupo requer E04a.",
           "O speedup do grupo fica no quinto inferior. E de IS e FT aproxima-se da base em p alto.",
           "Conecta máximos intermediários, o pico de CG e a recuperação de BT aos custos em eficiência.", eixo_x_comum=True),
    Figura("E05", "E05_speedup_eficiencia_paineis_log_largura_reduzida", (1, 2), (7.8, 15.4),
           (Painel("speedup", TODOS, escala_y="log"), Painel("eficiencia", TODOS, escala_y="log")),
           "2 painéis empilhados com eixos y logarítmicos em largura reduzida",
           "A escala logarítmica dá espaço aos speedups abaixo de 1 e às eficiências de IS e FT abaixo de 5%.",
           "A meia largura prioriza a leitura vertical. A distância em y exprime razões e a faixa superlinear fica compacta.",
           "Os rótulos 8 e 9 ficam vizinhos e algumas séries se sobrepõem em p baixo. A legenda ocupa várias linhas.",
           "Reúne as duas métricas em meia largura e permite comparar ordens de grandeza na cauda.", eixo_x_comum=True),
)

TABELAS = (
    Tabela("T01", "T01_sintese_desempenho_completa", 15.6,
           ("benchmark", "p", "tempo", "ic", "speedup", "eficiencia", "eficiencia_max_p"),
           "7 colunas × 8 benchmarks",
           "Inclui a precisão do tempo médio mínimo e a eficiência nas duas configurações de interesse.",
           "O IC refere-se ao tempo mínimo observado. As colunas de eficiência recebem cabeçalhos em duas linhas.",
           "Cabe na largura útil com booktabs e fonte de 10 pt no modelo auxiliar, sem redimensionamento.",
           "Explicita a diferença entre a melhor configuração observada e o uso da maior quantidade de processos."),
    Tabela("T02", "T02_sintese_desempenho_compacta", 11.5,
           ("benchmark", "p", "tempo", "speedup", "eficiencia_max_p"),
           "5 colunas × 8 benchmarks",
           "Deixa os cinco indicadores principais em 11,5 cm de largura.",
           "O IC do tempo e a eficiência no melhor p ficam disponíveis em T01.",
           "Os valores alinhados à direita e os cabeçalhos curtos permitem usar a tipografia natural.",
           "Resume onde cada mínimo ocorre e quanta eficiência permanece no maior p avaliado."),
)
