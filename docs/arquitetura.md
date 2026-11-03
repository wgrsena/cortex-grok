# Arquitetura – Conecta Cortex (MVP)

> Diagrama em Mermaid. **Sintaxe NÃO validada** (sem mermaid-cli e sem instalar nada). Mantive o formato simples (flowchart + subgraph); conferir colando em https://mermaid.live.

```mermaid
flowchart LR
  subgraph CASCAS["1. Cascas de mercado"]
    ADS["Anuncio / Influencer<br/>(id_criativo, id_influencer)"]
    MC["ManyChat<br/>filtro de comentarios"]
    BSP["API WhatsApp<br/>360dialog ou Zenvia"]
    RIO["respond.io<br/>unifica canais (opcional)"]
    HUB["HubSpot gratis<br/>pipeline"]
  end

  subgraph BACK["2. Backend proprio (Supabase Edge Function)"]
    WH["Webhook atendimento<br/>validacao + idempotencia"]
    LGPD["Consentimento LGPD"]
    CTX["Montagem de contexto"]
    LEIS["Leis executaveis<br/>regex: alerta sem bloquear"]
    DB[("Postgres<br/>leads, mensagens, vendas")]
  end

  subgraph IA["3. Grok API (sem estado)"]
    GROK["System prompt Centauro<br/>+ historico + RAG + tools"]
  end

  subgraph RAGB["4. RAG"]
    VEC[("pgvector<br/>atendimentos passados")]
  end

  subgraph DISAL["5. Motor Disal (interno)"]
    ENG["Radar de grupos<br/>flags tem_lance_fixo / pct_embutido_max"]
    RES[("grupos + resultados Disal")]
  end

  subgraph VOZ["6. Voz (fase 2)"]
    LK["LiveKit Agents"]
    TEL["SIP: Twilio ou Zenvia Voz"]
  end

  subgraph HAND["7. Handoff"]
    DOS["Dossie para o vendedor<br/>grupo + mediana + embutido cobre?"]
    HUM["Wagner / vendedor<br/>decide e fecha"]
  end

  ADS --> MC --> BSP
  ADS --> BSP
  BSP --> RIO
  BSP -->|webhook| WH
  RIO -.->|webhook se plano permitir| WH
  WH --> LGPD --> CTX
  CTX --> VEC
  CTX --> DB
  CTX --> ENG
  ENG --> RES
  CTX -->|contexto sem grupo/mediana| GROK
  GROK --> LEIS
  LEIS -->|resposta| BSP
  LEIS --> DB
  CTX -->|lead quente| DOS
  ENG -->|dados tecnicos| DOS
  DOS --> HUM
  DOS --> HUB
  HUM -->|venda com id rastreado| DB
  LK --> TEL
  LK --> GROK
  LK --> LGPD
```

## Camadas
1. **Cascas:** ManyChat filtra comentários; a API do WhatsApp (360dialog ou Zenvia) entrega as mensagens; respond.io é opcional (ver `docs/custos.md`); HubSpot grátis só como pipeline.
2. **Backend próprio:** única fonte da verdade. Valida, deduplica, checa consentimento, monta contexto, chama a IA, aplica as leis, envia e registra.
3. **Grok API:** sem estado; recebe system prompt (playbook Centauro), histórico, trechos de RAG e tools.
4. **RAG:** pgvector sobre atendimentos anteriores.
5. **Motor Disal:** usa flags do catálogo (`tem_lance_fixo`, `pct_embutido_max`), nunca número de grupo no código. Roda no backend.
6. **Voz (fase 2):** LiveKit + SIP; exige opt-in específico de biometria de voz.
7. **Handoff:** dossiê interno (grupo, mediana, embutido cobre) vai ao vendedor; o vendedor revela ao cliente na hora certa.

## Decisões de desenho
- **A IA não recebe grupo, mediana nem embutido** para o texto ao cliente. Ela só recebe um sinal de escassez genérico (ex.: "há poucos grupos maduros na faixa"). O dado técnico segue direto para o dossiê. Isso "segura o cartão" por construção, além da regra regex. **A confirmar com o Wagner.**
- Leis são alerta, não bloqueio; Wagner arbitra pelo registro em `alertas_compliance`.
- Venda carrega `id_criativo`, `id_influencer`, `id_grupo` (laço criativo → venda → feedback).
