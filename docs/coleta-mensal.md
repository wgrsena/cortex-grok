# Coleta mensal

**A coleta semanal é o motor** (job `scrap/resumo_semanal.py`). Ao entrar a **tabela de novembro**, faz-se um **rerun completo**:

- a mediana das 6 últimas assembleias muda;
- os flags revalidam (`tem_lance_fixo`, `pct_embutido_max`);
- as datas renovam (`data_coleta`, `proxima_assembleia`, prazo de entrada).

## Checklist do rerun
- [ ] Exportar a coleta nova (Drive `WEBDISAL_RESULTADOS`: planilha principal, calendário, log, `00_CONSOLIDADO`) para `dados/` (pasta ignorada pelo git). Nunca versionar dado bruto nem segredo.
- [ ] Conferir o `webdisal_log_coleta` (data e falhas) antes de rodar.
- [ ] Atualizar o cofre (`scrap/cofre.py`, append-only; o runtime nunca toca).
- [ ] Rodar `scrap/resumo_semanal.py` (`--cofre`, `--ativos`, `--catalogo`, `--saida`): recalcula c1..c6, M, p, `qtd_fixo_contemplado_mes`, `n_ofertantes_fixo_medio` e `mediana_lance_livre`; grava `data_coleta`; repassa `proxima_assembleia`.
- [ ] Confirmar que a lista de ativos tem só os ~70 grupos vivos (grupo encerrado sai, grupo novo entra).
- [ ] Revalidar os flags de lance fixo e embutido (a regra do Arquimedes olha o histórico inteiro; o 003300 mudou de 25% para 10% assim: decisão (c) em `arquimedes-disal.md`).
- [ ] Conferir o snapshot atômico (`snapshots/<id>.json` + `ATUAL.json`).
- [ ] Rodar `python -m pytest -q scrap` e, se tocar regra, `solver`.
- [ ] Arquimedes regenera a tabela ranqueada em branch separada; diff para o Wagner; Cortex Build commita só com "manda".
- [ ] Rodar o backtest (`scrap/backtest.py`) quando houver dado real.

## Pendências
- Mediana: definição (todos os lances livres da janela × menores por assembleia) é V4 em `solver/NOTAS_DUVIDAS.md`.
- Esquema real do cofre e do catálogo ainda é suposição; alinhar às 20 colunas da aba `2_Parametros` (V7).
- Agendamento (cron) do job está fora deste pacote.
