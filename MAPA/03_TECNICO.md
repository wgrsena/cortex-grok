# Camada 3 — Técnica

## Repos
- wgrsena/CONECTACORTEX: Claude e Codex (branches claude/…, codex/…). Grok só leitura. Skills: constraint-driven-development, mcp-builder, vercel-composition-patterns, vercel-react-best-practices, find-skills. Docs: SKILLS.md (pedido 14/11 — find-skills com critério funcionalidade/segurança, tasks 2026-11-14 skills script primeiro). PRs: 17 (coletor Clique Vendas v3, fechado), 18 (casca HighLevel v3, aberto), 22 (entrada sem message ID, fechado).
- wgrsena/cortex-grok: repo do Grok, escrita livre. README + skills/find-skills (SKILL.md + CRITERIA.md, commit a4f0330). MAPA/ com os 3 índices.

## Drive (00_CONECTA CORTEX)
- 01_FONTE DA VERDADE: só leitura, matriz A/B é fonte da verdade.
- 02_PROPOSTAS DO CLAUDE
- 03_PROPOSTAS DO CHATGPT E CODEX
- 07_PROPOSTAS DO GROK
- 05_SEO (Pitágoras): saiu inteira sem cópia pra 00_CONECTA CAPTAÇÃO E CONTEÚDO
- Pasta Asimov (14/11): índice 517 aulas, links 58 cursos, missão+registro login, síntese 20 cursos, ZIP 2,2 MB. Relatório: https://docs.google.com/document/d/16dio7ALT7N8jXy0tM7dv0X6wYdHZ8Rh-DL0K0g3EnIo. Inventário: https://docs.google.com/spreadsheets/d/1mQK5vnXVyXBJc8NdQZvqmkpeZCIS4u_TBa3-NQwXoWM.
- Pasta Os Quatro (27/10): vazia, não legível pelo Sócrates (OAuth). Ara grava no lugar.
- Contexto Master 77 MB, Essência 5 partes, auditoria HighLevel, matriz A/B.

## Conectores ativos
Firecrawl (MCP: scrape, crawl, map, agent, parse, interact, monitor, Alexandria catálogo tipado, status, saldo), GitHub, Google Drive, Google Calendar, Gmail, Netlify, APIFY, Kairogen, HighLevel (subconta oficial produção + subconta lab Grok), Automations.

## MCPs
- Firecrawl V3: Alexandria (descoberta grátis, dados tipados Receita/imóveis/vagas/cotações). Plugin Grok Bot instala CLI + 10 skills no computador do bot — camada por cima do MCP, não substituto.
- useapi.net: Gemini Ultra (conta Flow) + NotebookLM (conta Flow separada). Pendente: token validado.

## Leis executáveis (versionadas, Cortex Lab)
- Lei 8: pós-contemplação Disal. Categoria = crédito + taxa ADM. Saldo devedor − lance total − 1ª parcela light, ÷ (prazo − 1). Seguro 0,08168% fora.
- Constituição de 7 leis: regras executáveis versionadas e mutáveis em runtime.
- Violação: alerta sem bloqueio, Wagner arbitra.

## Dados
- Cofre: 57.239 contemplações append-only. Tabela fato: ~70 grupos ativos Clique Vendas. Job semanal: scrap filtra ativos, calcula estatísticas.
- Runtime nunca toca o cofre.
- RAG: HNSW no Postgres, filtro por metadados antes da similaridade, poda por score.
- Aprendizado mora no banco (embeddings + score + metadados), não na memória da IA.

## Casca voz
- LiveKit (WebRTC) + bridge Twilio/Zenvia Voz. Thread WhatsApp + controle de áudio na mesma tela. Botão assumir silencia IA.
- Avaliados: Nemotron 3.5 Transcribe (30B, 2,8% erro) e Nemotron 3 VoiceChat (11B, ~450ms latência) pra upgrade.
- Voz: aviso gravação + opt-in textual LGPD. Áudio bruto → Whisper → texto antes do modelo.

## API
- Grok 4.7: $2 entrada/$6 saída por milhão tokens. Atendimento completo voz ~30-60k tokens, <R$1. Créditos pré-pagos console.x.ai.

## Bug conhecido
- Indexação celular→desktop falha desde 09/11. Memória via edit_memory é o elo confiável. Workaround: "grava" no fim de cada conversa densa.