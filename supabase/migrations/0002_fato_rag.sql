-- Conecta Cortex – migração 0002 (rascunho): cofre protegido, tabela fato e busca RAG.
-- STATUS: NÃO TESTADA (sem Postgres local). Revisada só por leitura. Não aplicar sem aprovação do Wagner.
-- Depende de 0001 (resultados_disal, rag_embeddings, extensão vector).

-- ---------------------------------------------------------------------------
-- Cofre append-only: resultados_disal só recebe inserts (o runtime nunca o consulta)
-- ---------------------------------------------------------------------------
create or replace function public.cofre_somente_insercao() returns trigger
language plpgsql as $$
begin
  raise exception 'resultados_disal é append-only (cofre)';
end $$;

create trigger trg_cofre_sem_update_delete before update or delete on public.resultados_disal
  for each row execute function public.cofre_somente_insercao();
create trigger trg_cofre_sem_truncate before truncate on public.resultados_disal
  for each statement execute function public.cofre_somente_insercao();

-- ---------------------------------------------------------------------------
-- Tabela fato: o que o solver lê (~70 grupos ativos). Populada pelo job semanal em scrap/.
-- PENDENTE: alinhar as colunas às 20 da aba 2_Parametros da planilha mestra (ainda não exportada; não inventar colunas).
-- Cada execução do job cria um snapshot; só um é o atual.
-- ---------------------------------------------------------------------------
create table public.fato_snapshots (
  id          text primary key,                 -- snapshot_id (guardado também na proposta)
  gerado_em   timestamptz not null default now(),
  atual       boolean not null default false
);
create unique index fato_snapshot_unico_atual on public.fato_snapshots ((true)) where atual;

create table public.fato_cotas (
  snapshot_id       text not null references public.fato_snapshots(id) on delete cascade,
  cota_id           text not null,
  grupo             text not null,                -- código do grupo, 6 dígitos (só dado, nunca regra por número)
  serie             text not null,
  tipo_bem          text not null,
  plano_pct         int  not null check (plano_pct in (75, 100)),
  credito           numeric(14,2) not null,
  taxa_pct          numeric(6,4)  not null,
  parcela           numeric(14,2) not null,
  pct_embutido_max  numeric(5,4)  not null check (pct_embutido_max between 0 and 1),  -- fração da categoria (0.10 = 10%); I2: fração em todo o banco (0003 converte grupos_disal)
  tem_lance_fixo    boolean not null default false,
  c                 numeric(6,4)[] check (c is null or array_length(c, 1) = 6),   -- c1..c6, mais recente primeiro
  qtd_fixo_contemplado_mes numeric(8,2),
  -- v1.1 (27/10/2026). mediana_lance_livre é só dado comercial (embutido_cobre_mediana): não entra em probabilidade nem ranking.
  mediana_lance_livre numeric(6,4),             -- fração da categoria; mediana dos lances livres contemplados na janela de 6 assembleias; null = desconhecida
  data_coleta       date,                       -- quando o dado do grupo foi coletado; > 8 dias = oportunidade desatualizada
  proxima_assembleia date,                      -- opcional; base do prazo de entrada de cliente novo (2 dias antes, dia útil)
  -- (revisão N1) sem coluna embutido_excecao: grupo sem fixo é DADO (tem_lance_fixo = false; embutido 10% pela regra geral N5).
  extra             jsonb not null default '{}',  -- demais campos do snapshot JSON (M, p, n_ofertantes_fixo_medio...)
  -- (I1) status, categoria_veiculo, qtd_min, qtd_truncada, lance_fixo_pct, n_ofertantes_fixo_medio, lance_ref_irmaos
  -- e prazo_total viram colunas tipadas na 0005 (populadas a partir de `extra`).
  primary key (snapshot_id, cota_id, plano_pct)
);
create index on public.fato_cotas (snapshot_id, tipo_bem);

alter table public.fato_snapshots enable row level security;
alter table public.fato_cotas     enable row level security;   -- sem policy: só service_role (o solver)

-- ---------------------------------------------------------------------------
-- RAG: metadados para filtrar ANTES da similaridade + função de busca com poda por score
-- ---------------------------------------------------------------------------
alter table public.rag_embeddings
  add column tipo_bem text,
  add column cidade   text,
  add column credito  numeric(14,2);

create index on public.rag_embeddings (tipo_bem, cidade);
create index on public.rag_embeddings (credito);

create or replace function public.rag_buscar(
  p_embedding   vector(1536),
  p_tipo_bem    text    default null,
  p_cidade      text    default null,
  p_credito_min numeric default null,
  p_credito_max numeric default null,
  p_score_min   real    default 0.75,
  p_limite      int     default 8
) returns table (id uuid, conteudo text, score real)
language plpgsql set search_path = public as $$
begin
  -- pgvector >= 0.8: sem isso, filtro + HNSW pode devolver menos resultados do que existem
  perform set_config('hnsw.iterative_scan', 'relaxed_order', true);
  perform set_config('hnsw.ef_search', '100', true);
  return query
  select r.id, r.conteudo, (1 - (r.embedding <=> p_embedding))::real
    from public.rag_embeddings r
   where (p_tipo_bem    is null or r.tipo_bem = p_tipo_bem)
     and (p_cidade      is null or r.cidade = p_cidade)
     and (p_credito_min is null or r.credito >= p_credito_min)
     and (p_credito_max is null or r.credito <= p_credito_max)
     and (r.embedding <=> p_embedding) <= 1 - p_score_min      -- poda por score
   order by r.embedding <=> p_embedding
   limit p_limite;
end $$;
revoke all on function public.rag_buscar(vector, text, text, numeric, numeric, real, int) from public, anon, authenticated;
