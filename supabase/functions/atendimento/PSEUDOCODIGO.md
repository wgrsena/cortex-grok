# Pseudocódigo – Edge Function `atendimento`

Não é código executável nem foi testado. Serve de contrato para a implementação (TypeScript/Deno).
Esquema das tabelas: `supabase/migrations/0001_init.sql`, `0002_fato_rag.sql` e `0003_fracao_embutido_mediana.sql` (percentuais em fração 0..1).

> **Revisão do Cortex Reviewer (01/11/2026):** o passo 5 estava defasado (consultava `grupos_disal` direto e citava a "faixa ideal 65–85%"). O motor Disal agora é o **serviço solver v1.1** (`solver/app.py`), que lê só a tabela fato (`fato_cotas`/snapshot). A Edge Function chama o serviço; não refaz regra.

## Fluxo
```
POST /atendimento   (webhook do BSP: 360dialog ou Zenvia)

1. RECEBER E VALIDAR
   - validar assinatura/segredo do webhook (TODO: formato depende do BSP escolhido)
   - ignorar eventos que não são mensagem de cliente (status, entrega, leitura)
   - responder 200 rápido; processar o resto sem estourar o timeout do webhook
   - extrair: wamid, telefone E.164, texto/mídia, referral do anúncio (id_criativo)

2. IDEMPOTÊNCIA
   - INSERT em mensagens(wamid UNIQUE, direcao='entrada', ...) ON CONFLICT DO NOTHING
   - se já existia -> encerrar (reentrega do BSP)

3. LEAD
   - upsert em leads por telefone; gravar id_criativo / id_influencer na 1ª vez (não sobrescrever)
   - achar ou abrir atendimento aberto (janela de 24h)

4. CONSENTIMENTO LGPD
   - buscar consentimentos_lgpd vigente (tipo='atendimento_whatsapp', concedido, sem revogação, retencao_ate futura)
   - se NÃO há: enviar mensagem de 1º contato com aviso + pedido de aceite (texto versionado);
     registrar; NÃO chamar a IA; encerrar. Aceite do cliente -> grava consentimento e segue.
   - se cliente pediu "parar"/revogar -> registrar revogação, confirmar, encerrar
   - voz: tipo='voz_biometria' exige opt-in próprio; nunca inferir do consentimento de texto

5. CONTEXTO
   - histórico: últimas N mensagens do atendimento (resumir o que for antigo)
   - criativo: criativos/influencers do lead (promessa do anúncio, para coerência)
   - RAG: embedding da mensagem -> top-k em rag_embeddings (TODO: modelo de embedding e dimensão)
   - motor Disal (interno): chamar o serviço solver v1.1 (backend; header `X-API-Token` lido de segredo da
     Edge Function, nunca no código):
        POST /probabilidade  (Função 2; recurso_proprio = 0 -> ramo lance fixo)
        POST /combinacoes    (Função 1)
     o solver usa os flags do catálogo (`tem_lance_fixo`, `pct_embutido_max`, fração 0..1) – nunca número de grupo
     -> usa os campos v1.1 da resposta: `mediana_lance_livre`, `embutido_cobre_mediana`, `desatualizada`,
        `prazo_entrada`, `assembleia_aplicavel`, `prazo_vencido`, `motivo_assembleia_aplicavel`, `datas_invalidas`
     -> gera `dossie_interno` {grupo, mediana, embutido_cobre_mediana}  (NÃO vai no prompt; % só na apresentação)
     - faixa ideal 65–85% da idade (view `grupos_disal_faixa`): MANTIDA (01/11/2026, sem evidência de descarte;
       ver solver/NOTAS_DUVIDAS.md). Não entra no solver v1.1
     -> gera `sinal_escassez` genérico, sem código de grupo nem mediana (vai no prompt)

6. CHAMAR O GROK (stateless)
   - system prompt = playbook Centauro (comercial, lidera, cria curiosidade, escassez real,
     não revela grupo/mediana/embutido, "segura o cartão")
   - + histórico + RAG + sinal_escassez + tools permitidas
   - tratar timeout/erro: 1 retry; depois mensagem de contingência e alerta ao Wagner
   - registrar tokens e custo por mensagem (para medir o custo real)

7. COMPLIANCE DE SAÍDA (alerta, NÃO bloqueia)
   - aplicar leis vigentes (leis_compliance, regex versionadas) sobre a resposta
   - incluir checagem de vazamento: códigos de grupo (6 dígitos), "mediana", "embutido"
   - para cada acerto: INSERT em alertas_compliance (regra, versão, trecho, severidade)
   - a resposta segue; Wagner arbitra depois
   - PENDENTE: vazamento de dado técnico deveria bloquear? (decisão do Wagner)

8. ENVIAR
   - enviar via BSP; gravar mensagens(direcao='saida', wamid do BSP, tokens, custo)
   - falha de envio: reenfileirar com limite; alertar

9. HANDOFF (lead quente)
   - critério (TODO definir com Wagner): intenção de compra + perfil + prazo, ou pedido de falar com humano
   - gravar handoffs {lead, grupo, mediana, embutido_cobre, resumo}
   - notificar Wagner/vendedor com o dossiê; criar/atualizar negócio no HubSpot (TODO)
   - marcar leads.status='em_handoff'; a IA para de responder sozinha (ou só acolhe)
   - o vendedor revela os dados técnicos ao cliente no momento certo

10. LOG
   - atualizar atendimentos (último evento, status, ultima_mensagem_em)
   - venda fechada (fora deste endpoint): vendas com id_criativo, id_influencer, id_grupo
```

## Regras de negócio que não podem vazar para o código
- Nada de `if grupo == '003300'`. Exceções sem lance fixo (003300, série 004100–004104, 006207) são **dados** em `grupos_disal.tem_lance_fixo = false`.
- Todo lance acima da categoria = crédito + taxa (campo `base_lance` nos resultados).
- Mediana menor ou igual ao embutido máximo = contemplação sem desembolso (`embutido_cobre_mediana`, calculado no solver, não no prompt).

## TODOs
- Segredo/assinatura do webhook por BSP.
- Modelo de embedding e dimensão (a migration assume 1536 como placeholder).
- Fila/reprocessamento (pgmq ou tabela de pendentes) se o timeout da Edge Function apertar.
- Texto jurídico do consentimento (revisão jurídica) e prazo de retenção.
- Porte do `compliance.mts` do conecta-sdr para regras no banco (sem tocar naquele repositório).
