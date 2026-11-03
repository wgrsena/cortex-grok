# Regras-chave Disal (memória do Wagner, 28/10/2026)

Lista consolidada. Conflitos com o código ficam na seção final.

**Regra geral (N5, decisão do Wagner, 01/11/2026):** embutido máximo **25%** da categoria se o grupo **teve lance fixo**, **10%** se **não teve**. O solver lê só os flags do catálogo (`tem_lance_fixo` → `pct_embutido_max` 0,25 ou 0,10), nunca o número do grupo. As exceções sem fixo (003300, 004100 a 004104, 006207) não são regra no código: chegam como `tem_lance_fixo = false` no catálogo e, pela regra geral, `pct_embutido_max = 0,10`. `pct_embutido_max = 0` continua valor válido de catálogo (grupo sem embutido), mas não é como essas exceções são marcadas.

## Regras
1. **Lance fixo 25%** do grupo 3301 para cima, com exceções **sem fixo**: 003300, 004100 a 004104, 006207.
2. **Embutido** até 25% nos grupos com fixo; 10% nos grupos sem fixo (regra geral, N5). A referência antiga "10% abaixo de 3300" é só a leitura por número da mesma regra; no código vale o flag.
3. **Todo lance incide sobre a categoria** (crédito + taxa).
4. **Plano light 75%** ou **integral 100%**.
5. **Parcela reduzida 75%** priorizada como **pré-filtro**.
6. **Teto de 10% de sobra de crédito removido.**
7. **Unificação de cartas** antes da contemplação.
8. **Ágio/transferência** fora do escopo do resolvedor.
9. **Lance fidelidade** descartado.
10. **Base em escada** descartada.
11. **Probabilidade = sequência / 6**, nunca comunicada como número frio.
12. **Casca comercial:** todo número frio sai embalado (ex.: "nas últimas 3 assembleias seguidas o senhor contemplava").
13. **3 caixas de filtro:** núcleo MVP **executa**; camada futura **fila com data**; ruído **registra**.
14. **Mudança de arquitetura:** para e avisa.
15. **Executa só com "manda" ou "grava".**

## Conflitos com o código atual
(Base: `solver/ESPECIFICACAO_V1_1.md`, `solver/NOTAS_DUVIDAS.md`, `solver/modelos.py`, `solver/niveis.py`, `supabase/migrations/0001*.sql`.)

| # | Regra do Wagner | Código/spec atual | Situação |
|---|---|---|---|
| 1 | Embutido 25% **se teve fixo** (Arquimedes) / **por número** (3301+) | Flag `pct_embutido_max` ∈ {0; 0,10; 0,25} vindo do catálogo, nunca por número (spec seção 1, V6) | **Resolvido (N5, 01/11):** regra geral 25% com fixo / 10% sem fixo, aplicada pelo flag do catálogo (`tem_lance_fixo` → `pct_embutido_max`); o solver nunca usa o número. Quem preenche o flag a partir do histórico é o catálogo/Arquimedes. |
| 2 | Exceções sem fixo (003300, 004100-004104, 006207) e "embutido 10% abaixo de 3300" | Exceções = `pct_embutido_max = 0` e `tem_lance_fixo = false` na spec; 003300 revalidado pelo Arquimedes em **10%** | **Resolvido (N5, 01/11):** as exceções são `tem_lance_fixo = false` no catálogo e, pela regra geral, embutido 10% (inclui o 003300, como o Arquimedes revalidou). Nenhum número de grupo no código (teste N10). |
| 3 | Teto de 10% de sobra removido | `delta_credito = None` por padrão (`modelos.py`); a sobra aparece em `gap.sobra_credito`; spec 4.5 e D2 ainda descrevem o teto como **opcional** | **Alinhado.** Risco residual: D2/`refino_respeita_teto_credito` ainda existe; a opção `delta_credito` reativa o teto. |
| 4 | Probabilidade = sequência/6, nunca número frio | Padrão `sequencia_W_sobre_6`; `centauro/frases.py` traduz W em frase sem percentual | **Alinhado no padrão.** Mas a saída do solver ainda expõe `p` e `probabilidade_conjunta` numéricos (contrato interno; a Centauro não os recebe). O documento de parâmetros revisado manda ranquear pela sequência da carta mais fraca, enquanto o código ranqueia pelo produto (README, conflito (a)). |
| 5 | Ranking do Arquimedes por menor mediana de lance livre | Spec 0/A1: mediana **nunca** entra em probabilidade nem ranking | **Dois rankings distintos.** Registrar que o do Arquimedes é comercial/contábil. |
| 6 | Mediana em % | Spec: **fração da categoria**; migration 0001 guardava `mediana_lance_pct` em % (0..100) | **Resolvido (revisão I2, 01/11):** fração 0..1 em código e banco (migration 0003), `<=` no solver e na view. |
| 7 | Parcela pós, seguro de vida à parte, simulação na 1ª assembleia | Fase 2, não implementada | **Falta código** (documentado, fora de escopo da v1.1). |
| 8 | Junção de cartas sem limite, entre prazos | Função 2 sem limite; Função 1 limita `max_cartas_enum` = 6; ramo fixo não unifica | **Parcial.** |
| 9 | Plano 75% como pré-filtro | Implementado (`funcao2.py`, C3) | Alinhado. |
| 10 | Lance fidelidade e base em escada descartados | Busca por "fidelidade"/"escada" no repo: **nenhuma ocorrência** | Alinhado (nada a remover). |
| 11 | Ágio/transferência fora do escopo | Spec "Fora do escopo" | Alinhado. |
| 12 | Lance fixo 25% | `lance_fixo_pct` padrão 0,25 na cota; a chance do fixo `1/n_ofertantes` (V1) está em conflito com o documento de parâmetros que remove `n_ofertantes_fixo_medio` | **Conflito aberto (V1)**. |
| 13 | Parcela reduzida 75% como pré-filtro | Spec A7: categoria e % de embutido valem igual nos dois planos; "conferir na planilha" | Pendente de planilha. |
| 14 | 3 caixas de filtro; "manda"/"grava"; para e avisa | Processo, não código | Sem equivalente no código. |
