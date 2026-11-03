# Resolvedor de combinações de cartas Disal (veículo) — Especificação matemática v1.1

**v1.1 — 27/10/2026.** Renomeada de `ESPECIFICACAO_V1.md` (`git mv`; o histórico da v1 está no git). Cada mudança sobre a v1 vem marcada com **[v1.1]**. Resumo:

| # | Mudança sobre a v1 | Onde |
|---|---|---|
| 1 | Probabilidade padrão = sequência W / 6 (nunca exibida ao cliente como número frio; W e cobertura continuam na saída). h/N fica só como opção de comparação. | A1, seção 2 |
| 2 | Teto de 10% de sobra de crédito (A5) removido: sem trava, a sobra aparece em `gap.sobra_credito`. | A5, 4.5, 4.10 |
| 3 | Base do teto de embutido = categoria (crédito + taxa), agora FIXA. Passo de 5 pontos; teto 10% ou 25% pelo flag `pct_embutido_max`, verificado por série, nunca por número de grupo. Exceções sem fixo são dado do catálogo (`tem_lance_fixo = false` → 10%, regra geral N5), não código. | seção 1 |
| 4 | Lance fixo: ramo separado; chance = 1 / nº de ofertantes, sem mediana; também é oportunidade para cliente sem recurso (ranking multi-critério). | seção 2, `ramo_fixo.py` |
| 5 | Plano 75% é pré-filtro: testado sempre primeiro; o 100% só se o 75% não resolver, ou como alternativa rotulada. | `funcao2.py` |
| 6 | Mediana do lance livre do grupo volta como DADO COMERCIAL (`mediana_lance_livre`), com o flag `embutido_cobre_mediana`; nunca entra em probabilidade nem ranking. | seção 9 e 10 |
| 7 | Validade: `data_coleta` com mais de 8 dias (parâmetro) = `desatualizada`. | seção 9 e 10, `prazos.py` |
| 8 | Prazo de entrada de cliente novo: 2 dias corridos antes da assembleia; fim de semana ou feriado recua para o dia útil anterior; fora do prazo vale a assembleia seguinte. | seção 10, `prazos.py` |
| 9 | Saída por oportunidade ganha flags de validade e prazo. | seção 10 |
| 10 | Schema da tabela fato ganha `mediana_lance_livre`, `data_coleta`, `proxima_assembleia`. Alinhamento com as 20 colunas da aba `2_Parametros` da planilha mestra: **PENDENTE** (planilha não exportada). | seção 9 |

Escopo v1: pré-contemplação. Planos 100% e 75%. Só veículo. Sem pós-contemplação (fase 2, ver seção 11).
Fora do escopo: ágio, transferência, teto de 85% por assembleia, Beta-Binomial. **[v1.1]** A mediana continua fora do cálculo; ela só existe como dado comercial (seção 9).

## 0. Premissas assumidas (cada uma é um parâmetro ou um campo; mudar não exige refazer o modelo)

- A1. **[v1.1]** Probabilidade individual de uma carta num nível de lance = W / 6, onde W = sequência consecutiva (1..6) de assembleias que o lance teria coberto (`modo_probabilidade = "sequencia_W_sobre_6"`, padrão). Nunca comunicada ao cliente como número frio (a Centauro fala em sequência); W e a cobertura (`ganharia_em` de `de_assembleias`) seguem na saída. Alternativa de comparação no backtest: p = h / N (`"fracao_h_sobre_N"`), com N = nº de assembleias válidas nas últimas 6 e h = nº dessas em que o lance cobriria. v1: o padrão era h / N.
- A2. "Contempla" = toda carta com cobertura W >= w_min (padrão 1). Ranking da camada de probabilidade: probabilidade conjunta desc (com tolerância tol_prob, padrão 0), depois taxa total asc, parcela asc, recurso usado asc, embutido asc, nº de cartas asc.
- A3. Lance fixo pode ser financiado por embutido (a fórmula da fase 2 subtrai lance fixo e embutido juntos).
- A4. Probabilidade conjunta = produto das individuais (regra mantida). Cartas do mesmo grupo no mesmo combo geram aviso `mesmo_grupo`, sem restrição.
- A5. **[v1.1]** SEM teto de sobra de crédito: `delta_credito = None` (padrão). O solver devolve tudo que é viável e a sobra aparece explícita em `gap.sobra_credito`. Um valor (ex.: 0,10) reativa o teto alvo*(1+delta_credito) como parâmetro. v1: padrão 0,10.
- A6. Histórico de lance é em % da categoria. O menor lance contemplado exclui sorteios e lance fixo.
- A7. Categoria e % de embutido valem igual nos planos 100% e 75% (só a parcela muda). Conferir na planilha planos_creditos.

## 1. Conjuntos e dados

K = tipos de cota (cotas idênticas agregadas: mesmo grupo, plano, crédito, taxa, parcela).
Π = cota física (agrupa as variantes de plano da mesma cota). q_π = quantidade disponível, no máximo 15 (piso, nunca usar mais).
Para cada tipo k:
- C_k crédito; t_k taxa de adm (fração); Cat_k = C_k (1 + t_k) categoria (sem seguro e sem fundo de reserva).
- TaxaR$_k = C_k t_k (taxa sobre a carta total).
- P_k parcela do plano (100% ou 75%).
- ē_k teto de embutido, fração da CATEGORIA, vindo dos flags `pct_embutido_max` (0, 0,10 ou 0,25). Nunca por número de grupo. **[v1.1]** O teste de sanidade por número de grupo da v1 foi REMOVIDO do código: o teto e a ausência de lance fixo em 003300, 004100 a 004104 e 006207 chegam como DADO do catálogo, verificado empiricamente por série. **[N5, 01/11/2026]** Regra geral: `tem_lance_fixo = true` → `pct_embutido_max = 0,25`; `false` → 0,10 (as exceções acima são `tem_lance_fixo = false`, logo 10%). `pct_embutido_max = 0` segue válido como dado (grupo sem embutido). O solver só alerta (`flag_invalido`) se o valor do flag não for 0, 0,10 ou 0,25.
- Embutido por unidade: e <= ē_k Cat_k. Exemplo: C = 70.000, t = 16% -> Cat = 81.200; 25% = 20.300.
- **[v1.1]** A base do teto é a categoria (crédito + taxa): decisão FIXA (antes pendente). Todo lance (livre, fixo, embutido) incide sobre a categoria.
- **[v1.1]** Percentuais permitidos de embutido: J = {0, 5, 10, 15, 20, 25}% intersecção [0, ē_k] (passo de 5; o 21% da v1 saiu).

Entradas do pedido: A crédito líquido alvo, Pmax parcela máxima, B recurso próprio (orçamento de lance), tipo de bem = veículo. Parâmetros: w_min = 1, delta_credito, tol_prob, K_top.

## 2. Níveis de lance por tipo (pré-calculado por snapshot, por grupo)

Para cada grupo g, c_{g,j} = menor lance livre contemplado na assembleia j (j = 1 mais recente ... 6), em % da categoria; nulo se a assembleia não teve lance livre contemplado (exclui sorteio e fixo).
Cobertura de w assembleias seguidas exige lance >= M_{g,w} = max(c_{g,1..w}). M é não decrescente em w (usar só enquanto os c existirem em sequência).
Nível livre l = w: lance% = M_{g,w}; h_{g,w} = #{j <= N : c_j <= M_{g,w}}; **[v1.1]** p_{g,w} = w / 6 (padrão; v1: h_{g,w} / N, hoje só como `fracao_h_sobre_N`).
Se M_{g,w} = M_{g,w+1}, manter só o w maior (domina).
Nível fixo F (se tem_lance_fixo): lance% = 0,25 (trava em 25% da categoria); p_F = 1 / n̄_ofertantes (média das últimas até 6 assembleias com fixo; limitar a [0,1]). **[v1.1]** É um ramo separado ("1 contra o número de ofertantes", sem mediana). Para cliente sem recurso (B = 0) o ramo fixo (`ramo_fixo.py`) ranqueia por critério múltiplo e expõe `chance_fixo = 1 / n̄` só como informação: o ranking não usa esse número. Conflito aberto: o documento de parâmetros revisado manda remover `n_ofertantes_fixo_medio` (ver NOTAS_DUVIDAS).
Lance em reais: R_{k,l} = lance%_l * Cat_k.
Histórico: N = 0 -> flag SEM_HISTORICO: p = null, sem número inventado; fallback = lance de referência dos grupos irmãos (mesma série e plano), só informativo; fora do ranking por padrão (param incluir_sem_historico). N entre 1 e 5 -> flag PARCIAL (p calculado com o N disponível, mostrar N).
Lance acima de 100% da categoria é descartado (limite matemático, não é a trava de 85%).

## 3. Variáveis (Função 2, MILP)

- n_{k,l} inteiro >= 0: unidades do tipo k no nível de lance l.
- e_{k,l} contínuo >= 0: embutido total da célula (k,l).
- Folgas (só nos modos de aproximação): sA, sP, sB >= 0.

## 4. Restrições

1. Disponibilidade: Σ_{k∈π} Σ_l n_{k,l} <= q_π para toda cota física π. Isto impede usar o mesmo exemplar em dois planos.
2. Teto de embutido: e_{k,l} <= ē_k Cat_k n_{k,l}.
3. Sem excesso de embutido: e_{k,l} <= R_{k,l} n_{k,l}.
4. Recurso próprio (fungível entre cartas): Σ (R_{k,l} n_{k,l} − e_{k,l}) − sB <= B. O embutido NÃO é fungível: as restrições 2 e 3 valem célula a célula.
5. Crédito líquido: Σ (C_k n_{k,l} − e_{k,l}) + sA >= A, e, **só se `delta_credito` estiver definido (v1.1: padrão sem teto)**, Σ (C_k n_{k,l} − e_{k,l}) <= A (1 + delta_credito).
6. Parcela: Σ P_k n_{k,l} − sP <= Pmax.
7. Cobertura mínima: só existem níveis com cobertura >= w_min (níveis abaixo de w_min não são criados). Nível F sempre é elegível.
8. Imóvel nunca entra no universo (filtro duro antes do modelo).
9. Sem limite de cartas: nenhuma restrição de cardinalidade no modelo.
10. Pré-filtros: remover P_k > Pmax, C_k > A (1 + delta_credito) (**[v1.1]** só com teto ativado), saiu_da_venda, q = 0, e SEM_HISTORICO (se não incluir).

## 5. Objetivo (resolução lexicográfica em solves sequenciais, não soma ponderada)

Escalar valores em milhares de reais dentro do solver.
- S1: maximizar L = Σ n_{k,l} ln p_{k,l} (log da probabilidade conjunta; produto linearizado). P* = exp(L*).
- S2: fixar L >= L* − ln(1/(1 − tol_prob)) (com tol_prob = 0, L >= L*) e minimizar a taxa total Σ TaxaR$_k n_{k,l}.
- S3: fixar taxa <= taxa* + 0,5 e minimizar a parcela total.
- S4: minimizar o recurso usado (Σ lance − Σ e), depois o embutido total Σ e (usa o necessário, nunca o máximo).
- S5: minimizar o nº de cartas Σ n.
Tempo limite por solve, gap relativo 0,5%; devolver melhor solução com o gap do solver.
Solver: HiGHS (highspy ou PuLP com HiGHS).

## 6. Pipeline da Função 2 (probabilidade + ranking)

1. Carregar snapshot, filtrar (4.10), construir níveis (seção 2), agregar cotas idênticas.
2. Gerar K_top candidatos (padrão 20): resolver S1..S5, adicionar corte de exclusão sobre o conjunto de tipos usados (indicadores binários u_k, n_k <= q u_k, n_k >= u_k) e repetir.
3. Refinamento exato por candidato (aritmética em centavos, Decimal):
   - Fixar cartas e níveis. R_i por unidade i, lacuna G = Σ R_i − B.
   - Se G <= 0: nenhum embutido.
   - Senão escolher, por unidade, pct_i ∈ J ∩ [0, ē] minimizando Σ e_i com Σ e_i >= G e e_i <= R_i (DP sobre unidades; poucos itens).
   - Reverificar líquido, parcela e recurso. Se o arredondamento discreto violar o líquido, marcar o candidato `descartado_discreto` e seguir para o próximo.
4. Probabilidade conjunta = Π p_i (e produto em log). Reportar a sequência W por carta.
5. Ordenar pela chave A2. Atribuir cotas físicas (ids reais) às unidades.
6. Reservas: devolver combos de reserva com cotas físicas disjuntas do principal, para trocar quando uma carta sair da venda.

## 7. Se não houver solução exata (aproximada com gap explícito)

Relaxar em ordem (contemplação é prioridade 1; a camada anterior só relaxa se a anterior for inviável):
- R1: manter cobertura e recurso B rígidos; relaxar crédito (sA) e parcela (sP). Minimizar sA/A + sP/Pmax.
- R2: se ainda inviável, relaxar também o recurso (sB): minimizar sB/B (ou sB absoluto se B = 0).
Devolver até 3 opções: mais perto em crédito, mais perto em parcela, mais perto em recurso. Gap por dimensão: gap_credito = max(0, A − líquido), gap_parcela = max(0, ΣP − Pmax), gap_recurso = max(0, recurso necessário − B). Passar do alvo de crédito dentro da faixa não é gap.

## 8. Função 1 (todas as combinações válidas, sem ranquear)

Mesmas restrições 4.1 a 4.10, sem objetivo. Não usar MILP para enumerar. Enumeração em Python por busca em profundidade sobre tipos agregados, com poda por faixa de crédito, parcela e orçamento (opcionalmente meet-in-the-middle). Lance usa o nível de referência w_ref (parâmetro, padrão w_min).
Para cada combo listar as duas versões:
- SEM embutido: líquido = ΣC, recurso necessário = ΣR; viavel se ΣR <= B e ΣC dentro da faixa [A, A(1+delta)].
- COM embutido: G = max(0, ΣR − B); embutido mínimo distribuído por teto de cada carta (e_i <= ē_i Cat_i e <= R_i); líquido = ΣC − Σ e; viavel se G for coberto, líquido dentro da faixa e parcela <= Pmax.
Saída paginada com `max_combos` e `max_cartas_enum` (limite de performance, não regra de negócio; padrão 6; devolver `truncado: true` quando cortar).

## 9. Schema

fato_cota (uma linha por cota física e snapshot):
snapshot_id, cota_id, grupo, serie, tipo_bem, plano_pct (100 ou 75), credito, taxa_pct, categoria, parcela, prazo_total, prazo_restante, pct_embutido_max, tem_lance_fixo, lance_fixo_pct, n_ofertantes_fixo_medio, qtd_min, qtd_truncada, status (disponivel, saiu_da_venda), data_proxima_assembleia (**[v1.1]** `proxima_assembleia`), **[v1.1]** `mediana_lance_livre` (fração da categoria; dado comercial calculado pelo job a partir do cofre, nunca entra na probabilidade nem no ranking; null = desconhecida), **[v1.1]** `data_coleta` (quando o dado foi coletado; o job grava), n_assembleias_validas, c1..c6, M1..M6, p1..p6 (derivados), historico_flag (OK, PARCIAL, SEM_HISTORICO), atualizado_em. **[revisão 01/11]** `embutido_excecao` saiu da lista (N1): a exceção sem fixo/embutido é derivada de `pct_embutido_max = 0` e `tem_lance_fixo = false`. **[I1, 01/11/2026]** `status`, `categoria_veiculo`, `qtd_min`, `qtd_truncada`, `lance_fixo_pct` (fração 0..1), `n_ofertantes_fixo_medio`, `lance_ref_irmaos` (fração 0..1) e `prazo_total` são colunas tipadas da `fato_cotas` (migration `0005`), populadas a partir de `extra` pela regra de `solver/fato_colunas.py` (inválido vira NULL, nunca erro); `extra` continua com os derivados (M, p) e os valores originais. `categoria` e `prazo_restante` são calculados (não são coluna); `n_assembleias_validas`, `historico_flag` e c1..c6 seguem no array `c`/derivados.
hist_assembleia: grupo, data, menor_lance_livre_pct, n_contemplados_livre, n_sorteio, n_fixo, n_ofertantes_fixo.
Atualização do snapshot atômica (troca de ponteiro), com frescor no JSON.
**[v1.1] Duas bases:** cofre append-only (57.239 contemplações; "museu", o runtime NUNCA toca) e tabela fato (~70 grupos ativos do Clique Vendas), populada pelo job semanal `scrap/resumo_semanal.py`.
**[v1.1] PENDENTE:** alinhar as colunas da fato às 20 colunas da aba `2_Parametros` da planilha mestra (Drive `1DrXxebqL0RWIB6GDHgqCC7-k-PRbglnkqFwvs7Ht5MM`; abas `1_Indice_fontes`, `2_Parametros`, `3_Historico_6`, `4_Oportunidades`, `Dicionario` com classes FIXA/VIVA/HISTÓRICO/CALCULADA). A planilha ainda não foi exportada para `dados/`; nenhuma coluna foi inventada.

## 10. Infra e contrato

- Edge Function Supabase (Deno) só autentica e repassa. O solver roda num serviço Python separado (Cloud Run ou Fly) com HiGHS. Alternativa: HiGHS WASM. A tabela do snapshot é carregada em memória por `snapshot_id`.
- Endpoints: POST /combinacoes (Função 1), POST /probabilidade (Função 2), POST /revalidar (checa saiu_da_venda).
- Entrada: {tipo_bem, credito_liquido_alvo, parcela_max, recurso_proprio, parametros?}.
- Saída por combinação: cartas[{cota_id, grupo, plano, credito, taxa_pct, categoria, parcela, nivel_lance (livre w ou fixo), lance_pct, lance_rs, embutido_pct, embutido_rs, recurso_alocado_rs, p, W, flags}], totais {credito_liquido, parcela, taxa_total, recurso_usado, embutido_total}, probabilidade_conjunta, gap {credito, parcela, recurso, sobra_credito}, avisos [mesmo_grupo, sem_historico, parcial, qtd_piso, truncado], snapshot_id, atualizado_em, versao_regras.
- **[v1.1] Campos extras por carta/oportunidade** (compatíveis com os da v1; sem dado ou sem `hoje` saem `null`, nunca erro):
  `mediana_lance_livre`, `embutido_cobre_mediana` (mediana <= `pct_embutido_max`, ambos em fração da categoria **[revisão I2, 01/11]**; `null` se a mediana é desconhecida), `data_coleta`, `desatualizada` (`data_coleta` com MAIS de `max_dias_coleta` = 8 dias; exatamente 8 vale), `proxima_assembleia`, `prazo_entrada`, `assembleia_aplicavel`, `prazo_vencido`, **[revisão 01/11]** `motivo_assembleia_aplicavel` (por que `assembleia_aplicavel` é `null`) e `datas_invalidas` (campos de data malformados, que saem `null` em vez de erro). No ramo fixo, cada linha também traz `chance_fixo`.
  `hoje` (ISO) e `feriados` (lista de datas ISO) entram em `parametros`; o solver nunca lê o relógio nem codifica feriado.
- **[v1.1] Prazo de entrada de cliente novo** (`prazos.py`, funções puras): `prazo_entrada_cliente_novo(data_proxima_assembleia, feriados, dias_antes=2)` = 2 dias corridos antes da assembleia; se cair em sábado, domingo ou feriado, recua até o dia útil anterior (a sexta, no fim de semana). `assembleia_aplicavel(hoje, proximas_assembleias, feriados)` = primeira assembleia cujo prazo ainda não venceu (prazo INCLUSIVO: entrar no dia do prazo vale); fora do prazo vale a seguinte. **[revisão 01/11]** `proxima_assembleia` aceita uma data ou uma lista; com uma data só e prazo vencido, `assembleia_aplicavel` = `null` e `motivo_assembleia_aplicavel` = `prazo_vencido_sem_assembleia_seguinte_cadastrada` (a assembleia seguinte não é inventada). Feriado como "recuar para o dia útil anterior" é interpretação a confirmar com o Wagner.
- saiu_da_venda: antes do handoff, /revalidar. Se uma cota sumiu, trocar pela reserva disjunta; se não houver, recalcular excluindo a cota. Status: valida, recalculada, invalidada.

## 11. Fase 2 (documentada, NÃO implementar)

Saldo devedor = crédito + taxa − parcelas pagas − lance fixo − embutido − recurso próprio. Nova parcela = saldo devedor / parcelas restantes, mais seguro de vida se houver. Caso Adriano como prova.

## 12. Testes de aceite

1. Exemplo numérico: C = 70.000, t = 16% -> Cat = 81.200; embutido 25% = 20.300. **[v1.1]** O 0% das exceções vem do dado do catálogo; o teste confere que o resultado é idêntico em qualquer número de grupo.
2. Contra força bruta em instâncias com até 8 tipos: solver = força bruta em probabilidade e taxa.
3. Nunca imóvel; nunca mais de q_π cotas; nunca embutido acima do teto da carta; embutido não migra entre cartas.
4. Embutido = 0 quando B cobre o lance; senão embutido mínimo necessário.
5. Grupo sem histórico: p = null com flag e sem número inventado.
6. Backtest do modelo de cobertura nas 57.239 contemplações: prever assembleia a assembleia com as 6 anteriores e medir calibração (Brier e curva de confiabilidade).
7. Revalidação: remover uma cota do combo e conferir troca ou recálculo.
8. **[v1.1]** `test_v1_1.py`: W/6 (1), sobra no gap sem teto (2), teto só pelo flag e independente do número do grupo (3), `chance_fixo` sem mexer no ranking (4), mediana sem efeito na probabilidade/ranking e `embutido_cobre_mediana` (6), validade com bordas de 8 e 9 dias (7), prazo de entrada em dia útil, sábado, domingo, feriado e entrada no dia do prazo (8), campos de saída (9). `scrap/test_scrap.py`: mediana, `data_coleta` e `proxima_assembleia` no job (6, 7, 10).

## Revisão I2 (01/11/2026): unidade e comparação
Todo percentual de regra (`pct_embutido_max`, `mediana_lance_livre`, lances) é FRAÇÃO da categoria, 0..1, no código e no banco (a migration `0003` converte as colunas da `0001`, que eram 0..100). % só na apresentação. `embutido_cobre_mediana = mediana <= pct_embutido_max` (o embutido que iguala a mediana cobre o lance), igual no solver e na view `grupos_disal_faixa`. Regras de negócio sem mudança; equivalência numérica coberta por teste (`scrap/test_scrap.py::TI2UnidadeFracao`).
