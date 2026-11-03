-- Conecta Cortex – migração inicial (rascunho)
-- STATUS: NÃO TESTADA (sem Postgres local disponível). Revisada apenas por leitura.
-- Requer Supabase (usa auth.jwt(), role service_role e extensão pgvector).
-- Não aplicar em produção sem revisão e aprovação do Wagner.

create extension if not exists vector;

-- ---------------------------------------------------------------------------
-- Utilitários
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- papel do usuário logado, vindo de um claim customizado no JWT ('admin' | 'vendedor')
create or replace function public.papel_app() returns text
language sql stable as $$
  select coalesce(auth.jwt() ->> 'papel_app', '')
$$;

-- ---------------------------------------------------------------------------
-- Origem: influencers e criativos (laço criativo -> venda -> feedback)
-- ---------------------------------------------------------------------------
create table public.influencers (
  id         uuid primary key default gen_random_uuid(),
  nome       text not null,
  contato    text,
  ativo      boolean not null default true,
  created_at timestamptz not null default now()
);

create table public.criativos (
  id            uuid primary key default gen_random_uuid(),
  codigo        text not null unique,            -- id rastreável (ex.: vem no referral do anúncio)
  id_influencer uuid references public.influencers(id),
  canal         text,                            -- ex.: instagram, tiktok, meta_ads
  descricao     text,
  promessa      text,                            -- o que o criativo prometeu
  ativo         boolean not null default true,
  created_at    timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Motor Disal: catálogo de grupos e resultados
-- Regras por flag, nunca por número de grupo.
-- ---------------------------------------------------------------------------
create table public.grupos_disal (
  id                uuid primary key default gen_random_uuid(),
  codigo            text not null unique,        -- ex.: '003300'
  categoria         text,                        -- ex.: auto, imovel
  prazo_meses       int  not null check (prazo_meses > 0),
  data_inicio       date,                        -- idade do grupo = hoje - data_inicio
  tem_lance_fixo    boolean not null,            -- exceções (ex.: 003300) = false
  pct_embutido_max  numeric(5,2) not null default 0 check (pct_embutido_max between 0 and 100),
  mediana_lance_pct numeric(6,2),                -- mediana recente dos lances vencedores (% do crédito)
  ativo             boolean not null default true,
  recon             boolean not null default false,  -- grupo em Recon
  atualizado_em     timestamptz not null default now(),
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create trigger trg_grupos_updated before update on public.grupos_disal
  for each row execute function public.set_updated_at();

create table public.resultados_disal (
  id              bigint generated always as identity primary key,
  id_grupo        uuid not null references public.grupos_disal(id),
  data_assembleia date not null,
  cota            text,
  tipo            text not null check (tipo in ('sorteio','lance_livre','lance_fixo','lance_limitado')),
  lance_pct       numeric(6,2),
  base_lance      text not null default 'credito_mais_taxa', -- todo lance acima da categoria = crédito + taxa
  created_at      timestamptz not null default now()
);

-- visão com a idade e a faixa ideal (65–85% da idade do grupo) calculadas na hora
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

-- ---------------------------------------------------------------------------
-- Leads, consentimento LGPD, atendimentos
-- ---------------------------------------------------------------------------
create table public.leads (
  id             uuid primary key default gen_random_uuid(),
  telefone_e164  text not null unique,
  nome           text,
  status         text not null default 'novo'
                 check (status in ('novo','em_atendimento','em_handoff','fechado','perdido','descartado')),
  quente         boolean not null default false,
  id_criativo    uuid references public.criativos(id),
  id_influencer  uuid references public.influencers(id),
  vendedor       text,
  retencao_ate   timestamptz not null default (now() + interval '12 months'), -- PLACEHOLDER: prazo a definir com jurídico
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create trigger trg_leads_updated before update on public.leads
  for each row execute function public.set_updated_at();

create table public.consentimentos_lgpd (
  id               uuid primary key default gen_random_uuid(),
  id_lead          uuid not null references public.leads(id) on delete cascade,
  tipo             text not null check (tipo in
                   ('atendimento_whatsapp','marketing','compartilhamento_vendedor','voz_biometria')),
  concedido        boolean not null,
  texto_versao     text not null,                -- versão do texto mostrado ao cliente
  evidencia        text,                         -- wamid/trecho que comprova o aceite
  concedido_em     timestamptz not null default now(),
  revogado_em      timestamptz,
  retencao_ate     timestamptz not null,         -- prazo obrigatório; sem default de propósito
  created_at       timestamptz not null default now()
);

create table public.atendimentos (
  id                  uuid primary key default gen_random_uuid(),
  id_lead             uuid not null references public.leads(id) on delete cascade,
  canal               text not null default 'whatsapp' check (canal in ('whatsapp','voz')),
  status              text not null default 'aberto' check (status in ('aberto','handoff','encerrado')),
  ultima_mensagem_em  timestamptz,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create trigger trg_atendimentos_updated before update on public.atendimentos
  for each row execute function public.set_updated_at();

create table public.mensagens (
  id              bigint generated always as identity primary key,
  id_atendimento  uuid not null references public.atendimentos(id) on delete cascade,
  wamid           text unique,                   -- idempotência: id da mensagem no WhatsApp/BSP
  direcao         text not null check (direcao in ('entrada','saida')),
  autor           text not null default 'cliente' check (autor in ('cliente','ia','humano')),
  conteudo        text,
  tokens_entrada  int,
  tokens_saida    int,
  custo_brl       numeric(10,4),                 -- custo estimado da chamada à IA
  retencao_ate    timestamptz not null default (now() + interval '12 months'), -- PLACEHOLDER
  created_at      timestamptz not null default now()
);

-- RAG sobre atendimentos. Dimensão 1536 = PLACEHOLDER (depende do modelo de embedding).
create table public.rag_embeddings (
  id              uuid primary key default gen_random_uuid(),
  id_atendimento  uuid references public.atendimentos(id) on delete cascade,
  fonte           text not null default 'atendimento',
  conteudo        text not null,
  embedding       vector(1536) not null,
  retencao_ate    timestamptz not null default (now() + interval '12 months'), -- PLACEHOLDER
  created_at      timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Compliance: leis executáveis versionadas e alertas (alerta, não bloqueio)
-- ---------------------------------------------------------------------------
create table public.leis_compliance (
  id            uuid primary key default gen_random_uuid(),
  codigo        text not null,
  versao        int  not null,
  descricao     text,
  padrao_regex  text not null,
  severidade    text not null default 'media' check (severidade in ('baixa','media','alta')),
  vigente_de    timestamptz not null default now(),
  vigente_ate   timestamptz,
  unique (codigo, versao)
);

create table public.alertas_compliance (
  id             bigint generated always as identity primary key,
  id_mensagem    bigint references public.mensagens(id) on delete set null,
  id_lei         uuid references public.leis_compliance(id),
  trecho         text,
  severidade     text not null default 'media' check (severidade in ('baixa','media','alta')),
  status         text not null default 'aberto' check (status in ('aberto','aceito','corrigido','ignorado')),
  decisao_por    text,                           -- Wagner arbitra
  decisao_em     timestamptz,
  created_at     timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Handoff e vendas
-- ---------------------------------------------------------------------------
create table public.handoffs (
  id               uuid primary key default gen_random_uuid(),
  id_lead          uuid not null references public.leads(id) on delete cascade,
  id_atendimento   uuid references public.atendimentos(id) on delete set null,
  id_grupo         uuid references public.grupos_disal(id),  -- grupo identificado
  mediana_lance_pct numeric(6,2),                            -- mediana do grupo
  embutido_cobre   boolean,                                  -- embutido cobre a mediana?
  resumo           text,
  vendedor         text,
  created_at       timestamptz not null default now()
);

create table public.vendas (
  id             uuid primary key default gen_random_uuid(),
  id_lead        uuid references public.leads(id) on delete set null,
  id_criativo    uuid references public.criativos(id),
  id_influencer  uuid references public.influencers(id),
  id_grupo       uuid references public.grupos_disal(id),
  valor_credito  numeric(14,2),
  vendedor       text,
  fechado_em     timestamptz not null default now(),
  created_at     timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Índices
-- ---------------------------------------------------------------------------
create index on public.criativos (id_influencer);
create index on public.resultados_disal (id_grupo, data_assembleia desc);
create index on public.grupos_disal (ativo, tem_lance_fixo);
create index on public.leads (status);
create index on public.leads (id_criativo);
create index on public.leads (retencao_ate);
create index on public.consentimentos_lgpd (id_lead, tipo);
create index on public.atendimentos (id_lead, status);
create index on public.mensagens (id_atendimento, created_at);
create index on public.mensagens (retencao_ate);
create index on public.rag_embeddings using hnsw (embedding vector_cosine_ops);
create index on public.alertas_compliance (status, created_at desc);
create index on public.alertas_compliance (id_mensagem);
create index on public.handoffs (id_lead);
create index on public.vendas (id_criativo);
create index on public.vendas (id_influencer);
create index on public.vendas (id_grupo);

-- ---------------------------------------------------------------------------
-- Retenção LGPD: expurgo manual (agendar com pg_cron depois de aprovado)
-- ---------------------------------------------------------------------------
create or replace function public.expurgar_vencidos() returns void
language plpgsql security definer set search_path = public as $$
begin
  delete from public.rag_embeddings where retencao_ate < now();
  delete from public.mensagens      where retencao_ate < now();
  update public.leads
     set nome = null, telefone_e164 = 'anon:' || id::text
   where retencao_ate < now() and telefone_e164 not like 'anon:%';
end $$;
revoke all on function public.expurgar_vencidos() from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- RLS: tudo ligado. A Edge Function usa service_role (ignora RLS).
-- Sem policy = ninguém além do service_role acessa (consentimentos, rag, leis).
-- ---------------------------------------------------------------------------
alter table public.influencers          enable row level security;
alter table public.criativos            enable row level security;
alter table public.grupos_disal         enable row level security;
alter table public.resultados_disal     enable row level security;
alter table public.leads                enable row level security;
alter table public.consentimentos_lgpd  enable row level security;
alter table public.atendimentos         enable row level security;
alter table public.mensagens            enable row level security;
alter table public.rag_embeddings       enable row level security;
alter table public.leis_compliance      enable row level security;
alter table public.alertas_compliance   enable row level security;
alter table public.handoffs             enable row level security;
alter table public.vendas               enable row level security;

-- leitura para equipe (admin = Wagner, vendedor)
create policy equipe_le on public.leads         for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.atendimentos  for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.mensagens     for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.handoffs      for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.grupos_disal  for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.resultados_disal for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.criativos     for select to authenticated using (public.papel_app() in ('admin','vendedor'));
create policy equipe_le on public.influencers   for select to authenticated using (public.papel_app() in ('admin','vendedor'));

-- somente admin: vendas e alertas (e arbitragem dos alertas)
create policy admin_le  on public.vendas              for select to authenticated using (public.papel_app() = 'admin');
create policy admin_le  on public.alertas_compliance  for select to authenticated using (public.papel_app() = 'admin');
create policy admin_upd on public.alertas_compliance  for update to authenticated
  using (public.papel_app() = 'admin') with check (public.papel_app() = 'admin');
