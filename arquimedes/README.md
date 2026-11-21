# Arquimedes — grid de oportunidades por faixa

Gera, para cada faixa de crédito (padrão R$ 50, 80, 100, 180, 200 e 250 mil), as K melhores combinações de cartas (padrão K = 1) dos grupos disponíveis. Só as ranqueadas saem impressas ou persistidas (`public.oportunidades`, migration `0004`; a 0003 é reservada para `0003_fracao_embutido_mediana.sql`, da branch `cortex/revisao-reviewer`). Usa só a biblioteca padrão.

> **Status:** rascunho na branch `cortex/arquimedes-grid`. Nada foi commitado nem implantado. O `exemplo_top5.json` traz **dados informados, não validados**.

## Uso
```
python -m arquimedes.grid --entrada arquimedes/exemplo_top5.json [--faixas 50000,80000,...] [--top-k 3]
```
A entrada é um JSON `{data_coleta, grupos:[{grupo, categoria, taxa_adm|credito, cartas, parcela_antes, mediana_lance_livre, prazo_restante, pct_embutido, proxima_assembleia, tem_lance_fixo}]}`. Percentuais > 1 são lidos como % (45,56 → 0,4556; 25 → 0,25), a mesma convenção do job semanal.

## Estratégia (o passo do grid está na geração)
1. Cada faixa T tem uma janela `[T, teto)` com `teto = min(T × 1,25, próxima faixa)`. As faixas não se sobrepõem e o gerador nunca estende um ramo que já passou do teto: valores fora da escala não chegam a ser gerados, então não há filtro depois.
2. Busca em profundidade (branch-and-bound) sobre a soma de crédito em centavos. Os itens (grupo, valor da carta) vêm ordenados pela chave do ranking, com quantidade 1..cartas disponíveis. Uma folha só vale se for **cobertura mínima** (soma ≥ T e soma − menor carta < T). Os multiconjuntos são únicos por construção: índice crescente, e duplicatas idênticas de (grupo, crédito) são fundidas.
3. As podas são exatas e lexicográficas, contra o pior dos K melhores: limite inferior da mediana ponderada; no empate exato, limite superior do embutido; depois do prazo; depois do nº de cartas. Todos os limites são monótonos no índice, então uma poda corta o resto do laço. Uma poda de alcançabilidade usa somas de sufixo. Trava de segurança `max_nos` = 300 mil nós por faixa: só dispara em empates totais artificiais, e a faixa sai marcada como "sem prova de ótimo".

Medições (70 grupos × 6 faixas): dados variados levam ~0,003 s. Com medianas empatadas em 3 valores ou todas iguais, ≤ 0,015 s (K = 1 e K = 5). No caso degenerado (mediana, embutido e prazo idênticos em todos os grupos), ~5 s com a trava em uma faixa. O resultado bate com força bruta em 360 faixas (60 sementes) e nos 12 testes parametrizados.

## Ranking (menor é melhor)
`(mediana ponderada, −embutido ponderado, −prazo, excedente sobre a faixa, nº de cartas, chave canônica)`. Na mesma mediana, 25% de embutido vem antes de 10%. A chave canônica deixa o resultado determinístico.

## Agregação de uma combinação
| Campo | Regra |
|---|---|
| Mediana | Σ(mediana × categoria) / Σ categoria (= lance total / categoria total) |
| Embutido | ponderado pela categoria |
| Prazo | o **menor** prazo restante (pior caso) |
| Próxima assembleia | a **mais cedo** (prazo real de venda) |
| Faixa | medida pelo crédito bruto (o embutido não é descontado; o crédito líquido sai por carta) |
| Parcelas pós | separadas por grupo, mais o total do mês 1 e o fluxo `[(mês_ini, mês_fim, valor)]` |

## Fórmula por carta (contemplação simulada na 1ª assembleia)
- Lance = mediana × categoria. A mediana é uma **fração da categoria**.
- Embutido usado = min(% embutido, mediana) × categoria; recurso próprio = lance − embutido usado.
- Parcela paga = `parcelas_pagas` (1) × parcela antes.
- Pós = (categoria − lance − parcela paga) / prazo restante. O seguro de vida fica à parte.
- O divisor é o prazo restante (fórmula literal). Com `descontar_pagas_no_divisor=True`, usa prazo − 1. No grupo 3301 isso dá 963,75 (literal) ou 989,80 (flag); o Wagner citou 989,89. Não forcei a conta.

## Persistência
`persist.py` define o protocolo `Gravador`, com `GravadorMemoria` (testes) e `GravadorSQL(executar)`, que recebe a função de execução e não depende de driver. Regravar uma rodada substitui as linhas dela. O banco garante unicidade em `(rodada, faixa_alvo, rank)` e `(rodada, chave_cartas)`.
