-- Conecta Cortex – migração 0004 (rascunho; 0003 reservada para a revisão do Reviewer: fração do embutido e mediana): tabela de oportunidades do Arquimedes.
-- STATUS: NÃO TESTADA em Postgres (sem banco local). Validada só por leitura e por sqlcheck.
-- Só as oportunidades RANQUEADAS do grid entram aqui; combinações intermediárias nunca são gravadas.
-- Unidades: dinheiro em R$; mediana e embutido em FRAÇÃO da categoria (0.4556 = 45,56%).

create table public.oportunidades (
  id                  bigint generated always as identity primary key,
  rodada              text not null,
  data_coleta         date not null,
  faixa_alvo          numeric(14,2) not null check (faixa_alvo > 0),
  rank                int not null check (rank >= 1),
  chave_cartas        text not null,
  credito_total       numeric(14,2) not null,
  categoria_total     numeric(14,2) not null,
  cartas              jsonb not null,
  mediana_lance_livre numeric(8,6) not null check (mediana_lance_livre between 0 and 1),
  prazo_meses         int not null check (prazo_meses > 0),
  embutido_pct        numeric(8,6) not null check (embutido_pct between 0 and 1),
  parcela_pos_total   numeric(14,2) not null,
  parcelas_pos        jsonb not null,
  proxima_assembleia  date,
  created_at          timestamptz not null default now()
);

-- Uma posição por faixa por rodada e o mesmo multiconjunto de cartas no máximo uma vez por rodada.
create unique index oportunidades_rodada_faixa_rank on public.oportunidades (rodada, faixa_alvo, rank);
create unique index oportunidades_rodada_cartas on public.oportunidades (rodada, chave_cartas);
create index oportunidades_data_coleta on public.oportunidades (data_coleta desc);
create index oportunidades_proxima_assembleia on public.oportunidades (proxima_assembleia);

alter table public.oportunidades enable row level security;   -- sem policy: só service_role
