# NOTAS_DUVIDAS — ambiguidades e contradições da ESPECIFICACAO_V1_1.md (antes ESPECIFICACAO_V1.md)

Cada item: seção da spec, o que está escrito, leitura adotada (a mais literal) e pergunta ao Wagner.

**D1 — S4 (seção 5) × teste 4 (seção 12): "minimizar o recurso usado" × "embutido mínimo necessário".**
Minimizar `Σ lance − Σ e` empurraria o embutido para o máximo; o próprio parêntese de S4 ("usa o necessário, nunca o máximo") e o teste 4 pedem o mínimo.
Adotado: embutido mínimo necessário (recurso usado = ΣR − e_min). Pergunta: confirmar que a prioridade é "embutido mínimo", não "recurso mínimo"?

**D2 — 4.5 (faixa superior do crédito) × 6.3 (refinamento só com G = ΣR − B).**
O MILP pode exigir embutido só para não passar de A(1+δ) (ex.: 2 cartas somando 100.000 com A=70.000, mesmo com B cobrindo todo o lance). O refinamento da 6.3 só garante Σe ≥ G e depois "reverifica o líquido", então esses candidatos viram `descartado_discreto`. Também conflita com o teste 4 ("embutido = 0 quando B cobre").
Adotado: leitura literal (`Parametros.refino_respeita_teto_credito = False`). A opção `True` usa Σe ≥ max(G, ΣC − A(1+δ)). Pergunta: qual vale? Com a literal, boa parte dos candidatos do MILP seria descartada.

**D3 — Seção 2: `h = #{j <= N : c_j <= M}`.** N conta assembleias válidas (não nulas), mas j indexa posições 1..6 (com possíveis nulos).
Adotado: h = nº de c_j NÃO nulos (entre c1..c6) com c_j <= M. Pergunta: correto?

**D4 — W = 0 com N >= 1 (c1 nulo).** Não há nível livre com w >= 1 (w_min = 1); só sobra o nível fixo, se houver. Adotado assim. Pergunta: aceitável, ou c1 nulo deve usar o último c disponível?

**D5 — SEM_HISTORICO e nível fixo (2 × 4.10).** 4.10 remove SEM_HISTORICO, mas o nível F não depende do histórico livre. Adotado: remove o tipo inteiro (literal). Com `incluir_sem_historico=True` entra com um nível "referencia" (lance dos irmãos, p = None) e, se houver, o fixo. Pergunta: grupo sem histórico livre mas com lance fixo deveria entrar só pelo nível fixo?

**D6 — Ranking com p = None (incluir_sem_historico).** A spec diz "fora do ranking por padrão" mas não diz como ranquear quando incluído. Adotado: combos com p nulo ficam depois de todos os que têm p, e entre si seguem o resto da chave A2. Pergunta: como devem aparecer?

**D7 — Nível fixo: n̄ ausente ou 0.** Sem n̄ não há p = 1/n̄. Adotado: sem nível fixo (não inventa p). n̄ < 1 → p = 1 (limite [0,1]).

**D8 — 8 (Função 1), versão SEM: parcela.** O texto lista só ΣR ≤ B e faixa de ΣC; 4.6 (parcela) vale ("mesmas restrições 4.1 a 4.10"). Adotado: parcela ≤ Pmax nas duas versões. Combo entra na saída se ao menos uma versão for viável.

**D9 — Função 1 usa só o nível w_ref.** Adotado: um nível livre por tipo (o de menor w mantido ≥ w_ref); o nível fixo não é usado na Função 1. Tipo sem esse nível não entra. Pergunta: incluir o nível fixo na Função 1?

**D10 — Função 1, COM embutido: "distribuído por teto de cada carta".** Distribuição não definida. Adotado: preenchimento guloso na ordem das cartas até o teto (o total é o mínimo G; só a divisão entre cartas é arbitrária).

**D11 — S3 "taxa <= taxa* + 0,5": unidade.** O texto diz "escalar em milhares de reais dentro do solver"; 0,5 pode ser R$ 0,50 ou R$ 500. Adotado R$ 0,50 (`tol_taxa_rs`). S4/S5 sem tolerância (parcela e recurso congelados no ótimo exato).

**D12 — "Ranking" com tol_prob (A2).** Tolerância não gera ordem total. Adotado: seleção iterativa (pega o melhor com P ≥ P_max(1 − tol_prob), remove, repete).

**D13 — cota_id × planos × q_π (seção 1/9).** fato_cota diz "uma linha por cota física" mas tem plano_pct. Adotado: linhas com o mesmo `cota_id` são variantes de plano da mesma cota física e dividem q_π (menor qtd_min das linhas, teto 15); `cota_id` se repete por unidade na saída. Tipos idênticos de cota_ids diferentes são agregados, com atribuição de ids por emparelhamento.

**D14 — qtd_min/qtd_truncada.** Adotado: q = min(qtd_min, 15); aviso `qtd_piso` se algum tipo usado tem qtd_truncada. Pergunta: confirmar semântica de qtd_min.

**D15 — Troca por reserva na revalidação (seção 10).** Os status são valida/recalculada/invalidada. Adotado: troca por reserva = `recalculada` com `metodo="reserva"`. Reservas: próximos do ranking com cota_ids disjuntos do principal, `n_reservas` = 2 (valor meu). Pergunta: quantas reservas e qual status para a troca?

**D16 — Valores padrão sem definição na spec:** `max_combos` = 100 (página), `n_reservas` = 2. A Função 1 pagina com `offset`; `truncado` = true quando há mais combos após a página ou quando algum ramo poderia passar de `max_cartas_enum`.

**D17 — Campo W na saída.** Devolvo `W` (sequência consecutiva do grupo, 0..6), `N` e o `w` do nível em `nivel_lance`. Pergunta: "W por carta" é isso?

**D18 — Teto/flag inválido.** pct_embutido_max fora de {0, 0,10, 0,25} gera alerta `flag_invalido` (vale o flag assim mesmo). Divergência flag × regra por número gera alerta `divergencia_teto`; vale o flag.

## Decisões provisórias aguardando Wagner (TODO Wagner)

- **P1 — `modo_probabilidade`** = `sequencia_W_sobre_6` (decidido pelo Wagner) | `fracao_h_sobre_N`. Flag em `Parametros`; backtest compara os dois.
- **P2 — `delta_credito`** = None (decidido pelo Wagner: sem teto de sobra; o `gap` mostra a sobra). Valor opcional reativa o teto.
- **D1 provisório:** S4 = embutido mínimo necessário, depois recurso mínimo (`ORDEM_CANDIDATOS`); o ranking final A2 mantém a ordem da spec (recurso → embutido). Alternativas: D2 `refino_respeita_teto_credito`.
- **Candidatos (K_top):** o MILP escolhe candidatos por S1..S5 + exclusão por conjunto de tipos usados; força bruta usa a mesma ordem (oráculo).
- **Nível sem p:** `LN_NULA = -50` no objetivo de log-probabilidade quando o nível não tem p (só `incluir_sem_historico`).
- **Seção 7:** além de R1 (crédito, parcela) e R2, sempre tento a opção "recurso" (sA=sP=0, mínimo sB); a spec só pede R2 se R1 for inviável. Até 3 opções. O universo da aproximação é reconstruído sem o filtro de parcela quando se passa o snapshot.
- **Gap do MILP** 0,5% e tempo limite 10 s por solve (parâmetros); os testes usam gap 0.
- **Ramo lance fixo:** só cota única por grupo (sem unificar cartas no ramo fixo); `top_fixo` = 10; crédito alvo medido sobre o crédito líquido (bruto − embutido necessário); filtros duros: parcela ≤ Pmax e crédito bruto ≤ A(1+δ); `fixo_exigir_embutido_cobrir` = False (grupos com teto < 25% aparecem com `falta_recurso_rs` > 0 e `embutido_cobre_lance` = false). Pesos padrão: fixo 0,40; crédito 0,30; taxa 0,15; parcela 0,15 (ajustáveis, ponto 1). Pergunta: com B = 0 e teto < 25%, excluir esses grupos?
- **Regra de W (ponto 4):** depois da probabilidade (dentro de `tol_prob`) e ANTES da taxa, desempata pela soma de W dos níveis das cartas (`Combo.w_soma`; fixo conta 0). Flag `w_desempate`. No MILP é um estágio lexicográfico entre L e taxa. Alternativa não adotada: W como peso multiplicativo da probabilidade.
- **Job semanal:** 1 assembleia ≈ 1 mês (qtd_fixo_contemplado_mes = fixos nas últimas ≤ 6 assembleias ÷ nº dessas assembleias); n_ofertantes_fixo_medio = média das assembleias em que a coluna `n_ofertantes_fixo` veio preenchida. Esquema do cofre (colunas em `cofre.py`) é suposição: TODO Wagner confirmar. Percentuais > 1 são lidos como % (15 → 0,15).
- **Backtest:** y = (M ≥ menor lance livre contemplado em t); avalia todos os níveis de cada assembleia com lance livre; assembleias com t = 0 (sem passado) são puladas.
- **Categoria de veículo:** campo `categoria_veiculo` (carro|moto|caminhao) na cota e opcional no pedido; sem ele cada categoria é resolvida separadamente (nunca mistura) e o ranking final junta os resultados. Prazo (`prazo_total`) é só informativo: prazos diferentes sempre liberados; sem limite de cartas além de `max_cartas_enum` (Função 1) e `MAX_Q` por cota física.

## Conflitos entre a orientação final e a ESPECIFICACAO_V1_1.md (então ESPECIFICACAO_V1.md) (a orientação prevaleceu)

| # | Spec | Orientação (aplicada) |
|---|---|---|
| C1 | J = {0,5,10,15,20,21,25}% | J = {0,5,10,15,20,25}% ∩ [0, teto]; 21% removido (`embutido.J`). |
| C2 | Lance livre sempre via MILP | recurso_proprio = 0 → ramo lance fixo, sem MILP e sem probabilidade (`ramo_fixo.py`). |
| C3 | Plano 75/100 tratados como variantes no mesmo universo | 75% testado SEMPRE primeiro; 100% só se o 75 não resolver ou como `alternativa_100` rotulada (`funcao2.py`). |
| C4 | Ranking A2: probabilidade, recurso, embutido, taxa… | W (sequência) desempata depois da probabilidade e antes da taxa. |
| C5 | Seção 5 cita CBC como fallback | CBC descartado; sem menção no código. Removida a frase da linha 69 da então ESPECIFICACAO_V1.md (hoje ESPECIFICACAO_V1_1.md). Força bruta = só oráculo de teste. |
| C6 | Seção 3/10: fato_cota lido do Postgres/snapshot de qualquer origem | Solver só lê a tabela fato (JSON local + ponteiro atômico); o cofre só entra no job semanal e no backtest. |
| C7 | Tabela fato sem `qtd_fixo_contemplado_mes` | Coluna nova (Cota, job e snapshot). |
| C8 | Sem noção de categoria de veículo | `categoria_veiculo` (nunca mistura carro/moto/caminhão). |

## v1.1 (27/10/2026): decisões novas e dúvidas abertas

- **V1 — `n_ofertantes_fixo_medio` × documento de parâmetros (CONFLITO ABERTO, decisão do Wagner).** O documento de parâmetros revisado pelo Claude manda REMOVER `n_ofertantes_fixo_medio`; a decisão do Wagner (relay do MiroFish Cortex) diz que a chance do lance fixo é 1 / nº de ofertantes. Hoje o campo existe (nível fixo da Função 2 e `chance_fixo` informativo no ramo fixo; o ranking multi-critério NÃO o usa). Se o Wagner confirmar o documento, remove-se o campo, o nível fixo `p_F` e `chance_fixo`.
- **V2 — Prazo de entrada e feriado (a decidir pelo Wagner).** Implementado: prazo = assembleia − 2 dias corridos; se cair em sábado, domingo ou feriado, recua até o dia útil anterior (feriado tratado igual a fim de semana). Alternativas possíveis: contar 2 DIAS ÚTEIS antes; ou feriado fazer o prazo avançar. Feriados entram só como parâmetro (`parametros.feriados`), nunca codificados. Prazo é inclusivo (entrar no dia do prazo vale).
- **V3 — Assembleia seguinte.** O snapshot carrega só `proxima_assembleia` (uma data por cota/grupo). Fora do prazo a saída marca `prazo_vencido = true` e `assembleia_aplicavel = null`; a função pura `assembleia_aplicavel` sabe escolher a seguinte, mas precisa da lista de próximas datas (não existe no snapshot). Pergunta: o job deve gravar a lista? **[revisão N4, 01/11]** Parcialmente resolvido: o snapshot JSON já aceita lista em `proxima_assembleia` e o solver usa a seguinte; a coluna `fato_cotas.proxima_assembleia` (0002) continua uma data só e o job ainda não grava a lista.
- **V4 — `mediana_lance_livre`.** Definição adotada: mediana de TODOS os lances livres contemplados nas últimas ≤ 6 assembleias do grupo (fração da categoria). Alternativa: mediana dos menores lances por assembleia (c1..c6). **Resolvido na revisão I2 (01/11):** `embutido_cobre_mediana` = `mediana <= pct_embutido_max`, tudo em fração da categoria, no solver e na view (migration 0003). Antes: solver com `<` estrito e view da 0001 com `<=` e %.
- **V5 — `data_coleta`.** O job grava a data da execução quando o catálogo não traz `data_coleta`; `atualizado_em` do snapshot NÃO é usado como substituto (é a hora de gerar o snapshot, não da coleta). Sem `data_coleta` ou sem `hoje`, `desatualizada = null`.
- **V6 — Teste de sanidade por número de grupo removido.** `teto_esperado_por_numero`/`divergencia_teto` e a lista de exceções saíram do código (decisão: nunca por número de grupo). Perde-se o alerta automático de flag errado; a verificação por série é do catálogo (empírica).
- **V7 — PLANILHA MESTRA PENDENTE.** Drive `1DrXxebqL0RWIB6GDHgqCC7-k-PRbglnkqFwvs7Ht5MM` (abas `1_Indice_fontes`, `2_Parametros` com 20 colunas por grupo e plano, `3_Historico_6`, `4_Oportunidades`, `Dicionario` com classes FIXA/VIVA/HISTÓRICO/CALCULADA): sem conector de Drive, não foi lida. NÃO foram inventadas as 20 colunas. Falta exportar para `dados/` (pasta ignorada pelo git); depois alinhar `fato_cotas` (migration 0002) e `schema/snapshot.exemplo.json`.
- **V8 — Desempate de sequências iguais** segue em aberto (hoje: probabilidade, depois soma de W, depois taxa, parcela, recurso, embutido, nº de cartas).

## Pendências

- **Backtest com dado real (teste de aceite 6): BLOQUEADO.** Sem conector de Drive/Sheets nesta sessão e `DownloadFile` não aceita Drive; não usei navegador nem contornei. `backtest.py` e `cofre.py` prontos e testados com dado sintético; basta colocar o export em `/workspace/disal-solver/dados/` (CSV ou xlsx, esquema em `cofre.py`).
- Esquema real do cofre e do catálogo de cotas (entrada do job): suposto, a confirmar.
- Carga do catálogo/cotas a partir do Postgres e agendamento do job (cron): fora deste pacote.
- Unificação no ramo lance fixo (combinar várias cartas de fixo): não modelada.
- Fórmula pós-contemplação (fase 2, ponto 7): só documentada no README. Ágio e transferência (ponto 8): fora de escopo.
- Fase 2 (seção 11): não implementada, conforme a spec.

## Revisão do Cortex Reviewer (01/11/2026, branch local `cortex/revisao-reviewer`, sem commit)

- **I2 — Unidade e comparação (RESOLVIDO; decisão de engenharia autorizada pelo Wagner, regra de negócio intacta).**
  - **Unidade:** todo percentual de regra é **fração da categoria (crédito + taxa), 0..1**, no código e no banco: `pct_embutido_max` ∈ {0; 0,10; 0,25}, `mediana_lance_livre`/`mediana_lance_pct`, `resultados_disal.lance_pct`. Conversão para % só na apresentação (texto ao cliente, dossiê). Motivo: solver, 0002 (`fato_cotas`), job semanal e snapshot JSON já eram fração; só a 0001 usava 0..100. Mudar uma migration é mais barato e menos arriscado que mudar todo o código, e um padrão único elimina o erro de comparar 45,56 com 0,25.
  - **Como:** migration nova `0003_fracao_embutido_mediana.sql` (divide por 100, troca os checks para 0..1, recria a view `grupos_disal_faixa`). A 0001 não foi editada: migration aplicada não se reescreve, e a 0003 funciona com banco vazio ou já migrado. `x / 100` é exato (25 → 0,25). Base = categoria (`base_lance = 'credito_mais_taxa'`); o comentário "% do crédito" da 0001 estava errado quanto à base. `idade_pct` da view continua em % (dado de apresentação calculado, não regra). Nomes de coluna mantidos (`*_pct` já é fração no código, ex.: `taxa_pct`).
  - **Comparação:** `<=` — o embutido que IGUALA a mediana cobre o lance. Fonte única no solver: `prazos.embutido_cobre_mediana`; a view usa o mesmo `<=`.
  - **Equivalência (`scrap/test_scrap.py::TI2UnidadeFracao`):** flags 0/10/25 % ÷ 100 == `TETOS_VALIDOS`; embutido em R$ igual; `embutido_cobre_mediana` idêntico à regra da view antiga (% com `<=`) em toda a grade de 0 a 60 % (centésimos de ponto, inclui mediana == teto); contagem de contemplações, média na janela de 6, menor lance contemplado e mediana idênticos com o lance do cofre em '23,5%', '23.5' ou '0.235'. Não existe média de 3 meses no código (nada a converter).
  - **Única mudança visível:** mediana exatamente igual ao teto agora sai `embutido_cobre_mediana = true` no solver (antes `false`); a view já era assim.
- **I1 — RESOLVIDO (01/11/2026, decisão do Wagner: implementar).** Migration `0005_fato_cotas_colunas_i1.sql` adiciona à `fato_cotas` 8 colunas tipadas: `status text` (disponivel | saiu_da_venda), `categoria_veiculo text` (carro | moto | caminhao), `qtd_min int` (>= 1), `qtd_truncada boolean`, `lance_fixo_pct numeric` (fração 0..1), `n_ofertantes_fixo_medio numeric` (>= 0), `lance_ref_irmaos numeric` (fração 0..1) e `prazo_total int` (>= 1, meses). Populadas de `extra` com as chaves de mesmo nome (as do snapshot JSON). Casts seguros: inválido/ausente vira NULL; percentual em (1, 100] vira fração (/100), padrão I2. Idempotente (`add column if not exists`, constraints recriadas, UPDATE só preenche NULL). `extra` mantido. Regra única em Python: `solver/fato_colunas.py` (`colunas_de_extra`), usada pelo job (`scrap/resumo_semanal.linhas_fato_cotas`, opção `--linhas-fato`) e pela leitura (`contrato.snapshot_de_dict` cai no `extra` se a coluna faltar). Testes: `solver/test_i1_fato_colunas.py`. Limite: valor `1` é lido como fração (100%), não 1%. **Não rodada em Postgres** (sem servidor de teste no ambiente): rodar 0003, 0004 (branch do grid) e 0005 em banco de teste antes de produção.
- **N5 — FECHADO (01/11/2026, decisão do Wagner).** Regra geral: embutido 25% se o grupo teve lance fixo, 10% se não teve. Exceções sem fixo (003300, 004100–004104, 006207) entram como `tem_lance_fixo = false` no catálogo → `pct_embutido_max = 0,10`; nunca número de grupo no código (teste N10 varre o repo; `.md` fora da varredura por ser documentação). Código já consistente: o solver lê `pct_embutido_max`/`tem_lance_fixo` do catálogo e só alerta `flag_invalido` fora de {0; 0,10; 0,25}; nada mudou no código. Mudança de leitura na spec: as exceções deixam de ser descritas como "sem embutido (0%)" e passam a 10% (como o Arquimedes revalidou o 003300). `pct_embutido_max = 0` segue aceito como dado.
- **Faixa ideal 65–85% da idade do grupo — MANTIDA (01/11/2026).** Sem evidência de descarte em: `README.md`, `docs/*.md`, `solver/*.md`, `schema/README.md`, `supabase/migrations/0001`–`0005`, `supabase/functions/atendimento/PSEUDOCODIGO.md` e no histórico do git (`git log -S'faixa ideal'`). Continua na view `grupos_disal_faixa` (`na_faixa_ideal`, recriada igual na 0003). O solver v1.1 não a usa (não entra em probabilidade nem ranking); isso é ausência, não descarte.
- **I6 — Confirmado resolvido.** Verificado: nenhum módulo de produção importa `forca_bruta` (teste `test_i3_producao_nao_importa_forca_bruta`, varre os `.py` do solver que não são teste/oráculo); `forca_bruta.py` fica fora da imagem (`solver/.dockerignore`); C5 já dizia "força bruta = só oráculo de teste".
- **S1, S3, S4 — não localizados:** não há relatório do Reviewer no repo com esses itens; S1..S5 da spec são estágios do MILP, não itens de revisão. Nada inventado.

## Arquimedes grid (01/11/2026, branch `cortex/arquimedes-grid`)

Decisões tomadas sem consulta (rotineiras; revisar):
- **Faixas:** 50/80/100/180/200/250 mil; janela `[T, min(1,25·T, próxima))`; tolerância 25% configurável. A faixa é medida pelo crédito **bruto**.
- **Top-K por faixa = 1.** Multiconjuntos equivalentes aparecem uma vez só, e só as combinações de cobertura mínima entram (tirar a menor carta derruba abaixo da faixa).
- **Agregação:** mediana e embutido ponderados pela categoria; prazo = menor; próxima assembleia = mais cedo.
- **Desempate:** mediana < embutido maior < prazo maior < excedente menor < menos cartas < chave canônica.
- **Mediana:** fração da categoria (entrada > 1 lida como %). TODO Wagner: confirmar que a mediana da planilha é % da categoria, e não do crédito.
- **Parcela paga:** 1 × parcela antes; divisor = prazo restante (fórmula literal). Para o 3301 dá 963,75. Com a flag `descontar_pagas_no_divisor`, dá 989,80. A conta citada (989,89) não fecha em nenhuma das duas. TODO Wagner: qual divisor?
- **Embutido usado** = min(% embutido, mediana) × categoria: o embutido nunca passa do lance.
- **Trava `max_nos`** (300 mil por faixa): só em empate total artificial; a CLI avisa quando a faixa saiu sem prova de ótimo.
- **Exemplo top 5:** taxa ADM de 3304, 3308 e 3312 assumida em 18% só no exemplo. A faixa de 80 mil sai vazia porque 1 carta (~59–69 mil) fica abaixo e 2 cartas (≥ 118 mil) passam do teto de 100 mil.
- `0004_oportunidades.sql` (renumerada de 0003 em 01/11/2026; a 0003 fica reservada para `0003_fracao_embutido_mediana.sql`, da branch `cortex/revisao-reviewer`, que não existe nesta branch) só passou no `sqlcheck`. Não foi testada em Postgres: rodar 0003, 0004 e 0005 em ambiente de teste antes de produção.
