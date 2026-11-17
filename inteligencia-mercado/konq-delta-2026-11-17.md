# Konq — delta 2026-11-17 (gerador de link e pontuação dos forms)

Captura em **17/11/2026, 15:23** (páginas) e **15:25** (bundles JS públicos dos forms), horário de Brasília (America/Bahia, UTC-3).

Base: [inteligencia-mercado/dossie-konq-completo-2026-11-17.md](https://github.com/wgrsena/cortex-grok/blob/main/inteligencia-mercado/dossie-konq-completo-2026-11-17.md) (commit com SHA `fada329`, ~37 KB). Este arquivo traz só o que o dossiê pedia para aprofundar e o que ainda não estava especificado: o gerador de link como especificação do «link do parceiro», e a tabela completa de pontuação dos formulários (incluindo o de `forms.crm.finq.com.br`). O dossiê não foi editado.

Método: leitura do HTML e do JavaScript estático das páginas (GET HTTP). O gerador **não** foi aberto com `?gerar` nem usado para emitir link. Nenhum formulário foi preenchido. Nenhum endpoint de coleta, submit, planilha ou verificação foi chamado. Chaves, tokens e a URL do Apps Script não são reproduzidos.

Contas Firecrawl testadas neste turno: `user-Firecrawl` com saldo `-100` (inutilizável); `user-Firecraw-xai` com `1025` créditos restantes (plano 1000, ciclo 17/11/2026–17/12/2026). A captura usou GET HTTP, então **créditos Firecrawl gastos nesta varredura: 0**, abaixo do teto de 150.

Marcadores: **[confirmado]** (fato no HTML/JS, com link) e **[indício]** (leitura nossa).

---

## 1. Gerador de link para vendedores

Fonte: [https://konq.com.br/agenda-eduardo-ribeiro](https://konq.com.br/agenda-eduardo-ribeiro) — captura 17/11/2026, 15:23, America/Bahia. O modo `?gerar` só troca a vista para o cartão «Para vendedores / Gere o seu link de indicação»; o código do gerador está no mesmo HTML da página limpa. [confirmado]

### 1.1 Campos e validações do gerador

O formulário do gerador (seção `#vGen`, oculta até existir `?gerar`) tem estes campos. [confirmado]

| Campo (label) | id | Obrigatório | Validação no código |
|---|---|---|---|
| Link da sua agenda | `gAgenda` | Sim (sem ele o botão «Copiar link» fica desabilitado e o texto é «Cole o link da sua agenda para gerar.») | Precisa passar em `agendaValida`: protocolo `https:` e hostname em `forms.crm.konq.com.br`, `calendar.app.google`, `calendar.google.com`, `calendly.com`, `cal.com`, `outlook.office.com`, `outlook.office365.com`, `zcal.co` ou `tidycal.com` (ou um subdomínio desses). Senão: «Use o link de uma agenda do Google, Calendly, Cal.com, Outlook, Zcal ou TidyCal, começando com https://.» |
| Seu WhatsApp (opcional) | `gZap` | Não | Só entra no link se, depois de `digitos()` (só números; remove o prefixo `55` quando o restante tem 10 ou 11 dígitos), o comprimento for 10 ou 11. Caso contrário o parâmetro `zap` não é escrito. |
| Seu nome, como o cliente vai ver | `gNome` | Não para gerar o link | Se preenchido, vai para `nome`. Não há validação extra no gerador (na leitura do link, o nome é cortado em 60 caracteres). |
| Seu cargo (opcional) | `gCargo` | Não | Só vai para `cargo` se o texto existir **e** for diferente do cargo padrão da página (`Especialista de consórcio`). |
| Link da sua foto (opcional) | `gFoto` | Não | No gerador, só entra se começar com `https://`. Se houver valor que não começa assim, o link é gerado **sem** a foto e aparece: «O link da foto precisa começar com https://. O link foi gerado sem a foto.» |
| Seu link (saída) | `gOut` | — | Montado como `origem + pathname + ?` + query. O botão «Copiar link» copia essa string. |

Nota no rodapé do gerador: «Sem foto, a página mostra as iniciais do seu nome. O nome também identifica os seus contatos na planilha.» [confirmado]

A string gerada **não inclui** `ref`, `origem` nem UTMs. Só `agenda`, e, quando passam na validação, `zap`, `nome`, `cargo` e `foto`. [confirmado]

### 1.2 Parâmetros de URL que a página lê

Captura 17/11/2026, 15:23, America/Bahia, mesma fonte. [confirmado]

| Parâmetro | O que muda |
|---|---|
| `gerar` | Se presente (`qs.has("gerar")`), mostra a vista do gerador (`vGen`). Qualquer valor serve; a presença é que conta. |
| `agenda` | Substitui a agenda padrão (o formulário `forms.crm.konq.com.br/f/agenda-eduardo-ribeiro`). Se a URL falhar em `agendaValida`, a agenda fica vazia e o visitante vê «Este link está sem a agenda de quem te indicou…». |
| `zap` | WhatsApp do vendedor (10 ou 11 dígitos depois de `digitos`). Se inválido, o botão «Prefiro combinar pelo WhatsApp» permanece oculto. O padrão da página sem `zap` é vazio. |
| `nome` | Nome exibido do consultor/vendedor, limitado a 60 caracteres. Sem o parâmetro, vale o padrão «Eduardo Ribeiro». |
| `cargo` | Cargo exibido, limitado a 80 caracteres. Sem o parâmetro, vale «Especialista de consórcio». |
| `foto` | Foto do card. Na leitura (não no gerador), `fotoValida` aceita `https:` ou um endereço da mesma origem da página, e rejeita `javascript:`. Se inválida, é descartada. Se não houver foto válida e o nome for o padrão, a página usa a foto embutida do consultor padrão. |
| `ref` | Primeira fonte do identificador de indicação (`REF`). Ver 1.4. |
| `utm_source` | Segunda fonte de `REF`, se `ref` estiver ausente. Também é enviada, se presente, no pacote de UTMs do lead (abaixo). |
| `origem` | Terceira fonte de `REF`, se `ref` e `utm_source` estiverem ausentes. |
| `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` | Não entram no `REF`. Se existirem na URL, são copiados para o corpo do lead no CRM (e para o «toque») com o mesmo nome. |

A página também guarda, em armazenamento local, até 25 parâmetros de query cuja chave casa com `^[A-Za-z0-9_.\-\[\]]{1,64}$` (valor cortado em 300 caracteres). Isso é o rastreio de origem da visita, não o gerador. [confirmado]

### 1.3 Campos do lead enviados ao CRM e ao GTM (só os nomes)

Captura 17/11/2026, 15:23, America/Bahia, mesma fonte. Os destinos (endpoint de collect do CRM e planilha da equipe) existem no código; as URLs de coleta e a chave **não** são reproduzidas. Nenhum POST foi feito. [confirmado]

**No `dataLayer` (GTM), evento `lead_gerado`:** `event_id`; `lead.nome`; `lead.telefone`; `lead.origem`. Neste push, `lead.origem` recebe o valor fixo da LP (`lp-agenda-eduardo-ribeiro`), não o `REF`.

**No corpo enviado ao CRM (collect de lead), nomes dos campos:** `name`; `phone`; `lp_source`; `anonymous_id` (se existir o id da visita em `localStorage["konq:aid"]`); `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` (só os que vierem na URL); e, dentro de `extra_params`: `event_id`; `consultora`; `investimento`; `conhecimento`; `indicacao`.

**No «toque» do CRM (nomes):** `anonymous_id`; `landing_url`; `referrer`; as mesmas UTMs; e, em `extra_params`: `etapa`; `consultora`; `lp_source`. Valores de `etapa` vistos no código: `clicou_agendar`, `abriu_agenda`, `clicou_whatsapp`.

**Na planilha da equipe (nomes, função `dados()`):** `id`; `etapa`; `nome`; `whatsapp`; `investimento`; `conhecimento`; `ciente`; `dia`; `horario`; `origem`; `agenda`. Aqui o campo `origem` recebe `REF`, ou a string fixa `"indicacao"` se `REF` estiver vazio.

Há também um evento GTM à parte, `cta_formulario`, com o campo `cta_texto`. Não é o payload do lead.

### 1.4 Como o nome do vendedor vira o campo `indicacao`

Captura 17/11/2026, 15:23, America/Bahia, mesma fonte. [confirmado]

O gerador **não** escreve `ref` no link. Ele escreve `nome` (e os outros campos da tabela 1.2). Quando o visitante abre esse link, a página calcula:

```
REF = qs.get("ref") || qs.get("utm_source") || qs.get("origem") || (NOME ? slug(NOME) : "")
```

`NOME` já veio de `?nome=` (até 60 caracteres) ou do padrão da página. A função `slug` faz minúsculas, decompõe acentos (NFD), tira as marcas, troca qualquer sequência que não seja `[a-z0-9]` por hífen e remove hífens das pontas.

O valor `REF` é o que entra em `extra_params.indicacao` no collect do CRM (e em `origem` da planilha). Portanto, no fluxo normal do gerador (link só com `nome=…`, sem `ref`/`utm_source`/`origem`), `indicacao` é o **slug do nome do vendedor**, não o nome cru. Exemplo no código: um nome viraria um identificador tipo `nome-sobrenome`.

Se o link trouxer `ref`, `utm_source` ou `origem`, esses valores têm prioridade nessa ordem e o slug do nome não é usado.

O dossiê resumia isso como «o campo `indicacao` (nome do vendedor, ou `ref`/`utm_source`/`origem`)». A regra exata, no código, é a cadeia acima. [confirmado]

### 1.5 Eventos do GTM

Captura 17/11/2026, 15:23, America/Bahia, mesma fonte. Só o que o JavaScript estático coloca em `dataLayer.push`. [confirmado]

| Evento | Quando (no código) | Campos além de `event` |
|---|---|---|
| `lead_gerado` | Ao concluir o passo 1 da LP («Respondeu as perguntas»), junto com o envio do lead ao CRM. Uma vez por visita (`leadEnviado`). | `event_id`; `lead.nome`; `lead.telefone`; `lead.origem` (`lp-agenda-eduardo-ribeiro`) |
| `cta_formulario` | No clique de «Agendar com o consultor». | `cta_texto` com o literal «Agendar com o consultor» |

O `event: "gtm.js"` do snippet do container é o carregamento padrão do GTM, não um evento de negócio desta LP. Ids de container e de pixel já estão no dossiê e não são repetidos.

Os «toques» `clicou_agendar`, `abriu_agenda` e `clicou_whatsapp` vão ao CRM, não ao `dataLayer`. [confirmado]

Para a Conecta reproduzir o «link do parceiro»: a LP do parceiro precisa (1) gerar uma URL com a agenda permitida e o nome do parceiro; (2) na abertura, derivar um `indicacao` estável — no molde Konq, o slug do nome, salvo se `ref` / `utm_source` / `origem` já vierem no link; (3) gravar esse identificador no lead, com as UTMs e o id da visita, **antes** do agendamento. [indício] (leitura da especificação, não um fato novo da página)

---

## 2. Pontuação dos formulários do CRM

Fonte dos cinco HTML: captura 17/11/2026, 15:23, America/Bahia. Schema lido no payload Next.js embutido (`self.__next_f`). A fórmula que junta peso e pontos, e a nota de corte, foram procuradas também no bundle público `https://forms.crm.konq.com.br/_next/static/chunks/6633-782e66881b16bef9.js` (mesmo hash no domínio finq), capturado às 15:25. [confirmado]

**O que o cliente não calcula.** No bundle, `option_scores` e `weight` não aparecem. O front envia o payload para `/public/forms/{slug}/submit` (esse endpoint **não** foi chamado). Com `tier_routing_enabled`, o encaixe de consultor acontece depois do envio, no servidor. [confirmado]

**Nota de corte / regra de qualificação:** não há campo de corte, mínimo ou faixa de nota no JSON embutido nem no bundle público. **Não capturado:** a regra numérica, se existir, está no servidor. O que existe no payload é a flag `tier_routing_enabled` (true ou false) e os pesos/pontos por opção. [confirmado]

Nos quatro forms classic, `option_scores` da renda familiar ainda lista chaves antigas (`50k+`, `10-20k`, `20-35k`, `35-50k`, `ate-10k`) além das chaves das opções atuais. As linhas das tabelas abaixo usam só as opções visíveis e os pontos da chave correspondente. [confirmado]

Textos de agendamento (`chat_config`) são os mesmos nos cinco forms. [confirmado]

- Agendamento: título «Consultoria gratuita com especialista»; mensagem «Tudo pronto, {{first_name}}! Escolha o melhor horário pra sua conversa gratuita com um especialista KONQ.»
- Depois de marcar: título «Obrigado, {{first_name}}!»; «Agendado, {{first_name}}! O convite com o link da videochamada foi enviado para o seu e-mail. Vamos te lembrar pelo WhatsApp 1 hora antes.»
- Sem booking: «Recebemos suas respostas. Um consultor KONQ vai falar com você pelo WhatsApp.»

O `thank_you_text` do form (campo separado) varia e vai em cada bloco. CTA de thank-you: nulo nos cinco.

Para as escalas sem `options` no JSON, o bundle monta os ticks de `1` até `scoring.scale_max` (ou 5, se `scale_max` não existir). [confirmado]

### 2.1 `agenda-eduardo-ribeiro` (chat) — sem pontuação no schema

[https://forms.crm.konq.com.br/f/agenda-eduardo-ribeiro](https://forms.crm.konq.com.br/f/agenda-eduardo-ribeiro) — 17/11/2026, 15:23, America/Bahia. [confirmado]

- Título: «Diagnóstico de Consórcio». Modo `chat`. `thank_you_text`: «Obrigado!».
- `tier_routing_enabled`: **false**. Agenda pública no payload: reunião de 60 min, antecedência mínima 60 min, janela de 365 dias, disponibilidade de segunda a domingo, 08:00–21:00.
- Todos os seis campos têm `scoring: null`. Não há tabela de pontos neste form.

| Pergunta | Opção | Pontos | Peso |
|---|---|---|---|
| Nome completo | (texto) | — | — |
| WhatsApp | (telefone) | — | — |
| Seu nível de conhecimento | Nunca estudei / Sei o básico / Entendo como funciona / Já tive ou tenho cota / Uso como estratégia (`1`…`5`) | — | — |
| Interesse | Comprar meu primeiro bem; Alavancagem financeira; Alavancagem patrimonial; Ainda não sei, quero um diagnóstico | — | — |
| Investimento mensal | Até R$ 1 mil; R$ 1 mil a R$ 3 mil; R$ 3 mil a R$ 5 mil; R$ 5 mil a R$ 10 mil; Acima de R$ 10 mil | — | — |
| E-mail | (e-mail) | — | — |

### 2.2 `webnario-diario-eduardo-schroder-consultoria-patrimonial`

[https://forms.crm.konq.com.br/f/webnario-diario-eduardo-schroder-consultoria-patrimonial](https://forms.crm.konq.com.br/f/webnario-diario-eduardo-schroder-consultoria-patrimonial) — 17/11/2026, 15:23, America/Bahia. [confirmado]

- Título: «Consultoria Patrimonial». Modo `classic`. `thank_you_text`: «Reunião confirmada!». Descrição de pré-reserva de cotas (sem compromisso de aquisição), já citada no dossiê.
- `tier_routing_enabled`: **true**. Booking: 60 min, antecedência mínima 120 min, janela de 4 dias; `availability_by_day` veio vazio no payload (a grade, se existir, viria depois do envio).

| Pergunta | Opção | Pontos | Peso |
|---|---|---|---|
| Nome | (texto) | — | — |
| E-mail | (e-mail) | — | — |
| WhatsApp com DDD | (telefone) | — | — |
| Quanto você pode investir por mês? | Até R$ 1.000 | 1 | 30 |
| | R$ 1.000 a R$ 2.000 | 2 | 30 |
| | R$ 2.000 a R$ 3.500 | 3 | 30 |
| | R$ 3.500 a R$ 5.000 | 4 | 30 |
| | R$ 5.000 a R$ 8.000 | 5 | 30 |
| | Acima de R$ 8.000 | 5 | 30 |
| Qual sua renda familiar mensal? | Até R$ 3.000 | 1 | 20 |
| | R$ 3.000 a R$ 6.000 | 2 | 20 |
| | R$ 6.000 a R$ 10.000 | 3 | 20 |
| | R$ 10.000 a R$ 20.000 | 4 | 20 |
| | R$ 20.000 a R$ 50.000 | 5 | 20 |
| | Acima de R$ 50.000 | 5 | 20 |
| Vínculo profissional | CLT | 4 | 20 |
| | PJ | 3 | 20 |
| | Autônomo | 3 | 20 |
| | Empresário | 4 | 20 |
| | Servidor público | 5 | 20 |
| | Aposentado | 5 | 20 |
| Quanto você conhece sobre consórcio hoje? | escala (sem `options` nem `scoring`) | — | — |
| De 1 a 5, o quão pronto você está para avançar agora? | escala `scale_max: 5` | não listados por tick | 30 |

### 2.3 `roberth-formulario-de-consultoria-patrimonial-12-07`

[https://forms.crm.konq.com.br/f/roberth-formulario-de-consultoria-patrimonial-12-07](https://forms.crm.konq.com.br/f/roberth-formulario-de-consultoria-patrimonial-12-07) — 17/11/2026, 15:23, America/Bahia. [confirmado]

- Mesmo título, modo, `thank_you_text`, descrição e textos de agendamento do 2.2. Pede também os campos de identificação CPF e Cidade / Estado (só o **nome** do campo; nenhum valor foi lido nem copiado).
- `tier_routing_enabled`: **true**. Booking: 60 min, antecedência 120 min, janela de 33 dias; `availability_by_day` vazio no payload.
- Pontos e pesos de investir, renda, vínculo e prontidão: **iguais** ao 2.2. Conhecimento: sem `scoring`. Objetivo:

| Pergunta | Opção | Pontos | Peso |
|---|---|---|---|
| Qual seu objetivo com consórcio? | Investimento | 0 | 0 |
| | Construção de patrimônio | não há chave em `option_scores` | 0 |

### 2.4 `roberth-resende-consultoria-patrimonial-evento-organico-10-11-2026`

[https://forms.crm.konq.com.br/f/roberth-resende-consultoria-patrimonial-evento-organico-10-11-2026](https://forms.crm.konq.com.br/f/roberth-resende-consultoria-patrimonial-evento-organico-10-11-2026) — 17/11/2026, 15:23, America/Bahia. [confirmado]

- Mesmos 8 campos, pontos e pesos do 2.2 (sem CPF, cidade nem objetivo). `thank_you_text`: «Reunião confirmada!». `tier_routing_enabled`: **true**.
- Booking: 60 min, antecedência 120 min, janela de 305 dias; disponibilidade de segunda a domingo no payload (horários não listados aqui além do que o objeto trouxer; o objeto trouxe as chaves dos sete dias).

### 2.5 `consultoria-patrimonial-30-05` (domínio finq)

[https://forms.crm.finq.com.br/f/consultoria-patrimonial-30-05](https://forms.crm.finq.com.br/f/consultoria-patrimonial-30-05) — 17/11/2026, 15:23, America/Bahia. [confirmado]

O dossiê registrou o endereço como indício e anotou que «finq.com.br bloqueia leitura». Nesta captura o GET do HTML respondeu **200**, título «Consultoria Patrimonial · KONQ», com o mesmo app Next.js (mesmos hashes de bundle) e schema completo no payload.

- Modo `classic`, `thank_you_text`: «Reunião confirmada!», mesma descrição de pré-reserva de cotas, mesmos textos de agendamento.
- `tier_routing_enabled`: **true**. Booking: 60 min, antecedência 120 min, janela de 15 dias; `availability_by_day` vazio no payload.
- Campos: Nome, E-mail, WhatsApp com DDD, Cidade / Estado (sem pontuação); investir, renda, vínculo e prontidão com **os mesmos pontos e pesos** do 2.2; conhecimento sem `scoring`; objetivo igual ao 2.3 (peso 0; «Investimento» com 0 pontos; «Construção de patrimônio» sem chave de pontos).
- Não pede CPF (diferença em relação ao form 12-07 do Roberth).

[indício] Os quatro forms classic (Konq e Finq) compartilham a mesma tabela de score; mudam identificação (CPF, cidade, objetivo) e a janela/antecedência da agenda. O form chat do Eduardo Ribeiro é outro produto, sem score e sem roteamento por faixa.

---

## O que falhou e por quê

1. **Fórmula da nota e nota de corte.** Os pontos e os pesos estão no JSON do form. O JavaScript público não soma esses valores e não declara mínimo, máximo nem faixa de qualificação. Com `tier_routing_enabled: true`, o encaixe de consultor ocorre depois do `/submit`, no servidor, e esse endpoint não foi chamado (regra: não gerar lead). Fica **não capturado**, com motivo.
2. **Pontos por tick da escala de prontidão.** O schema só traz `{weight: 30, scale_max: 5}`, sem `option_scores`. Não inventado.
3. **«Construção de patrimônio» no objetivo.** Não tem chave em `option_scores` (só `investimento: 0`), peso 0. O efeito na nota, se houver, não está no cliente.
4. **Grade de horários ao vivo** nos forms cuja `availability_by_day` veio vazia, e a lista de consultores do roteamento: dependem de APIs `/booking-slots-*` e `/vendors` após um envio ou de um GET que exporia nomes. Não chamadas.
5. **Firecrawl da conta nova.** Testada (`user-Firecraw-xai`, 1025 créditos), mas não usada: o HTML/JS estático já respondia por GET. A conta antiga `user-Firecrawl` segue negativa (`-100`). O namespace `user-Firecrawl-xai` da varredura da manhã não aparece mais instalado.
6. **Uso do gerador.** De propósito não foi aberto com `?gerar` nem se emitiu link. A especificação veio do código da página limpa, que já contém a seção `#vGen`.
