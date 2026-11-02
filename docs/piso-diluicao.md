# Piso de diluição: `lastPaidInstallment` e `dilutionFloorPercent`

Status: **proposta para validação do Wagner**, 01/11/2026 (America/Bahia). Não é runtime e não implementa cálculo. Nada aqui foi usado em página pública.

## 1. Problema

`calculateLedger` (lei 8, pós-contemplação) pede dois campos que **nenhum dado Disal coletado traz**:

- `dilutionFloorPercent`;
- `lastPaidInstallment`.

O código de `calculateLedger` **não foi encontrado**: não está em `wgrsena/conecta-cortex` nem em `wgrsena/cortex-grok`, e `wgrsena/CONECTACORTEX` está sem acesso. A referência usada aqui é a **lei 8 versionada no Cortex Lab** (v0.1.0, 01/11/2026), que roda como proposta isolada:

| Artefato do Lab | sha256 (01/11/2026 22:33) |
|---|---|
| `leis/lei8_piso_diluicao.ts` (`DILUTION_FLOOR_PERCENT = 50`, `aplicarLance`) | `7bb08885…9880a5` |
| `docs/LEI8_PISO_DILUICAO.md` | `6a706454…ff3c8cd` |
| `leis/lei8_piso_diluicao.test.ts` | rodado com `node --experimental-strip-types`: **14 casos ok** |

## 2. O que o regulamento diz

Fonte: Regulamento Disal, 27ª edição (Drive `1ROCKgYAu7gV_hod0neeNVLCwYs4BL4Ns`). Trechos literais:

| Cláusula (pág.) | Texto |
|---|---|
| 12.2 (p. 17) | "O CONSORCIADO CONTEMPLADO por lance poderá optar pela diluição do percentual pago a este título nas parcelas mensais vincendas, desde que:" |
| 12.2 a | a opção é feita "por escrito até, no máximo, a data da realização da Assembleia Geral Ordinária seguinte" |
| 12.2 b | "O valor da parcela mensal, após a diluição do lance, não resulte em uma diferença inferior a 50% (cinquenta por cento) do valor da última parcela paga pelo CONSORCIADO, antes da diluição" |
| 12.2 c | "Se ainda houver saldo do lance e já alcançado o limite do inciso anterior, o saldo será utilizado para quitação das parcelas vincendas pela ordem inversa" |
| 12.3 / 16.12.3 (p. 27) / 16.14.2 | o lance fixo e o embutido do lance fixo **não diluem**: vão só para a ordem inversa |
| 5.6.2 a / 5.6.4 a (p. 8), Plano Light | o excedente "reduzirá o percentual de amortização das parcelas posteriores à contemplação, até o limite de 50 % (cinquenta por cento) do valor da última parcela cobrada" |

## 3. Cruzamento com a coleta de 25/10/2026

Pasta: Drive 00_CONECTA CORTEX › 04_DOCUMENTOS OFICIAIS › 02_DISAL › WEBDISAL_RESULTADOS. A análise foi feita pelo Cortex Lab (`resumo_analise_piso.json`), e eu conferi os campos de catálogo em `grupos_a_venda_2026-10-25`.

| Pergunta | Resposta nos dados | Consequência |
|---|---|---|
| Os resultados de assembleia (57.239 linhas) trazem R$? | Não: `lance_valor` e `valor_credito_ou_categoria` estão vazios em todas as linhas. Há só `lance_percentual` e `Qtde Parc` | não dá para medir o piso |
| Há algum caso de diluição? | Não. Na última assembleia por grupo, a coluna "Opção" tem Red. Prazo 1.427, Quitação 2 e vazio 469 (sorteio) | o piso é inobservável na coleta |
| O catálogo traz a "última parcela paga"? | Não. Traz `valor_1a_parcela_c_seguro` por grupo, plano e crédito. `parcelas_a_pagar_contemplacao` = 0 em toda a amostra | serve só como proxy de **pré-venda** |
| O lance livre mínimo serve como piso? | Não. Ele limita a **oferta**; o piso limita a **parcela** | não usar |

## 4. Proposta por campo

| Campo | Proposta | Tipo | Premissa a validar |
|---|---|---|---|
| `dilutionFloorPercent` | **constante 50**, camada fixa (regulamento 27ª ed.), com a edição registrada junto (`regulamento_edicao = 27`) | contratual | (P1) leitura da 12.2 b = "nova parcela ≥ 50% da última paga". Também é a leitura da 5.6.2 a/5.6.4 a e bate com o caso real do Lab (parcela caiu ~50%) |
| `lastPaidInstallment`, **cota real** (pós-venda) | campo novo por cota, vindo do **extrato da cota** (R$ da última parcela paga antes da diluição). **Nulo** enquanto não houver extrato: sem diluição simulada, com aviso, e só ordem inversa. **Nunca 0** | dado de cliente | (P2) a base inclui ou não o seguro de vida; (P3) "paga" (12.2 b) ou "cobrada" (5.6.2 a) |
| `lastPaidInstallment`, **simulação** (pré-venda) | estimativa documentada = `valor_1a_parcela_c_seguro` do catálogo (grupo × plano × crédito), sempre marcada `estimativa: true` e com aviso; vale só para contemplação logo depois da adesão (sem reajuste) | estimativa | (P2) e (P4) se é aceitável simular diluição na venda |
| aplicabilidade | só lance **livre** com opção **escrita** de diluição; lance fixo e embutido do fixo → ordem inversa | regra | — |

Exemplo de estimativa, só ilustração e **não** número para o lead: grupo 003301, plano 003080 (75% Light 48M), crédito R$ 50.000,00 → `valor_1a_parcela_c_seguro` R$ 1.271,89 (coleta 25/10/2026) → piso 50% ≈ R$ 635,95.

### Esboço de schema (rascunho, não aplicar sem OK)

Para a tabela de cotas do `conecta-cortex` (`fato_cotas` ou equivalente), em migração **rascunho**:

```sql
-- RASCUNHO: depende de P1–P4. Não executar.
alter table fato_cotas
  add column ultima_parcela_paga        numeric(12,2),           -- R$, do extrato; null = desconhecido
  add column ultima_parcela_paga_fonte  text,                    -- 'extrato' | 'estimativa_catalogo'
  add column ultima_parcela_paga_em     date,
  add column piso_diluicao_pct          numeric(5,2) default 50, -- Regulamento Disal 27ª ed., cl. 12.2 b
  add column regulamento_edicao         smallint;
```

No contrato de `calculateLedger`: `lastPaidInstallment ← ultima_parcela_paga` e `dilutionFloorPercent ← piso_diluicao_pct`. Se `ultima_parcela_paga` for null, `calculateLedger` não dilui e devolve um aviso (é o mesmo comportamento de `aplicarLance` no Lab).

## 5. Premissas a validar (Wagner ou Disal)

- **P1.** Redação da 12.2 b ("diferença inferior a 50%"): confirmar que significa nova parcela ≥ 50% × última paga, e não "redução ≥ 50%".
- **P2.** O seguro de vida entra na base? O proxy de catálogo inclui seguro e infla o piso.
- **P3.** "Última parcela paga" (12.2 b) ou "última parcela cobrada" (5.6.2 a)? Diferem quando a cota está inadimplente ou houve reajuste.
- **P4.** Pode simular diluição na pré-venda com a estimativa, ou só depois de haver extrato?
- **P5.** Grupos antigos seguem edições anteriores do regulamento? O piso pode ser outro; por isso `regulamento_edicao` fica por cota.
- **P6.** Regra da sobra: no caso real do Lab a parcela ficou R$ 7–9 abaixo de 50% exatos, e a ordem "dilui até o piso, depois quita" (H1) não está confirmada.

## 6. O que falta

1. Acesso ao código de `calculateLedger` (provavelmente `wgrsena/CONECTACORTEX`) para integrar.
2. Extrato por cota, com R$ da última parcela paga. É dado de cliente e não entra em repositório.
3. Uma coleta de assembleia com **casos de diluição**, ou o arquivo de resultados com `lance_valor`, crédito e opção de destino.
