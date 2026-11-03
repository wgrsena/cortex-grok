# Cenário: prazos mistos (3301 + 3304 no mesmo orçamento)

> **Ilustrativo.** Usa só as parcelas pós informadas pelo Wagner (989,89 e 905,99; **não verificadas**). **Sem lance, sem seguro de vida, sem taxa extra.** Não é proposta comercial.

## Premissa
Junção de cartas é autorizada sem limite, inclusive entre grupos de prazos diferentes. As parcelas pós ficam **separadas** no orçamento: o cliente paga as duas até a menor zerar.

| Carta | Parcela pós (R$) | Meses restantes |
|---|---|---|
| 3301 | 989,89 | 38 |
| 3304 | 905,99 | 40 |

## Linha do tempo
| Meses | Parcelas ativas | Fluxo mensal (R$) |
|---|---|---|
| 1 a 38 | 3301 + 3304 | 989,89 + 905,99 = **1.895,88** |
| 39 a 40 | só 3304 | **905,99** |

## Total pago (contas)
- 3301: 989,89 × 38 = **37.615,82**
- 3304: 905,99 × 40 = **36.239,60**
- Soma: **73.855,42** (confere: 1.895,88 × 38 = 72.043,44, mais 905,99 × 2 = 1.811,98, igual a 73.855,42).

## Observações
- O pico do fluxo (1.895,88) cai nos primeiros 38 meses; os 2 meses finais caem para 905,99. Se o orçamento do cliente exige uma parcela única, é preciso outra carta/grupo, não esta combinação.
- Duas contemplações precisam ocorrer: as cartas são de grupos distintos, com assembleias diferentes (3304 em 12/11, 3301 em 26/11, segundo o Wagner). O cenário supõe as duas já contempladas.

## O solver v1.1 cobre isso?
- **Junção de cartas pré-contemplação: sim.** A Função 2 combina cartas de grupos diferentes sem limite de cardinalidade (só `MAX_Q` = 15 por cota física); `prazo_total` é informativo e "prazos diferentes sempre liberados" (`NOTAS_DUVIDAS.md`). A Função 1 limita a enumeração a `max_cartas_enum` (padrão 6), por performance.
- **Parcelas pós separadas por prazo: não.** A fórmula pós-contemplação é fase 2 e **não está implementada** (spec seção 11; README do solver, ponto 7). O solver trabalha com a parcela de antes (`Pmax`), não gera fluxo mensal pós.
- **Falta (sem implementar):** (1) função pura de fluxo mensal que receba a lista de (parcela pós, meses) e devolva a soma por mês; (2) a própria fórmula pós por carta, com lance total e parcela paga; (3) seguro de vida à parte; (4) definição de "parcela paga" (ver `arquimedes-disal.md`, Pontos a conferir 5); (5) lance fixo no ramo fixo ainda não unifica cartas.
