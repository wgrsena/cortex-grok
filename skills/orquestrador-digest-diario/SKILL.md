---
name: orquestrador-digest-diario
description: >-
  Use uma vez por dia (ou quando pedirem o digest do orquestrador) para cruzar
  os scores da auditoria de 30 dias mais recente com as pendências abertas no
  Linear e propor a fila de quem deveria estar trabalhando e não está. Só
  propõe; nunca executa.
---
# Orquestrador: digest diário

Regra dura: só propõe. Nunca envia mensagem a bot, cria ou move issue, altera descrição, rotina ou skill. A saída é uma fila para o dono decidir.
Regra anti-ruído: todo item da fila cita a fonte (arquivo da auditoria + linha/bot, id ou URL da issue no Linear, id de mensagem). Sem fonte, `unknown`. Não estime.

## 1. Auditoria mais recente
- Localize a auditoria mais recente feita com `auditing-a-bot-at-30-days` / `bot-lifecycle-decision` (arquivo versionado no repositório de skills/bots do dono ou no box). Use a data no nome ou no conteúdo; registre caminho e data.
- Por bot extraia: nome, id, score (Quiet/Noisy/Very noisy), taxa, total de mensagens, status (ativo/inativo), veredito de calibração.
- Bots marcados como inativos ficam fora da fila (só listados em `Ignorados`).
- Se a auditoria tiver mais de 35 dias, avise no topo: `auditoria vencida`.

## 2. Pendências abertas no Linear
- Use o connector Linear (se pedir sign-in, peça ao dono pelo fluxo de autenticação; não use navegador). Liste issues não concluídas (estados não Done/Canceled), com: id, título, responsável/label do bot, estado, data de atualização, URL.
- Associe issue a bot por responsável, label ou nome do bot no título. Sem associação clara, vai para `Sem dono`.

## 3. Sinal de atividade
- Para cada bot com pendência, verifique a última atividade real (ReadTranscript/SearchTranscripts do bot, último commit ou última mensagem enviada). Registre data e fonte.

## 4. Fila: quem deveria estar trabalhando e não está
Entra na fila o bot ativo que tem ≥1 pendência aberta associada E nenhuma atividade nas últimas 48h (ou issue sem atualização há >7 dias).
Ordene por:
1. Segurança: pendência que envolve dado pessoal, chave/segredo ou ação jurídica vem primeiro (trava dura).
2. Efetividade: score Quiet antes de Noisy antes de Very noisy (bot que entrega com pedido é o melhor candidato a retomar).
3. Desempate: issue mais antiga sem atualização.
Bot Very noisy com pendência: não sugerir retomar; sugerir revisar escopo (aponta `bot-lifecycle-decision`).

## 5. Saída (português, sintético)
```
Digest <data> (<fuso>) | Auditoria: <caminho> de <data> [vencida?]
Fila:
1. <bot> — <issue id + título> (<URL>) — parado desde <data> (<fonte>) — score <x> — proposta: <uma frase>
...
Sem dono: <issues sem bot associado>
Ignorados: <bots inativos com pendência>
Unknowns: <o que não deu pra verificar>
```
Se a fila estiver vazia, diga `fila vazia` em uma linha. Termine sem executar nenhuma proposta; o dono aprova item a item.
