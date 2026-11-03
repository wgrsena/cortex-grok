# CANÔNICO SEO — CONECTA CORTEX
Versão 1.1.0 | Data 2026-11-02 | Autor Pitágoras | Aprovação Wagner Sena | Status FONTE DA VERDADE

Changelog: 1.1.0 (2026-11-02) — §2, §3, §4, §5, §6, §7, §8 e §10 relaxados por autorização explícita do Wagner Sena (t71u). §1, §9 e §11 sem mudança; regras duras de embalagem (§1) e citação (§3) mantidas.

## 1. REGRA DE EMBALAGEM
Blog NUNCA publica grupo Disal, mediana, embutido ou dado do Arquimedes. Só formato das administradoras. A regra "parcela só se vier de fonte viva (Arquimedes)" do doc 05 é PROIBIDA no blog.

## 2. REGRA DO GANCHO
Posts de oportunidade e de mercado: abertura 1) hook com número real e fonte (dado do grupo OU número de mercado ABAC/Anfavea/Fenabrave/BCB com data de acesso), 2) oportunidade, 3) oferta. Posts de formato/educação (como funciona, o que é lance) podem abrir com pergunta ou contexto em vez de número. Em qualquer post, sem fonte e data, número não entra.

## 3. REGRAS DE CITAÇÃO
Todo número factual: fonte nomeada, link, data de acesso. "Fonte: Google" sem link/data = reprovação. "A CONFERIR" = reprovação. Soma do autor identificada como tal. A bio do autor pode conter trajetória profissional sem fonte externa, desde que identificada como afirmação do próprio autor; bio não é citação factual.

## 4. REGRA DE SLUG
Todo post tem slug. Slug sem ID de criativo = aviso (não reprova) até o fluxo de ID estar 100% no circuito. Meta: todo slug com ID de criativo; ID segue em todo o circuito.

## 5. E-E-A-T/YMYL
Autor Wagner Sena (bio completa na memória). Foto real ou avatar geométrico até a foto existir. Link Giro Automotivo na bio obrigatório. LinkedIn linkado obrigatório.

## 6. CORE WEB VITALS
LCP ≤2,5s, INP ≤200ms, CLS ≤0,1 medidos via Chrome headless; scores Lighthouse ≥90 quando o Lighthouse estiver instalado — instalação autorizada. Lighthouse headless via check.py.

## 7. DADOS ESTRUTURADOS
JSON-LD Article/BlogPosting. IPTC com autor, link Giro, ID criativo, TransmissionReference=FR-001. FR-001: versão vigente do FR no momento da publicação (não trava); FR-001 v1.0.0 aceito como provisório no blog atual. Largura mínima 1080px aprovada.

## 8. DESIGN
Referência Stripe Blog. Avatar geométrico. Sem imagem bagunçada: todo asset passa FR-001 antes de publicar. Proporções disponíveis no momento; 9:16 e 4:5 entram quando o Midas renderizar.

## 9. TIPOS DE POST
Notícia de oportunidade (hook=número do grupo) e notícia de mercado (hook=número de mercado). Proporção 60% mercado/40% oportunidade.

## 10. FLUXO
Cortex Build check.py+Lighthouse → Wagner aprova (única etapa bloqueante) → publica → noindex removido só com aprovação explícita. Pitágoras valida e Midas renderiza FR-001 em paralelo, sem travar o merge.

## 11. DOCS BASE
01 a 08 + diário em Cortex Lab NotebookLM pack. Doc 02 vira template de notícia de mercado.
