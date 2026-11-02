#!/usr/bin/env python3
"""Gate SEO de PR do blog (stdlib pura). Falha fechado.

Uso:
  python3 tools/gate_seo/gate.py --canonico docs/seo-canonico/<versao>.meta.json --alvo <worktree do PR> \
      [--base <ref>] [--pr N] [--atestado <json>] [--registrar-readme README.md] [--json]

Saída: PASS (exit 0) ou BLOCK com a lista de IDs violados (exit 1). Erro de uso: exit 2.

Ordem:
  1. Canônico: o snapshot existe, o sha256 confere, está na pasta 01_FONTE DA VERDADE, tem versão,
     e cada requisito tem ID SEO-xxx, data, fonte, severidade e status. Qualquer falha → BLOCK (GATE-CANON-*).
  2. Requisitos bloqueantes e ativos:
     - com checagem automática (mapa_checks.json ou campo "Verificação: auto:R7,L4") → roda tools/check.py
       do alvo e marca o ID como violado se alguma regra mapeada der FALHA;
     - sem checagem automática → "verificação manual": só passa com atestado (revisor + data) para o commit.
       Manual sem atestado → BLOCK (nunca passa calado).
  3. FALHA do tools/check.py do alvo que não está mapeada a nenhum ID também bloqueia (GATE-CHECKPY).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from canonico import parse, parse_secoes  # noqa: E402
import canon_checks  # noqa: E402

PASTA_CANONICA_ID = "1Vw46Po3-AuOp0EmEeSWGONYZyRlKTwMN"  # 00_CONECTA CORTEX › 01_FONTE DA VERDADE (só leitura)
REPO = AQUI.parent.parent
# Exceção única à regra da pasta do Drive: o canônico versionado no próprio repo, aprovado pelo Wagner
# (t69u, 2026-11-02: a pasta 01_FONTE DA VERDADE é só leitura para o conector). Vale SÓ para este caminho
# e só com a aprovação registrada no .meta.json (aprovacao_repo: por, data, ref).
CANON_REPO_PATH = "docs/CANONICO_SEO.md"
RE_FALHA = re.compile(r"^FALHA \[([^\]]+)\]\s*(.*)$")


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def aprovacao_repo_ok(meta) -> bool:
    ap = meta.get("aprovacao_repo") or {}
    return (meta.get("origem") == "repo" and meta.get("arquivo_repo") == CANON_REPO_PATH
            and all(ap.get(k) for k in ("por", "data", "ref")))


def carregar_canonico(meta_path: Path, alvo: Path = None):
    """→ (meta, Canonico|None, [(codigo, msg)])

    origem "drive" (padrão): snapshot exportado ao lado do .meta.json, exige a pasta 01_FONTE DA VERDADE.
    origem "repo": lê `arquivo_repo` no alvo (worktree do PR) ou na raiz deste repo; a regra da pasta do Drive
    é dispensada só para docs/CANONICO_SEO.md com aprovação registrada (aprovacao_repo).
    """
    probs = []
    if not meta_path.exists():
        return {}, None, [("GATE-CANON-AUSENTE", f"arquivo canônico ausente: {meta_path} não existe — merge bloqueado")]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("origem") == "repo":
        rel = meta.get("arquivo_repo", "")
        cands = [b / rel for b in ([alvo] if alvo else []) + [REPO] if rel]
        md = next((x for x in cands if x.exists()), cands[0] if cands else meta_path.parent / "?")
        meta = {**meta, "arquivo": rel}
    else:
        md = meta_path.parent / meta.get("arquivo", "")
    if not meta.get("arquivo") or not md.exists():
        return meta, None, [("GATE-CANON-AUSENTE", f"snapshot {md} ausente — merge bloqueado")]
    dados = md.read_bytes()
    if hashlib.sha256(dados).hexdigest() != meta.get("sha256"):
        probs.append(("GATE-CANON-SHA", f"sha256 de {md.name} não confere com o .meta.json (arquivo alterado depois do registro)"))
    if meta.get("origem") == "repo":
        if not aprovacao_repo_ok(meta):
            probs.append(("GATE-CANON-FORA-DA-PASTA",
                          f"canônico no repo ({meta.get('arquivo_repo')}) sem a exceção aprovada: só {CANON_REPO_PATH} com aprovacao_repo (por, data, ref)"))
    elif meta.get("pasta_drive_id") != PASTA_CANONICA_ID:
        probs.append(("GATE-CANON-FORA-DA-PASTA",
                      f"o arquivo lido está em '{meta.get('pasta_drive_nome', '?')}', não em 00_CONECTA CORTEX › 01_FONTE DA VERDADE"))
    if meta.get("formato") == "secoes-numeradas":
        c = parse_secoes(dados.decode("utf-8"), meta.get("prefixo_id", "CANON-SEO"),
                         meta.get("severidade_padrao", ""), meta.get("arquivo", ""))
    else:
        c = parse(dados.decode("utf-8"))
    if not c.versao:
        probs.append(("GATE-CANON-SEM-VERSAO", "arquivo canônico sem versão declarada — merge bloqueado"))
    if not c.requisitos:
        probs.append(("GATE-CANON-VAZIO", "nenhum requisito encontrado no arquivo canônico"))
    sem = {k: [r for r in c.requisitos if k in r.faltando()] for k in ("id", "data", "fonte", "severidade", "status")}
    for k, lst in sem.items():
        if lst:
            probs.append((f"GATE-CANON-SEM-{k.upper()}", f"{len(lst)} de {len(c.requisitos)} requisitos sem campo '{k}' (ex.: “{lst[0].titulo[:60]}”, linha {lst[0].linha})"))
    ids = [r.id for r in c.requisitos if r.id]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        probs.append(("GATE-CANON-ID-DUPLICADO", ", ".join(dup)))
    return meta, c, probs


def rodar_check(alvo: Path):
    """→ (disponível, {regra: [msgs]}, saída)"""
    chk = alvo / "tools" / "check.py"
    if not chk.exists():
        return False, {}, ""
    p = sh([sys.executable, str(chk)], cwd=alvo)
    falhas = {}
    for linha in p.stdout.splitlines():
        m = RE_FALHA.match(linha)
        if m:
            for regra in m.group(1).split("/"):
                falhas.setdefault(regra.strip(), []).append(m.group(2))
    return True, falhas, p.stdout


def checks_do_requisito(r, mapa):
    if r.id in mapa:
        return list(mapa[r.id])
    v = r.verificacao.strip()
    if v.lower().startswith("auto:"):
        return [x.strip() for x in v[5:].split(",") if x.strip()]
    return []


def diff_info(alvo: Path, base: str):
    head = sh(["git", "rev-parse", "--short", "HEAD"], alvo).stdout.strip()
    arquivos = set()
    if base:
        arquivos |= set(sh(["git", "diff", "--name-only", f"{base}...HEAD"], alvo).stdout.split())
    arquivos |= set(sh(["git", "diff", "--name-only", "--cached"], alvo).stdout.split())
    arquivos |= set(sh(["git", "diff", "--name-only"], alvo).stdout.split())
    return head, sorted(arquivos)


def avaliar(meta_path: Path, alvo: Path, base: str = "", atestado: dict = None, mapa: dict = None):
    atestado = atestado or {}
    mapa = mapa if mapa is not None else json.loads((AQUI / "mapa_checks.json").read_text(encoding="utf-8"))["mapa"]
    meta, c, probs = carregar_canonico(meta_path, alvo)
    head, arquivos = diff_info(alvo, base) if (alvo / ".git").exists() else ("", [])
    disp, falhas_chk, _ = rodar_check(alvo)
    auto_canon = canon_checks.avaliar(alvo) if meta.get("formato") == "secoes-numeradas" else {}
    res = {
        "commit": head, "arquivos_no_diff": len(arquivos),
        "canonico": {"arquivo": meta.get("arquivo"), "drive_id": meta.get("drive_id"), "versao": c.versao if c else "",
                     "sha256": meta.get("sha256"), "drive_modified_utc": meta.get("drive_modified_utc"),
                     "requisitos": len(c.requisitos) if c else 0, "origem": meta.get("origem", "drive"),
                     "aprovacao_repo": meta.get("aprovacao_repo") if meta.get("origem") == "repo" else None},
        "estrutura": [{"codigo": k, "msg": m} for k, m in probs],
        "violados": [], "manual_pendente": [], "manual_atestado": [], "auto_ok": [],
        "check_py": {"disponivel": disp, "falhas": falhas_chk},
    }
    mapeadas = set()
    if c and not probs:
        for r in c.requisitos:
            if not (r.ativo and r.bloqueante):
                continue
            regras = checks_do_requisito(r, mapa)
            at = atestado.get(r.id) or {}
            auto = auto_canon.get(r.id, [])
            if r.id in auto_canon or at.get("veredito"):
                # seção do canônico em seções: checagem automática PARCIAL + avaliação manual por seção
                falhas_auto = [m for ok, m in auto if not ok]
                at_valido = at.get("revisor") and at.get("data") and at.get("commit") in (head, "", None)
                veredito = (at.get("veredito") or "").lower() if at_valido else ""
                item = {"id": r.id, "titulo": r.titulo, "auto": [{"ok": ok, "msg": m} for ok, m in auto],
                        "motivo": at.get("motivo", "") if at_valido else ""}
                if falhas_auto or veredito == "violado":
                    item["falhas"] = {"auto": falhas_auto} if falhas_auto else {}
                    res["violados"].append(item)
                elif veredito == "ok":
                    res["manual_atestado"].append({**item, "revisor": at["revisor"], "data": at["data"]})
                else:
                    item["motivo"] = item["motivo"] or "sem atestado manual válido para este commit"
                    res["manual_pendente"].append(item)
                continue
            if regras and disp:
                mapeadas |= set(regras)
                hit = [x for x in regras if x in falhas_chk]
                (res["violados"] if hit else res["auto_ok"]).append(
                    {"id": r.id, "titulo": r.titulo, "regras": regras, "falhas": {x: falhas_chk[x] for x in hit}})
            else:
                if at and at.get("revisor") and at.get("data") and at.get("commit") in (head, "", None):
                    res["manual_atestado"].append({"id": r.id, "titulo": r.titulo, **at})
                else:
                    res["manual_pendente"].append({"id": r.id, "titulo": r.titulo,
                                                   "motivo": "sem checagem automática" if not regras else "tools/check.py ausente no alvo"})
    soltas = {k: v for k, v in falhas_chk.items() if k not in mapeadas}
    if soltas:
        res["estrutura"].append({"codigo": "GATE-CHECKPY", "msg": f"tools/check.py com FALHA em regras {sorted(soltas)}"})
    bloqueios = [e["codigo"] for e in res["estrutura"]] + [v["id"] for v in res["violados"]] \
        + [f"{m['id']} (manual pendente)" for m in res["manual_pendente"]]
    res["resultado"] = "BLOCK" if bloqueios else "PASS"
    res["bloqueios"] = bloqueios
    return res


def texto(res, pr=None):
    L = [f"Gate SEO — {'PR #' + str(pr) + ' · ' if pr else ''}commit {res['commit'] or '?'} · {res['arquivos_no_diff']} arquivos no diff",
         f"Canônico lido: {res['canonico']['arquivo'] or 'AUSENTE'} · versão {res['canonico']['versao'] or '—'} · "
         f"sha256 {(res['canonico']['sha256'] or '')[:12]} · {res['canonico']['requisitos']} requisitos",
         f"RESULTADO: {res['resultado']}"]
    for e in res["estrutura"]:
        L.append(f"  BLOCK {e['codigo']}: {e['msg']}")
    for v in res["violados"]:
        if "auto" in v:
            why = "; ".join(v["falhas"].get("auto", [])) if v.get("falhas") else ""
            L.append(f"  BLOCK {v['id']} ({v['titulo']}): " + " | ".join(x for x in (why, v.get("motivo", "")) if x))
        else:
            L.append(f"  BLOCK {v['id']} ({v['titulo']}): regras {list(v['falhas'])} com FALHA")
    for m in res["manual_pendente"]:
        L.append(f"  BLOCK {m['id']} verificação manual pendente: {m['titulo']} ({m['motivo']})")
    for m in res["manual_atestado"]:
        L.append(f"  ok    {m['id']} manual atestado por {m['revisor']} em {m['data']}")
    for v in res["auto_ok"]:
        L.append(f"  ok    {v['id']} automático ({', '.join(v['regras'])})")
    chk = res["check_py"]
    L.append(f"tools/check.py do alvo: {'ausente' if not chk['disponivel'] else ('0 FALHAS' if not chk['falhas'] else 'FALHA em ' + ', '.join(sorted(chk['falhas'])))}")
    return "\n".join(L)


def registrar_readme(readme: Path, res, pr):
    """Acrescenta uma linha na tabela 'Validação SEO por PR' do README vivo."""
    t = readme.read_text(encoding="utf-8")
    cab = "## Validação SEO por PR"
    if cab not in t:
        t = t.rstrip("\n") + f"\n\n{cab}\n\n| Data (America/Bahia) | PR | Commit | Versão do canônico lida (arquivo · sha256) | Resultado |\n|---|---|---|---|---|\n"
    agora = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    cn = res["canonico"]
    sha = cn["sha256"] or "—"
    versao = f"{cn['versao'] or 'sem versão'} · `{cn['arquivo'] or 'ausente'}` · `{sha if cn.get('origem') == 'repo' else sha[:12]}`"
    resultado = res["resultado"] + (": " + ", ".join(res["bloqueios"]) if res["bloqueios"] else "")
    linha = f"| {agora} | {pr or '—'} | `{res['commit']}` | {versao} | {resultado} |\n"
    ini = t.index(cab)
    prox = t.find("\n## ", ini + len(cab))
    fim = len(t) if prox == -1 else prox + 1
    linhas = t[ini:fim].splitlines(keepends=True)
    ult = max(i for i, x in enumerate(linhas) if x.startswith("|"))  # linha logo após a última linha da tabela
    linhas.insert(ult + 1, linha)
    t = t[:ini] + "".join(linhas) + t[fim:]
    readme.write_text(t, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--canonico", default=str(AQUI.parent.parent / "docs" / "seo-canonico" / "canonico.meta.json"),
                    help="sidecar .meta.json do canônico (padrão: docs/seo-canonico/canonico.meta.json; ausente → BLOCK)")
    ap.add_argument("--alvo", required=True, help="worktree do PR (HTML já gerado)")
    ap.add_argument("--base", default="", help="ref base do diff (ex.: origin/main)")
    ap.add_argument("--pr", default="")
    ap.add_argument("--atestado", default="", help="JSON {SEO-xxx: {revisor, data, commit, nota}}")
    ap.add_argument("--registrar-readme", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    alvo = Path(a.alvo).resolve()
    if not alvo.is_dir():
        print(f"alvo não existe: {alvo}", file=sys.stderr)
        return 2
    at = json.loads(Path(a.atestado).read_text(encoding="utf-8")) if a.atestado else {}
    res = avaliar(Path(a.canonico), alvo, a.base, at)
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else texto(res, a.pr))
    if a.registrar_readme:
        registrar_readme(Path(a.registrar_readme), res, a.pr)
    return 0 if res["resultado"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
