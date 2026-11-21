# schema: dados do Conecta Cortex

As migrations ficam em `../supabase/migrations/` (a CLI do Supabase exige essa pasta). Aqui fica o mapa dos três armazenamentos e o contrato entre eles.

| Armazenamento | Tabelas / arquivos | Quem escreve | Quem lê |
|---|---|---|---|
| **Cofre** (append-only) | `resultados_disal` (57.239 contemplações), protegida por trigger em `0002` | carga única + novas assembleias | só o job semanal e o backtest, nunca o runtime |
| **Fato** (~70 grupos ativos) | `fato_snapshots`, `fato_cotas` (`0002`); hoje o job grava `snapshots/<id>.json` + `ATUAL.json` | `scrap/resumo_semanal.py` | `solver/` |
| **RAG** | `rag_embeddings` (HNSW) + função `rag_buscar` (`0001` e `0002`) | Edge Function após cada atendimento | Edge Function / Centauro |

Campos novos na fato (v1.1, 27/10/2026): `mediana_lance_livre` (dado comercial, fora de probabilidade e ranking), `data_coleta` (validade: mais de 8 dias = desatualizada), `proxima_assembleia` (opcional, prazo de entrada de cliente novo; no JSON aceita também uma lista de datas). `embutido_excecao` foi **removido** na revisão de 01/11/2026 (N1): a exceção é derivada de `pct_embutido_max = 0` e `tem_lance_fixo = false`; JSON antigo com o campo continua sendo lido (campo ignorado). **Pendente:** alinhar as colunas às 20 da aba `2_Parametros` da planilha mestra (Drive `1DrXxebqL0RWIB6GDHgqCC7-k-PRbglnkqFwvs7Ht5MM`); ela ainda não foi exportada para `dados/`, então nenhuma coluna foi inventada.

Contrato do snapshot da tabela fato: `snapshot.exemplo.json` (SINTÉTICO, só mostra o formato). Valores monetários e frações viajam como string para não perder precisão.

Regras que valem para todo o schema: flags de catálogo (`tem_lance_fixo`, `pct_embutido_max`) verificadas empiricamente por série, nunca codificadas por número de grupo; segredos fora do banco versionado e fora do git.
