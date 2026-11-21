"""Cofre SINTÉTICO (rotulado) para testes do job e do backtest. Nunca usar como dado real."""


def cofre_sintetico(semente=1, grupos=("001000", "001001", "003500"), n_assembleias=30):
    """SINTÉTICO rotulado: linhas de contemplação (strings, como no CSV) de grupos com lance livre ~ iid por grupo."""
    import random
    from datetime import date
    rng, rows = random.Random(semente), []
    for gi, g in enumerate(grupos):
        centro = 0.12 + 0.07 * gi
        for t in range(n_assembleias):
            d = date(2024 + t // 12, t % 12 + 1, 15).isoformat()
            for _ in range(rng.randint(1, 3)):
                rows.append({"grupo": g, "data_assembleia": d, "tipo": "livre",
                             "lance_pct": f"{min(0.5, max(0.01, centro + rng.choice((-0.04, -0.02, 0, 0.02, 0.04)))):.2f}"})
            for _ in range(rng.randint(0, 3)):
                rows.append({"grupo": g, "data_assembleia": d, "tipo": "fixo", "lance_pct": "0.25",
                             "n_ofertantes_fixo": str(rng.randint(3, 9))})
            rows.append({"grupo": g, "data_assembleia": d, "tipo": "sorteio", "lance_pct": ""})
    return rows
