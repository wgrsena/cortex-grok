# Motor de oportunidade — README de origem (conecta-cortex)

> **Proveniência.** Portado em 03/11/2026 do repositório `wgrsena/conecta-cortex` (que não foi alterado nem recebeu push), branch local `cortex/motor-oportunidade` = `cortex/revisao-reviewer` (`8bfd5d4`) + merge de `cortex/arquimedes-grid` (`517b4ab`, inclui o fix da vírgula na 0002, `71bf30e`); commit de merge local `8fae241`. Os diretórios estão nos **mesmos caminhos** do conecta-cortex (`solver/`, `scrap/`, `rag/`, `centauro/`, `schema/`, `supabase/`, `arquimedes/`, `docs/`), para alinhar com os arquivos vendorizados no PR #2 (`cortex/backtest-rolante`). Este arquivo é o README original do conecta-cortex, sem edição de conteúdo; o status vivo fica no `README.md` da raiz, seção "Motor de oportunidade". Avisos de "sem commit"/"nada enviado ao GitHub" abaixo refletem a data em que foram escritos.

## Conecta Cortex (README original)

Inteligência comercial de consórcio. A IA (persona **Centauro**) atende e qualifica no WhatsApp com os critérios do Wagner; **um humano decide e fecha**. Não é CRM nem bot de script.

> **AVISO: nada foi implantado.** Não há deploy, não há banco aplicado, nada foi commitado nem enviado ao GitHub. Tudo aqui é rascunho local na branch `cortex/bootstrap`, aguardando revisão do Wagner.

Última atualização: 01/11/2026 (revisão do Cortex Reviewer, branch local `cortex/revisao-reviewer` a partir de `cortex/consolidacao-28-10`, sem commit). Antes: 28/10/2026 (consolidação) e 27/10/2026 (solver v1.1).

## Estrutura
| Pasta | O que é | Estado |
|---|---|---|
| `solver/` | Serviço Python (FastAPI + HiGHS) do motor Disal, separado da Edge Function; spec e notas de dúvidas | Código e testes (dados sintéticos); v1.1 (27/10/2026) em revisão; sem deploy |
| `scrap/` | Cofre, job semanal que gera a tabela fato e backtest rolante | Código e testes sintéticos; **sem dado real** |
| `rag/` | Busca nos atendimentos: HNSW no Postgres, filtro por metadados, poda por score | Montador de chamada testado; **SQL não testado** |
| `centauro/` | Persona do WhatsApp: contrato de fala e fluxo | Só `frases.py` e README; **WhatsApp não integrado** |
| `schema/` | Mapa dos três armazenamentos (cofre, fato, RAG) e exemplo do contrato | Documentação |
| `supabase/` | Migrations (`0001`–`0005`) e pseudocódigo da Edge Function | **Migrations não testadas** (sem Postgres local) |
| `arquimedes/` | Grid de oportunidades por faixa (top-K, B&B, migration `0004`) — ver `arquimedes/README.md` | Código e testes sintéticos; exemplo com dados não validados |
| `docs/` | Custos (`custos.md`) e arquitetura (`arquitetura.md`, Mermaid **não validado**) | Rascunho |

Testes: `python -m pytest -q solver scrap rag centauro arquimedes` (150 passam após o merge revisão + grid em 03/11/2026: 124 da revisão + 26 do arquimedes).

## Arquimedes grid
`python -m arquimedes.grid --entrada arquimedes/exemplo_top5.json` gera as melhores combinações por faixa (50/80/100/180/200/250 mil). O passo do grid está na geração: janela `[T, min(1,25T, próxima faixa))` e branch-and-bound com cobertura mínima. Ranking: menor mediana, maior embutido (25% antes de 10%), maior prazo. Só as ranqueadas são persistidas em `public.oportunidades` (`0004`, validada só no `sqlcheck`, sem Postgres). Decisões em `arquimedes/README.md` e `solver/NOTAS_DUVIDAS.md`.

## Decisões tomadas (rascunho)
- **Solver:** serviço Python separado; a Edge Function só autentica e repassa. Otimização em HiGHS; CBC descartado.
- **Regra do solver:** embutido sobre a categoria (crédito + taxa) em passos de 5% até o teto da série; sem teto de sobra de crédito (a sobra aparece em `gap`); lance fixo é um ramo à parte (recurso próprio zero); cobertura como sequência W/6, nunca comunicada como número frio.
- **Solver v1.1 (27/10/2026):** probabilidade = sequência W/6 (nunca como número frio); sem teto de sobra; embutido sobre a categoria, passo de 5, teto pelo flag da série (exceções são dado do catálogo, nunca número de grupo); lance fixo com `chance_fixo` = 1/ofertantes só informativa; mediana do lance livre guardada como dado comercial (`embutido_cobre_mediana`); oportunidade `desatualizada` se a coleta tem mais de 8 dias; prazo de entrada de cliente novo (2 dias antes, dia útil, feriado como parâmetro). Detalhes em `solver/ESPECIFICACAO_V1_1.md`.
- **Dois bancos:** cofre append-only (nunca consultado em runtime) e tabela fato dos ~70 grupos ativos, alimentada por job semanal; backtest só com grupos vivos na data.
- **RAG:** o aprendizado fica no banco; filtro por metadados antes da similaridade e poda por score.
- **Meta cobra por mensagem**: serviço R$ 0,035 após 1.000 grátis/número/mês; marketing R$ 0,3217. A premissa de "R$ 0,006" estava desatualizada (ver `docs/custos.md`).
- A estimativa de R$ 300/mês da pilha "Frankenstein" não fecha: **≈ R$ 574** fixos sem respond.io, **≈ R$ 1.668** com respond.io Growth. O maior custo variável é o Grok.
- Fase 1 sugerida: API WhatsApp + backend próprio (Supabase) + HubSpot grátis; respond.io só se provar necessário.
- A IA **não recebe** grupo/mediana/embutido para falar com o cliente; só um sinal de escassez genérico. O dado técnico vai no dossiê de handoff.
- Regras do motor Disal por flags (`tem_lance_fixo`, `pct_embutido_max`), nunca por número de grupo; exceções ficam como dado.
- Compliance = alerta com registro, sem bloqueio; Wagner arbitra.
- LGPD: consentimento no 1º contato, `retencao_ate` obrigatório, voz = opt-in específico (`voz_biometria`).

## O que falta / pontos em aberto
0. **Pendências da v1.1:** (g) planilha mestra do Drive (`2_Parametros` com 20 colunas) ainda não exportada: o alinhamento do schema da fato está PENDENTE; (h) interpretação de feriado no prazo de entrada (recuar para o dia útil anterior); (i) definição da mediana (todos os lances livres da janela). Ver `solver/NOTAS_DUVIDAS.md`, V1 a V8.
0. **Conflitos para o Wagner decidir:** (a) o documento de parâmetros revisado pelo Claude manda tirar a probabilidade e ranquear pela sequência da carta mais fraca, enquanto o código segue sequência/6; (b) o mesmo documento remove `n_ofertantes_fixo_medio`, que o ramo fixo usa; (c) o pedido falou em "HiGHS/CBC" e o código usa só HiGHS; (d) `grupos_disal.mediana_lance_pct` (0001) existe, mas o solver não usa mediana; (e) regra de desempate entre sequências iguais; (f) backtest real depende da planilha das 57.239 contemplações em `dados/`.
1. **Webhook × respond.io:** se o número ficar no respond.io, ele provavelmente passa a ser o dono do webhook; o webhook para o backend aparece só no plano Advanced (≈ R$ 1.920/mês). Verificar se o fluxo precisa dele.
2. 360dialog: inconsistência sobre o preço das mensagens de serviço (docs × calculadora).
3. Zenvia: tarifa de Voz e de ligação WhatsApp no Brasil **não encontrada**; confirmar recebimento por webhook no plano Specialist.
4. Supabase: confirmar pgvector no plano Pro e região São Paulo (LGPD).
5. Dimensão do embedding (1536 é placeholder) e prazos de retenção (12 meses é placeholder; precisa de jurídico).
6. Vazamento de dado técnico pela IA deve só alertar ou bloquear? (decisão do Wagner)
7. Critério de "lead quente" para o handoff.
8. Portar o `compliance.mts` do conecta-sdr (sem tocar naquele repositório) e o `playbook.mts` como persona.
9. Testar a migration em Postgres local/branch do Supabase e validar o Mermaid.
10. Medir custo real de tokens do Grok por atendimento no piloto.

## Próximos passos
1. Wagner revisa o diff e decide sobre commit/PR (nada feito ainda).
2. Escolher BSP (360dialog × Zenvia) e confirmar pendências 1–3.
3. Testar `0001_init.sql` e importar catálogo/resultados Disal (57.239 resultados, 76 grupos ativos + Recon).
4. Implementar a Edge Function `atendimento` conforme o pseudocódigo (fase 1: 6–8 semanas; fase 2: outbound, pós-venda silencioso, unit economics).

## Atualização 28/10/2026 (consolidação, branch local `cortex/consolidacao-28-10`, sem commit)
Docs novos (rascunho; números do Wagner **não verificados**): [`docs/arquimedes-disal.md`](arquimedes-disal.md) (spec do bot, Top 5, pontos a conferir) · [`docs/cenario-prazos-mistos.md`](cenario-prazos-mistos.md) · [`docs/fluxo-cascata.md`](fluxo-cascata.md) · [`docs/coleta-mensal.md`](coleta-mensal.md) · [`docs/time-e-responsabilidades.md`](time-e-responsabilidades.md) · [`docs/regras-disal.md`](regras-disal.md) (inclui conflitos com o código) · [`docs/insight-comercial.md`](insight-comercial.md) · [`centauro/leis/README.md`](../centauro/leis/README.md) (bloqueado).

**Decisões tomadas:** regras-chave Disal (lista em `docs/regras-disal.md`); fluxo em cascata (só se renderiza o que o Wagner escolhe); time e papéis (só o Cortex Build commita, só com aprovação); embutido 25% se o grupo teve lance fixo, 10% se não teve (regra geral, N5 fechado em 01/11: ver `docs/regras-disal.md`; exceções sem fixo vêm do flag de catálogo `tem_lance_fixo = false`, nunca de número de grupo no código); coleta semanal é o motor, rerun completo na tabela mensal.

**Decisões abertas novas:** (a) aceitar a inversão do ranking ou forçar o filtro 25% primeiro; (b) autorizar o GitHub para o Cortex Build; (c) confirmar 003300 = 25% (revalidado em 10%: 52 assembleias sem fixo; 25 grupos com 25% e 46 com 10%, soma 71 × "~70"). **Já abertas:** `solver/NOTAS_DUVIDAS.md` V1 a V8 (em especial V1 `n_ofertantes_fixo_medio`, V2 feriado, V4 mediana e `<` × `<=`, V7 planilha mestra).

**A conferir:** unidade das medianas citadas pelo Wagner (45–54 é % de quê? o armazenamento já está decidido: fração da categoria, I2); fórmula pós do Wagner não reproduzível só com os dados informados; regra de embutido por histórico × por número × flag do catálogo.

**Bloqueado:** absorção de `conecta-sdr` (`compliance.mts`, `playbook.mts`) e `conecta-captacao` (`CLAUDE.md`): sem acesso de leitura (ver `centauro/leis/README.md`); planilha mestra do Drive; abertura de PRs (token sem permissão de Pull requests).

## Revisão do Cortex Reviewer (01/11/2026, branch local `cortex/revisao-reviewer`, sem commit)
Itens mecânicos resolvidos (detalhes em `solver/NOTAS_DUVIDAS.md`, seção "Revisão do Cortex Reviewer"):
- **Solver:** `embutido_excecao` removido (campo morto; a exceção sem fixo é o flag `tem_lance_fixo = false`, ver N5); `chance_fixo` com fonte única (`niveis.py`); `extras_oportunidade` em `prazos.py`; limite de 8 dias numa constante só (`modelos.MAX_DIAS_COLETA`); `proxima_assembleia` aceita lista e usa a seguinte quando o prazo venceu (com uma data só: `null` + `motivo_assembleia_aplicavel`); data malformada vira `null` + `datas_invalidas` em vez de erro; `Combo.faixa_credito` removido; ranking de produção extraído para `ranking.py` (o serviço não importa mais `forca_bruta.py`, que fica fora da imagem via `solver/.dockerignore`).
- **Job semanal:** `data_coleta` pela data local da Bahia (`America/Bahia`, fallback UTC-3); `cofre.assembleias` guarda listas de lances só na janela de 6.
- **I2 (unidade e comparação, decidido com autorização do Wagner):** tudo em fração da categoria 0..1 no código e no banco (migration nova `0003_fracao_embutido_mediana.sql` converte as colunas 0..100 da `0001`); % só na apresentação; `embutido_cobre_mediana` = `mediana <= pct_embutido_max` no solver e na view. Regras de negócio sem mudança; teste de equivalência em `scrap/test_scrap.py`. Motivo: solver, `0002` e job já eram fração; só a `0001` destoava.
- **Testes:** varredura de número de grupo no repo inteiro (exclusões documentadas no teste); imports sem uso removidos.
- **Fechados em 01/11/2026 (decisões do Wagner):** I1 (8 colunas tipadas na `fato_cotas`, migration `0005`, populadas do `extra`; ver `solver/NOTAS_DUVIDAS.md`) e N5 (regra geral do embutido abaixo). Faixa ideal 65–85% da idade do grupo: **mantida** na view `grupos_disal_faixa` (sem evidência de descarte; ver NOTAS).
- **Migrations não testadas em Postgres:** `0003` (fração), `0004` (oportunidades, branch `cortex/arquimedes-grid`) e `0005` (I1) só passaram no `sqlcheck`. Não há servidor Postgres de teste neste ambiente: rodar as três num banco de **teste** antes de produção.

### Embutido: regra geral (N5)
**Regra geral (N5, decisão do Wagner, 01/11/2026):** embutido máximo **25%** da categoria se o grupo **teve lance fixo**, **10%** se **não teve**. O solver lê só os flags do catálogo (`tem_lance_fixo` → `pct_embutido_max` 0,25 ou 0,10), nunca o número do grupo. As exceções sem fixo (003300, 004100 a 004104, 006207) não são regra no código: chegam como `tem_lance_fixo = false` no catálogo e, pela regra geral, `pct_embutido_max = 0,10`. `pct_embutido_max = 0` continua valor válido de catálogo (grupo sem embutido), mas não é como essas exceções são marcadas.


