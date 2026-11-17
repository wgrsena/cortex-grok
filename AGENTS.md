# AGENTS.md — cortex-grok

Instruções para agentes de IA trabalhando neste repositório.

## Estrutura

- `bots/` — descrições versionadas de cada bot (só DESCRIPTION.md, sem código)
- `skills/` — skills versionadas (SKILL.md + CRITERIA.md quando houver)
- `inteligencia-mercado/` — pesquisas e dossiês de mercado (Konq, concorrentes)
- `jobs/` — specs de jobs agendados e automações
- `MAPA/` — mapa executivo, operacional e técnico do Cortex
- branches `cortex/*` — trabalho de código do Cortex Build
- branches `skill/*` — trabalho de skills
- branches `midas/*`, `tooling/*`, `docs/*` — frentes isoladas

## Regras

1. Toda skill nova vai em `skills/<nome>/SKILL.md` versionado.
2. Todo bot novo ganha pasta em `bots/<nome>/DESCRIPTION.md` antes de ser criado.
3. Pesquisa de mercado vai em `inteligencia-mercado/` com data no nome: `AAAA-MM-DD · assunto.md`.
4. Não commitar segredo, token, CPF ou dado pessoal.
5. Branch de feature: `<eixo>/<assunto>` (ex.: cortex/motor-oportunidade).
6. PR em draft até teste passar; merge só com verde.
7. Este repo é do Grok: escrita livre. CONECTACORTEX (Claude/Codex) é só leitura.
