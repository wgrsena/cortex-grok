# cortex-grok
Repositório próprio do Grok/Ara no Conecta Cortex. Escrita livre. Leitura do CONECTACORTEX (Claude/Codex) via acesso de leitor.

---

# Gate SEO: validação de PR do blog contra o arquivo canônico do Pitágoras

> Documento vivo. Regra do Wagner (2026-11-02): antes de cada merge ou PR de blog, ler o arquivo canônico SEO
> (pasta `00_CONECTA CORTEX › 01_FONTE DA VERDADE` do Drive) e validar o diff contra os requisitos **bloqueantes**.
> Violou → merge bloqueado, com o ID do requisito. Cada leitura fica registrada abaixo com a versão do canônico.
> Sem dependência nova (Python 3 stdlib). Sem deploy. O arquivo do Drive é do Pitágoras: o gate só lê.

## Estado (2026-11-02, America/Bahia)

| Item | Estado |
|---|---|
| Arquivo canônico em `01_FONTE DA VERDADE` | **ausente.** A pasta tem um único arquivo, `Conecta Cortex · Fonte da Verdade (doc-mestre)`, sem requisitos SEO |
| Diário do Pitágoras | existe fora da pasta canônica: `DIARIO_SEO_PITAGORAS` v1.3 (2026-11-02), em `00_CONECTA CAPTAÇÃO E CONTEÚDO › 05_SEO`, com 106 requisitos, todos ativos. **Não tem ID `SEO-xxx` nem campo de severidade** (tem requisito, fonte, data de descoberta, status, impacto) |
| Gate | pronto e fechado: sem canônico válido, **todo PR de blog dá BLOCK** |
| Testes | `python3 tools/gate_seo/test_gate.py`: 19 OK |

## Como rodar

```
# antes de abrir/mergear PR de blog (alvo = worktree do PR, com o HTML gerado)
python3 tools/gate_seo/gate.py --alvo ../cg-blog --base origin/main --pr 1 --registrar-readme README.md
# exit 0 = PASS · exit 1 = BLOCK (lista os IDs) · exit 2 = erro de uso
```

Quando o Pitágoras publicar o canônico em `01_FONTE DA VERDADE`:
1. Exportar o Doc como Markdown pelo conector do Drive (só leitura) em `docs/seo-canonico/<versão>.md`.
2. Gerar o sidecar com sha256, ID e pasta do Drive: `python3 tools/gate_seo/snapshot.py docs/seo-canonico/<versão>.md --drive-id … --nome … --pasta-id 1Vw46Po3-AuOp0EmEeSWGONYZyRlKTwMN --pasta-nome "00_CONECTA CORTEX › 01_FONTE DA VERDADE" --modified <modifiedTime>`.
3. Copiar o sidecar para `docs/seo-canonico/canonico.meta.json` (é o padrão do gate) e mapear os IDs bloqueantes em `tools/gate_seo/mapa_checks.json`.

## Regras do gate (falha fechado)

1. **Canônico** (`GATE-CANON-*`). O gate bloqueia em qualquer um destes casos:
   - snapshot ausente (`AUSENTE`);
   - sha256 que não confere (`SHA`);
   - arquivo fora da pasta `01_FONTE DA VERDADE` (`FORA-DA-PASTA`);
   - sem versão (`SEM-VERSAO`);
   - algum requisito sem ID, data, fonte, severidade ou status (`SEM-ID`, `SEM-DATA`, `SEM-FONTE`, `SEM-SEVERIDADE`, `SEM-STATUS`);
   - ID duplicado.
2. **Bloqueante e ativo com checagem automática.** O ID aparece em `mapa_checks.json` ou o requisito tem o campo `Verificação: auto:R7,L4`. O gate roda o `tools/check.py` do alvo; se uma regra mapeada der FALHA, o ID é **violado**.
3. **Bloqueante e ativo sem checagem automática.** Vira **verificação manual**, que só passa com atestado `{SEO-xxx: {revisor, data, commit}}` do mesmo commit (`--atestado`). Sem atestado, dá BLOCK como "manual pendente"; nunca passa calado.
4. FALHA do `tools/check.py` que não corresponde a nenhum ID também bloqueia (`GATE-CHECKPY`).
5. Requisitos não bloqueantes ou não ativos (envelhecido ou substituído) ficam fora do gate.

Formato do requisito que o parser aceita: as duas grafias que o Google Docs exporta (`- **Campo:** valor` e `- [ ] Campo: valor`).

```
### SEO-001 — Título
- **Requisito:** …
- **Fonte:** …
- **Data:** 2026-11-02
- **Severidade:** bloqueante
- **Status:** ativo
```

## Arquivos

```
tools/gate_seo/canonico.py      parser (ID / data / fonte / severidade / status / versão)
tools/gate_seo/gate.py          gate: PASS ou BLOCK + IDs; registra no README
tools/gate_seo/snapshot.py      grava o .meta.json (drive_id, pasta, versão, sha256) do snapshot exportado
tools/gate_seo/mapa_checks.json ID canônico → regras do tools/check.py do blog (vazio até existirem IDs)
tools/gate_seo/test_gate.py     19 testes (parser + gate)
docs/seo-canonico/candidato-DIARIO_SEO_PITAGORAS-v1.3.md (+ .meta.json)
                                snapshot do diário v1.3 (Drive 1BrYkzsmedHKHg8mp6mVPiJCK2Bkbzl--lPNXBY3sRVw,
                                modificado 2026-11-02 12:18 America/Bahia). NÃO é o canônico: está fora da pasta e sem IDs
```

## Pendências (do Pitágoras, não do gate)

- Publicar o canônico em `00_CONECTA CORTEX › 01_FONTE DA VERDADE`, com ID `SEO-xxx`, data, fonte, **severidade** e status em cada requisito.
- Dizer quais requisitos são bloqueantes. O gate não infere severidade: nada é inventado.

## Validação SEO por PR

| Data (America/Bahia) | PR | Commit | Versão do canônico lida (arquivo · sha256) | Resultado |
|---|---|---|---|---|
| 2026-11-02 12:52 | #1 blog-stripe-clone | `4f51fda` | sem versão · `ausente` · `—` | BLOCK: GATE-CANON-AUSENTE |
| 2026-11-02 12:52 | oportunidades (staged em cg-op, sem PR) | `4f51fda` | sem versão · `ausente` · `—` | BLOCK: GATE-CANON-AUSENTE |

Diagnóstico das mesmas duas leituras contra o candidato `DIARIO_SEO_PITAGORAS` v1.3 (sha256 `2357f75bcd7d`). Também dá BLOCK, com `GATE-CANON-FORA-DA-PASTA`, `GATE-CANON-SEM-ID` (106/106) e `GATE-CANON-SEM-SEVERIDADE` (106/106). O `tools/check.py` dos dois alvos tem 0 FALHAS.
