#!/usr/bin/env python3
"""Gerador estático da rota /oportunidades (stdlib pura, sem dependência nova).

Fluxo: coleta real (CSV do Drive) -> entrada.py -> Arquimedes (vendor/, sem alteração) -> checagem de estoque
compartilhado -> HTML estático (CSS embutido, pronto para colar na subconta oficial HighLevel) + sitemap.

Regras de dado (docs/arquitetura-rota-oportunidades.md):
- número público só com fonte e data (atributo data-fonte apontando para um item da lista de fontes);
- campo sem fonte viva = lacuna marcada ("dado não disponível"), nunca estimativa;
- faixa sem combinação = "o motor não achou nada hoje";
- coleta com mais de `max_dias_coleta` dias = nenhum card;
- comparação com financiamento só com a taxa do Banco Central (SGS 20749) buscada por tools/oportunidades/bcb.py;
- a mediana de lance e o embutido entram só no ranking e ficam em dados/oportunidades/saida/ (fora da pasta servida).

Uso: python3 tools/oportunidades/gerar.py [--hoje AAAA-MM-DD]
"""
import argparse
import html
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from arquimedes.grid import gerar as arquimedes_gerar  # noqa: E402
from arquimedes.modelos import ParametrosGrid  # noqa: E402
import entrada  # noqa: E402

BAHIA = timezone(timedelta(hours=-3))
CFG = json.loads((ROOT / "config" / "oportunidades.json").read_text(encoding="utf-8"))
SITE = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
OUT = ROOT / "oportunidades"
IMG = OUT / "assets" / "img"
BASE = CFG["canonical_base"].rstrip("/")
GAP = "dado não disponível"
ILUSTRATIVA = "imagem ilustrativa gerada por IA; não é o bem da carta"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
e = html.escape


# ---------- formatação ----------
def brl(v) -> str:
    s = f"{Decimal(v):,.2f}"
    return "R$ " + s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(v, casas=2) -> str:
    return f"{Decimal(v):.{casas}f}".replace(".", ",") + "%"


def dbr(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def mil(faixa: int) -> str:
    return f"{faixa // 1000} mil"


# ---------- links ----------
def utm(url: str, conteudo: str = "") -> str:
    q = {"utm_source": CFG["utm_source"], "utm_medium": CFG["utm_medium"],
         "utm_campaign": SITE["etiqueta_origem"], "utm_content": CFG["utm_content"] + (f"-{conteudo}" if conteudo else ""),
         "ref": SITE["codigo_fluxo"]}
    return url + ("&" if "?" in url else "?") + urlencode(q)


def url_pagina(faixa=None) -> str:
    return f"{BASE}{CFG['rota']}" + (f"{faixa // 1000}/" if faixa else "")


def wa(texto: str, conteudo: str) -> str:
    return utm(f"https://wa.me/{SITE['whatsapp_oficial']}?text={quote(texto)}", conteudo)


# ---------- dados ----------
def carregar_bcb():
    p = ROOT / CFG["bcb_arquivo"]
    if not p.exists():
        return None, "arquivo da taxa do Banco Central não existe (rode tools/oportunidades/bcb.py)"
    d = json.loads(p.read_text(encoding="utf-8"))
    buscado = datetime.fromisoformat(d["buscado_em"]).date()
    return d, buscado


def pmt(credito: Decimal, aa: float, n: int) -> Decimal:
    i = (1 + aa / 100) ** (1 / 12) - 1
    return Decimal(str(round(float(credito) * i / (1 - (1 + i) ** -n), 2)))


def checar_estoque(op, itens) -> list:
    """Arquimedes trata cada valor de carta como estoque próprio; no portal o estoque é do grupo/plano/prazo."""
    uso = Counter()
    for c in op.cartas:
        uso[c.grupo] += c.qtd
    pools = {it.rotulo: it.cotas for it in itens.values()}
    return [f"{rot}: usa {q}, portal lista {pools[rot]}" for rot, q in uso.items() if q > pools[rot]]


def rodar(hoje: date):
    coleta = date.fromisoformat(json.loads((ROOT / CFG["coleta_dir"] / "fontes.json").read_text(encoding="utf-8"))["data_coleta"])
    idade = (hoje - coleta).days
    res = {"hoje": hoje.isoformat(), "data_coleta": coleta.isoformat(), "idade_coleta_dias": idade,
           "fresca": idade <= CFG["max_dias_coleta"], "faixas": {}, "log": {}, "estoque_descartadas": []}
    if not res["fresca"]:
        for f in CFG["faixas"]:
            res["faixas"][f] = {"ops": [], "combinacoes": 0}
        return res, {}
    grupos, itens, log = entrada.carregar(ROOT / CFG["coleta_dir"], hoje)
    res["log"] = {k: {"linhas": len(v), "exemplos": v[:10]} for k, v in log.items()}
    res["grupos_entrada"] = len(grupos)
    p = ParametrosGrid(faixas=tuple(Decimal(f) for f in CFG["faixas"]), top_k=CFG["top_k"])
    ops, est = arquimedes_gerar(grupos, p, instrumentar=True)
    res["arquimedes"] = {"avaliadas": est.avaliadas, "nos": est.nos, "podas": getattr(est, "podas", None),
                         "truncadas": est.truncadas, "parametros": {"top_k": p.top_k, "tolerancia_pct": str(p.tolerancia_pct)}}
    n_por = Counter(a // 100 for a, _t, _c, _n in est.creditos_avaliados)
    por_item = {(it.rotulo, entrada.cent(it.credito)): it for it in itens.values()}
    for f in CFG["faixas"]:
        lst = []
        for o in [o for o in ops if int(o.faixa_alvo) == f]:
            prob = checar_estoque(o, itens)
            if prob:
                res["estoque_descartadas"].append({"faixa": f, "chave": o.chave_cartas, "motivo": prob})
                continue
            lst.append(o)
        res["faixas"][f] = {"ops": lst, "combinacoes": n_por.get(f, 0)}
    return res, por_item


# ---------- HTML ----------
CSS = """
:root{--ink:#0a2540;--muted:#5b6b7f;--line:#e3e8ee;--soft:#f6f9fc;--accent:#0b6e4f;--r:12px;--max:1080px}
*,*::before,*::after{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);line-height:1.6;font-size:1.0625rem}
img{display:block;max-width:100%;height:auto}a{color:var(--accent);text-underline-offset:3px}
.wrap{max-width:var(--max);margin:0 auto;padding:0 20px}.skip{position:absolute;left:-9999px}.skip:focus{left:16px;top:16px;background:#fff;padding:8px}
.brand{padding:20px 0;font-weight:700}.brand a{color:var(--ink);text-decoration:none}
.meta{font-size:.875rem;color:var(--muted)}h1{font-size:clamp(1.9rem,5vw,3rem);line-height:1.1;letter-spacing:-.03em;margin:.2em 0}
.lede{font-size:1.2rem;color:var(--muted);max-width:60ch}.author{display:flex;gap:12px;align-items:center;margin:12px 0}.author img{border-radius:50%}
.cover{margin:24px 0}.cover img{border-radius:var(--r);background:var(--soft)}.cover figcaption{font-size:.8125rem;color:var(--muted);margin-top:6px}
.faixas{display:flex;flex-wrap:wrap;gap:8px;padding:0;list-style:none}.faixas a{display:inline-block;padding:6px 12px;border:1px solid var(--line);border-radius:999px;text-decoration:none}
.faixas a[aria-current]{border-color:var(--ink);color:var(--ink);font-weight:600}
.prose{max-width:760px}.prose h2{font-size:1.5rem;margin:2em 0 .5em}
.card{border:1px solid var(--line);border-radius:var(--r);padding:20px;margin:0 0 24px}.card h3{margin:0 0 4px;font-size:1.25rem}
.card .foto{display:grid;grid-template-columns:160px 1fr;gap:12px;align-items:center;margin:12px 0}.card .foto img{border-radius:8px}
.campos{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:16px 0}.campos div{background:var(--soft);border-radius:8px;padding:10px 12px}
.campos dt{font-size:.8125rem;color:var(--muted)}.campos dd{margin:0;font-weight:600}
.lacuna{color:var(--muted);font-weight:400;font-style:italic}.det{font-size:.9375rem;color:var(--muted)}
.gancho{border-top:1px solid var(--line);margin-top:12px;padding-top:12px}.gancho h4{margin:0 0 6px}
.notice{background:var(--soft);border-left:3px solid var(--accent);padding:16px 20px;border-radius:0 var(--r) var(--r) 0;font-size:.9375rem}
.sources{font-size:.9375rem;color:var(--muted);border-top:1px solid var(--line);padding-top:16px;margin-top:32px}.sources h2{font-size:1rem;color:var(--ink)}
.vazio{padding:20px;border:1px dashed var(--line);border-radius:var(--r)}
"""


def imagens_faixa(f: int) -> dict:
    """{prop: (arquivo, w, h, ilustrativa_ia)} — JPEG do Drive (IA) ou PNG placeholder gerado aqui."""
    out = {}
    for prop, w, h in (("16x9", 1200, 675), ("4x3", 1200, 900), ("1x1", 1200, 1200)):
        jpg = IMG / f"faixa-{f // 1000}-{prop}.jpg"
        out[prop] = (jpg.name, w, h, True) if jpg.exists() else (f"faixa-{f // 1000}-{prop}.png", w, h, False)
    return out


def gerar_placeholders():
    sys.path.insert(0, str(ROOT / "tools"))
    from gen_placeholders import png
    for f in CFG["faixas"]:
        for prop, (nome, w, h, ia) in imagens_faixa(f).items():
            if not ia and not (IMG / nome).exists():
                png(IMG / nome, w, h, (232, 238, 244), (90, 110, 130), "algorithmicMedia",
                    f"PLACEHOLDER faixa {mil(f)} {prop} - TODO foto real do veiculo")


def asset(nome: str) -> str:
    return f"{BASE}{CFG['rota']}assets/img/{nome}"


def fontes_html(res, bcb, conteudo) -> str:
    fx = json.loads((ROOT / CFG["coleta_dir"] / "fontes.json").read_text(encoding="utf-8"))
    col = dbr(date.fromisoformat(res["data_coleta"]))
    li = [
        f'<li id="fonte-portal">Portal Clique Vendas (Disal), menu Nova Venda: grupos, planos, valores de crédito, 1ª parcela com seguro, '
        f'taxa de administração, prazo e cotas disponíveis. Coleta de {col}; arquivo “{e(fx["arquivos"]["grupos_a_venda.csv"]["drive_nome"])}”.</li>',
        f'<li id="fonte-calendario">WebDisal, calendário de assembleias por grupo. Coleta de {col}; arquivo '
        f'“{e(fx["arquivos"]["calendario.csv"]["drive_nome"])}”.</li>',
        '<li id="fonte-motor">Motor Arquimedes (Conecta Cortex): ordena as cartas pelo histórico de lances do grupo, prazo e excesso sobre a faixa. '
        'É um ordenamento interno, não uma previsão.</li>',
    ]
    if bcb:
        d, buscado = bcb
        ref = date.fromisoformat(d["referencia"])
        li.append(f'<li id="fonte-bcb">Banco Central do Brasil, Sistema Gerenciador de Séries Temporais, série 20749: taxa média de juros '
                  f'das operações de crédito com recursos livres, pessoas físicas, aquisição de veículos: {pct(Decimal(str(d["valor_aa"])))} ao ano, '
                  f'referência {MESES[ref.month - 1]}/{ref.year}, consultada em {dbr(buscado)}. '
                  f'<a href="{e(utm(d["pagina"], conteudo))}">Página da série no Portal de Dados Abertos do BCB</a>.</li>')
    return '<aside class="sources"><h2>Fontes</h2><ol>' + "".join(li) + "</ol></aside>"


def cabecalho(titulo, desc, url, imgs, gerado, autor_ld, res):
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": titulo, "description": desc,
          "mainEntityOfPage": url, "image": [asset(imgs[p][0]) for p in ("16x9", "4x3", "1x1")],
          "datePublished": gerado, "dateModified": gerado, "author": [autor_ld],
          "publisher": {"@type": "Organization", "name": CFG["publisher"], "url": BASE + "/"}}
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)} | Conecta Cortex</title>
<meta name="description" content="{e(desc)}">
<!-- Indexável desde o dia um (decisão Wagner, t55u). Canonical na subconta oficial HighLevel, nunca no lab. -->
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:image" content="{asset(imgs['16x9'][0])}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="675">
<meta name="cc:data-coleta" content="{res['data_coleta']}">
<meta name="cc:gerado-em" content="{gerado}">
<style>{CSS}</style>
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
</head>
"""


def capa(imgs, alt, conteudo):
    a, b, c = imgs["16x9"], imgs["4x3"], imgs["1x1"]
    nota = ILUSTRATIVA if b[3] else f"imagem provisória (sem foto); foto do veículo: {GAP}"
    return f"""<figure class="cover">
<picture>
<source media="(min-width: 768px)" srcset="{asset(a[0])}" width="{a[1]}" height="{a[2]}">
<source media="(max-width: 359px)" srcset="{asset(c[0])}" width="{c[1]}" height="{c[2]}">
<img src="{asset(b[0])}" width="{b[1]}" height="{b[2]}" fetchpriority="high" decoding="async" alt="{e(alt)} ({e(nota)})">
</picture>
<figcaption data-lacuna="foto-real">{e(nota[:1].upper() + nota[1:])}.</figcaption>
</figure>"""


def autor_html(conteudo):
    a = CFG["autor"]
    ld = {"@type": "Person", "name": a["nome"], "image": BASE + a["imagem"], "jobTitle": a["cargo"]}
    h = f"""<div class="author">
<!-- TODO: autor real (pessoa identificada, foto real; nunca avatar de IA). -->
<img src="{BASE}{a['imagem']}" width="56" height="56" loading="lazy" decoding="async" alt="Foto do autor (TODO)">
<div><strong>{e(a['nome'])}</strong><span class="meta"> · {e(a['cargo'])}</span></div>
</div>"""
    return h, ld


def nav_faixas(atual, conteudo):
    li = [f'<li><a href="{e(utm(url_pagina(), conteudo))}"{" aria-current=\"page\"" if atual is None else ""}>Todas as faixas</a></li>']
    for f in CFG["faixas"]:
        cur = ' aria-current="page"' if f == atual else ""
        li.append(f'<li><a href="{e(utm(url_pagina(f), conteudo))}"{cur}>Faixa de {mil(f)}</a></li>')
    return '<nav aria-label="Faixas de crédito"><ul class="faixas">' + "".join(li) + "</ul></nav>"


NOTICE = ('<p class="notice">Consórcio não é financiamento: a carta só é liberada quando a cota é contemplada em assembleia, '
          'por sorteio ou por lance, e ninguém pode prometer quando isso acontece. As cartas abaixo são o que o motor achou na '
          'coleta citada nas fontes; podem já ter sido vendidas. Valores, regras do plano e reajuste devem ser confirmados no '
          'contrato antes de qualquer decisão.</p>')


def card(o, idx, faixa, por_item, bcb, imgs, res):
    fr = CFG["fr_padrao"]
    cid = f"F{faixa // 1000}-{idx}"
    itens = [(c, por_item[(c.grupo, c.credito)]) for c in o.cartas]
    parcela = sum((it.parcela_1a_c_seguro * c.qtd for c, it in itens), Decimal(0))
    titulo_grupo = " + ".join(f"{c.qtd}× grupo {it.grupo} (plano {it.plano_codigo})" for c, it in itens)
    bens = []
    for c, it in itens:
        nomes = ", ".join(f"“{e(x)}”" for x in sorted(set(it.bens)))
        bens.append(f"carta referenciada, sem modelo fixo; código no portal: {nomes}" if it.modo == "referenciado"
                    else f"descrição do bem no portal (texto original): {nomes}")
    det = "".join(
        f'<li data-fonte="fonte-portal">{c.qtd}× carta de {brl(it.credito)} · grupo {it.grupo} · plano {e(it.plano)} · '
        f'prazo restante {it.prazo_cota} meses · taxa de administração {pct(it.taxa_adm_pct)} · '
        f'1ª parcela com seguro {brl(it.parcela_1a_c_seguro)} · cotas listadas no portal: {it.cotas}'
        f'{" (o portal mostra no máximo 15)" if it.cotas >= 15 else ""}</li>' for c, it in itens)
    prox = o.proxima_assembleia
    assembleia = (f'<dd data-fonte="fonte-calendario">{dbr(prox)}</dd>' if prox else
                  f'<dd class="lacuna" data-lacuna="assembleia">{GAP} (grupo sem data futura no calendário coletado)</dd>')
    # gancho: financiamento equivalente só com taxa oficial do BCB
    if bcb:
        d, _ = bcb
        ref = date.fromisoformat(d["referencia"])
        fin = pmt(o.credito_total, float(d["valor_aa"]), o.prazo)
        comparacao = (
            f'<p data-campo="financiamento" data-fonte="fonte-bcb">Financiar {brl(o.credito_total)} em {o.prazo} meses à taxa média do Banco Central '
            f'para veículos ({pct(Decimal(str(d["valor_aa"])))} ao ano, {MESES[ref.month - 1]}/{ref.year}) daria uma parcela de cerca de '
            f'<strong>{brl(fin)}</strong>, com o carro na hora.</p>'
            f'<p data-campo="consorcio" data-fonte="fonte-portal">No consórcio, a 1ª parcela desta combinação é <strong>{brl(parcela)}</strong> '
            f'(com seguro), mas o carro só vem depois da contemplação, sem data prometida.</p>'
            '<p class="det">Conta simples (tabela Price, crédito total financiado, prazo igual ao restante da cota). Não inclui IOF, tarifas, '
            'seguro do financiamento nem entrada. No plano light, a parcela pode subir depois da contemplação.</p>')
    else:
        comparacao = (f'<p class="lacuna" data-campo="financiamento" data-lacuna="bcb">Comparação com financiamento: {GAP} '
                      '(a taxa oficial do Banco Central não foi carregada nesta rodada).</p>')
    texto_wa = (f"Olá! Vi no motor de oportunidades a combinação {cid} ({titulo_grupo}, crédito {brl(o.credito_total)}). "
                f"Código {fr} (FLUXO-REV). Quero entender se faz sentido pra mim.")
    thumb = imgs["4x3"]
    return f"""<section class="card" id="{cid}" data-faixa="{faixa}">
<h3>Combinação {cid} · {o.n_cartas} carta{"s" if o.n_cartas > 1 else ""}</h3>
<p class="det" data-fonte="fonte-portal">{(lambda t: t[:1].upper() + t[1:])("; ".join(dict.fromkeys(bens)))}</p>
<p class="det" data-fonte="fonte-motor">Posição {o.rank} do motor nesta faixa · {titulo_grupo}</p>
<div class="foto">
<img src="{asset(thumb[0])}" width="{thumb[1]}" height="{thumb[2]}" loading="lazy" decoding="async" alt="{e(ILUSTRATIVA if thumb[3] else 'imagem provisória sem foto')}">
<p class="lacuna" data-lacuna="foto-real">Foto real do veículo: {GAP} (a coleta do portal não traz foto). Imagem ao lado: {ILUSTRATIVA if thumb[3] else "provisória"}.</p>
</div>
<dl class="campos">
<div><dt>Crédito</dt><dd data-campo="credito" data-fonte="fonte-portal">{brl(o.credito_total)}</dd></div>
<div><dt>Entrada (recurso próprio)</dt><dd class="lacuna" data-campo="entrada" data-lacuna="entrada">{GAP}</dd></div>
<div><dt>Parcela (1ª, com seguro)</dt><dd data-campo="parcela" data-fonte="fonte-portal">{brl(parcela)}</dd></div>
<div><dt>Próxima assembleia</dt>{assembleia.replace("<dd ", '<dd data-campo="assembleia" ', 1)}</div>
<div><dt>Código</dt><dd data-campo="fr">{fr}</dd></div>
</dl>
<p class="det lacuna" data-lacuna="entrada-pos">Entrada e parcela depois da contemplação: {GAP}. Dependem do lance que o grupo aceita e da regra do plano depois da contemplação, que ainda não foram verificados com a administradora.</p>
<ul class="det">{det}</ul>
<div class="gancho">
<h4>Compraria esse carro ou não?</h4>
{comparacao}
</div>
<p><a class="cta" href="{e(wa(texto_wa, cid))}">Conversar no WhatsApp sobre a combinação {cid} ({fr} · FLUXO-REV)</a></p>
</section>"""


def pagina(faixa, res, por_item, bcb, gerado, todas_paginas):
    conteudo = f"faixa-{faixa // 1000}" if faixa else "indice"
    url = url_pagina(faixa)
    col = dbr(date.fromisoformat(res["data_coleta"]))
    hoje = dbr(date.fromisoformat(res["hoje"]))
    imgs = imagens_faixa(faixa or 100000)
    autor, autor_ld = autor_html(conteudo)
    fr = CFG["fr_padrao"]
    if faixa:
        info = res["faixas"][faixa]
        titulo = f"Cartas de consórcio de carro na faixa de {mil(faixa)}: o que o motor achou hoje"
        desc = (f"Combinações de cartas de consórcio de automóvel perto de {mil(faixa)}, com crédito, parcela e próxima assembleia "
                f"tirados da coleta do portal da administradora. Sem promessa de contemplação.")
        h1 = f"Faixa de {mil(faixa)}: o que o motor achou hoje"
        lede = ("Cartas de consórcio de automóvel à venda que somam perto desse valor, com a fonte de cada número. "
                "Ferramenta de leitura, não oferta de contemplação.")
        if not res["fresca"]:
            corpo = (f'<p class="vazio" data-fonte="fonte-portal">O motor não achou nada hoje: a coleta disponível é de {col} e passou do '
                     f'limite de atualização. Nenhuma carta é mostrada com dado velho.</p>')
        elif not info["ops"]:
            corpo = '<p class="vazio">O motor não achou nada hoje nesta faixa com os dados da coleta citada nas fontes.</p>'
        else:
            corpo = (f'<p data-fonte="fonte-motor">O motor avaliou {info["combinacoes"]} combinações de cartas dentro da tolerância desta faixa '
                     f'e mostra as {len(info["ops"])} primeiras do ordenamento.</p>'
                     + "\n".join(card(o, i, faixa, por_item, bcb, imgs, res) for i, o in enumerate(info["ops"], 1)))
        intro_h2 = "O que o motor achou"
    else:
        titulo = "Oportunidades em cartas de consórcio de carro: o que o motor achou hoje"
        desc = ("Ferramenta da Conecta Cortex que cruza grupos, planos e assembleias do portal da administradora e mostra combinações "
                "de cartas por faixa de crédito, com fonte e data de cada número.")
        h1 = "Oportunidades: o que o motor achou hoje"
        lede = ("Escolha a faixa de crédito. Cada página mostra as combinações de cartas que o motor achou na última coleta, "
                "com crédito, parcela, próxima assembleia e a fonte de cada número.")
        li = []
        for f in CFG["faixas"]:
            info = res["faixas"][f]
            n = len(info["ops"])
            txt = (f'<span data-fonte="fonte-motor">{n} combinação(ões) mostradas, de {info["combinacoes"]} avaliadas</span>' if n
                   else "o motor não achou nada hoje")
            li.append(f'<li><a href="{e(utm(url_pagina(f), conteudo))}">Faixa de {mil(f)}</a>: {txt}</li>')
        corpo = "<ul>" + "".join(li) + "</ul>"
        corpo += ('<h2>Como o motor funciona</h2><p>O motor lê os grupos de automóvel à venda no portal, junta cartas do mesmo grupo ou '
                  'de grupos diferentes até chegar perto de cada faixa e ordena as combinações pelo histórico de lances do grupo, '
                  'pelo prazo e pelo excesso sobre a faixa. O ordenamento usa dados internos que não são publicados aqui porque '
                  'ainda não foram verificados. Ele não prevê contemplação.</p>')
        intro_h2 = "Faixas de crédito"
    cta_txt = f"Falar no WhatsApp com a Conecta Cortex ({fr} · FLUXO-REV)"
    cta_wa = wa(f"Olá! Vim pelo motor de oportunidades ({'faixa de ' + mil(faixa) if faixa else 'página geral'}). Código {fr} (FLUXO-REV).", conteudo)
    alt = f"Carro ilustrativo da faixa de {mil(faixa or 100000)}" if faixa else "Carro ilustrativo da página de oportunidades"
    corpo_html = f"""<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="wrap brand"><a href="{e(utm(url_pagina(), conteudo))}">Conecta Cortex · Oportunidades</a></header>
<main id="conteudo" class="wrap">
<article class="article">
<header>
<p class="meta">Gerado em <time datetime="{gerado}">{hoje}</time> · <span data-fonte="fonte-portal">dados da coleta de {col}</span></p>
<h1>{e(h1)}</h1>
<p class="lede">{e(lede)}</p>
{autor}
</header>
{capa(imgs, alt, conteudo)}
{nav_faixas(faixa, conteudo)}
<div class="prose">
{NOTICE}
<h2>{intro_h2}</h2>
{corpo}
{fontes_html(res, bcb, conteudo)}
<p class="cta-end">Quer que alguém da equipe olhe uma dessas combinações com você? <a class="cta" href="{e(cta_wa)}">{cta_txt}</a></p>
</div>
</article>
</main>
</body>
</html>
"""
    return cabecalho(titulo, desc, url, imgs, gerado, autor_ld, res) + corpo_html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoje", default=datetime.now(BAHIA).date().isoformat())
    a = ap.parse_args()
    hoje = date.fromisoformat(a.hoje)
    gerado = f"{hoje.isoformat()}T09:00:00-03:00"
    res, por_item = rodar(hoje)
    bcb_d, bcb_info = carregar_bcb()
    bcb = None
    if bcb_d and (hoje - bcb_info).days <= CFG["bcb_max_dias_busca"]:
        bcb = (bcb_d, bcb_info)
    else:
        res["bcb_lacuna"] = bcb_info if not bcb_d else f"taxa buscada em {bcb_info}, acima de {CFG['bcb_max_dias_busca']} dias"
    gerar_placeholders()
    paginas = [None] + CFG["faixas"]
    for f in paginas:
        dest = OUT / (f"{f // 1000}/" if f else "") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(pagina(f, res, por_item, bcb, gerado, paginas), encoding="utf-8")
    sm = "".join(f"  <url><loc>{url_pagina(f)}</loc><lastmod>{hoje.isoformat()}</lastmod></url>\n" for f in paginas)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                     f'<!-- Sitemap da rota /oportunidades na subconta oficial ({BASE}). Não listar no sitemap do lab. -->\n'
                                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n", encoding="utf-8")
    # saída interna (tem mediana/embutido: NÃO servir)
    saida = {k: v for k, v in res.items() if k != "faixas"}
    saida["bcb"] = {"usada": bool(bcb), **({"valor_aa": bcb_d["valor_aa"], "referencia": bcb_d["referencia"],
                                           "buscado_em": bcb_d["buscado_em"]} if bcb_d else {})}
    saida["faixas"] = {}
    for f, info in res["faixas"].items():
        saida["faixas"][f] = {"combinacoes_avaliadas": info["combinacoes"], "mostradas": [
            {"rank": o.rank, "chave": o.chave_cartas, "credito_total": str(o.credito_total), "prazo_min": o.prazo,
             "proxima_assembleia": o.proxima_assembleia.isoformat() if o.proxima_assembleia else None,
             "INTERNO_mediana_agregada": str(o.mediana_agregada), "INTERNO_embutido": str(o.embutido)} for o in info["ops"]]}
    dir_saida = ROOT / "dados" / "oportunidades" / "saida"
    dir_saida.mkdir(parents=True, exist_ok=True)
    (dir_saida / f"rodada-{hoje.isoformat()}.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    for f, info in res["faixas"].items():
        print(f"faixa {f}: {len(info['ops'])} mostradas de {info['combinacoes']} combinações avaliadas")
    print("coleta:", res["data_coleta"], f"({res['idade_coleta_dias']} dias)", "· BCB:", "ok" if bcb else res.get("bcb_lacuna"))
    if res["estoque_descartadas"]:
        print("descartadas por estoque:", res["estoque_descartadas"])


if __name__ == "__main__":
    main()
