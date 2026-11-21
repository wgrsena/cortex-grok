// Auditoria Lighthouse headless do blog (§6 do docs/CANONICO_SEO.md v1.1.0). Preset desktop.
// Uso: node tools/lighthouse/run.mjs [--saida artifacts/lighthouse] [--chrome /usr/bin/google-chrome]
// Sobe o blog com `python3 -m http.server` na raiz do repo, roda o Lighthouse em cada página e grava
// <data>-<commit>.json + .md em artifacts/lighthouse/. Exit 1 se algum limite do §6 falhar.
// INP não é mensurável em laboratório (precisa de interação real): o proxy de lab é o TBT, reportado como tal.
// O noindex deliberado derruba a auditoria `is-crawlable` do SEO: o score sai bruto e também sem essa auditoria.
import { spawn, execSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import lighthouse from "lighthouse";
import desktop from "lighthouse/core/config/desktop-config.js";
import * as chromeLauncher from "chrome-launcher";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const SAIDA = resolve(ROOT, arg("--saida", "artifacts/lighthouse"));
const CHROME = arg("--chrome", process.env.CHROME_PATH || "/usr/bin/google-chrome");
const PORTA = Number(arg("--porta", "8765"));
const PAGINAS = [
  ["home (hero + destaque + lista)", "/"],
  ["artigo em destaque / artigo individual (artigo-exemplo)", "/artigo-exemplo/"],
  ["página do autor", "/autor/wagner-sena/"],
];
const LIM = { lcp_ms: 2500, cls: 0.1, tbt_ms: 200, performance: 90, seo: 90 };

const git = (c) => execSync(`git ${c}`, { cwd: ROOT }).toString().trim();
const commit = git("rev-parse --short HEAD");
const sujo = git("status --porcelain -- '*.html' assets config").length > 0;
const srv = spawn("python3", ["-m", "http.server", String(PORTA), "--bind", "127.0.0.1"], { cwd: ROOT, stdio: "ignore" });
await new Promise((r) => setTimeout(r, 800));
const chrome = await chromeLauncher.launch({ chromePath: CHROME, chromeFlags: ["--headless=new", "--no-sandbox", "--disable-gpu"] });

const semAuditoria = (lhr, cat, fora) => {
  let soma = 0, peso = 0;
  for (const ref of lhr.categories[cat].auditRefs) {
    const a = lhr.audits[ref.id];
    if (!ref.weight || fora.includes(ref.id) || a.score === null) continue;
    soma += a.score * ref.weight; peso += ref.weight;
  }
  return peso ? Math.round((soma / peso) * 100) : null;
};

const res = [];
try {
  for (const [nome, path] of PAGINAS) {
    const url = `http://127.0.0.1:${PORTA}${path}`;
    const { lhr } = await lighthouse(url, { port: chrome.port, output: "json", logLevel: "error" }, desktop);
    const A = lhr.audits, C = lhr.categories, sc = (k) => Math.round(C[k].score * 100);
    const r = {
      pagina: nome, path,
      scores: { performance: sc("performance"), accessibility: sc("accessibility"), best_practices: sc("best-practices"),
        seo: sc("seo"), seo_sem_is_crawlable: semAuditoria(lhr, "seo", ["is-crawlable"]) },
      is_crawlable: { score: A["is-crawlable"].score, motivo: "noindex deliberado até aprovação do Wagner (não é violação)" },
      metricas: { lcp_ms: Math.round(A["largest-contentful-paint"].numericValue), cls: +A["cumulative-layout-shift"].numericValue.toFixed(4),
        tbt_ms: Math.round(A["total-blocking-time"].numericValue), ttfb_ms: Math.round(A["server-response-time"].numericValue),
        fcp_ms: Math.round(A["first-contentful-paint"].numericValue), inp: "não mensurável em lab (sem interação); proxy = TBT" },
      bp_falhas: C["best-practices"].auditRefs.filter((x) => x.weight && A[x.id].score !== null && A[x.id].score < 1).map((x) => x.id),
      seo_falhas: C.seo.auditRefs.filter((x) => x.weight && A[x.id].score !== null && A[x.id].score < 1).map((x) => x.id),
    };
    r.falhas = [
      r.metricas.lcp_ms > LIM.lcp_ms && `LCP ${r.metricas.lcp_ms} ms > ${LIM.lcp_ms}`,
      r.metricas.cls > LIM.cls && `CLS ${r.metricas.cls} > ${LIM.cls}`,
      r.scores.performance < LIM.performance && `Performance ${r.scores.performance} < 90`,
      (r.scores.seo_sem_is_crawlable ?? 0) < LIM.seo && `SEO (sem is-crawlable) ${r.scores.seo_sem_is_crawlable} < 90`,
    ].filter(Boolean);
    r.avisos = [r.metricas.tbt_ms > LIM.tbt_ms && `TBT ${r.metricas.tbt_ms} ms > ${LIM.tbt_ms} (proxy de INP)`].filter(Boolean);
    res.push(r);
  }
} finally {
  await chrome.kill(); srv.kill();
}

const data = new Date().toLocaleString("sv-SE", { timeZone: "America/Bahia" }).replace(" ", "T");
const rel = {
  data_america_bahia: data, commit, html_com_mudanca_nao_commitada: sujo, lighthouse: (await import("lighthouse/package.json", { with: { type: "json" } })).default.version,
  chrome: execSync(`${CHROME} --version`).toString().trim(), preset: "desktop", servidor: "python3 -m http.server (local)",
  limites: LIM, canonico: "docs/CANONICO_SEO.md §6", resultado: res.some((r) => r.falhas.length) ? "FALHA" : "OK", paginas: res,
};
mkdirSync(SAIDA, { recursive: true });
const base = join(SAIDA, `${data.slice(0, 10)}-${commit}`);
writeFileSync(`${base}.json`, JSON.stringify(rel, null, 2) + "\n");
const md = [`# Lighthouse — baseline ${data.slice(0, 10)} · commit \`${commit}\``, "",
  `Lighthouse ${rel.lighthouse} · ${rel.chrome} · preset desktop · servidor local · ${data} (America/Bahia). Resultado §6: **${rel.resultado}**.`, "",
  "| Página | Perf | A11y | BP | SEO bruto | SEO sem is-crawlable | LCP | CLS | TBT (proxy INP) | TTFB | §6 |", "|---|---|---|---|---|---|---|---|---|---|---|",
  ...res.map((r) => `| ${r.pagina} (\`${r.path}\`) | ${r.scores.performance} | ${r.scores.accessibility} | ${r.scores.best_practices} | ${r.scores.seo} | ${r.scores.seo_sem_is_crawlable} | ${(r.metricas.lcp_ms / 1000).toFixed(2)} s | ${r.metricas.cls} | ${r.metricas.tbt_ms} ms | ${r.metricas.ttfb_ms} ms | ${r.falhas.length ? "FALHA: " + r.falhas.join("; ") : "OK"} |`),
  "", "- INP não é mensurável em laboratório (precisa de interação real). O TBT é o proxy de lab; INP de campo só com tráfego real (CrUX).",
  "- SEO bruto perde a auditoria `is-crawlable` por causa do `noindex` deliberado (até a aprovação do Wagner). Não é violação; o limite de 90 vale para o SEO sem essa auditoria.",
  "- Servidor local: o TTFB não representa o hosting final.", ""].join("\n");
writeFileSync(`${base}.md`, md);
console.log(md);
process.exit(rel.resultado === "OK" ? 0 : 1);
