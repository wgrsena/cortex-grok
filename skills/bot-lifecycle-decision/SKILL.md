---
name: bot-lifecycle-decision
description: >-
  Use depois da auditoria de 30 dias (auditing-a-bot-at-30-days) para propor,
  bot a bot, manter, refatorar, desligar ou criar um bot, e para tirar do loop
  assuntos travados. Só propõe; o dono aprova.
---
# Decisão de ciclo de vida de bots

Trava dura: esta skill SÓ PROPÕE. Nunca desliga, cria, edita perfil, reescreve skill, pausa rotina nem manda tarefa a outro bot por conta própria. A execução só acontece depois de aprovação explícita do dono, item a item.

Aplica `verifying-sources-before-emitting`: toda evidência tem fonte (id de mensagem, transcrição, arquivo, commit) e data, ou sai `unknown`. Sem evidência com fonte, a decisão é `sem base` e não é proposta.

## 1. Entradas
- Resultado da `auditing-a-bot-at-30-days` de cada bot: score (Quiet/Noisy/Very noisy), taxa, total, calibração (alinhada/desalinhada) e correção proposta. Use só auditorias da janela atual; auditoria ausente = `unknown`.
- Data da última atividade real de cada bot (tarefa executada, saída produzida, rotina que fez algo). Mensagens de saudação ou de rotina sem resultado não contam.
- Dores documentadas (Drive, repo, conversas) que nenhum bot atual cobre.
- Histórico das rodadas anteriores desta skill (as propostas e vereditos passados), para a trava anti-loop.

## 2. Trava anti-loop (rode primeiro)
Para cada assunto (bot ou dor) com 2 rodadas seguidas sem veredito novo do dono, ou com a mesma proposta repetida sem mudança de evidência:
- Tire o assunto do loop. Não gere a terceira proposta.
- Leve direto ao dono com as duas posições lado a lado (ex.: proposta da skill vs. posição do bot ou de quem discordou), cada uma com sua evidência e fonte, e a pergunta de decisão em uma frase.

## 3. Critérios de decisão (ordem de precedência)
1. **Sem atividade real por 30+ dias** ou **Very noisy** → `propor desligamento`.
2. **Noisy** com calibração **desalinhada** → `mandar pro Refatorador` (refatoração de descrição e skills).
3. **Noisy** com calibração **alinhada** → `manter e reauditar` na próxima janela (o ruído vem do comportamento, não da descrição).
4. **Quiet** com calibração **desalinhada** → `mandar pro Refatorador`.
5. **Quiet** com calibração **alinhada** → `manter`.
6. **Dor documentada sem bot** (gap de capacidade) → `propor criação`. Só com a dor com fonte e depois de checar que nenhum bot atual a cobre, nem com uma refatoração.
7. Auditoria ausente ou dado essencial `unknown` → `sem base: auditar primeiro`.

Amostra pequena (marcada na auditoria) nunca sustenta desligamento sozinha: vira `manter e reauditar`, salvo inatividade comprovada.

## 4. Saída (português, sintético)
Uma linha por bot ou dor, em tabela:

| Bot | Score atual | Decisão proposta | Motivo (1 frase) | Evidência com fonte |
|---|---|---|---|---|

Decisões possíveis: `manter`, `manter e reauditar`, `mandar pro Refatorador`, `propor desligamento`, `propor criação`, `sem base: auditar primeiro`, `fora do loop: decisão do dono`.

Depois da tabela:
- **Fora do loop:** cada assunto travado com as duas posições lado a lado.
- **Aguardando aprovação:** lista do que precisa do ok do dono. Nada é executado antes disso.
- **Unknowns:** o que não deu pra verificar.

## 5. Depois da aprovação
Execute só o item aprovado, exatamente como aprovado, e registre a decisão (data, item, veredito do dono) para que a próxima rodada da trava anti-loop a enxergue.
