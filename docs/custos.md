# Custos – pesquisa de preços (Conecta Cortex)

**Data da consulta:** 26/10/2026. Preços mudam; reconferir antes de contratar.
**Regra:** nada foi inventado. Onde não achei o dado, está escrito **"não encontrado"**.

**Câmbio usado nas conversões (estimativa, não é cotação de contratação):**
- US$ 1 = R$ 5,5007 (PTAX venda BCB, 26/10/2026 – via busca; fonte: https://ptax.bcb.gov.br/ptax_internet/consultarUltimaCotacaoDolar.do)
- € 1 = R$ 5,6422 (PTAX venda do euro de 23/10/2026, a última publicada na consulta; fonte: https://ptax.bcb.gov.br/ptax_internet/conversaoDeMoedas.do?method=exibirFormularioConversaoMoedas, via busca)
- Valores em R$ convertidos por mim estão marcados "≈". Impostos, IOF e spread de cartão **não** estão incluídos.

---

## 1. Correção importante da premissa

A premissa "serviço após 1.000 conversas gratuitas/mês a R$ 0,006 no Brasil" está **desatualizada/imprecisa**:

- Desde 01/07/2025 a Meta cobra **por mensagem entregue**, não por conversa.
- Desde **01/10/2026** (tabela em BRL "effective October 1, 2026"), mensagens de *serviço* (resposta dentro da janela de 24h) têm **1.000 grátis por número/mês** e, depois, **R$ 0,035 cada**.
- Marketing: **R$ 0,3217** por mensagem. Utilidade e autenticação: **R$ 0,035**.
- O R$ 0,006 não aparece na tabela atual. Parece mais um valor em US$ (utilidade ≈ US$ 0,0068 ≈ R$ 0,037) confundido com R$.

Fonte oficial: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing (tabela BRL linkada na página, em planilha). Consulta 26/10/2026.
Mensagens do cliente para a empresa, mensagens não entregues e a janela de 72h de anúncios Click-to-WhatsApp (entry point) são grátis.

A estimativa "~R$ 300/mês" do stack Frankenstein também **não fecha** (ver seção 4): só as mensalidades das camadas já passam de ≈ R$ 570 (enxuto) e chegam a ≈ R$ 1.670 (com respond.io Growth), antes de Meta e Grok.

---

## 2. Preços por fornecedor

### 2.1 Meta (taxa repassada por todo BSP)
| Item | Valor | Fonte |
|---|---|---|
| Marketing (BR) | R$ 0,3217 / msg | página oficial acima |
| Utilidade / Autenticação (BR) | R$ 0,035 / msg | idem |
| Serviço (BR) | 1.000 grátis/número/mês, depois R$ 0,035 | idem |
| Faixas de volume (utilidade/autenticação) | a partir de 250 mil msgs/mês – **não reconferido na Meta**, veio de https://www.flowcall.co/blog/whatsapp-business-api-pricing | secundária |
| Ligação WhatsApp (Calling) no Brasil | **não encontrado** | – |

### 2.2 360dialog (BSP)
- Planos por número/mês: **Regular € 49 (US$ 59)** ≈ R$ 276; Premium € 99 (US$ 119) ≈ R$ 559; Higher Throughput € 249 (US$ 299); Scale € 500; Marketplace € 99.
- Taxas da Meta repassadas **sem markup**. Marketing enviado pelo endpoint padrão (e não pela Marketing Messages API) tem **+7%**.
- Cobrança só em EUR/USD (**não encontrado** em BRL).
- ⚠ Inconsistência: a documentação diz que serviço é cobrado como utilidade; a calculadora diz que as primeiras 1.000 de serviço são grátis (a Meta confirma as 1.000 grátis). Confirmar com o comercial.
- Fontes: https://360dialog.com/pricing e https://docs.360dialog.com/docs/get-started/pricing

### 2.3 Zenvia (BSP brasileira, cobra em R$)
- Plataforma: Starter R$ 0; Specialist R$ 600; Expert R$ 1.800; Professional R$ 3.900 por mês.
- Pacote de canais obrigatório a partir de R$ 100/mês. Setup R$ 649 (R$ 1.999 / R$ 3.999 nos planos maiores).
- No pacote de R$ 100: template WhatsApp **R$ 0,55**; mensagem de serviço **R$ 0,069** (1.000 primeiras grátis); chamada WhatsApp **R$ 0,0950/min**; SMS R$ 0,10.
- Comparando com a Meta: template ≈ +71%, serviço ≈ +97%. Pacotes maiores podem baixar as tarifas (**não encontrado** o detalhe).
- API de Voz (Torpedo de Voz): **não encontrado – tarifa sob consulta**.
- Desconto de 20% no software para contas fechadas até 31/10/2026: só em fonte secundária (https://dmcompared.com/brazil/ferramentas/zenvia/), **não confirmado**.
- Fontes: https://zenvia.com/precos/ , https://zenvia.com/zoe/ , FAQ https://zenvia.movidesk.com/kb/en/article/600343/preguntas-frecuentes-nuevas-reglas-de-cobro-de-whatsapp-business , voz https://support.zenvia.com/kb/pt-br/article/294779/torpedo-de-voz
- Dúvida: se o plano Specialist permite receber mensagens por webhook (a página fala de "envio de mensagens" na API). **Verificar.**

### 2.4 respond.io (unificação de canais)
- Starter US$ 79/mês (anual) ou US$ 99 (mensal) ≈ R$ 435 / R$ 545.
- Growth US$ 159 / US$ 199 ≈ R$ 875 / R$ 1.095.
- Advanced US$ 279 / US$ 349 ≈ R$ 1.535 / R$ 1.920.
- Enterprise: sob consulta. Cobrança por contato ativo mensal (MAC); taxas do WhatsApp **não** incluídas. Excedente no Growth: US$ 12 por 100 MAC (valor lido na página; preço no Brasil em R$ **não encontrado**).
- A página lista **Webhooks e passo HTTP Request só no Advanced**; o Growth tem Developer API. Isso importa para o backend próprio (ver pendências).
- Fonte: https://respond.io/pricing

### 2.5 ManyChat (filtro de comentários)
- Free US$ 0 (limite exibido: 25); Essential US$ 14; **Pro US$ 29 (2.500 contatos)** ≈ R$ 160; Business US$ 69; Advanced US$ 139. Excedente no Pro: US$ 0,05/contato.
- O preço varia conforme o país de cobrança; valor em R$ **não encontrado**.
- Fonte: https://manychat.com/pricing

### 2.6 HubSpot (pipeline)
- **CRM grátis:** 2 usuários, 1.000 contatos, 10 propriedades personalizadas, com marca HubSpot (tabela Free × Starter da própria HubSpot).
- Starter: **US$ 20/usuário/mês**; promoção "por tempo limitado" US$ 7 (anual) ou US$ 10 (mensal) por usuário.
- A página de preços principal (https://www.hubspot.com/pricing/crm) **não carregou**; dados vindos de https://www.hubspot.com/products/crm/starter. Limites de API do plano grátis: **não encontrado**.

### 2.7 Twilio
- **WhatsApp** (página "as of September 2026"): US$ 0,005 por mensagem (entrada e saída) **+ taxa da Meta**; falha US$ 0,001. A página tem trecho contraditório sobre cobrança de serviço (pode estar desatualizada em relação à Meta de 01/10/2026). Fonte: https://www.twilio.com/en-us/whatsapp/pricing
- **WhatsApp Calling:** US$ 0,005/min + taxa de conectividade da Meta; valor do Brasil **não encontrado**.
- **Voz Brasil** ("as of August 2026"): saída fixo US$ 0,0310/min; saída celular US$ 0,0663/min; entrada fixo US$ 0,0100/min + número US$ 4,25/mês; SIP/BYOC US$ 0,0040/min; navegador/app US$ 0,0040/min; gravação US$ 0,0025/min; Media Streams US$ 0,0044/min; ConversationRelay US$ 0,07/min. Fonte: https://www.twilio.com/en-us/voice/pricing/br

### 2.8 LiveKit (voz em tempo real)
- Build US$ 0; **Ship US$ 50/mês**; Scale US$ 500/mês.
- Ship: 5.000 min de agente incluídos, depois US$ 0,01/min; SIP de terceiros US$ 0,004/min; conectores Twilio/WhatsApp US$ 0,004/min; 150 mil min WebRTC incluídos, depois US$ 0,0005/min.
- Estimativa da página para a pilha padrão: **US$ 0,0479/min** (LLM Grok 4.7 listado a US$ 0,0070/min). Retenção zero de dados disponível.
- Número de telefone brasileiro direto pela LiveKit: **não encontrado** (usaria SIP via Twilio/Zenvia).
- Fonte: https://livekit.io/pricing

### 2.9 Supabase
- Free US$ 0 (500 MB; pausa após 1 semana sem uso – **não serve para produção**).
- **Pro a partir de US$ 25/mês** ≈ R$ 138: 8 GB, 2 M invocações de Edge Function incluídas (depois US$ 2/M), crédito de computação US$ 10. Team US$ 599. PITR (backup ponto-no-tempo) US$ 100/mês.
- pgvector: **não confirmado nesta página**. Região São Paulo (LGPD/latência): **não verificada**.
- Fonte: https://supabase.com/pricing

### 2.10 Netlify (alternativa de backend)
- Free US$ 0 (300 créditos); Personal US$ 9 (1.000); **Pro US$ 20 (3.000 créditos)** ≈ R$ 110. Crédito ≈ US$ 0,00667.
- Fonte: https://www.netlify.com/pricing/

### 2.11 Grok API (custo variável da IA – item que não estava na lista)
- grok-4.7: US$ 2,00 entrada / US$ 0,50 entrada em cache / US$ 6,00 saída por 1 M de tokens (até 200k de contexto); acima disso US$ 4 / 1 / 12. Endpoint regional EUA ×1,1.
- Fonte: https://docs.x.ai/developers/pricing

---

## 3. Premissas dos cenários (hipóteses minhas, **ajustar com dados reais**)
| | Baixo volume | Campanha |
|---|---|---|
| Leads novos/mês | 300 | 5.000 |
| Respostas da IA por lead | 10 | 10 |
| Mensagens de serviço/mês | 3.000 | 50.000 |
| Templates de marketing/mês | 100 | 2.000 |
| Janela grátis de anúncio (72h) | ignorada (conservador) | ignorada (conservador) |
| Tokens por resposta do Grok | 6.000 entrada (sem cache) + 1.000 saída ≈ US$ 0,018 ≈ **R$ 0,099** | idem |
| ManyChat | 1 plano Pro | Pro + 500 contatos de excedente (US$ 25) |
| Número de WhatsApp | 1 | 1 |

Custo Meta: serviço = (mensagens − 1.000) × R$ 0,035; marketing = templates × R$ 0,3217.
Baixo: 2.000 × 0,035 + 100 × 0,3217 = **R$ 102**. Campanha: 49.000 × 0,035 + 2.000 × 0,3217 = **R$ 2.358**.
Grok: 3.000 × 0,099 = **R$ 297**; 50.000 × 0,099 = **R$ 4.951**.
Voz (fase 2) fica fora das tabelas; ver 3.1.

## 4. Comparativo de custo mensal (R$, ≈, câmbio do topo do documento)

| Camada | A) "Frankenstein" (360dialog + respond.io Growth + ManyChat Pro + HubSpot grátis + Supabase Pro) | B) Enxuto fase 1 (360dialog + ManyChat Pro + HubSpot grátis + Supabase Pro) | C) Zenvia (Specialist + Supabase Pro, sem ManyChat) |
|---|---|---|---|
| Canal/BSP fixo | 276 | 276 | 600 (+ setup único R$ 649) |
| respond.io | 1.095 (mensal) | – | – |
| ManyChat | 160 | 160 | – |
| HubSpot | 0 | 0 | 0 |
| Supabase Pro | 138 | 138 | 138 |
| **Fixo total (baixo volume)** | **≈ 1.668** | **≈ 574** | **≈ 738** |
| Mensagens (baixo) | Meta 102 | Meta 102 | Zenvia 193 (2.000×0,069 + 100×0,55) |
| Grok (baixo) | 297 | 297 | 297 |
| **TOTAL baixo volume** | **≈ 2.067** | **≈ 973** | **≈ 1.228** |
| Extras no cenário campanha | respond.io +4.000 MAC ≈ +2.640; ManyChat excedente ≈ +138 | ManyChat excedente ≈ +138 | – |
| Mensagens (campanha) | Meta 2.358 | Meta 2.358 | Zenvia 4.481 (49.000×0,069 + 2.000×0,55; tarifa do pacote R$ 100, sem desconto de volume) |
| Grok (campanha) | 4.951 | 4.951 | 4.951 |
| **TOTAL campanha** | **≈ 11.755** | **≈ 8.020** | **≈ 10.169** |

Observações:
- ManyChat no cenário campanha: US$ 25 ≈ R$ 138 de excedente (já incluído nos totais).
- Se for preciso webhook do respond.io, o Advanced custa US$ 349/mês ≈ R$ 1.920 (em vez de R$ 1.095 do Growth).
- Cenário A na campanha: o excedente de MAC estimado (US$ 12 por 100 MAC) pode ser menor com um plano de faixa maior; preço da faixa **não encontrado**.
- Em todos os cenários, **o maior custo é o Grok (tokens) e a Meta por mensagem**, não as ferramentas-casca. Cache de prompt e histórico resumido reduzem o Grok; anúncios Click-to-WhatsApp reduzem a Meta (janela de 72h grátis).
- Zenvia: C não inclui hipóteses de desconto por pacote maior nem o desconto de 20% (não confirmado).

### 4.1 Voz (fase 2, 300 min/mês de ligação – hipótese)
LiveKit ≈ US$ 0,0479/min + telefonia Twilio celular BR US$ 0,0663/min + SIP US$ 0,004/min ≈ US$ 0,118/min → 300 min ≈ US$ 35,5 ≈ **R$ 195**, mais o plano LiveKit Ship (US$ 50 ≈ R$ 275) se passar do uso do Build. Valores de Zenvia Voz e Ligação WhatsApp no Brasil: **não encontrado**.

## 5. Conclusões
1. Premissa de custo da Meta estava defasada: **R$ 0,035 por resposta após as 1.000 grátis** e **R$ 0,3217 por template de marketing**.
2. R$ 300/mês é irreal para a pilha Frankenstein: **≈ R$ 1.670 fixos** com respond.io Growth, **≈ R$ 574** sem respond.io, mais variáveis.
3. Provável economia na fase 1: dispensar respond.io até validar que o fluxo precisa dele (ver pendências).
4. Zenvia só compensa pelo faturamento em R$ com nota fiscal; a tarifa por mensagem é ≈ 2× a da Meta no pacote de R$ 100.
5. O custo do Grok por atendimento (≈ R$ 0,10 por resposta nas hipóteses) merece medição real no piloto.
