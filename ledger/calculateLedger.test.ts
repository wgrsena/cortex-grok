// Teste do calculateLedger. Rodar: node --experimental-strip-types ledger/calculateLedger.test.ts
// Valores sintéticos em centavos (sem dado de cliente), exceto o exemplo 003301 (catálogo público da coleta 25/10/2026).
import { calculateLedger, pisoParcelaDiluidaCents, DILUTION_FLOOR_PERCENT, type LedgerInput } from "./calculateLedger.ts";

let n = 0;
function ok(c: boolean, msg: string) { n++; if (!c) throw new Error("falhou: " + msg); }
const base: LedgerInput = { tipoLance: "livre", lanceParaDestinoCents: 0, parcelaAtualCents: 100000, parcelasRestantes: 60, lastPaidInstallment: 100000, lastPaidInstallmentFonte: "extrato", optouDiluicao: true };
const L = (o: Partial<LedgerInput>) => calculateLedger({ ...base, ...o });

// constante
ok(DILUTION_FLOOR_PERCENT === 50, "constante = 50 (cl. 12.2 b)");

// 1) sem extrato => sem simulação, nunca zero
let r = L({ lastPaidInstallment: null, lanceParaDestinoCents: 1200000 });
ok(r.status === "sem_extrato" && r.simulado === false, "sem extrato: status sem_extrato");
ok(r.novaParcelaCents === null && r.pisoCents === null && r.parcelasQuitadas === null && r.sobraCents === null, "sem extrato: números null, não 0");
ok(pisoParcelaDiluidaCents(null) === null && pisoParcelaDiluidaCents(0) === null, "base vazia ou 0 não vira piso 0");
ok(pisoParcelaDiluidaCents(100000, null) === 50000, "floor null cai na constante");

// 2) piso exato 50% e arredondamento para cima
ok(pisoParcelaDiluidaCents(100000) === 50000, "piso 50% de R$ 1.000,00 = R$ 500,00");
ok(pisoParcelaDiluidaCents(100001) === 50001, "meio centavo arredonda para cima (parcela nunca < 50%)");

// 3) diluição abaixo do piso: lance R$ 12.000 em 60 parcelas de R$ 1.000 -> R$ 800
r = L({ lanceParaDestinoCents: 1200000 });
ok(r.status === "diluicao" && r.novaParcelaCents === 80000 && r.parcelasQuitadas === 0 && r.sobraCents === 0, "diluição simples");

// 4) empate no piso: lance = custo exato até o piso (R$ 500 x 60 = R$ 30.000) -> parcela = piso, nada quitado
r = L({ lanceParaDestinoCents: 3000000 });
ok(r.novaParcelaCents === 50000 && r.novaParcelaCents === r.pisoCents && r.parcelasQuitadas === 0 && r.sobraCents === 0, "empate no piso");
ok(r.avisos.length === 0, "empate não aciona ordem inversa");

// 5) sobra em ordem inversa (12.2 c): R$ 32.000 + R$ 250 -> piso + 4 parcelas de R$ 500 quitadas, sobra R$ 250
r = L({ lanceParaDestinoCents: 3225000 });
ok(r.novaParcelaCents === 50000 && r.parcelasQuitadas === 4 && r.parcelasAPagar === 56 && r.sobraCents === 25000, "piso + ordem inversa");
ok((r.novaParcelaCents ?? 0) >= (r.pisoCents ?? Infinity), "nunca abaixo do piso");

// 6) resto de centavos na diluição não fura o piso: R$ 100,01 em 3 parcelas
r = L({ lanceParaDestinoCents: 10001, parcelasRestantes: 3 });
ok(r.novaParcelaCents === 96667 && r.sobraCents === 2, "redução em centavos inteiros, resto em sobra");

// 7) lance fixo não dilui (12.3 / 16.12.3)
r = L({ tipoLance: "fixo", lanceParaDestinoCents: 1250000 });
ok(r.status === "ordem_inversa" && r.novaParcelaCents === 100000 && r.parcelasQuitadas === 12 && r.sobraCents === 50000, "fixo em ordem inversa");
ok(r.avisos.some((a) => a.includes("12.3")), "fixo com opção de diluição avisa");
r = L({ tipoLance: "fixo", lastPaidInstallment: null, lanceParaDestinoCents: 300000 });
ok(r.status === "ordem_inversa" && r.parcelasQuitadas === 3, "fixo não depende de extrato");

// 8) sem opção escrita -> ordem inversa
r = L({ optouDiluicao: false, lanceParaDestinoCents: 500000 });
ok(r.status === "ordem_inversa" && r.parcelasQuitadas === 5, "sem opção = ordem inversa");

// 9) edição diferente da 27ª -> sem simulação (P5)
r = L({ regulamentoEdicao: 23, lanceParaDestinoCents: 1200000 });
ok(r.status === "edicao_nao_suportada" && r.simulado === false && r.novaParcelaCents === null, "outra edição sem simulação");

// 10) exemplo 003301 (plano 003080 75% Light 48M, crédito R$ 50.000,00, coleta 25/10/2026):
//     valor_1a_parcela_c_seguro R$ 1.271,89 -> piso R$ 635,95. ESTIMATIVA de catálogo, não extrato.
ok(pisoParcelaDiluidaCents(127189) === 63595, "003301: piso R$ 635,95");
r = L({ parcelaAtualCents: 127189, lastPaidInstallment: 127189, lastPaidInstallmentFonte: "estimativa_catalogo", parcelasRestantes: 48, lanceParaDestinoCents: 100000 }); // prazo do plano (48M); lance sintético
ok(r.estimativa === true && r.pisoCents === 63595 && r.avisos.some((a) => a.includes("estimativa")), "003301 marcado como estimativa");
ok(r.status === "diluicao" && (r.novaParcelaCents ?? 0) >= 63595, "003301 respeita o piso");

// 11) entradas não inteiras são recusadas (sem float)
let lancou = false;
try { L({ parcelaAtualCents: 1271.89 }); } catch { lancou = true; }
ok(lancou, "float recusado");

console.log(`ok: ${n} casos`);
