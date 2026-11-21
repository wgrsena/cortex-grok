# Arquimedes Disal: spec do bot compilador

> Rascunho de 28/10/2026, consolidado a partir da conversa do Wagner. Nada implantado, nada commitado. Os números do Top 5 são **dados do Wagner, a validar contra a planilha mestra** (não verificados).

- **Bot:** Arquimedes Disal (id `7e195838-d018-4757-97d5-cfc9afba5cc6`).
- **Perfil:** técnico-contábil. Lê a regra, aplica a regra. **Não faz comercial** (não vende, não escolhe oportunidade, não fala com cliente).
- **Repo:** `wgrsena/conecta-cortex` (privado). Arquimedes **não tem push**; quem commita é o Cortex Build (id `7ae7940b`), só com aprovação do Wagner.

## Entrada (Drive, coleta de 25/10)
Caminho: `00_CONECTA CORTEX › 04_DOCUMENTOS OFICIAIS › 02_DISAL › WEBDISAL_RESULTADOS`

| Arquivo | Uso |
|---|---|
| `webdisal_resultados_assembleia_2026-10-25` | Planilha principal |
| `webdisal_calendario_assembleias` | Datas das próximas assembleias |
| `webdisal_log_coleta` | Data e qualidade da coleta |
| `00_CONSOLIDADO` | Consolidação |

Ignora o **arquivo morto**. Considera só os **~70 grupos vivos** da tabela fato do Clique Vendas (o cofre de 57.239 contemplações não entra no runtime).

## Parâmetros por grupo
1. Cartas de crédito disponíveis (quantidade e valores).
2. Taxa ADM (varia por grupo).
3. Prazo restante em **meses correntes** (não a data de fundação).
4. Parcela antes da contemplação.
5. Mediana do lance livre das **últimas 6 assembleias**.
6. Percentual de embutido: **10 ou 25**.
7. Meses até o fim do grupo.
8. Flag de lance fixo.
9. Data da próxima assembleia = prazo real de venda.

## Regras
- **Embutido:** se o grupo teve lance fixo no histórico = **25%**; se só teve sorteio e lance livre = **10%**.
- **Foco total em lance livre.**
- **Ranking:** menor mediana de lance livre + maior prazo restante. Ajuste fino: na mesma mediana, embutido 25% antes de 10%.
- **Pós-contemplação:** `parcela_pós = (categoria − lance total − parcela paga) / meses restantes`. Seguro de vida à parte.
- **Simulação:** contemplação na 1ª assembleia.
- **Junção de cartas:** autorizada sem limite, inclusive entre grupos de prazos diferentes (parcelas pós separadas no orçamento; ver `cenario-prazos-mistos.md`).
- **Cartaz:** só dispara quando o Wagner escolhe da tabela (ver `fluxo-cascata.md`).

## Saída
Tabela ranqueada versionada, em branch separada, com diff para revisão. Nunca commita sem o Wagner.

## Top 5 embutido 25% (dados do Wagner, não verificados)
| Grupo | Categoria (R$) | ADM (%) | Cartas | Parcela antes (R$) | Mediana lance livre | Meses | Próx. assembleia | Parcela pós (R$) |
|---|---|---|---|---|---|---|---|---|
| 3301 | 70.800 | 18 | 5 | 1.921 | 45,56 | 38 | 26/11 | 989,89 |
| 3304 | 69.620 | n/i | 4 | 1.797 | 46,67 | 40 | 12/11 | 905,99 |
| 3308 | 75.520 | n/i | 9 | 1.903 | 48,33 | 41 | 26/11 | 927,89 |
| 3314 | 70.800 | 20 | 5 | 1.532 | 54 | 48 | 26/11 | 660,32 |
| 3312 | 81.420 | n/i | 7 | 1.836 | 54 | 46 | 26/11 | 791,48 |

n/i = não informado. Unidade da mediana: **não confirmada** (ver Pontos a conferir).

- **3314** = parcela pós mais baixa com o prazo mais longo.
- **3301** = mediana mais baixa.
- **Limites de entrada:** 10 a 24/11.

## Decisões abertas
- **(a)** Aceitar a inversão do ranking (menor mediana primeiro, o que tende a colocar grupos de 10% à frente) ou **forçar o filtro 25% primeiro**? *(Leitura minha de "inversão"; confirmar.)*
- **(b)** Autorizar o GitHub para o Cortex Build (commit/PR; hoje o token não abre PR, 403).
- **(c)** Confirmar **003300 = 25%**. Arquimedes revalidou: caiu para **10%** porque em 52 assembleias não teve lance fixo. Resultado geral: 25 grupos com 25%, 46 com 10%.

## Pontos a conferir
1. **Contagem de grupos:** 25 + 46 = **71**, mas o texto diz "~70". Falta saber se há um grupo duplicado/morto ou se o "~70" é aproximação.
2. **Regra de embutido em três versões:**
   - Arquimedes: 25% se **teve** lance fixo no histórico, senão 10% (derivada do histórico, só 10 ou 25).
   - Regras Disal (`regras-disal.md`): 25% "do grupo 3301 pra cima", **por número**, com exceções sem fixo (003300, 004100-004104, 006207) e 10% abaixo de 3300.
   - Solver: flag `pct_embutido_max` ∈ {0, 0,10, 0,25} **do catálogo**, nunca por número; a spec v1.1 trata 003300, 004100-004104 e 006207 como **0%**.
   Conflitos: (i) 003300 = 0% na spec, 10% no Arquimedes e 25% na memória do Wagner; (ii) a regra por número deixa o próprio 3300 de fora ("abaixo de 3300" × "3301 pra cima"); (iii) o Arquimedes não tem o valor 0 para as exceções. Isso é a decisão (c).
   **Fechado (N5, 01/11/2026):** vale a regra geral 25% com fixo / 10% sem fixo pelo flag do catálogo; exceções = `tem_lance_fixo = false` → 10%. Ver `regras-disal.md`.
3. **Mediana e ranking:** o Arquimedes ranqueia por mediana; a spec v1.1 diz que a mediana **nunca entra em probabilidade nem ranking** do solver. Não é erro (são ferramentas diferentes), mas precisa ficar explícito que o ranking do Arquimedes é comercial/contábil e o do solver é de probabilidade.
4. **Unidade da mediana:** 45,56 / 54 é % (da categoria? do crédito?) ou R$? A spec guarda **fração da categoria**; a migration `0001` guarda `mediana_lance_pct` em **% do crédito**. Não assumi. Se for % da categoria, ver `insight-comercial.md`.
5. **Conferência da fórmula pós** (contas simples; suposições marcadas):
   - Teste A, sem suposição: parcela pós × meses = categoria − (lance + parcela paga). Para 3301: 989,89 × 38 = **37.615,82**; 70.800 − 37.615,82 = **33.184,18** = lance total + parcela paga.
   - Suposição S1: a mediana é % da **categoria** e o lance = mediana. 3301: 45,56% × 70.800 = 32.256,48; sobra **927,70** para "parcela paga".
   - Mesma conta nos demais (S1): 3304 → 888,75; 3308 → 977,69; 3314 → 872,64; 3312 → 1.045,12.
   - Resultado: o "parcela paga" implícito fica em R$ 870–1.050, entre **0,48 e 0,57** da parcela antes (1.532–1.921). **Não bate com 1 parcela inteira** (nem com um número inteiro de parcelas). Ou a mediana não é o lance usado na simulação, ou a "parcela paga" tem outra definição (ex.: uma parcela do plano reduzido), ou os "pós" vêm de outra base. **Os números do Wagner não podem ser reproduzidos só com os dados informados.** Falta: o lance total simulado e a parcela paga de cada linha.
   - Checagem de ordem de grandeza (fora da fórmula): parcela antes × meses restantes fica 3,1% a 3,9% acima da categoria (3301: 1.921 × 38 = 72.998 contra 70.800). Pode ser seguro/fundo de reserva ou outra composição; **suposição, não confirmada**.
   - Observação: com mediana 54% e embutido máximo de 25%, o recurso próprio mínimo seria ~29% da categoria (S1; ver `insight-comercial.md`).
6. **Taxa ADM** só veio para 3301 (18) e 3314 (20); 70.800 / 1,18 = 60.000 e 70.800 / 1,20 = 59.000 (crédito implícito, coerente com categoria = crédito × (1 + ADM)).
7. **Planilha mestra** (Drive `1DrXxebqL0RWIB6GDHgqCC7-k-PRbglnkqFwvs7Ht5MM`, 20 colunas em `2_Parametros`) segue sem exportação: tudo acima é de dados colados, não da planilha.
