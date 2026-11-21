# cortex-grok
Repositório próprio do Grok/Ara no Conecta Cortex. Escrita livre. Leitura do CONECTACORTEX (Claude/Codex) via acesso de leitor.

## Motor de oportunidade (solver Disal + tabela fato + grid Arquimedes)
Atualizado em 03/11/2026 (Cortex Build). Origem: `wgrsena/conecta-cortex`, `cortex/revisao-reviewer` (`8bfd5d4`) + `cortex/arquimedes-grid` (`517b4ab`), juntadas por merge (sem rebase). Proveniência e README original em [`docs/motor-oportunidade.md`](docs/motor-oportunidade.md).

> **Status: nada aplicado em banco, nada implantado.** Sem projeto Supabase, sem `DATABASE_URL`, sem deploy. As migrations `0001`–`0005` nunca rodaram em Postgres (só leitura + `sqlcheck`).

| Pasta | O que é |
|---|---|
| `solver/` | Motor Disal v1.1 (Python, FastAPI + HiGHS). Flags de catálogo `tem_lance_fixo` / `pct_embutido_max` (fração 0..1); embutido 25% com lance fixo, 10% sem (N5); `embutido_cobre_mediana` com `<=` (I2); ranking de produção em `ranking.py` (sequência W/6); `fato_colunas.py` = fonte única das colunas da `fato_cotas` |
| `arquimedes/` | Grid de oportunidades por faixa (50/80/100/180/200/250 mil), branch-and-bound com cobertura mínima; persiste só as ranqueadas em `public.oportunidades` |
| `scrap/` | Cofre (append-only), job semanal que gera a tabela fato, backtest |
| `supabase/migrations/` | `0001` init · `0002` tabela fato (`fato_snapshots`, `fato_cotas`) e RAG · `0003` fração do embutido/mediana · `0004` `oportunidades` (fração 0..1) · `0005` 8 colunas tipadas na `fato_cotas` |
| `rag/`, `centauro/`, `schema/`, `docs/` | RAG (SQL não testado), persona do WhatsApp (não integrada), mapa dos armazenamentos, specs e docs Disal |

Testes: `python3 -m pytest -q solver scrap rag centauro arquimedes` → 150 passam (124 da revisão + 26 do grid).

Relação com o PR #2 (`cortex/backtest-rolante`): ele vendoriza `solver/modelos.py`, `solver/niveis.py`, `scrap/cofre.py` e `scrap/conftest.py`, idênticos aos daqui. Quem for mergeado depois resolve só `README.md`/`.gitignore`.

**Decisões abertas (Wagner):**
- **Ranking:** documento revisado pelo Claude (tirar probabilidade, ranquear pela carta mais fraca) × código atual (sequência/6, validado no backtest). O grid do Arquimedes ranqueia por menor mediana, maior embutido, maior prazo.
- **`n_ofertantes_fixo_medio`:** o documento do Claude remove; o ramo de lance fixo depende dele (V1).
- **Desempate** entre sequências iguais.
- **Feriado no prazo de entrada:** recuar para o dia útil anterior ou não (V2).
- **Grupo 003300:** embutido 25% ou 10% (revalidação deu 10%).
- **Vazamento de dado técnico pela IA:** só alertar ou bloquear.
- **Critério de lead quente** para o handoff humano.
- **BSP do WhatsApp:** 360dialog × Zenvia.
- Grid: mediana da planilha é % da categoria ou do crédito? Divisor da parcela pós (963,75 × 989,80; a conta citada 989,89 não fecha).

**Dados pendentes:**
- Export da planilha mestra `2_Parametros` (20 colunas) para alinhar o schema da `fato_cotas`.
- Coleta nova: a de 25/10/2026 venceu em 03/11/2026 (limite de 8 dias); oportunidades saem `desatualizada`.
- Base verificada de entrada e lance (hoje "dado não disponível").

**Para consolidar em banco:** criar o projeto Supabase (região São Paulo, pgvector), aplicar `0001`–`0005` num banco de **teste**, importar o catálogo (76 grupos) e uma cópia do cofre, rodar o grid gravando em `oportunidades`. Depende de credencial e confirmação do Wagner.
