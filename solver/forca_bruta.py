"""Resolvedor de FORÇA BRUTA em Python puro (até 8 tipos): SÓ oráculo dos testes (revisão I3).
Reproduz a Função 2 sem MILP: relaxação contínua por conjunto de tipos (S1..S5), K_top candidatos com
corte de exclusão por conjunto de tipos, refinamento exato em J (6.3), ranking A2 e reservas.
NÃO implementa as aproximações da seção 7 (R1/R2): sem solução exata devolve ranking vazio.
Nenhum módulo de produção importa este arquivo (teste `test_i3_producao_nao_importa_forca_bruta`) e ele fica fora da
imagem Docker (.dockerignore). O ranking compartilhado (melhor, ordenar_a2, refinar_e_ranquear, ORDEM_*) mora em
ranking.py."""
from embutido import fazer_celula, montar_combo
from enumeracao import percorrer, unidades_com_ids
from ranking import ORDEM_CANDIDATOS, melhor, refinar_e_ranquear

MAX_TIPOS_FORCA_BRUTA = 8


def resolver_forca_bruta(universo, pedido, params):
    if len(universo.tipos) > MAX_TIPOS_FORCA_BRUTA:
        raise ValueError(f"força bruta limitada a {MAX_TIPOS_FORCA_BRUTA} tipos (recebeu {len(universo.tipos)})")
    cels = [fazer_celula(t, n, params) for t in universo.tipos for n in t.niveis
            if n.tipo != "referencia" or params.incluir_sem_historico]
    pool = []
    for indices in percorrer(cels, universo, pedido, params, None, {}):
        c = montar_combo(unidades_com_ids(indices, cels, universo), pedido, params, "continuo")
        if c.viavel:
            pool.append(c)
    candidatos = []
    while pool and len(candidatos) < params.K_top:
        b = melhor(pool, params.tol_prob, params.tol_taxa_rs, ORDEM_CANDIDATOS, params.w_desempate)
        candidatos.append(b)
        pool = [x for x in pool if x.tipos_usados != b.tipos_usados]   # corte de exclusão
    ranking, descartados = refinar_e_ranquear(candidatos, pedido, params)
    reservas = []
    if ranking:
        reservas = [r for r in ranking[1:] if not (r.cota_ids & ranking[0].cota_ids)][:params.n_reservas]
    return {"metodo": "forca_bruta", "ranking": ranking, "descartado_discreto": descartados,
            "reservas": reservas, "aproximacao": None if ranking else "pendente (seção 7 só no MILP)"}
