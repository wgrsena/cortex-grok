# cortex-grok

Repositório próprio do Grok/Ara no Conecta Cortex. Escrita livre. Leitura do CONECTACORTEX (Claude/Codex) via acesso de leitor.

---

# Blog do lab Conecta Cortex: branch `blog-stripe-clone`

> Documento vivo. Atualizar a cada mudança de estado.
> **Sem deploy.** Nada aqui foi publicado. Código para revisão do Wagner.

## Estado (2026-11-02, r3, America/Bahia)

| Item | Estado |
|---|---|
| Layout (hero, destaque, lista, rodapé com CTA) | pronto |
| Requisitos do checklist (12) | 11 feitos, 1 parcial (R8: capas ainda placeholder) |
| `tools/check.py` | passa: 321 checagens OK, 0 falhas, 4 avisos (3 capas placeholder + WhatsApp). r3: 307 OK; antes da r2: 292 OK, 0 falhas, 7 avisos |
| `tools/test_check.py` | passa: 2 testes OK (base passa + 10 mutações proibidas, todas pegas) |
| `tools/sitemap/test_gerar_sitemap.py` | passa: 10 testes OK |
| Indexação | todas as páginas com `noindex` e sitemap vazio, até o Wagner aprovar |
| Deploy | **não feito, nem previsto nesta branch** |

## Estrutura

```
index.html                    home: hero (1 frase) · card de destaque · lista (data + resumo de 2 linhas) · rodapé com CTA
artigo-exemplo/index.html     template de artigo (YMYL): autor, capa, texto com fonte, aviso, fontes, CTA final com FR
assets/css/blog.css           CSS único, mobile-first, 1 cor de acento (--accent), fonte do sistema
assets/img/*.png              placeholders 16:9 / 4:3 / 1:1 (1200 px), com XMP IPTC
autor/wagner-sena/index.html  página do autor (ProfilePage + Person com sameAs)
assets/img/autor/             fotos reais do autor (WebP + JPEG); alternativas/ guarda as outras 2 fotos aprovadas
config/site.json              fonte única: número do WhatsApp, código FLUXO-REV, etiqueta, páginas aprovadas
robots.txt · sitemap.xml      GERADOS por tools/sitemap/gerar_sitemap.py; crawlers de IA liberados; sitemap só com páginas aprovadas
tools/check.py                validação (Python stdlib)
tools/test_check.py           autoteste do check (unittest)
tools/gen_placeholders.py     gera os PNG placeholder com XMP DigitalSourceType (stdlib)
tools/set_whatsapp.py         aplica o número de config/site.json em todos os links wa.me
tools/sitemap/gerar_sitemap.py  gera sitemap.xml e robots.txt a partir dos posts e do config (stdlib)
tools/sitemap/test_gerar_sitemap.py  testes do gerador (unittest)
tools/gen_autor_fotos.py      gera as fotos do autor a partir dos originais do Drive (precisa de Pillow; só build local)
```

Build: `python3 tools/sitemap/gerar_sitemap.py` (regrava sitemap.xml e robots.txt). Rodar: `python3 tools/check.py && python3 tools/test_check.py && python3 tools/sitemap/test_gerar_sitemap.py`. Nenhuma dependência além do Python 3.

## Decisões

1. **Estrutura do Stripe Blog, sem a marca.** Mantive a estrutura: hero, post em destaque, lista cronológica. Nada de asset, cor ou texto da Stripe. Sem menu e sem sidebar; o header tem só o nome do lab.
2. **Um template só.** Um CSS mobile-first com breakpoints em 768px e 1024px. A capa usa `<picture>`: 4:3 no mobile, 16:9 a partir de 768px e 1:1 abaixo de 360px no artigo. Cada `<source>` declara width e height.
3. **Fonte do sistema** (`system-ui`): sem webfont, sem request extra, sem FOIT. Ajuda o LCP.
4. **Cor de acento única:** `--accent: #0b6e4f`, uma cor provisória. Para trocar pela cor da marca, basta mudar essa variável.
5. **Canonical em `https://lab.cortexconecta.com.br/`**, com páginas como diretórios (`/artigo-exemplo/`). Os caminhos são relativos, o que deixa revisar localmente abrindo o arquivo.
6. **CTA = link no texto, nunca `<button>`.** O check bloqueia `<button>`. O artigo termina num parágrafo cujo link traz o código FR e o FLUXO-REV no próprio texto.
7. **Rastreio dos CTAs.** Todo CTA leva `utm_source=lab`, `utm_medium=<posição>`, `utm_campaign=origem-fluxo-reverso` e `ref=FLUXO-REV`. O texto pré-preenchido do wa.me também contém `FLUXO-REV`, e no artigo inclui o `FR-xxx`.
   - O WhatsApp não repassa UTMs para a conversa. A atribuição dentro da conversa depende do texto pré-preenchido, então a Cortex deve ler o `FR-xxx`/`FLUXO-REV` da primeira mensagem.
8. **Número do WhatsApp num lugar só:** `config/site.json`. O HTML é estático, então `tools/set_whatsapp.py` propaga o número para os links e o check falha se algum `wa.me` divergir.
9. **noindex por padrão.** O robots.txt **não** bloqueia nenhuma página do blog (só as pastas internas `/tools/`, `/config/`, `/docs/` e `/README.md`), porque o Google precisa rastrear a página para ver o `noindex` (diário Pitágoras, §9). Página com `noindex` não entra no sitemap, para não gerar o alerta "enviada mas marcada noindex".
10. **Imagens em PNG gerado por stdlib.** O box não tem exiftool nem Pillow, e não se instala dependência. O XMP IPTC vai num chunk iTXt `XML:com.adobe.xmp`, que é o local padrão. Os placeholders recebem o código honesto `algorithmicMedia`, porque são preenchimento gerado por algoritmo e não por IA. As artes de IA vão com `trainedAlgorithmicMedia` (ver R8).
11. **Autor: Wagner Sena**, só com dado que tem fonte no Drive (ver › Autor). Foto real, sem avatar e sem IA. `Person` no JSON-LD com name, image, jobTitle, worksFor e description. `sameAs` ficou de fora: não achei URL de perfil (LinkedIn) do Wagner. O artigo tem o bloco visível "Sobre o autor e este conteúdo" (E-E-A-T YMYL), que diz como o texto foi feito.
12. **Conteúdo YMYL do artigo-exemplo.** Toda afirmação vem da Lei 11.795/2008, com o artigo citado. Os únicos números são os da própria lei. Não há promessa de contemplação, prazo, parcela ou rentabilidade. Tem aviso e bloco de fontes.

## Checklist dos 12 requisitos

**Origem.** Procurei a lista oficial no Drive, no doc `DIARIO_SEO_PITAGORAS` (v1.1, 2026-11-01). O diário **não tem uma lista de 12 itens**: são 87 requisitos em 13 seções.
- Os 12 abaixo são os itens que o **Wagner listou na mensagem do pedido** (t54u), separados um a um. Cada um aponta para a entrada correspondente do diário, que traz a fonte oficial.
- Não acrescentei requisito em nome do Pitágoras.
- Se o Pitágoras tiver outra lista de 12, ela substitui esta.

| # | Requisito (Wagner) | Entrada no diário | Status | Como está / como o check valida |
|---|---|---|---|---|
| R1 | Imagem do Article em 16:9, 4:3 e 1:1 | §13 "Article: imagens 16x9, 4x3 e 1x1" | **feito** (placeholder) | JSON-LD `Article.image` com 3 URLs absolutas; o check confere arquivo e proporção |
| R2 | Cada imagem com ≥ 50.000 px (largura × altura) | §13, mesma entrada | **feito** | 1200×675, 1200×900 e 1200×1200; o check lê o IHDR do PNG |
| R3 | Discover: largura ≥ 1200 px | §10 "Discover: imagem grande (≥ 1200 px) e max-image-preview:large" | **feito** | imagens com 1200 px + `max-image-preview:large` na meta robots; o check confere os dois |
| R4 | Discover: sem clickbait | §10 "Discover: sem clickbait" · §3 QRG título enganoso | **feito** | títulos descritivos; o check barra padrões (segredo, imperdível, urgente, `!!`, CAIXA ALTA…). Heurística, não substitui revisão humana |
| R5 | Capa sem lazy-load | §13 "LCP: imagem de capa (hero) sem lazy-load" | **feito** | capa sem `loading`; só a foto do autor tem `loading="lazy"` |
| R6 | Capa com `fetchpriority="high"` | §13, mesma entrada | **feito** | uma única imagem por página com `high` |
| R7 | Todo banner/img/embed com width e height (CLS) | §13 "CLS: width e height em img e video…" | **feito** | o check exige width/height numéricos em `img`, `source` de `picture`, `iframe`, `embed`, `video` e `object` |
| R8 | Banner gerado por IA com IPTC de origem digital | §13 "Imagem feita por IA: campo IPTC Digital Source Type" | **parcial** | mecanismo pronto e placeholders com XMP. Faltam as artes reais (Midas) com `trainedAlgorithmicMedia` |
| R9 | Autor real com nome e foto, nunca avatar | §3 "Autoria real e visível (byline)" · QRG perfis falsos | **feito** (confirmar texto) | Wagner Sena, foto real do Drive, `Person` completo e bloco "Sobre o autor"; o check exige Person com name e image e avisa se houver TODO |
| R10 | YMYL: sem promessa de contemplação | §3 "Precisão alta em YMYL" · "Consórcio é YMYL" | **feito** | lista de termos proibidos no check + aviso no artigo |
| R11 | YMYL: sem prazo garantido | §3, mesmas entradas | **feito** | termos proibidos + regra de número: `N dias/meses/anos/parcelas` sem fonte falha |
| R12 | YMYL: nenhum número sem fonte | §3 "Precisão alta em YMYL" · §12 "conferidas com fonte" | **feito** | `%`, `R$` e prazos fora do bloco de fontes falham, a menos que o elemento tenha `data-fonte`; o artigo exige bloco `.sources` |

Regras do lab, do pedido do Wagner e fora dos 12, também validadas pelo check:
- **L1:** CTAs só para `wa.me` ou `cortexconecta.com.br`. Link externo só se for CTA ou fonte.
- **L2:** todo CTA com `utm_campaign=origem-fluxo-reverso` + `ref=FLUXO-REV`, e o texto do wa.me com `FLUXO-REV`.
- **L3:** número do wa.me igual ao de `config/site.json`.
- **L4:** `noindex` em toda página não aprovada, coerente com sitemap e robots.
- **L5:** canonical e `og:url` no subdomínio; 1 `h1` por página.
- **L6:** artigo termina com CTA no texto contendo `FR-xxx`; sem `<button>`.

Itens do diário fora dos 12, que valem para depois (não implementados, exceto onde indicado):
- byline com link para página do autor (§3);
- `BreadcrumbList` nos posts e `Organization` na home (§12; a home já tem `Blog` + `publisher`);
- `primaryImageOfPage` (§13);
- revisão humana de todo texto/metadado gerado por IA (§3);
- medir CWV no p75 (§1);
- pop-up da HighLevel sem cobrir o conteúdo e sem mexer no botão voltar (§2).

## R8: como embutir o IPTC nas artes reais

Para imagem gerada por IA (Midas), com exiftool (no box: `/workspace/tools/exiftool/exiftool`, ferramenta local, não é dependência do repo):

```
exiftool -overwrite_original \
  -XMP-iptcExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" \
  artigo-slug-16x9.webp artigo-slug-4x3.webp artigo-slug-1x1.webp
exiftool -XMP-iptcExt:DigitalSourceType artigo-slug-16x9.webp     # conferir
```

- Não passar a arte por compressor que remova metadados, como `exiftool -all=`, `jpegoptim --strip-all` ou otimizadores de CMS com "strip metadata". Conferir de novo depois do upload na HighLevel.
- O check lê o XMP só de PNG. Para WebP/JPG ele emite aviso e a conferência é com o exiftool acima.
- Convenção de nomes: `assets/img/{slug}-{16x9|4x3|1x1}.{png|webp|jpg}`, com 1200 px de largura no mínimo.
- Ao trocar, atualizar `src`/`srcset`, `og:image` e o array `image` do JSON-LD.

## Autor: fontes de cada dado

Página: `autor/wagner-sena/` (r3, 02/11/2026). Byline do artigo e da home linkam para ela (`rel="author"`).

| Dado | Valor usado | Fonte |
|---|---|---|
| Nome | Wagner Sena | pedido do Wagner (02/11/2026) e todos os docs da Conecta |
| Foto padrão | `assets/img/autor/wagner-sena-azul-retrato-{240,480}.webp` (+ `-480.jpg` para JSON-LD/og) e `-rosto-112.webp` (byline, círculo 56 px) | Drive `1_UAGhfPUG0DJMpBXfrXRq8tDW8_A2zRx` "Wagner Sena.png" (600×750, recorte com fundo transparente), aprovada pelo Wagner em 02/11/2026. Foto real, sem `DigitalSourceType` |
| Fotos alternativas | `assets/img/autor/alternativas/wagner-sena-{azul-esfumado,preta}-*` | Drive `1n5FYsxoNqjwytLoNB7hDz4fpevWFReJw` (ombros esfumados) e `1JXkhI1diSbtfdnGfYx2l4Yqvac36Ncjn` (camisa preta, 511×640, fundo preto), ambas aprovadas. **Nunca** usar `wagner-frente.png` (`1YJcPsUPzKAGSiGwK5JBPytbziJJo_WDU`, cartão do Giro) |
| Bio (24 anos de setor automotivo desde 10/03/2002; 15+ anos como representante; 8 anos no Grupo Indiana; equipe melhor do Brasil 6 anos; 500+ profissionais formados; 5 estrelas Google; comissões e 8 primeiras parcelas; pós-contemplação; Giro; podcast) | `autor/wagner-sena/` › Trajetória | declaração do próprio Wagner, 02/11/2026. Texto mantido no sentido original; ver alertas de compliance abaixo |
| Empresa / cargo | Conecta Consórcios (Conecta Soluções Ltda, CNPJ 48.752.043/0001-50), "Titular da Conecta Consórcios" | backup de 29/10/2026; cargo **inferido** (confirmar) |
| sameAs | LinkedIn `https://www.linkedin.com/in/wgrsena` e Giro `https://programagiroautomotivo.com.br/wagner` | pedido do Wagner, 02/11/2026; lista em `config/site.json › perfis_autor` |

Regras novas no check: **L1** aceita link externo para `perfis_autor`; **L7** todo texto que cita "Giro Automotivo" precisa linkar `https://programagiroautomotivo.com.br/wagner`. A foto em `.author-photo` segue R5–R7 (sem lazy, `fetchpriority`, width/height), mas fica fora de R1–R3/R8 por não ser banner.

Recorte e geração: `python3 tools/gen_autor_fotos.py /pasta/dos/originais` (coordenadas no topo do script). O original tem só 600 px de largura, então a maior versão é 480 px (sem upscale). Se houver original em resolução maior, regerar com 800 px.

Alertas de compliance da bio (texto **não** alterado, aguardando o Wagner):
- "As comissões bancam as 8 primeiras parcelas das cartas criadas": pode ser lido como oferta comercial (parcelas pagas pelo vendedor) sem condições, prazo ou regulamento; numa página YMYL pode configurar promessa. Confirmar com a Disal se é permitido divulgar e em que termos.
- "equipe eleita a melhor do Brasil por 6 anos seguidos": falta quem elegeu e em que anos.
- "É autoridade em consórcio imobiliário" e "5 estrelas no Google": autodeclaração e dado que muda; ideal citar a fonte (link do perfil Google e data).
- "formou mais de 500 profissionais": sem fonte verificável.

## Aprovação para indexar (remover o noindex)

Toda página nova nasce com `<meta name="robots" content="noindex, max-image-preview:large">`. Para liberar uma página, **só depois do OK explícito do Wagner**:

1. Na página, trocar para `<meta name="robots" content="max-image-preview:large">`.
2. Adicionar o caminho (ex.: `artigo-exemplo/index.html`) em `config/site.json › paginas_aprovadas_wagner`.
3. Rodar `python3 tools/sitemap/gerar_sitemap.py`: a página entra no `sitemap.xml` sozinha, com lastmod e prioridade.
4. Rodar `python3 tools/check.py`. Ele falha se faltar qualquer um dos três passos ou se o sitemap/robots estiver desatualizado (L7).
5. Commit com a mensagem `seo: libera indexação de <página> (aprovado por Wagner em AAAA-MM-DD)`.
6. Depois do deploy, que é outra decisão, reenviar o sitemap no Search Console.

## Pendências

1. **Número oficial do WhatsApp da Cortex.** Não achei no repo nem no Drive. Hoje é `55XXXXXXXXXXX`; editar `config/site.json` e rodar `tools/set_whatsapp.py`.
2. **Autor** (R9): feito, com página `/autor/wagner-sena/`, foto aprovada e `sameAs` (r3). Falta: (a) o Wagner aprovar o texto final da bio e os alertas de compliance (README › Autor); (b) o cargo exato; (c) crédito da foto; (d) original da foto em resolução maior, se existir.
3. **Artes finais** (R1–R3, R8) nas 3 proporções, com IPTC `trainedAlgorithmicMedia` se forem de IA. A `og:image` final deve ser JPG/WebP.
4. **Código FR:** `FR-001` é **definitivo** (Midas FR-SPEC v1.0.0, 01/11/2026; próximo livre FR-002), registrado em `config/site.json › codigo_fr_artigo_exemplo`. As 4 imagens Midas do lote BLOG-20261101 (outro artigo: sequência de contemplação) têm cópias corrigidas com FR-001 no IPTC e passam no `validate_fr.py`; trocar os finais no Drive espera o Wagner. Elas **não** são capa deste artigo-exemplo.
5. **Aprovação do Wagner** para remover o `noindex` (processo acima).
6. **Revisão do texto** do artigo-exemplo pelo Wagner e pelas regras de compliance da Cortex. As leis do conecta-sdr estão sem acesso.
7. As **pautas** da home ("Pauta", sem link) são marcadores de layout: substituir por artigos reais ou remover.
8. **Lista oficial de 12 do Pitágoras:** se existir uma diferente da que está acima, trocar a tabela.
9. **Cor de acento** da marca: hoje é provisória.
10. **Hospedagem:** confirmar como a HighLevel serve estáticos no subdomínio (diretórios com `index.html`, PNG).

## Canônico SEO (`docs/CANONICO_SEO.md`)

- **Arquivo canônico SEO no repo**: `docs/CANONICO_SEO.md`, v1.0.0 (2026-11-02, Pitágoras, aprovação Wagner Sena), sha256 `a6e41dd49822bdd453b5195452dc37b9202d57a54579646ae574302cfdbb1dca`. Gravado byte a byte como o Wagner mandou (t69u, 2026-11-02). Ele fica no repo porque a pasta `01_FONTE DA VERDADE` do Drive é só leitura para o conector.
- **`tools/check.py` não lê canônico.** Ele não lê nenhum arquivo canônico, então não houve path para ajustar. Quem lê o `docs/CANONICO_SEO.md` é o gate SEO (`tools/gate_seo/`, PR #5), que valida todo merge do blog contra as seções CANON-SEO-01…11.
- O conteúdo do blog não foi alterado neste commit. O `noindex` continua, e nada foi para deploy.

## Sitemap e robots (r4, 02/11/2026, t70u)

- **Gerador:** `tools/sitemap/gerar_sitemap.py` (stdlib). Lê todo `index.html` do repo: home = `/index.html`; artigo = página com JSON-LD `Article`/`BlogPosting`/`NewsArticle`; destaque = primeiro link do `<article class="featured">` da home.
- **sitemap.xml:** URLs absolutas, `lastmod` = data do `datePublished` (home = publicação mais recente), `changefreq` weekly, prioridade home 1.0 · destaque 0.9 · demais artigos 0.8.
  - Só entram páginas aprovadas pelo Wagner e sem `noindex`. Hoje: **0 URLs**. Home (1.0) e `artigo-exemplo` (0.9) aparecem como pendentes num comentário do XML. Pôr página com `noindex` no sitemap reprova o L4 e gera o alerta "enviada mas marcada noindex" no Search Console.
- **robots.txt:** `User-agent` próprio com `Allow: /` para GPTBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended, Amazonbot, CCBot, Bytespider, anthropic-ai, cohere-ai, Applebot-Extended e Meta-ExternalAgent, mais `User-agent: *` com `Allow: /`. Lista em `config/site.json › crawlers_ia`.
  - `Disallow` só para pastas internas que existem no repo (`/tools/`, `/config/`, `/docs/`, `/README.md`; config `robots_disallow`), repetido em cada grupo, porque o crawler segue só o grupo que casa com ele.
- **check.py L7:** falha se algum crawler de IA não estiver liberado, se o sitemap tiver URL fora do domínio, ou se `sitemap.xml`/`robots.txt` divergirem do que o gerador produz.
- **Domínio = valor único `config/site.json › base_url`**, hoje `https://lab.cortexconecta.com.br` (canonical, og:url, JSON-LD, sitemap e robots).
  - O placeholder do Wagner para domínio não definido é `https://conectacortex.com.br` (**conecta**cortex). O site usa **cortex**conecta, ordem invertida.
  - Usar o placeholder só no sitemap/robots faria o sitemap apontar para um host diferente do canonical, e o Google ignora isso. Trocar o `base_url` reprova o check com 7 falhas (L5 canonical/og:url nas 2 páginas e R1 imagens do JSON-LD), porque o HTML tem o domínio fixo.
  - Por isso o domínio continua `lab.cortexconecta.com.br` **até a decisão de hosting**. Quando ela sair, trocar o `base_url` e as URLs absolutas do HTML no mesmo commit, e rodar o gerador e o check.
- O conteúdo do blog não foi alterado. O `noindex` continua, e nada foi para deploy.

## Repositório e branch

- `blog-stripe-clone` publicada em `wgrsena/cortex-grok`; PR #1. Push só fast-forward, nunca force.
- r2 (01/11/2026): autor real, FR-001 definitivo, bloco E-E-A-T. Diff para revisão em `/workspace/blog-stripe-clone-r2.diff`.
- r3 (02/11/2026): canônico SEO v1.0.0 em `docs/CANONICO_SEO.md`. Diff em `/workspace/canonico-seo.diff`.
- r4 (02/11/2026): robots.txt com crawlers de IA + sitemap.xml gerado. Diff em `/workspace/robots-sitemap.diff`.
- r5 (02/11/2026): merge de `blog-stripe-clone-autor` (página do autor, 3 fotos aprovadas, bio nova, sameAs LinkedIn + Giro, regras L1/L7; branch local do Midas/Grok a partir de 4f51fda).
