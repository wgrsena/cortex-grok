# Solver Disal (cartas de veículo)

Estado: núcleo + MILP (HiGHS via highspy; CBC descartado) + serviço FastAPI. O job semanal e o backtest ficam em `../scrap/`. Sem deploy; dado real não carregado.
Spec: `ESPECIFICACAO_V1_1.md` (v1.1, 27/10/2026; mudanças sobre a v1 marcadas com **[v1.1]**). Dúvidas, decisões provisórias e conflitos com a spec: `NOTAS_DUVIDAS.md`.

## Como funciona
- **Dois bancos.** O "cofre" (contemplações, append-only) NÃO é consultado em runtime. O job semanal `../scrap/resumo_semanal.py` filtra
  as contemplações pelos grupos ativos, calcula c1..c6, M, p, `qtd_fixo_contemplado_mes`, `n_ofertantes_fixo_medio`, `mediana_lance_livre` e `data_coleta` e grava a tabela fato
  (`snapshots/<id>.json` + ponteiro `ATUAL.json`, troca atômica via `os.replace`). O solver só lê essa tabela.
- **Entrada única:** `funcao2.resolver_funcao2(snapshot, pedido, params)` (Função 2) e `resolver_funcao1` (Função 1).
  - `recurso_proprio == 0` → **ramo lance fixo** (`ramo_fixo.py`): sem MILP; ranking multi-critério (volume de fixo, crédito, taxa, parcela; pesos em `Parametros`) + mensagem comparativa sorteio × lance fixo. Cada linha traz `chance_fixo` = 1 / nº de ofertantes ("1 contra o número de ofertantes", sem mediana), só informativa: não entra no score.
  - senão, por categoria de veículo (carro/moto/caminhão, nunca misturadas; imóvel nunca): **plano 75% sempre primeiro**; o 100% só se o 75% não resolver ou como `alternativa_100` rotulada.
  - Probabilidade = cobertura temporal, padrão sequência seguida W / 6 (decisão do Wagner; nunca mostrada ao cliente como número frio, só como sequência). A fração h/N das últimas assembleias fica como opção de comparação. A mediana não entra na conta. A sequência W também desempata após a probabilidade (`w_desempate`).
  - Embutido sobre a CATEGORIA (crédito + taxa), em passos de 5% até o teto da série (10% ou 25%): J = {0,5,10,15,20,25}% ∩ [0, teto]. Usa o necessário para fechar a diferença, nunca o máximo por padrão. Lance fixo = 25% da categoria (trava).
  - Unificação: quantas cartas de veículo forem necessárias, prazos diferentes liberados, sem limite de cartas; é **proposta, não contemplação**.
- **Validade e prazo (v1.1, `prazos.py`):** funções puras, sem relógio e sem feriado codificado. `oportunidade_desatualizada(data_coleta, hoje, max_dias=8)`: mais de 8 dias = desatualizada (exatamente 8 vale). `prazo_entrada_cliente_novo(assembleia, feriados, dias_antes=2)`: 2 dias corridos antes; sábado, domingo ou feriado recuam para o dia útil anterior. `assembleia_aplicavel(hoje, proximas, feriados)`: primeira assembleia cujo prazo (inclusivo) não venceu. `proxima_assembleia` da cota aceita uma data ou uma lista: vencido o prazo da primeira, vale a seguinte da lista; com uma data só e prazo vencido, `assembleia_aplicavel` sai `null` com `motivo_assembleia_aplicavel` (revisão N4). Data malformada nunca derruba a requisição: o campo sai `null` e o nome vai em `datas_invalidas` (revisão N9). Saída por oportunidade: `desatualizada`, `data_coleta`, `prazo_entrada`, `assembleia_aplicavel`, `prazo_vencido`, `motivo_assembleia_aplicavel`, `datas_invalidas`, mais `mediana_lance_livre` e `embutido_cobre_mediana` (mediana <= teto de embutido, ambos em fração da categoria, revisão I2; dado comercial, fora de probabilidade e ranking). `hoje` e `feriados` entram em `parametros`; sem eles os campos saem `null`.
- **Exceções sem fixo/embutido** são DADO do catálogo (`tem_lance_fixo`, `pct_embutido_max` por série; sem campo `embutido_excecao` desde a revisão N1); nada no código do repo cita número de grupo (teste varre o repo inteiro).
- **Saída por cenário** (`contrato.combo_dict`): por carta grupo de origem, crédito, taxa adm da série, plano, parcela pré-contemplação sobre o crédito cheio, lance mínimo (maximiza a cobertura) e `cobertura` ("ganharia em h de N assembleias"); junção com `credito_total` e `probabilidade_conjunta`.
- **Motor:** MILP em HiGHS (`milp.py`, lexicográfico S1..S5 + exclusão por conjunto de tipos), refinamento exato em Decimal, aproximação com gap (seção 7). Ranking A2 e refinamento compartilhados em `ranking.py`. `forca_bruta.py` é só o oráculo dos testes: nenhum módulo de produção o importa e ele, os `test_*.py` e as fixtures ficam fora da imagem (`.dockerignore`).

## Parâmetros em aberto (TODO Wagner, padrões do MiroFish)
- `modo_probabilidade`: `"sequencia_W_sobre_6"` (padrão, decisão do Wagner) | `"fracao_h_sobre_N"` (só comparação).
- `hoje`, `feriados`, `max_dias_coleta` (8, constante única `modelos.MAX_DIAS_COLETA`): validade e prazo (v1.1).
- `delta_credito` = sem teto (padrão, decisão do Wagner): devolve tudo viável e a sobra aparece no `gap`. Um valor (ex.: 0,10) reativa o teto.
Outros ajustáveis: `w_desempate`, `incluir_alternativa_100`, `peso_credito/taxa/fixo/parcela`, `top_fixo`, `fixo_exigir_embutido_cobrir`, `milp_gap_relativo` (0,005), `milp_tempo_limite_s` (10).

## Fase 2 (somente documentação, NÃO implementada): fórmula pós-contemplação
Ponto 7 da orientação do Wagner: a fórmula pós-contemplação (cálculo depois que a carta é contemplada) fica para a fase 2; nada foi implementado. Ágio e transferência de cota: fora de escopo.

## Rodar
```
python -m venv .venv && .venv/bin/pip install -r solver/requirements.txt   # na raiz do repo
.venv/bin/python -m pytest -q solver                         # ~1 min (a maior parte é o teste 2, MILP × força bruta)
cd solver && DISAL_SOLVER_TOKEN=... DISAL_DADOS_DIR=../fato uvicorn app:app --port 8000
# job semanal e backtest: ver ../scrap/README.md
```
API (header `X-API-Token`; sem `DISAL_SOLVER_TOKEN` no ambiente o serviço recusa tudo com 503): `POST /combinacoes`, `POST /probabilidade`,
`POST /revalidar`, `GET /saude`. Corpo: `{"pedido": {...}, "snapshot_id": "atual", "parametros": {}}`. `snapshot_id` só aceita `[A-Za-z0-9._-]{1,64}`.
Dados reais (planilha de contemplações) nunca entram no repositório: ficam em `dados/`, que o `.gitignore` ignora.

## Arquivos
`modelos` (dados, parâmetros) · `niveis` (níveis, universo) · `embutido` (J, refinamento) · `enumeracao` (Função 1) · `forca_bruta` (oráculo) ·
`milp` · `funcao2` (orquestração 75%/categoria/ramo fixo) · `ramo_fixo` · `prazos` (validade e prazo de entrada) · `contrato` (JSON) · `revalidacao` · `app` · `dados_sinteticos` · `test_aceite`, `test_milp`, `test_novos`, `test_padroes`, `test_v1_1` · `Dockerfile` (sem build) · `requirements.txt`.
