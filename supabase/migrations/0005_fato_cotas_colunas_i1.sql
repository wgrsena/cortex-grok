-- 0005 — I1 (01/11/2026): 8 colunas tipadas na tabela fato `public.fato_cotas`, populadas a partir de `extra` (jsonb).
-- Alinha a tabela à spec §9 (solver/ESPECIFICACAO_V1_1.md) e ao modelo `Cota` (solver/modelos.py).
-- Mesma regra da função Python `solver/fato_colunas.colunas_de_extra` (fonte única; teste confere o espelho).
-- Idempotente: `add column if not exists`, constraints recriadas, UPDATE só preenche coluna ainda nula.
-- Casts seguros: valor ausente, de tipo errado ou fora do domínio vira NULL (nunca erro).
-- Unidade (I2): lance_fixo_pct e lance_ref_irmaos são FRAÇÃO da categoria 0..1; valor em (1, 100] é % e vira /100.
-- `extra` é mantido como está (compatibilidade); o job passa a gravar as colunas tipadas E o extra.
-- NÃO testada em Postgres real (sem servidor de teste no ambiente): rodar 0003, 0004 e 0005 em banco de teste antes de produção.

alter table public.fato_cotas
  add column if not exists status                  text,
  add column if not exists categoria_veiculo       text,
  add column if not exists qtd_min                 int,
  add column if not exists qtd_truncada            boolean,
  add column if not exists lance_fixo_pct          numeric,
  add column if not exists n_ofertantes_fixo_medio numeric,
  add column if not exists lance_ref_irmaos        numeric,
  add column if not exists prazo_total             int;

-- funções auxiliares (removidas no fim da migration)
create or replace function public._i1_num(v jsonb) returns numeric language sql immutable as $$
  select case
    when jsonb_typeof(v) = 'number' then (v #>> '{}')::numeric
    when jsonb_typeof(v) = 'string' and (v #>> '{}') ~ '^\s*-?[0-9]+(\.[0-9]+)?\s*$' then trim(v #>> '{}')::numeric
  end
$$;

create or replace function public._i1_fracao(v jsonb) returns numeric language sql immutable as $$
  select case
    when x is null or x < 0 or x > 100 then null
    when x <= 1 then x
    else x / 100
  end from (select public._i1_num(v) as x) s
$$;

create or replace function public._i1_inteiro(v jsonb) returns int language sql immutable as $$
  select case
    when x is null or x <> trunc(x) or x < 1 or x > 2147483647 then null
    else x::int
  end from (select public._i1_num(v) as x) s
$$;

create or replace function public._i1_bool(v jsonb) returns boolean language sql immutable as $$
  select case
    when jsonb_typeof(v) = 'boolean' then (v #>> '{}')::boolean
    when jsonb_typeof(v) = 'string' and lower(trim(v #>> '{}')) in ('true', 'false') then lower(trim(v #>> '{}'))::boolean
  end
$$;

create or replace function public._i1_texto(v jsonb, validos text[]) returns text language sql immutable as $$
  select case
    when jsonb_typeof(v) = 'string' and lower(trim(v #>> '{}')) = any (validos) then lower(trim(v #>> '{}'))
  end
$$;

update public.fato_cotas set
  status                  = coalesce(status, public._i1_texto(extra -> 'status', array['disponivel', 'saiu_da_venda'])),
  categoria_veiculo       = coalesce(categoria_veiculo, public._i1_texto(extra -> 'categoria_veiculo', array['carro', 'moto', 'caminhao'])),
  qtd_min                 = coalesce(qtd_min, public._i1_inteiro(extra -> 'qtd_min')),
  qtd_truncada            = coalesce(qtd_truncada, public._i1_bool(extra -> 'qtd_truncada')),
  lance_fixo_pct          = coalesce(lance_fixo_pct, public._i1_fracao(extra -> 'lance_fixo_pct')),
  n_ofertantes_fixo_medio = coalesce(n_ofertantes_fixo_medio,
                              case when public._i1_num(extra -> 'n_ofertantes_fixo_medio') >= 0
                                   then public._i1_num(extra -> 'n_ofertantes_fixo_medio') end),
  lance_ref_irmaos        = coalesce(lance_ref_irmaos, public._i1_fracao(extra -> 'lance_ref_irmaos')),
  prazo_total             = coalesce(prazo_total, public._i1_inteiro(extra -> 'prazo_total'));

drop function public._i1_texto(jsonb, text[]);
drop function public._i1_bool(jsonb);
drop function public._i1_inteiro(jsonb);
drop function public._i1_fracao(jsonb);
drop function public._i1_num(jsonb);

alter table public.fato_cotas drop constraint if exists fato_cotas_status_check;
alter table public.fato_cotas drop constraint if exists fato_cotas_categoria_veiculo_check;
alter table public.fato_cotas drop constraint if exists fato_cotas_qtd_min_check;
alter table public.fato_cotas drop constraint if exists fato_cotas_lance_fixo_pct_check;
alter table public.fato_cotas drop constraint if exists fato_cotas_n_ofertantes_fixo_medio_check;
alter table public.fato_cotas drop constraint if exists fato_cotas_lance_ref_irmaos_check;
alter table public.fato_cotas drop constraint if exists fato_cotas_prazo_total_check;
alter table public.fato_cotas
  add constraint fato_cotas_status_check check (status is null or status in ('disponivel', 'saiu_da_venda')),
  add constraint fato_cotas_categoria_veiculo_check check (categoria_veiculo is null or categoria_veiculo in ('carro', 'moto', 'caminhao')),
  add constraint fato_cotas_qtd_min_check check (qtd_min is null or qtd_min >= 1),
  add constraint fato_cotas_lance_fixo_pct_check check (lance_fixo_pct is null or lance_fixo_pct between 0 and 1),
  add constraint fato_cotas_n_ofertantes_fixo_medio_check check (n_ofertantes_fixo_medio is null or n_ofertantes_fixo_medio >= 0),
  add constraint fato_cotas_lance_ref_irmaos_check check (lance_ref_irmaos is null or lance_ref_irmaos between 0 and 1),
  add constraint fato_cotas_prazo_total_check check (prazo_total is null or prazo_total >= 1);

comment on column public.fato_cotas.status is 'disponivel | saiu_da_venda (I1, 0005)';
comment on column public.fato_cotas.categoria_veiculo is 'carro | moto | caminhao; nunca misturar numa unificação (I1, 0005)';
comment on column public.fato_cotas.qtd_min is 'quantidade mínima de cartas da cota (I1, 0005)';
comment on column public.fato_cotas.qtd_truncada is 'true quando a quantidade foi truncada no limite do solver (I1, 0005)';
comment on column public.fato_cotas.lance_fixo_pct is 'lance fixo, fração da categoria 0..1 (I1, 0005)';
comment on column public.fato_cotas.n_ofertantes_fixo_medio is 'média de ofertantes no lance fixo; chance = 1/n (I1, 0005)';
comment on column public.fato_cotas.lance_ref_irmaos is 'lance de referência dos grupos irmãos (SEM_HISTORICO, só informativo), fração 0..1 (I1, 0005)';
comment on column public.fato_cotas.prazo_total is 'prazo total do grupo em meses (I1, 0005)';
