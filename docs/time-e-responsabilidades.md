# Time e responsabilidades

Regra geral: **só o Cortex Build commita, e só com aprovação do Wagner**. Ninguém envia e-mail/mensagem sem cartão de rascunho. Mudança de arquitetura: para e avisa.

| Papel | O que faz | O que NÃO faz |
|---|---|---|
| **Arquimedes Disal** (compilador, id `7e195838-…`) | Lê a coleta, aplica as regras Disal, entrega tabela ranqueada em branch separada com diff | Comercial; push no GitHub; disparar cartaz sem escolha do Wagner |
| **Comercial** (futuro) | Vende | Calcular regra Disal |
| **Marketing** (futuro) | Cria cartazes/peças dos grupos que o Wagner escolheu | Escolher grupo; renderizar grupo não escolhido |
| **Cortex Lab** | Visão geral; evita contradição de regras entre bots e repos; absorve compliance/playbook | Escrever código de produção; alterar os repos originais (conecta-sdr, conecta-captacao) |
| **Cortex Build** (id `7ae7940b`) | Código; **único que commita**, só com aprovação do Wagner; mantém o README vivo | Commitar sem aprovação; instalar dependência sem perguntar; deploy em produção sem confirmação; mexer fora de `conecta-cortex` |
| **Cortex Reviewer** (id `0a435370-ffed-4e02-909f-b602003dbd29`) | Revisa o diff | Commitar; alterar o código revisado |
| **VSL Cortex** | Corta a VSL | Regra de consórcio; comercial |
| **MiroFish Cortex** | Simula enxame (cenários, relay de decisões) | Substituir a decisão do Wagner |
| **Sócrates / Tácito / Tales / Narciso** (Os Quatro) | Perspectivas de análise/debate | Executar ou commitar |
| **Vigilante LGPD** | Vigia consentimento, retenção e voz opt-in | Bloquear atendimento (compliance = alerta com registro; o Wagner arbitra) |
| **Filtro** | Intermediário voz → Ara | Decidir; guardar voz sem opt-in específico |
| **Grok Bot** | Genérico (pesquisa, apoio) | Papéis acima; ações externas sem aprovação |

*Observação:* a descrição de Sócrates/Tácito/Tales/Narciso, Filtro e Vigilante LGPD é inferida só pelos nomes e pelo contexto de LGPD do repo; **confirmar com o Wagner**.
