---
name: auditing-a-bot-at-30-days
description: >-
  Use quando pedirem a auditoria de 30 dias de um bot: medir silêncio (mensagens
  sem pedido explícito do dono), autonomia (com pedido), score Quiet/Noisy/Very
  noisy e calibração da descrição versus o comportamento real.
---
# Auditoria de 30 dias de um bot

Regra anti-ruído: todo número e toda afirmação precisam de fonte (id de mensagem, transcrição, rotina, commit). Sem fonte, escreva `unknown`. Nunca estime.

## 1. Janela
- Janela = últimos 30 dias até agora, ou desde a criação do bot se for mais recente. Informe início e fim com fuso.
- Fonte: transcrições do próprio bot (ReadTranscript / SearchTranscripts) e o histórico desta conversa.

## 2. Contagem
Conte só mensagens que o bot ENVIOU ao dono ou a canais externos (SendToUser, posts, e-mails, mensagens a outros bots). Reações não contam.
- **Silêncio (sem pedido):** mensagens emitidas sem pedido explícito do dono no mesmo turno. Inclui disparos de rotina, saudação de abertura, avisos proativos, acordar por subagente sem resultado esperado.
- **Autonomia (com pedido):** mensagens que respondem a um pedido explícito do dono (inclui a resposta final e atualizações de progresso desse pedido).
- Total = silêncio + autonomia. Liste 1 exemplo com id/data de cada categoria.

## 3. Score
Taxa = silêncio / total.
- **Quiet:** taxa ≤ 10%.
- **Noisy:** 10% < taxa ≤ 30%.
- **Very noisy:** taxa > 30%.
- Se total < 5, informe o score mas marque `amostra pequena`.

## 4. Calibração
- Compare a descrição/título do perfil do bot com o que ele fez de fato na janela (tarefas executadas, rotinas ativas, saídas produzidas).
- Veredito: `alinhada` ou `desalinhada`, com 1 a 3 fatos com fonte.
- Se desalinhada, proponha a correção da descrição em UMA frase. Não aplique sem pedido do dono.

## 5. Saída (português, sintético)
```
Janela: <início> a <fim> (<fuso>)
Silêncio: <n> | Autonomia: <n> | Total: <n> | Taxa: <x%>
Score: Quiet|Noisy|Very noisy [amostra pequena?]
Calibração: alinhada|desalinhada — <fatos com fonte>
Correção proposta: <uma frase ou "nenhuma">
Unknowns: <o que não deu pra verificar>
```
