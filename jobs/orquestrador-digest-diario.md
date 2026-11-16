# Job: orquestrador-digest-diario

- Skill: `skills/orquestrador-digest-diario/SKILL.md` (biblioteca: `/home/box/agent-data/workflows/orquestrador-digest-diario/SKILL.md`)
- Executor: Refatorador de Skills (Grok Bot), rotina "Orquestrador: digest diário"
- Agenda: dias úteis, ~08:00 America/Bahia (janela flexível ±15 min), cron `0 8 * * 1-5`
- Fontes (só leitura):
  - Auditoria mais recente: `/workspace/lifecycle_2026-11-15_v2.md` (re-auditoria 15/11/2026); usa a mais nova se aparecer
  - Commits de descrição v2: `/workspace/lifecycle/commits_2026-11-15.md` e `bots/` deste repo
  - Linear: workspace cortexconecta, time Conecta (CON)
- Destino: DM no Slack para o Wagner (user U0AKC556YTS). Escolha: digest só propõe, então não vai pra canal da empresa.
- Falha de Slack/Linear: não gera digest; avisa em uma linha no chat do Grok Bot qual ferramenta bloqueou.
- Regra dura: só propõe. Não cria/comenta/move issue, não manda mensagem a bot, não altera descrição/rotina/skill.
- Criado: 15/11/2026 (America/Bahia), pedido t27u/t28u do Wagner.
