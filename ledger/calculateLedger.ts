// calculateLedger: destino do lance pós-contemplação com piso de diluição. v1.0.0, 2026-11-01.
// Porte da lei 8 do Cortex Lab v0.1.0 (leis/lei8_piso_diluicao.ts, sha256 7bb08885…9880a5), com duas mudanças:
//   1. aritmética exata em centavos (inteiros), sem float;
//   2. sem extrato (lastPaidInstallment null), com opção de diluição: NÃO simula (status "sem_extrato"),
//      em vez de cair na ordem inversa.
//
// Origem normativa: Regulamento Disal, 27ª edição (Drive 1ROCKgYAu7gV_hod0neeNVLCwYs4BL4Ns):
//   cl. 12.2 b (p. 17): "O valor da parcela mensal, após a diluição do lance, não resulte em uma diferença
//                inferior a 50% (cinquenta por cento) do valor da última parcela paga pelo CONSORCIADO,
//                antes da diluição". Leitura adotada (P1): nova parcela >= 50% x última parcela paga.
//   cl. 12.2 c: saldo do lance, depois de atingido o piso, quita parcelas vincendas em ordem inversa.
//   cl. 12.3 e 16.12.3 (p. 27): lance fixo não dilui, só ordem inversa.
// Premissas P1–P6: defaults adotados (Wagner 01/11/2026), ver docs/piso-diluicao.md §5.

export const LEDGER_VERSAO = "1.0.0";
export const ORIGEM = "Cortex Lab lei 8 v0.1.0 (leis/lei8_piso_diluicao.ts)";

/** Piso de diluição, em %. Constante regulatória (cl. 12.2 b, Regulamento Disal 27ª ed., p. 17). */
export const DILUTION_FLOOR_PERCENT = 50;
/** Edição do regulamento para a qual o piso acima foi lido (P5). */
export const REGULAMENTO_EDICAO = 27;

export type TipoLance = "livre" | "fixo";
export type FonteUltimaParcela = "extrato" | "estimativa_catalogo";

export interface LedgerInput {
  tipoLance: TipoLance;
  /** Centavos do lance que vão para destino (já descontada a diferença do Plano Light, cl. 5.6.2). */
  lanceParaDestinoCents: number;
  /** Centavos da parcela vigente antes da diluição. */
  parcelaAtualCents: number;
  /** Parcelas a vencer na contemplação. */
  parcelasRestantes: number;
  /** Centavos da última parcela paga antes da diluição (cl. 12.2 b). null = sem extrato. Nunca 0. */
  lastPaidInstallment: number | null;
  /** Origem de lastPaidInstallment. "estimativa_catalogo" = valor_1a_parcela_c_seguro (pré-venda, P4). */
  lastPaidInstallmentFonte?: FonteUltimaParcela;
  /** Opção escrita de diluição até a AGO seguinte (cl. 12.2 a). Sem opção = ordem inversa. */
  optouDiluicao: boolean;
  /** Default DILUTION_FLOOR_PERCENT. null/undefined cai na constante; nunca vira 0. */
  dilutionFloorPercent?: number | null;
  /** Edição do regulamento da cota (P5). Diferente de 27 = sem simulação. */
  regulamentoEdicao?: number | null;
}

export type LedgerStatus = "diluicao" | "ordem_inversa" | "sem_extrato" | "edicao_nao_suportada";

export interface LedgerResult {
  status: LedgerStatus;
  /** false quando não há base para simular (sem_extrato, edicao_nao_suportada): todos os números são null. */
  simulado: boolean;
  novaParcelaCents: number | null;
  parcelasQuitadas: number | null;
  parcelasAPagar: number | null;
  /** Centavos que não fecham parcela inteira. P6: não são rateados nem abatidos; ficam informados. */
  sobraCents: number | null;
  pisoCents: number | null;
  /** true se a base do piso é estimativa de catálogo (nunca vai ao lead como número). */
  estimativa: boolean;
  avisos: string[];
}

function inteiro(v: number, nome: string, min: number): void {
  if (!Number.isSafeInteger(v) || v < min) throw new Error(`entrada inválida: ${nome} deve ser inteiro >= ${min}`);
}

/** Piso em centavos = teto(base x pct / 100): arredonda para cima (a parcela nunca fica abaixo de 50%). */
export function pisoParcelaDiluidaCents(lastPaidCents: number | null, floorPercent: number | null = DILUTION_FLOOR_PERCENT): number | null {
  if (lastPaidCents == null) return null;
  inteiro(lastPaidCents, "lastPaidInstallment", 0);
  if (lastPaidCents === 0) return null; // zero não é base válida
  const pct = floorPercent ?? DILUTION_FLOOR_PERCENT;
  inteiro(pct, "dilutionFloorPercent", 1);
  if (pct > 100) throw new Error("entrada inválida: dilutionFloorPercent > 100");
  return Math.floor((lastPaidCents * pct + 99) / 100);
}

function semSimulacao(status: LedgerStatus, estimativa: boolean, avisos: string[]): LedgerResult {
  return { status, simulado: false, novaParcelaCents: null, parcelasQuitadas: null, parcelasAPagar: null, sobraCents: null, pisoCents: null, estimativa, avisos };
}

function ordemInversa(e: LedgerInput, piso: number | null, estimativa: boolean, avisos: string[]): LedgerResult {
  const k = Math.min(e.parcelasRestantes, Math.floor(e.lanceParaDestinoCents / e.parcelaAtualCents));
  return {
    status: "ordem_inversa", simulado: true, novaParcelaCents: e.parcelaAtualCents, parcelasQuitadas: k,
    parcelasAPagar: e.parcelasRestantes - k, sobraCents: e.lanceParaDestinoCents - k * e.parcelaAtualCents,
    pisoCents: piso, estimativa, avisos,
  };
}

/**
 * Aplica o lance (hipótese H1, P6): dilui todas as parcelas restantes até o piso; o excedente quita
 * parcelas inteiras (no valor do piso) a partir da última. Reduções por parcela em centavos inteiros,
 * arredondadas para baixo (a parcela nova arredonda para cima); o resto fica em sobraCents.
 */
export function calculateLedger(e: LedgerInput): LedgerResult {
  inteiro(e.lanceParaDestinoCents, "lanceParaDestinoCents", 0);
  inteiro(e.parcelaAtualCents, "parcelaAtualCents", 1);
  inteiro(e.parcelasRestantes, "parcelasRestantes", 1);
  const avisos: string[] = [];
  const estimativa = e.lastPaidInstallment != null && e.lastPaidInstallmentFonte === "estimativa_catalogo";
  if (estimativa) avisos.push("base do piso é estimativa de catálogo (valor_1a_parcela_c_seguro): uso interno, nunca número ao lead");

  if (e.tipoLance === "fixo") {
    if (e.optouDiluicao) avisos.push("lance fixo não dilui (cl. 12.3 / 16.12.3): aplicado em ordem inversa");
    return ordemInversa(e, null, estimativa, avisos);
  }
  if (!e.optouDiluicao) return ordemInversa(e, null, estimativa, avisos);

  if (e.regulamentoEdicao != null && e.regulamentoEdicao !== REGULAMENTO_EDICAO) {
    avisos.push(`regulamento ${e.regulamentoEdicao}ª ed.: piso lido só na 27ª; diluição não simulada (P5)`);
    return semSimulacao("edicao_nao_suportada", estimativa, avisos);
  }
  const piso = pisoParcelaDiluidaCents(e.lastPaidInstallment, e.dilutionFloorPercent);
  if (piso == null) {
    avisos.push("sem extrato: lastPaidInstallment desconhecido, piso não verificável; diluição não simulada");
    return semSimulacao("sem_extrato", false, avisos);
  }

  const n = e.parcelasRestantes;
  const reducaoMax = Math.max(0, e.parcelaAtualCents - piso);
  const custoAtePiso = reducaoMax * n;
  if (e.lanceParaDestinoCents <= custoAtePiso) {
    const reducao = Math.floor(e.lanceParaDestinoCents / n);
    return {
      status: "diluicao", simulado: true, novaParcelaCents: e.parcelaAtualCents - reducao, parcelasQuitadas: 0,
      parcelasAPagar: n, sobraCents: e.lanceParaDestinoCents - reducao * n, pisoCents: piso, estimativa, avisos,
    };
  }
  const excedente = e.lanceParaDestinoCents - custoAtePiso;
  const novaParcela = Math.min(e.parcelaAtualCents, piso);
  const k = Math.min(n, Math.floor(excedente / novaParcela));
  avisos.push("piso atingido: excedente em ordem inversa (cl. 12.2 c)");
  return {
    status: "diluicao", simulado: true, novaParcelaCents: novaParcela, parcelasQuitadas: k,
    parcelasAPagar: n - k, sobraCents: excedente - k * novaParcela, pisoCents: piso, estimativa, avisos,
  };
}
