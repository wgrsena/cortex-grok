# Backtest rolante da sequência (`scrap/backtest_rolante.py`)

Valida a **sequência** do solver v1.1 (2 a 6 assembleias seguidas), e não a mediana, contra o histórico real do cofre, sem look-ahead.

## Definição da sequência (origem)
É a mesma do resolvedor: `solver/niveis.py::niveis_livres`, especificada em `solver/ESPECIFICACAO_V1_1.md` (A1) e em `docs/regras-disal.md` (item 11).
- `c = (c1..c6)` são os menores lances livres contemplados nas 6 últimas assembleias anteriores a D (c1 = a mais recente).
- W = número de assembleias seguidas com lance livre a partir de c1.
- Para cada w, o lance é `M_w = max(c1..cw)` e a probabilidade é `p = w/6` (modo `sequencia_W_sobre_6`).
- O backtest prevê com o **maior w entre 2 e 6**. W < 2 fica sem previsão.
- O script não redefine nada: chama `niveis_livres`.
- A **mediana** dos lances livres da assembleia-alvo aparece só como evidência e **desempate** no ranking por grupo. Nunca entra no acerto.

## Regra de acerto
- **Acerto:** `M_W >= menor lance livre contemplado` na assembleia-alvo.
- **Decisão Wagner 01/11: empate exato = contemplação.** A comparação é inclusiva. Essa regra é decidida, não é premissa.
- Tudo é comparado em `Decimal` exato. O percentual do WebDisal (`"7,4328"`) vira `Decimal("0.074328")` sem passar por float, para não perder empate por arredondamento. O teste dedicado é `test_empate_conta_como_contemplacao`.
- `seq_futura_coberta` e `manteve_w` são métricas secundárias. Elas indicam quantas assembleias seguidas a partir do alvo o lance teria coberto, e se esse número foi pelo menos W.

## Sem look-ahead
- As datas de referência D são o dia 1 de cada mês.
- A entrada usa só assembleias < D.
- O grupo só entra se já tinha assembleia antes de D. Se for passado `--ativos`, ele também precisa estar ativo em D (`cofre.ativo_em`).
- O alvo é a 1ª assembleia em [D, próximo corte).

## Cofre: só leitura
- O runtime nunca toca o cofre original. O script lê uma **cópia** local com permissão de só leitura (`chmod a-w`).
- O CSV/xlsx é aberto em modo leitura; sqlite é aberto com `mode=ro`.
- `--sha256` (ou `COFRE_SHA256`) aborta se o hash da cópia divergir.
- Cofre usado em 01/11/2026: a planilha Google "webdisal_resultados_assembleia_2026-10-25" (Drive › 00_CONECTA CORTEX › 04_DOCUMENTOS OFICIAIS › 02_DISAL › WEBDISAL_RESULTADOS).
  - Foi exportada como xlsx para fora do repo e convertida para CSV.
  - O CSV tem 57.239 linhas, sha256 `352363b1dfc3e6493affa1d74c3d8278ad1fd866b951569261885b4c9f74d910`.
  - O xlsx exportado tem sha256 `692d5cd0…f012a9`, mas esse hash muda a cada exportação. Os dois arquivos geram evidências idênticas.

## Como rodar
```
python scrap/backtest_rolante.py --cofre /caminho/copia.csv --sha256 <hash> [--ativos ativos.csv] [--datas 2025-01-01,2025-02-01] --saida backtest_saida
```
A saída vai para `backtest_saida/`, que é ignorada pelo git (ou outro diretório fora do repo). São gerados:
- `evidencias.csv`: uma linha por grupo × D, com entradas, w, p, lance previsto, alvo, menor real, empate e acerto.
- `por_grupo.csv`
- `resultado.json`: com metadados do cofre e o hash.
- `resumo.md`

## Resultado real (01/11/2026, cofre de 25/10/2026)
- 147 cortes mensais de 2014-09-01 a 2026-10-01, 162 grupos, **n = 7.670** avaliações.
- **Taxa geral: 6.263/7.670 = 0,8166.** O p médio previsto é 0,9143, então o modelo é otimista.
- Foram 20 empates exatos, todos contados como acerto.
- Nos últimos 12 meses (D ≥ 2025-11-01): 1.458 avaliações, taxa 0,8855.
- Por W:

  | W | p | n | taxa |
  |---|---|---|---|
  | 2 | 0,33 | 452 | 0,60 |
  | 3 | 0,50 | 392 | 0,62 |
  | 4 | 0,67 | 334 | 0,72 |
  | 5 | 0,83 | 292 | 0,78 |
  | 6 | 1,00 | 6.200 | 0,85 |

  W baixo é subestimado e W = 6 é superestimado.
- Exclusões: ver a seção abaixo.

## Premissas adotadas como default (decisão Wagner 01/11, t64u)
1. A data de referência D é o dia 1 de cada mês. O alvo é a primeira assembleia em ou após D, dentro do mês.
2. A assembleia-alvo sem lance livre contemplado fica fora da conta: não é acerto nem erro (437 casos).
3. O grupo existe em D se já teve assembleia antes de D. O cofre não tem data de criação do grupo; `--ativos` é opcional.
4. Os grupos 003/004/006 entram porque `tipo_bem` vem vazio no cofre (7.453 / 196 / 21 avaliações).

## Exclusões
- 1.674 casos sem previsão (W < 2);
- 66 sem assembleia no mês;
- 437 com alvo sem lance livre contemplado.

## Evidências
Os agregados e as evidências estão em `artifacts/backtest-rolante/`: `por_grupo.csv`, `resultado.json`, `resumo.md` e `evidencias.csv`. O cofre (CSV/xlsx) não vai para o repositório.
