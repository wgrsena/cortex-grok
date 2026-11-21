"""Leitura do "cofre" (contemplações, append-only) e agregação por assembleia. SÓ o job semanal e o backtest usam
isto; o solver em runtime NÃO consulta o cofre (ponto 9 do Wagner).
Colunas (TODO Wagner: confirmar o esquema real do cofre): grupo, data_assembleia, tipo (livre|fixo|sorteio),
lance_pct (fração da categoria; só p/ livre), n_ofertantes_fixo (opcional, nas linhas fixo).
Ativos: grupo, ativo_de, ativo_ate (datas opcionais, vazio = aberto)."""
import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from statistics import median

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def ler_xlsx(path):
    """Leitor mínimo de .xlsx (1ª aba) só com stdlib: openpyxl não é permitido neste projeto."""
    with zipfile.ZipFile(path) as z:
        ss = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        aba = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
        linhas = []
        for row in ET.fromstring(z.read(aba)).iter("{%s}row" % NS["m"]):
            vals = {}
            for c in row.findall("m:c", NS):
                v = c.find("m:v", NS)
                if c.get("t") == "inlineStr":
                    txt = "".join(t.text or "" for t in c.iter("{%s}t" % NS["m"]))
                elif v is None:
                    continue
                else:
                    txt = ss[int(v.text)] if c.get("t") == "s" else v.text
                vals[_col(c.get("r"))] = txt
            if vals:
                linhas.append([vals.get(i, "") for i in range(max(vals) + 1)])
    cab = [h.strip() for h in linhas[0]]
    return [dict(zip(cab, l + [""] * (len(cab) - len(l)))) for l in linhas[1:]]


def ler_tabela(path):
    if str(path).lower().endswith(".xlsx"):
        return ler_xlsx(path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_data(v):
    v = str(v).strip()
    if re.fullmatch(r"\d{5}(\.\d+)?", v):                       # serial do Excel
        return date(1899, 12, 30) + timedelta(days=int(float(v)))
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"data inválida: {v!r}")


def parse_frac(v):
    """'15%' -> 0,15; '0,15'/'0.15' -> 0,15; '15' -> 0,15 (valores > 1 são lidos como percentual)."""
    v = str(v).strip().replace(",", ".")
    pct = v.endswith("%")
    x = Decimal(v.rstrip("%"))
    return x / 100 if (pct or x > 1) else x


def ler_ativos(path):
    """{grupo: (ativo_de | None, ativo_ate | None)}."""
    out = {}
    for r in ler_tabela(path):
        g = str(r["grupo"]).strip().zfill(6)
        de, ate = (r.get("ativo_de") or "").strip(), (r.get("ativo_ate") or "").strip()
        out[g] = (parse_data(de) if de else None, parse_data(ate) if ate else None)
    return out


def ativo_em(ativos, grupo, data):
    if ativos is None:
        return True
    if grupo not in ativos:
        return False
    de, ate = ativos[grupo]
    return (de is None or de <= data) and (ate is None or data <= ate)


JANELA = 6   # janela das estatísticas do grupo (stats_grupo/c_recente): últimas 6 assembleias


def assembleias(rows, ativos=None, janela_livres=JANELA):
    """{grupo: [assembleia ...]} em ordem cronológica. Assembleia = (grupo, data): menor lance livre contemplado
    (None se não houve livre), nº de contemplados por fixo e nº de ofertantes do fixo (se informado).
    Só entram linhas de grupos ATIVOS na data da assembleia (backtest rolante, ponto 9).
    Revisão N12: `menor_livre` sai de um mínimo corrente (sem lista); a lista `livres` (usada só na mediana de
    stats_grupo) fica apenas nas `janela_livres` assembleias mais recentes de cada grupo; nas antigas `livres` = ().
    `janela_livres=None` guarda todas (comportamento antigo)."""
    rows = rows if isinstance(rows, list) else list(rows)
    chaves = []                                            # 1ª passada: (grupo, data) de cada linha ativa
    datas = defaultdict(set)
    for r in rows:
        g, d = str(r["grupo"]).strip().zfill(6), parse_data(r["data_assembleia"])
        if ativo_em(ativos, g, d):
            chaves.append((g, d))
            datas[g].add(d)
        else:
            chaves.append(None)
    manter = None if janela_livres is None else {g: set(sorted(ds)[-janela_livres:]) for g, ds in datas.items()}
    ag = defaultdict(dict)
    for r, k in zip(rows, chaves):                         # 2ª passada: agrega
        if k is None:
            continue
        g, d = k
        a = ag[g].get(d)
        if a is None:
            a = ag[g][d] = {"data": d, "menor_livre": None, "livres": [] if manter is None or d in manter[g] else None,
                            "n_fixo": 0, "ofertantes": None}
        tipo = str(r["tipo"]).strip().lower()
        if tipo == "livre":
            x = parse_frac(r["lance_pct"])
            if a["menor_livre"] is None or x < a["menor_livre"]:
                a["menor_livre"] = x
            if a["livres"] is not None:
                a["livres"].append(x)
        elif tipo == "fixo":
            a["n_fixo"] += 1
            if (r.get("n_ofertantes_fixo") or "").strip():
                a["ofertantes"] = Decimal(str(r["n_ofertantes_fixo"]).replace(",", "."))
    out = {}
    for g, ds in ag.items():
        out[g] = []
        for d in sorted(ds):
            a = ds[d]
            a["livres"] = () if a["livres"] is None else a["livres"]
            out[g].append(a)
    return out


def c_recente(asm, fim):
    """c1..c6 (c1 = mais recente) com as assembleias asm[:fim]."""
    ult = asm[max(0, fim - 6):fim][::-1]
    return tuple(a["menor_livre"] for a in ult) + (None,) * (6 - len(ult))


def stats_grupo(asm):
    """Estatísticas do grupo na janela das últimas 6 assembleias (1 assembleia ~ 1 mês: TODO Wagner).
    mediana_lance_livre = mediana de todos os lances livres contemplados na janela (fração da categoria)."""
    janela = asm[-JANELA:]
    if not janela:
        return {"c": (None,) * 6, "qtd_fixo_contemplado_mes": None, "n_ofertantes_fixo_medio": None,
                "mediana_lance_livre": None}
    of = [a["ofertantes"] for a in janela if a["ofertantes"] is not None]
    livres = [x for a in janela for x in a["livres"]]          # TODOS os lances livres contemplados na janela
    return {"c": c_recente(asm, len(asm)),
            # só dado comercial (item 6 da v1.1): NÃO entra em probabilidade nem em ranking
            "mediana_lance_livre": median(livres).quantize(Decimal("0.0001")) if livres else None,
            "qtd_fixo_contemplado_mes": (Decimal(sum(a["n_fixo"] for a in janela)) / len(janela)).quantize(Decimal("0.01")),
            "n_ofertantes_fixo_medio": (sum(of) / len(of)).quantize(Decimal("0.01")) if of else None}
