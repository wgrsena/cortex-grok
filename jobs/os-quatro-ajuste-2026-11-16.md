# Os Quatro + orquestrador: crítica e ajuste proposto (16/11/2026)

Fonte: descrições atuais dos bots (/home/box/agent-data/agents/<id>/profile.json, lidas em 16/11/2026 01:15 America/Bahia), rotina "Orquestrador: digest diário" e skill orquestrador-digest-diario v2 (commit 5e6a8ea).

## Crítica
1. O ciclo não tem saída. Narciso (inativo desde 15/11/2026) era o único que gravava na Fila de Prioridade (Drive, pasta Os Quatro). Hoje ideia que o Tales manda "avança" não tem destino escrito.
2. O ciclo não tem entrada. Sócrates "roda só quando o Wagner aciona, até haver rotina diária"; nenhum dos quatro tem rotina. Sem acionamento manual, nada roda.
3. O orquestrador não enxerga Os Quatro. Ele cruza só Linear + scores; o estado de Os Quatro vive no Drive (diário de rejeições, Fila de Prioridade, arquivo do dia). Um ciclo parado não aparece no digest.
4. Loop de leitura quebrado: Sócrates lê a Fila de Prioridade antes de cada ciclo, mas ninguém mais escreve nela.
5. Único alerta autônomo é o do Tales (fila vazia > 7 dias), que nunca dispara se nada chega a ele.

## Ajuste proposto (não aplicado; precisa de "aplica" do Wagner)
A. Tales absorve o confronto do Narciso como último passo: ideia com veredito "avança" é confrontada com o portfólio do Wagner (Conecta Cortex, Giro Automotivo, Carne Maluca, sete leis, resolvedor, RAG). Compete = descarta com motivo no diário de rejeições; complementa = anota; território virgem = grava na Fila de Prioridade (só acréscimo, com fonte). Motivo da escolha: Tales já tem os números de mercado e é Quiet-adjacente no fluxo; evita um quinto salto e não reativa bot Very noisy.
B. Os Quatro vira "Os Três"; a descrição do Narciso continua inativa, com a nota de que a função foi para o Tales.
C. Orquestrador ganha uma seção "Os Quatro" no digest: data do último arquivo de Sócrates, Tácito e Tales e da última linha da Fila de Prioridade no Drive (só leitura); ciclo sem arquivo há mais de 48h entra na fila do digest como "ciclo parado". Continua só propondo.
D. Entrada do ciclo: decisão do Wagner (estratégia). Opções: manter manual, ou rotina diária do Sócrates em dia útil. Sem isso, o item C vai mostrar "ciclo parado" todo dia.

## Rotina do orquestrador
Ativa: "Orquestrador: digest diário", CRON_TZ=America/Bahia 0 8 * * 1-5, flexível ±15 min (servidor escolheu 08:09). Primeira execução: 16/11/2026 ~08:09. Destino: DM no Slack para U0AKC556YTS. Lê Linear cortexconecta/CON e /workspace/lifecycle_2026-11-15_v2.md. Nada falta para rodar; falha de Slack ou Linear vira uma linha no chat do Refatorador.
