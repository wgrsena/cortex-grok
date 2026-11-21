-- 0003 — Revisão do Cortex Reviewer, item I2 (01/11/2026). Decisão de engenharia autorizada pelo Wagner; SEM mudança
-- de regra de negócio (embutido 25% / 10%, contagem e média de contemplações, menor lance contemplado intactos).
--
-- Padrão único: percentuais de regra guardados como FRAÇÃO da categoria (crédito + taxa), 0..1, como já fazem o solver,
-- a 0002 (fato_cotas) e o job semanal. Conversão para % só na apresentação. Esta migration converte as colunas da
-- 0001 que estavam em 0..100. Comparação de embutido_cobre_mediana: `<=` (o embutido que iguala a mediana cobre o
-- lance), igual ao solver (prazos.embutido_cobre_mediana).
-- Por que migration nova e não editar a 0001: funciona tanto em banco vazio quanto num banco onde a 0001 já tenha
-- sido aplicada (migration aplicada não se reescreve). Valores: x / 100 é exato (25 -> 0.25; 45.56 -> 0.4556).
-- A base da mediana/lance é a categoria (resultados_disal.base_lance = 'credito_mais_taxa'); o comentário antigo
-- "% do crédito" da 0001 estava errado quanto à base.

drop view if exists public.grupos_disal_faixa;

alter table public.grupos_disal drop constraint if exists grupos_disal_pct_embutido_max_check;
alter table public.grupos_disal
  alter column pct_embutido_max drop default,
  alter column pct_embutido_max type numeric(5,4) using (pct_embutido_max / 100),
  alter column pct_embutido_max set default 0,
  alter column mediana_lance_pct type numeric(6,4) using (mediana_lance_pct / 100);
alter table public.grupos_disal
  add constraint grupos_disal_pct_embutido_max_check check (pct_embutido_max between 0 and 1),
  add constraint grupos_disal_mediana_lance_pct_check check (mediana_lance_pct is null or mediana_lance_pct between 0 and 1);
comment on column public.grupos_disal.pct_embutido_max is 'fração da categoria (0.10 = 10%); 0..1 desde a 0003';
comment on column public.grupos_disal.mediana_lance_pct is 'mediana recente dos lances livres vencedores, fração da categoria (0..1) desde a 0003';

alter table public.resultados_disal
  alter column lance_pct type numeric(7,4) using (lance_pct / 100);
alter table public.resultados_disal
  add constraint resultados_disal_lance_pct_check check (lance_pct is null or lance_pct between 0 and 1);
comment on column public.resultados_disal.lance_pct is 'lance sobre a categoria (crédito + taxa), fração 0..1 desde a 0003';

alter table public.handoffs
  alter column mediana_lance_pct type numeric(6,4) using (mediana_lance_pct / 100);
comment on column public.handoffs.mediana_lance_pct is 'mediana do grupo no handoff, fração da categoria (0..1) desde a 0003';

-- mesma visão da 0001, agora com tudo em fração; `<=` mantido (o solver passou a usar `<=` também)
create view public.grupos_disal_faixa with (security_invoker = true) as
select g.*,
       case when g.data_inicio is null then null
            else round((((current_date - g.data_inicio) / 30.4375)::numeric) / g.prazo_meses * 100, 1)
       end as idade_pct,
       case when g.data_inicio is null then null
            else (((current_date - g.data_inicio) / 30.4375)::numeric) / g.prazo_meses between 0.65 and 0.85
       end as na_faixa_ideal,
       (g.mediana_lance_pct is not null and g.mediana_lance_pct <= g.pct_embutido_max) as embutido_cobre_mediana
from public.grupos_disal g;
