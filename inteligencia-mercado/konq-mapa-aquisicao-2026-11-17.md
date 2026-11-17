# Konq · mapa da aquisição, link por link (17/11/2026)

Varredura feita em 17/11/2026, entre 10h e 11h (Bahia), com Firecrawl no site, no CRM, nas landings e nos checkouts, e com a Biblioteca de Anúncios da Meta. O que é dedução está marcado como **[dedução]**; o resto foi visto direto na fonte do link.

---

## 1. Por que o botão do site dá "Página não encontrada"

- Em todo o site, o botão **"Falar com um consultor"** (topo, meio e rodapé) e o **"Conversar agora"** levam para `https://forms.crm.konq.com.br/f/diagnostico-de-consorcio`. Essa página responde **HTTP 404**, com ou sem os parâmetros de campanha.
  - Site: https://konq.com.br/
  - Formulário quebrado: https://forms.crm.konq.com.br/f/diagnostico-de-consorcio
- O link que você mandou carrega `utm_campaign=consultoria-patrimonial-site`, `kq_pixel=1400595315390784` (o ID do pixel da Meta) e `kq_aid` (o ID da visita). Pelo script de rastreio deles, o evento **Lead** só dispara quando o formulário abre. Com o formulário fora do ar, **o site não gera Lead nenhum por esse caminho**.
- Testei também `/f/consultoria-patrimonial`: 404. O `/calendario` pede login. O CRM é privado (`noindex`) e não aparece em nenhuma busca.
  - https://forms.crm.konq.com.br/login
- O agravante: desde **11/11** a página da marca Konq paga anúncio levando direto para `konq.com.br/`. Ou seja, **tráfego pago caindo num site cujo botão principal está quebrado**. Sobram dois caminhos que ainda podem funcionar: o formulário do rodapé ("Falar com um consultor no WhatsApp", que abre o WhatsApp com mensagem pronta) e o modal do simulador ("Confirmar com um consultor").
  - Anúncio da marca → home: https://www.facebook.com/ads/library/?id=1446958964210315
  - Outro, mesmo destino: https://www.facebook.com/ads/library/?id=1469598231987813
- **[dedução]** O formulário foi renomeado ou despublicado no CRM próprio e o site, que é estático (sitemap com última alteração em 25/08/2026), não foi atualizado. Uma pista: rota que não existe no site devolve a home com status 200 (`/quiz-gui` mostra a home), então o site ainda tem cara de rascunho.
  - Sitemap: https://konq.com.br/sitemap.xml

**Leitura:** o site institucional não é o funil deles. O dinheiro vai para os influenciadores, e lá o funil está vivo e sendo testado todo dia (itens 2 a 4).

---

## 2. O funil principal, passo a passo

```
Anúncio na página do influenciador (sem a palavra "consórcio")
  → landing no konq.com.br/<slug>, com ID de visita (kq_aid) e versão (kq_v)
    → QUIZ de 15 telas (pega nome + WhatsApp no meio) ou VSL com botão atrasado
      → Kiwify: ingresso da aula a R$ 27 ou R$ 47, vendido pela KONQ INTERMEDIACOES
        → aula ao vivo às 20h, de segunda a sexta + reprise no WhatsApp às 10h do dia seguinte
          → formulário de renda/aporte/prontidão → reunião de 1h gravada e transcrita (CRM próprio)
```

### 2.1 Anúncios (Biblioteca de Anúncios da Meta)

| Página | ID da página | Anúncios no histórico | O que roda |
|---|---|---|---|
| Roberth | 1416162394916749 | ~131 | "Verdades Secretas" e "Aproveite agora" |
| Eduardo Schroeder | 111040141539443 | ~89 (a maioria de outros negócios dele) | "Se você tivesse patrimônio.." |
| Konq (marca) | 1068820432977924 | 6 vistos | "Konq · Corretora de consórcio" |
| Busca "Konq" (Brasil) | — | ~189 | inclui páginas de terceiros que falam da Konq |

Links para abrir as páginas inteiras:
- Todos os anúncios do Roberth: https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=BR&view_all_page_id=1416162394916749
- Todos do Eduardo: https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=BR&view_all_page_id=111040141539443
- Todos da marca Konq: https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=BR&view_all_page_id=1068820432977924
- Busca "Konq": https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=BR&q=Konq&search_type=keyword_unordered

**Ondas de criativos (data de criação, horário da Bahia):**

| Onda | Quando | Exemplo (abre o anúncio) | Destino |
|---|---|---|---|
| Roberth · "Aproveite agora" (dezenas criadas no mesmo minuto) | 02/11, 07h24 | https://www.facebook.com/ads/library/?id=1775203417019793 | https://konq.com.br/roberth-aposentadoria-antecipada |
| Eduardo · "Se você tivesse patrimônio.." | 03/11, 22h47 | https://www.facebook.com/ads/library/?id=1165986289606619 | https://konq.com.br/renda-alem-do-trabalho |
| Roberth · "Verdades Secretas" | 10/11 | https://www.facebook.com/ads/library/?id=1711160230627241 | (mesma família) |
| Marca Konq | 11/11, 10h15 | https://www.facebook.com/ads/library/?id=1441125240822440 | https://konq.com.br/ (botão quebrado) |
| Marca Konq | 13/11, 12h23 | https://www.facebook.com/ads/library/?id=1446958964210315 | https://konq.com.br/ |
| Roberth · "Verdades Secretas" | 13/11 a 16/11 (8 criados em 16/11, 10h38–11h37) | https://www.facebook.com/ads/library/?id=1722261586128934 | https://konq.com.br/roberth-patrimonio → redireciona ao quiz |

Textos vistos:
- Roberth (02/11): "Construa seu patrimônio com especialistas! Descubra como planejar seu futuro financeiro… Clique em 'Saiba Mais'".
- Roberth (16/11): "Planejamento de Construção Patrimonial com especialistas neste domingo".
- Eduardo (03/11): "tem professora construindo MAIS patrimônio do que médico… o meu consultor patrimonial… vai te explicar".
- Marca (13/11): "Você alguma vez já pensou em construir um plano estruturado pro seu futuro?"

Nenhum texto de influenciador traz a palavra "consórcio". A Biblioteca não mostra quem pagou nem quanto foi gasto; a pesquisa anterior atribuiu esses anúncios à Konq pelo padrão, e o reel afirma que o pagador é a Konq.

### 2.2 Landings (todas no konq.com.br, fora do Google)

| Link | O que é | Para onde manda |
|---|---|---|
| https://konq.com.br/roberth-patrimonio | Redireciona para o quiz, com `kq_aid` e `kq_v=b` | https://konq.com.br/quiz-roberth-27?kq_v=b |
| https://konq.com.br/quiz-roberth-27 | **Quiz** "Se você parar de trabalhar hoje, quanto tempo você aguenta?" com o checkout de R$ 27 | Kiwify 1O6By6Z |
| https://konq.com.br/quiz-roberth-l1 | O quiz original, de que o de R$ 27 é cópia | [dedução] o checkout de R$ 47 |
| https://konq.com.br/roberth-aposentadoria-antecipada-27 | Página de R$ 27 sem quiz (o outro braço do teste) | https://pay.kiwify.com.br/1O6By6Z?hideBoleto=true |
| https://konq.com.br/roberth-aposentadoria-antecipada | VSL "[RRDIARIO] VSL 1 (Sem Gancho) - Controle", botão aos 11min02s | https://pay.kiwify.com.br/6KXGFqE (R$ 47) |
| https://konq.com.br/renda-alem-do-trabalho | VSL "[EDUARDO] VSL Cheirin Bão", botão aos 8min22s | https://pay.kiwify.com.br/M7CuZMe (R$ 47) |
| https://konq.com.br/politica-de-privacidade | Política das landings | — |

**Os testes, nas palavras do código da página:**
- **Preço:** o quiz de R$ 27 (código "rr-27", desde 13/11/2026) é o `quiz-roberth-l1` sem mudança de tela nem de texto, só com o checkout de R$ 27. A aula, a turma, o grupo e a régua são os mesmos do ingresso de R$ 47.
- **Formato:** "O link fixo do teste divide 50% para este quiz e 50% para a página de R$ 27". O link do anúncio (`/roberth-patrimonio`) sorteia entre o quiz e a página sem quiz, os dois a R$ 27. Quando caí no quiz, o endereço veio com `kq_v=b`; [dedução] o `kq_v=a` é a página.

### 2.3 O quiz por dentro (konq.com.br/quiz-roberth-27)

- **15 telas, cerca de 2 minutos.** Na tela 2 há um áudio de 30 s com a voz do Roberth **gerada no ElevenLabs** e legenda sincronizada (faster-whisper). O roteiro: "Eu cheguei a ganhar 50 mil por mês. E gastava 47… se eu parasse 30 dias, quem ia pagar as minhas contas? Ninguém."
- **Perguntas:** quanto tempo você aguenta parado; como quer estar daqui a 10 anos; o que faz hoje; quanto ganha por mês; há quanto tempo ganha isso; quanto disso virou patrimônio; o que aconteceu da última vez que a renda subiu; o que mais trava; se conseguiria guardar R$ 1.000 por mês. Há também uma tela de "imóvel dos sonhos" escolhido por foto.
- **No meio do quiz pega nome e WhatsApp** com aceite, e manda o lead ao painel deles **antes** do checkout. Quem não compra vira lead do mesmo jeito.
- **Simulação na tela 12** (comentário do próprio código), já com a conta de consórcio sem dizer a palavra: "taxa de administração 25%, fundo de reserva 0,5%, INCC 6% a.a., sempre o maior prazo (240 meses), parcela reduzida de 70% antes da contemplação". Faixas: parcela de R$ 500 → imóvel de R$ 130 mil; R$ 1.000 → R$ 270 mil; R$ 2.000 → R$ 540 mil; R$ 5.000 → R$ 1,36 mi. Detalhe: no simulador do site a taxa é 22%; no quiz, 25%.
- **Fotos de imóveis:** marcadas no código como "Foto de I.A." (`ilustrativa: true`), com aluguel estimado.
- **Rodapé sem a Konq:** "sem dados da Konq e sem termos/política (aprovado pelo Gabriel em 06/11/2026)". A instrução escrita é "comunicação neutra (nem ao vivo nem gravada) e nada da Konq para o visitante".
- **Eventos para a Meta:** só eventos personalizados (`QuizInicio`, `QuizContato`, `QuizCliqueComprar`). `InitiateCheckout` e `Purchase` saem da Kiwify. Em 06/11 eles desligaram o rastreio automático de cliques do pixel para não mandar as respostas do quiz à Meta.

### 2.4 Checkout (Kiwify, produtora KONQ INTERMEDIACOES LTDA)

| Link | Produto | Preço (visto com IP do Brasil) |
|---|---|---|
| https://pay.kiwify.com.br/1O6By6Z | Roberth Resende - Aposentadoria Antecipada | R$ 27,00 (até 6x) |
| https://pay.kiwify.com.br/6KXGFqE | Roberth Resende - Aposentadoria Antecipada | R$ 47,00 (pesquisa de 16/11) |
| https://pay.kiwify.com.br/M7CuZMe | Eduardo Schroeder - Renda Além do Trabalho | R$ 47,00 (até 11x) |

- Os três têm cronômetro e a mensagem "Os ingressos desse lote esgotaram! Estamos redirecionando você para o próximo lote agora!". Não vi order bump.
- O link do checkout leva `src=<kq_aid>` (é por ele que o painel deles liga a compra à visita), `s1=<lead_id>` e `hideBoleto=true`: **sem boleto**, só cartão e Pix.

### 2.5 Aula e régua de WhatsApp (pelo código do quiz)

- Aula às **20h, horário de Brasília, de segunda a sexta**.
- Reprise completa **no WhatsApp no dia seguinte, às 10h** (template `roberth_reprise`). Respostas prontas para "não consigo às 20h".
- O código cita **Unnichat** (automação de WhatsApp) como alternativa de recebimento do lead.
- A política das landings confirma: inscrição com "data e horário da sessão escolhida", "link de acesso à aula" e lembretes por WhatsApp, e-mail e telefone.

### 2.6 Depois da aula: CRM próprio e reunião gravada

- CRM em Next.js, com login Google e conta @konq.com.br: https://forms.crm.konq.com.br/login
- Aviso de privacidade do CRM (30/07/2026): https://forms.crm.konq.com.br/privacidade
  - Campos de qualificação: renda familiar, valor para investir por mês, conhecimento do produto e "disposição de avançar"; o aviso diz que eles **variam conforme a campanha**.
  - Reuniões feitas **dentro da plataforma**, com **gravação de áudio e transcrição por IA**, e IA lendo os documentos enviados. Guardam por 12 meses e "podem ser acompanhadas por profissionais autorizados".
  - Usuários da plataforma: "sócios, colaboradores, parceiros, representantes, consultores e prestadores de serviço". **[dedução]** O CRM foi feito para uma rede de vendedores externos, o modelo Loovi.
- **Administradoras confirmadas:** a política das landings diz que, ao marcar o aceite, os dados vão para a **Servopa** e a **Racon**. Isso fecha a lacuna da pesquisa de ontem.
  - https://konq.com.br/politica-de-privacidade

---

## 3. Infraestrutura de rastreio (para depurar)

| Peça | Valor ou link | Para que serve |
|---|---|---|
| Google Tag Manager | `GTM-5JLH9QNS` ("GTM KONQ WEB"), no quiz e no CRM | Liga o pixel e o PageView |
| Pixel da Meta | `1400595315390784` (no seu link, como `kq_pixel`) | Medição das campanhas |
| Script próprio | https://api.crm.konq.com.br/public/collect/kq.js | Origem e atribuição multi-toque |
| Painel de funis | https://konq-painel.services-2d8.workers.dev/ ("Painel de Funis Konq", login Google) | Etapa máxima de cada visitante, desistências, compra × visita |
| Microsoft Clarity | `xr4od3vykh` (no CRM) | Gravação de sessão |
| Player de VSL | vturb/ConverteAI (`cdn.converteai.net`) | VSL com autoplay e barra falsa de progresso |
| Voz | ElevenLabs (voz do Roberth no quiz) | Áudio sem gravar o influenciador |

Comentários do `kq.js` que mostram como eles operam:
- "Decisão do João em 11/09/2026": o Lead só dispara quando foi a landing que mandou a pessoa ao formulário. Quem chega "pelo webinário, pelo link da bio ou direto" não gera Lead.
- "Das 4.587 chegadas de 01/09/2026, ZERO trouxe parâmetro." Por isso o pixel vai no atributo da tag e não à mão em cada link. **[dedução]** Em setembro já havia tráfego de webinário rodando.
- Pixel de terceiro (agência ou parceiro) que estiver na página é descartado no servidor.

Nomes internos citados no código: Gabriel (trouxe o quiz em 05/11 e aprovou o rodapé em 06/11), João (regra do Lead em 11/09) e "Gui" ("como no quiz do Gui"). Os termos "Quiz V3 da Konq" e "Konquers Quiz" indicam que já houve outros quizzes antes.

---

## 4. Quem empresta o rosto

| Influenciador | Quem é | Links |
|---|---|---|
| Roberth Resende | Empresário e influenciador, fundador da Allpfit Home; vende "método de viralização"; aparece no site da Konq como cliente de plano de imóvel | https://www.instagram.com/eusouroberth/ · https://pt.wikipedia.org/wiki/Roberth_Resende · página de anúncios: https://www.facebook.com/61595908385369 |
| Eduardo Schroeder | Advogado de franchising, cofundador da Cheirin Bão e da Escola do Franchising ("+2.000 franquias vendidas"); roda funil de webinário próprio para vender franquia | https://www.instagram.com/schroedereduardo/ · https://bio.eduardoschroeder.com.br/ · https://franquia.cheirinbao.com.br/webinar/ |

**[dedução]** Eles escolheram rostos que já sabem vender por anúncio e webinário (franquia e app), não influenciadores de finanças. A aula é dada pelo "consultor patrimonial"; o influenciador só abre a porta.

---

## 5. Quem está surfando no assunto (não é a Konq)

- Math Lima (reel do "dossiê"): https://www.facebook.com/ads/library/?id=1100805536159886
- Kelvin Cleto, "DOSSIÊ COMPLETO: ACESSE A ESTRATÉGIA" (cerca de 12 anúncios em 15/11): https://www.facebook.com/ads/library/?id=1131651999568356
- Quokys (agência de CRM) usa a Konq como gancho, "Descobri o novo negócio bilionário do Marcos Paulo!": https://www.facebook.com/ads/library/?id=2240338593244606 · https://instagram.com/quokysbr
- Vídeo do Alfredo Soares que começou tudo (10/11): https://www.youtube.com/watch?v=WuTDh1kzi00

---

## 6. O que a Conecta tira disso

1. **O furo do 404 é a prova de que o funil deles é o do influenciador, não o site.** Não vale a pena disputar a marca Konq; vale disputar o tema "patrimônio".
2. **O quiz é a peça mais copiável e a que mais combina com o motor.** Em 15 telas, ele qualifica renda, aporte e intenção, pega o WhatsApp antes do pagamento e mostra uma simulação. A diferença da Conecta: no lugar da tabela fixa de 25% e das fotos de I.A., entra o Raio-X com grupo real e lance real.
3. **O lead nasce antes da compra.** Quem desiste no checkout já está no CRM deles, com as respostas. Para a Cortex, isso é o "contato do quiz" entrando no HighLevel com as respostas nos campos, e a régua seguindo mesmo sem compra.
4. **Dois testes ao mesmo tempo, medidos no próprio painel:** preço (R$ 47 contra R$ 27) e formato (quiz contra página, divisão 50/50). É o método de provar barato antes de escalar.
5. **O que não copiar:** "lote esgotado" com cronômetro, imóvel de I.A. vendido como exemplo e rodapé escondendo a empresa. São escolhas deles; para quem vende confiança local, viram passivo.

---

## 7. O que não deu para ver de fora (lacunas)

- O formulário pós-aula e a sala de reunião: estão atrás do login do CRM. Só dá para ver comprando o ingresso de R$ 27.
- O conteúdo e o fim do quiz: dá para ver no navegador respondendo as 15 telas, com nome e WhatsApp de teste.
- O número de WhatsApp do rodapé do site: o script não apareceu na extração.
- O gasto e o alcance dos anúncios: a Biblioteca não mostra para anúncio comercial no Brasil.
- Se a home continua com o 404: conferido em 17/11/2026, por volta das 10h50.
