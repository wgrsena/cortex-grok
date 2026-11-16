---
name: orquestrador-digest-diario
description: >-
  Use uma vez por dia (ou quando pedirem o digest do orquestrador) para cruzar
  os scores da auditoria de 30 dias mais recente com as pendências abertas no
  Linear e o estado de Os Quatro no Drive e propor a fila de quem deveria estar
  trabalhando e não está. Só propõe; nunca executa.
---
# Orquestrador: digest diário

Regra dura: só propõe. Nunca envia mensagem a bot, cria, comenta ou move issue, altera descrição, rotina ou skill. O único envio permitido é o próprio digest, no destino que a rotina nomear. A saída é uma fila para o dono decidir.
Regra anti-ruído: todo dado cita a fonte (arquivo da auditoria, id/URL da issue no Linear, commit, id de mensagem). Sem fonte, `unknown`. Não estime, não complete números de memória nem do pedido de alguém: o arquivo da auditoria manda.

## 1. Auditoria mais recente
- Localize a auditoria mais recente feita com `auditing-a-bot-at-30-days` / `bot-lifecycle-decision` (o caminho vem da rotina; senão, procure no repositório de skills/bots do dono e no box). Registre caminho e data.
- Por bot extraia: nome, score (Quiet/Noisy/Very noisy) com taxa, decisão, motivo de desalinhamento e status (ativo/inativo). Bot com `[INATIVO]` no nome ou marcado como desligado vai para `Ignorados`.
- Alinhamento: `desalinhado` se a auditoria apontou descrição ≠ comportamento; se houver commit de descrição nova do bot depois da data da auditoria, escreva `refatorado em <data> (<sha curto>)`; sem dado, `unknown`.
- Se a auditoria tiver mais de 35 dias, avise no topo: `auditoria vencida`.
- Conte os scores a partir do arquivo e mostre o total por score.

## 2. Pendências abertas no Linear
- Use o connector Linear (se pedir sign-in, avise o dono; não use navegador). Liste issues do time indicado com estado não concluído/cancelado: id, título, responsável, labels, estado, última atualização, URL.
- Associe issue a bot por responsável, label ou nome do bot no título/descrição. Sem associação clara, vai para `Sem dono`.

## 3. Sinal de atividade
- Só para bot com pendência associada: última atividade real (transcrição do bot, último commit ou última mensagem). Data e fonte, ou `unknown`.

## 3b. Os Quatro (Drive, só leitura)
- O ciclo é Sócrates → Tácito → Tales (Tales também faz o confronto com o portfólio e grava na Fila de Prioridade; Narciso está inativo desde 15/11/2026). O gatilho único do ciclo é a automação externa `os-quatro-ciclo-diario` (07:00 America/Bahia); não proponha nem crie outro gatilho.
- Com o connector do Google Drive, liste a pasta `Os Quatro`. Formato real (conferido em 16/11/2026): um diário único por dia, `os_quatro_<AAAA-MM-DD>_diario.md`, com seções `## <Bot> — ...`, e `os_quatro_fila_prioridade.md`, que pode ter várias cópias (use a de modificação mais recente). Para cada bot (Sócrates, Tácito, Tales), a última data é a do diário mais recente que tem uma seção `## <Bot>` (leia até os 5 diários mais recentes); para a Fila de Prioridade, a modificação da cópia mais recente. Converta para o fuso do dono e dê o link. Sem seção do bot nos diários lidos, `unknown`.
- `ciclo parado`: bot de Os Quatro sem arquivo novo há mais de 48h. Entra na Fila (seção 4) com proposta de uma frase (ex.: conferir se a automação das 07:00 rodou). Fim de semana conta no relógio, mas diga se o intervalo cobre sábado/domingo.
- Pasta não encontrada ou Drive sem acesso: escreva o bloqueio em `Unknowns`; não invente data.

## 4. Fila: quem deveria estar trabalhando e não está
Entra o bot ativo com ≥1 pendência associada E sem atividade nas últimas 48h (ou issue sem atualização há >7 dias), e todo bot de Os Quatro marcado `ciclo parado` na seção 3b.
Ordem: 1) segurança (dado pessoal, chave/segredo, ação jurídica) primeiro; 2) efetividade: Quiet, depois Noisy, depois Very noisy; 3) desempate: issue mais antiga sem atualização.
Bot Very noisy com pendência: não sugerir retomar; sugerir revisar escopo (`bot-lifecycle-decision`).

## 5. Saída (português, sintético, formatada para chat)
```
Digest <data> (<fuso>) — só propostas, nada foi executado
Auditoria: <caminho> de <data> [vencida?] | <n> Quiet, <n> Noisy, <n> Very noisy
Linear (<time>): <n> issues abertas, <n> ligadas a bot

Fila (quem deveria estar trabalhando e não está):
1. <bot> — <issue> (<URL>) — parado desde <data> (<fonte>) — <score> — proposta: <uma frase>
(ou: fila vazia)

Painel por bot:
<bot> — <score taxa> — <alinhamento> — pendência: <issue ou "nenhuma">
...
Os Quatro: Sócrates <data> | Tácito <data> | Tales <data> | Fila de Prioridade <data> — <ok ou "ciclo parado: bot(s)">
Sem dono: <issues sem bot>
Ignorados: <bots inativos>
Unknowns: <o que não deu pra verificar>
```
Termine sem executar nenhuma proposta; o dono aprova item a item.
