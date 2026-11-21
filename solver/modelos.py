"""Modelos de dados do resolvedor Disal v1.1 (ESPECIFICACAO_V1_1.md, seções 0, 1, 9, 10).

Dinheiro sempre em Decimal (centavos); probabilidades em Fraction (exatas).
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from fractions import Fraction
from typing import Optional

VERSAO_REGRAS = "v1.1"
MAX_Q = 15  # piso de quantidade por cota física: nunca usar mais (seção 1)
CENT = Decimal("0.01")
MODOS_PROB = ("fracao_h_sobre_N", "sequencia_W_sobre_6")
MAX_DIAS_COLETA = 8  # v1.1 item 7 (decisão do Wagner): dado com mais de 8 dias sai `desatualizada`. Fonte única (N7).


def D(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def cent(x: Decimal) -> Decimal:
    return D(x).quantize(CENT, rounding=ROUND_HALF_UP)


def cent_baixo(x: Decimal) -> Decimal:
    """Arredonda para baixo (usado em tetos: nunca exceder o teto)."""
    return D(x).quantize(CENT, rounding=ROUND_DOWN)


@dataclass(frozen=True)
class Parametros:
    """Premissas A1..A7 e demais parâmetros. Mudar não exige refazer o modelo."""
    # A1 — decidido pelo Wagner: padrão p = w/6 (sequência seguida / 6). Nunca comunicar como número frio ao cliente.
    # Alternativa "fracao_h_sobre_N": p = h/N (fração das assembleias cobertas), mantida só pra comparação no backtest.
    modo_probabilidade: str = "sequencia_W_sobre_6"
    # A2: cobertura mínima e tolerância de probabilidade no ranking
    w_min: int = 1
    tol_prob: Decimal = Decimal("0")
    # A3: lance fixo pode ser financiado por embutido
    a3_fixo_financiavel_por_embutido: bool = True
    # A4: probabilidade conjunta = produto; cartas do mesmo grupo geram aviso
    a4_avisar_mesmo_grupo: bool = True
    # A5 — decidido pelo Wagner: SEM teto de sobra de crédito (None). O solver devolve tudo que é viável e a sobra
    # aparece explícita no `gap` da saída. Um Decimal opcional (ex.: 0.10) reativa o teto A*(1+delta) como parâmetro.
    delta_credito: Optional[Decimal] = None
    # A6: histórico em % da categoria, sem sorteio e sem lance fixo (semântica dos dados; sem chave)
    # A7: categoria e % de embutido iguais nos planos 100%/75% (validação gera alerta)
    a7_validar_categoria_entre_planos: bool = True
    # demais
    K_top: int = 20
    w_ref: Optional[int] = None          # padrão = w_min
    max_combos: int = 100                 # tamanho de página da Função 1 (valor padrão: ver NOTAS_DUVIDAS)
    max_cartas_enum: int = 6              # limite de performance da Função 1, não regra de negócio
    incluir_sem_historico: bool = False
    tol_taxa_rs: Decimal = Decimal("0.50")  # S3: taxa <= taxa* + 0,5 (unidade: ver NOTAS_DUVIDAS)
    n_reservas: int = 2
    # MILP (seção 5): gap relativo por solve (0,5%) e tempo limite por solve em segundos
    milp_gap_relativo: float = 0.005
    milp_tempo_limite_s: float = 10.0
    # D1/D2 (NOTAS_DUVIDAS, decisão provisória aguardando Wagner). D2: False = leitura literal da 6.3 (Σe >= G apenas; viola a faixa superior -> descartado_discreto).
    # True = Σe >= max(G, ΣC − A(1+δ)), coerente com a restrição 4.5 do MILP.
    refino_respeita_teto_credito: bool = False
    # Orientação do Wagner (ponto 4): W (sequência seguida) desempata após a probabilidade, antes da taxa.
    w_desempate: bool = True
    # Orientação do Wagner (ponto 2): 75% é sempre testado primeiro; o 100% entra depois como alternativa rotulada.
    incluir_alternativa_100: bool = True
    # Orientação do Wagner (ponto 1): ramo lance fixo (recurso_proprio == 0). Pesos ajustáveis do ranking multi-critério.
    peso_credito: Decimal = Decimal("0.30")
    peso_taxa: Decimal = Decimal("0.15")
    peso_fixo: Decimal = Decimal("0.40")
    peso_parcela: Decimal = Decimal("0.15")
    top_fixo: int = 10
    fixo_exigir_embutido_cobrir: bool = False   # True: só grupos em que o embutido sozinho paga o lance fixo (25%)
    # v1.1 (itens 7-9): data de referência e feriados entram como parâmetro; o solver nunca lê o relógio.
    hoje: Optional[str] = None                  # ISO (AAAA-MM-DD); sem ele os campos de validade/prazo saem None
    feriados: tuple = ()                        # datas ISO tratadas como dia não útil no prazo de entrada
    max_dias_coleta: int = MAX_DIAS_COLETA      # dado com mais de N dias sai marcado `desatualizada`

    def __post_init__(self):
        if self.w_min < 1:
            raise ValueError("w_min >= 1 (nível w=0 não é definido na spec)")
        if self.modo_probabilidade not in MODOS_PROB:
            raise ValueError(f"modo_probabilidade inválido (use {MODOS_PROB})")

    def teto_credito(self, A):
        """Limite superior do crédito líquido: infinito quando não há teto de sobra (padrão)."""
        return Decimal("Infinity") if self.delta_credito is None else A * (1 + self.delta_credito)

    @property
    def w_ref_efetivo(self) -> int:
        return self.w_ref if self.w_ref is not None else self.w_min


@dataclass(frozen=True)
class Cota:
    """Uma linha de fato_cota (seção 9). cota_id identifica a cota física π;
    as variantes de plano (100/75) da mesma cota compartilham cota_id e quantidade."""
    cota_id: str
    grupo: str
    serie: str
    tipo_bem: str
    plano_pct: int
    credito: Decimal
    taxa_pct: Decimal            # fração (0,16 = 16%)
    parcela: Decimal
    pct_embutido_max: Decimal    # flag de catálogo, FRAÇÃO da categoria: 0, 0,10 ou 0,25 (I2: fração em todo o código e banco)
    tem_lance_fixo: bool = False
    lance_fixo_pct: Decimal = Decimal("0.25")
    n_ofertantes_fixo_medio: Optional[Decimal] = None
    qtd_min: int = 1
    qtd_truncada: bool = False
    status: str = "disponivel"   # disponivel | saiu_da_venda
    c: tuple = (None,) * 6       # c1 (mais recente) .. c6, fração da categoria; None = sem lance livre
    lance_ref_irmaos: Optional[Decimal] = None  # só informativo (SEM_HISTORICO)
    qtd_fixo_contemplado_mes: Optional[Decimal] = None   # média/mês de contemplados por lance fixo no grupo (job semanal)
    categoria_veiculo: str = "carro"                      # carro | moto | caminhao (nunca misturar numa unificação)
    prazo_total: Optional[int] = None                     # prazos diferentes são liberados na unificação
    # v1.1 — só dado comercial/validade; nenhum entra em probabilidade nem em ranking (exceto a validade, que só marca)
    mediana_lance_livre: Optional[Decimal] = None         # fração da categoria; calculada pelo job a partir do cofre
    data_coleta: Optional[str] = None                     # ISO; quando o dado do grupo foi coletado (gravada pelo job)
    proxima_assembleia: Optional[object] = None           # ISO ou lista/tupla de ISO (N4); opcional, por cota/grupo
    # I1 (resolvido, 01/11/2026): status, categoria_veiculo, qtd_min, qtd_truncada, lance_fixo_pct,
    # n_ofertantes_fixo_medio, lance_ref_irmaos e prazo_total são colunas tipadas da fato_cotas (0005), populadas do
    # `extra` pela regra de `fato_colunas.colunas_de_extra`; contrato.snapshot_de_dict lê coluna e cai no extra se faltar.
    # I2 (resolvido na revisão): pct_embutido_max e mediana_lance_livre são FRAÇÃO da categoria (0..1) aqui, na 0002
    # e na 0001 depois da 0003; `embutido_cobre_mediana` usa `<=`. Conversão para % só na apresentação.

    @property
    def categoria(self) -> Decimal:
        return cent(self.credito * (1 + self.taxa_pct))


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    atualizado_em: str
    cotas: tuple


@dataclass(frozen=True)
class Pedido:
    tipo_bem: str
    credito_liquido_alvo: Decimal
    parcela_max: Decimal
    recurso_proprio: Decimal
    categoria_veiculo: Optional[str] = None   # None: resolve cada categoria separadamente (nunca mistura)


@dataclass(frozen=True)
class Nivel:
    tipo: str                      # "livre" | "fixo" | "referencia"
    w: Optional[int]               # cobertura (livre)
    lance_pct: Decimal             # fração da categoria
    p: Optional[Fraction]          # None = sem probabilidade (SEM_HISTORICO / referência)
    h: int = 0
    N: int = 0


@dataclass(frozen=True)
class Tipo:
    """Tipo agregado: cotas idênticas (grupo, plano, crédito, taxa, parcela)."""
    idx: int
    grupo: str
    serie: str
    plano_pct: int
    credito: Decimal
    taxa_pct: Decimal
    categoria: Decimal
    parcela: Decimal
    taxa_rs: Decimal               # C * t
    teto_emb: Decimal              # ē (flag), fração da categoria
    fontes: tuple                  # cota_ids físicos que podem fornecer unidades
    niveis: tuple
    hist_flag: str                 # OK | PARCIAL | SEM_HISTORICO
    N: int
    W: int
    qtd_truncada: bool
    categoria_veiculo: str = "carro"
    prazo_total: Optional[int] = None
    mediana_lance_livre: Optional[Decimal] = None
    data_coleta: Optional[str] = None
    proxima_assembleia: Optional[str] = None


@dataclass(frozen=True)
class Universo:
    tipos: tuple
    caps: dict                     # cota_id -> q_π (<= 15)
    alertas: tuple
    excluidos: dict                # motivo -> contagem
