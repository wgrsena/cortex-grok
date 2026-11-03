# scrap: job semanal, cofre e backtest

Alimenta o solver sem que ele toque o cofre.

- **Cofre** (`cofre.py`): leitura das ~57 mil contemplações históricas. Append-only, é um "museu": o runtime nunca consulta.
- **Job semanal** (`resumo_semanal.py`): filtra só os grupos ativos (~70 do Clique Vendas), calcula c1..c6, M, p, `qtd_fixo_contemplado_mes`, `n_ofertantes_fixo_medio` e (v1.1) `mediana_lance_livre` (mediana dos lances livres contemplados nas últimas ≤ 6 assembleias; só dado comercial, fora de probabilidade e ranking), grava `data_coleta` (a do catálogo, ou a data da execução no fuso `America/Bahia`, revisão N8; `snapshot_id`/`atualizado_em` seguem em UTC) e repassa `proxima_assembleia` do catálogo. Grava a **tabela fato** como `snapshots/<id>.json` + ponteiro atômico `ATUAL.json`. Destino futuro: tabelas `fato_snapshots` e `fato_cotas` (migration `0002`), ainda não ligadas ao job.
- **Backtest rolante** (`backtest.py`): só usa grupos vivos na data de cada assembleia. Compara `sequencia_W_sobre_6` e `fracao_h_sobre_N`. **Sem dado real ainda**: precisa da planilha das 57.239 contemplações exportada para `dados/` (ignorada pelo git).
- `cofre_sintetico.py`: dados SINTÉTICOS só para teste.

Depende do `solver/` (contrato, modelos, níveis), nunca o contrário. Só biblioteca padrão do Python.

```
python scrap/resumo_semanal.py --cofre dados/cofre.csv --ativos dados/ativos.csv --catalogo dados/catalogo.json --saida fato
python scrap/backtest.py --cofre dados/cofre.csv --ativos dados/ativos.csv
python -m pytest -q scrap
```
Premissas a confirmar com o Wagner (ver `../solver/NOTAS_DUVIDAS.md`, V2 a V7): uma assembleia por mês; percentuais acima de 1 lidos como percentagem; colunas reais do cofre e do catálogo (hoje supostas). **Pendente:** alinhar a tabela fato às 20 colunas da aba `2_Parametros` da planilha mestra (ainda não exportada para `dados/`; nenhuma coluna foi inventada).
