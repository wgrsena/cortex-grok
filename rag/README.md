# rag: memória de atendimentos

O aprendizado mora no **banco**, não na memória da IA: cada atendimento relevante vira um registro em `rag_embeddings` (Postgres + pgvector).

- **Índice:** HNSW com distância de cosseno (criado em `0001`).
- **Filtro de metadados antes da similaridade:** tipo de bem, cidade e faixa de crédito, na função SQL `rag_buscar` (migration `0002`).
- **Poda por score:** só volta o que tem similaridade ≥ `score_min` (padrão 0,75, a calibrar), no máximo `limite` itens (padrão 8).
- **Limite conhecido:** no pgvector, filtro + índice HNSW pode perder resultados (o índice devolve poucos candidatos antes do filtro). A função liga `hnsw.iterative_scan` (pgvector ≥ 0.8). **Falta testar** no Supabase real e conferir a versão do pgvector.
- **Pendente:** dimensão real do embedding (1536 é placeholder), prazo de retenção (jurídico), quais atendimentos entram no índice.

`consulta.py` monta a chamada SQL (sem dependência nova; o driver é escolha de quem executa).
```
python -m pytest -q rag
```
