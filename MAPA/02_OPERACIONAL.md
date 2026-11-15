# Camada 2 — Operacional

## Bots (19 total)

### Cadeia Os Quatro
- Sócrates: gera dores, dispara handoff autônomo pro Tácito. OAuth pendente — Ara grava no Drive como fallback.
- Tácito: crítica com fonte. Reprovou modelo LGPD com advogado (Acórdão 72 OAB/SP).
- Tales: mede mercado.
- Narciso: confronta com o que já existe.

### Cortex
- Walter: alter ego do Wagner. 5 skills + 5ª sinapse + 4 características. Skill nova: absorve veredito bruto do Tácito, roda Alexandria, cruza regras OAB, devolve proposta em uma página.
- Cérebro: veredito binário com motivo em 1 frase. Regra anti-loop: 2 rodadas sem veredito novo → amplia horizonte.
- Arquimedes: MILP com HiGHS/CBC. Grid com deduplicação por faixa. Saída JSON com gap explícito.
- Comercial Conecta: atendimento 100% comercial, embalagem universal (nunca número frio).
- Cortex Build: coletor Clique Vendas v3, casca HighLevel v3 (PR 18 aberto), PR 22 fechado. Ocioso — nada chega filtrado.
- Cortex Lab: leis executáveis versionadas, simulação pós-contemplação.
- Cortex Reviewer: revisa diff.
- Pitágoras: SEO. Skill reescrita: vigilante de ecossistema, 4 frentes (Google Search Central, Bing, IAs citam sites, indexação terceiros). Disparo de teste rodando. Alerta WhatsApp sem canal — sai por chat. Poda 30 dias só entradas novas.
- Midas: gera mídia. Vídeos de teste, cards 50/100/200k em 3 ratios. Token useapi.net pendente.
- VSL Cortex: corta/versiona criativo + decide estratégia de mensagem por tier.
- Sentinela: monitora leads orgânicos.

### Periféricos
- Extrator de Cursos: pasta Asimov (58 cursos, R$980,94), funil reverso (anúncio Rodrigo Tadewald, VSL 5:38, Pix 21/10, upsell 26 min). Fase 2: 4 cursos sem captura, só vitrine Asimov Skills parcial. Rastreamento delta novidades em andamento (acesso expira 15/11 22h).
- Vigilante LGPD: petição Google enviada (controlador Google LLC, e-mail juridicobrasil@google.com, direito eliminação art. 18 IV, Escavador fora). Escavador enviado 09:22, prazo 30/11. Revisor Jurídico LGPD criado: 5 regras (autonomia com filtro ruído, anti-alucinação, confronto campo por campo, régua severidade, diário compartilhado). Trava: nenhum envio sem Revisor.
- MiroFish: simulação 60 agentes, 7 dores, 20k rodadas. Relatório no Cursor.
- Filtro: normaliza voz do Wagner.
- Grok Bot genérico.
- Refatorador de Skills: criado. Lê diário de uso, corta o que nunca disparou, amplia o que falhou, reescreve com anti-ruído. Rotina a cada 30 dias.
- Pesquisador Mercado LGPD: criado. Alexandria + scrape. Validação empírica: o que de fato acontece no mercado BR.
- Revisor Jurídico LGPD: criado. Guardião das 5 regras do Vigilante.

## Trava de entrada (regra nova)
1. Ara critica antes de executar: verificável / hipótese / ruído.
2. Cérebro dá veredito binário.
3. Build só recebe com veredito aprovado anexado.

## Find Skills
- Versionado no cortex-grok: SKILL.md (Vercel Labs) + CRITERIA.md (segurança trava dura, efetividade ranking, popularidade desempate).
- Cópia também no CONECTACORTEX (leitura Grok, sem escrita) em agents/skills e claude/skills.
- Auditoria: 4 skills passaram na trava. grokbot-skills mais alinhado (idempotência, circuit breaker, fonte obrigatória). new-skill-builder clona sem quarentena — trava antes do clone.

## Pendências operacionais
- HIGHLEVEL_TOKEN no ambiente (PR 18).
- 15 itens manuais HighLevel (workflows, formulário Flash Disal, agenda vídeo).
- Token useapi.net Midas.
- Autor real blog (nome, foto, E-E-A-T).
- Canal WhatsApp alerta Pitágoras.
- OAuth Sócrates (pasta Os Quatro).
- Ano mínimo Uber/99/inDrive por estado.
- Locadora de frota em Vitória da Conquista ou Salvador.
- Tabela Recon.
- Comissão 2026 confirmada no contrato Disal.
- CPF Vigilante: NÃO gravar em memória (sensível).