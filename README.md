# cortex-grok
Repositório próprio do Grok/Ara no Conecta Cortex. Escrita livre. Leitura do CONECTACORTEX (Claude/Codex) via acesso de leitor.

---

# Gate SEO: validação de PR do blog contra o arquivo canônico do Pitágoras

> Documento vivo. Regra do Wagner (2026-11-02): antes de cada merge ou PR de blog, ler o arquivo canônico SEO
> (pasta `00_CONECTA CORTEX › 01_FONTE DA VERDADE` do Drive) e validar o diff contra os requisitos **bloqueantes**.
> Violou → merge bloqueado, com o ID do requisito. Cada leitura fica registrada abaixo com a versão do canônico.
> Sem dependência nova (Python 3 stdlib). Sem deploy. O arquivo do Drive é do Pitágoras: o gate só lê.

## Estado (2026-11-02 r3, America/Bahia)

| Item | Estado |
|---|---|
| **Canônico vigente** | **`docs/CANONICO_SEO.md` v1.1.0** (no repo; branch `blog-stripe-clone`, commit `498f5f9`). sha256 `00f85be0162fa0cea5cfc18d92553e5a16120b8f654c580083db6bdd739f9ab8`, 11 seções → `CANON-SEO-01…11`. Todas são bloqueantes, menos CANON-SEO-04, que é aviso desde a v1.1.0. Meta: `docs/seo-canonico/canonico.meta.json`. A v1.0.0 (`a6e41dd4…1dca`, t69u) ficou no `historico` do meta |
| Exceção da pasta do Drive | aprovada pelo Wagner (t69u, 2026-11-02): o conector do Drive é só leitura em `01_FONTE DA VERDADE`, por isso o canônico fica no repo. Vale **só** para `docs/CANONICO_SEO.md` e só com `aprovacao_repo` no meta |
| Arquivo canônico em `01_FONTE DA VERDADE` (Drive) | ausente. A pasta tem só o `Conecta Cortex · Fonte da Verdade (doc-mestre)` |
| Diário do Pitágoras | existe fora da pasta canônica: `DIARIO_SEO_PITAGORAS` v1.3 (2026-11-02), em `00_CONECTA CAPTAÇÃO E CONTEÚDO › 05_SEO`, com 106 requisitos, todos ativos. **Não tem ID `SEO-xxx` nem campo de severidade** (tem requisito, fonte, data de descoberta, status, impacto) |
| Gate | pronto e fechado: sem canônico válido, **todo PR de blog dá BLOCK** |
| Testes | `python3 tools/gate_seo/test_gate.py`: 33 OK (19 da r1 + 9 da r2 + 5 da v1.1.0) |
| PR #1 (`ec01233`, r3) | **BLOCK**: CANON-SEO-07 e CANON-SEO-08 (capas placeholder sem FR-001). CANON-SEO-04 é aviso. Não foi mergeado. Detalhe abaixo |

## Canônico no repo: `docs/CANONICO_SEO.md` (r2)

- **Origem.** O texto é exatamente o que o Wagner mandou (t69u, 2026-11-02): versão 1.0.0, data 2026-11-02, autor Pitágoras, aprovação Wagner Sena, status FONTE DA VERDADE. O gate confere o sha256 a cada leitura, então um PR que altere o canônico bloqueia com `GATE-CANON-SHA`.
- **IDs.** O arquivo não tem `SEO-xxx`. O ID sai mecanicamente do número da seção (`## N.` → `CANON-SEO-NN`): 01 embalagem, 02 gancho, 03 citação, 04 slug, 05 E-E-A-T/YMYL, 06 Core Web Vitals, 07 dados estruturados, 08 design, 09 tipos de post, 10 fluxo, 11 docs base. Nenhum texto novo foi criado.
- **Severidade.** O arquivo não tem campo de severidade. Todas as 11 seções são tratadas como **bloqueantes**, porque o arquivo se declara "FONTE DA VERDADE" e usa "reprovação", "NUNCA", "PROIBIDA" e "obrigatória". A severidade vem do meta (`severidade_padrao`); sem ela, o gate bloqueia com `GATE-CANON-SEM-SEVERIDADE`. Data = cabeçalho; status "ativo" = "FONTE DA VERDADE".
- **Avaliação por seção.** A avaliação tem duas camadas:
  - **Checagens automáticas parciais** (`tools/gate_seo/canon_checks.py`, stdlib, lê HTML e XMP bruto):
    - §1: grupo Disal, mediana, Arquimedes, embutido com número;
    - §3: "A CONFERIR" e "Fonte: Google";
    - §4: slug com ID de criativo `BLOG-AAAAMMDD` (FR-SPEC v1.1.0);
    - §5: links do Giro e do LinkedIn na bio, foto do autor;
    - §7: JSON-LD Article/BlogPosting e XMP com TransmissionReference=FR-001, autor, Giro, ID de criativo, largura ≥ 1080;
    - §8: as 4 proporções 9:16, 1:1, 4:5 e 16:9, e nenhuma imagem placeholder.
  - **Atestado manual por commit** (`docs/seo-canonico/avaliacoes/PR<n>-<commit>.json`, com `veredito` ok, violado ou pendente, mais o motivo).
  - Uma falha automática ou um veredito "violado" viola o ID. Sem atestado "ok" do mesmo commit, o ID fica em manual pendente, que também bloqueia.
- **§6 (Lighthouse).** Na r2, o Lighthouse não estava instalado e o §6 bloqueava. Na r3 ele foi instalado (t71u); ver abaixo.

## Canônico v1.1.0 (r3, 2026-11-02, t71u)

O Wagner autorizou explicitamente relaxar §2, §3, §4, §5, §6, §7, §8 e §10 (t71u). §1, §9 e §11 não mudaram. O gate passou a ler o sha256 `00f85be0…9ab8`. Mudanças no gate:

- **Severidade por seção** no meta (`severidade_por_secao`). CANON-SEO-04 passou a `aviso`. Seção `aviso` com falha automática aparece em `AVISO …` na saída e na coluna Resultado do README, sem bloquear.
- **§3:** o texto de bio marcado como afirmação do autor (classe `about-author`/`author-bio` ou `data-fonte="Declaração do próprio …"`) fica fora da varredura de citação. Continua dentro da varredura de embalagem (§1).
- **§5:** os links Giro e LinkedIn são obrigatórios na bio do artigo **ou** na página do autor linkada com `rel="author"`. Aceita foto real ou avatar.
- **§6:** lê o baseline `artifacts/lighthouse/*.json` do blog (`tools/lighthouse/run.mjs`, Lighthouse 13.6.0). Só vale um baseline cujo HTML/assets/config seja idêntico ao do HEAD (`git diff`). Passa com LCP ≤ 2,5 s, CLS ≤ 0,1, Perf ≥ 90 e SEO ≥ 90 sem `is-crawlable`, auditoria que reprova só pelo `noindex` deliberado. O TBT é o proxy de lab para o INP.
- **§7:** a versão do FR não trava. Os campos IPTC (TransmissionReference=FR-001, autor, Giro, ID criativo) e a largura ≥ 1080 continuam obrigatórios.
- **§8:** regra dura = todo asset do Article com metadado FR-001 e nenhum placeholder. As proporções viraram informativas.
- **§10:** a única etapa bloqueante é a aprovação do Wagner, em `docs/seo-canonico/aprovacoes/PR<n>.json` (`por`, `data`, `ref`, `commit`), passada ao gate com `--aprovacao`. Sem registro para o HEAD, o §10 falha.

### PR #1 contra o canônico v1.1.0 (commit `ec01233`, 2026-11-02)

| ID | Veredito | Motivo |
|---|---|---|
| CANON-SEO-01 | ok | nada de grupo Disal, mediana, embutido com número ou Arquimedes, inclusive na bio e na página do autor |
| CANON-SEO-02 | ok | é post de formato/educação ("Como funciona…") e abre com contexto, como a v1.1.0 permite |
| CANON-SEO-03 | ok | não há "A CONFERIR" nem "Fonte: Google". A bio está marcada como declaração do Wagner. Alertas de compliance: "5 estrelas no Google", "8 primeiras parcelas", "melhor do Brasil por 6 anos", "mais de 500" |
| CANON-SEO-04 | aviso | o slug `artigo-exemplo` não tem ID de criativo; não bloqueia |
| CANON-SEO-05 | ok | Giro e LinkedIn estão na página do autor (rel=author, linkada da bio) e no sameAs; foto real |
| CANON-SEO-06 | ok | Lighthouse 13.6.0, desktop, 3 páginas: Perf 100, LCP 0,24 s, CLS 0, TBT 0 ms, SEO 100 sem is-crawlable (bruto 66/69 por causa do noindex) |
| CANON-SEO-07 | **violado** | as 3 capas placeholder não têm IPTC com autor, Giro, ID criativo nem FR-001 |
| CANON-SEO-08 | **violado** | as 3 capas são placeholder e não passaram pelo FR-001 |
| CANON-SEO-09 | ok (interpretação) | a §9 rege as notícias (60/40); o post é educativo, tipo que a §2 v1.1.0 reconhece. O Wagner deve confirmar |
| CANON-SEO-10 | ok | aprovação do Wagner registrada (t71u, 2026-11-02, `ec01233`); check.py com 0 falhas; Lighthouse OK |
| CANON-SEO-11 | ok | seção de referência |

O `tools/check.py` do blog tem 427 OK, 0 falhas e 4 avisos. Com `--lighthouse`, são 428 OK. Para destravar, o Midas precisa entregar as capas finais com FR-001 (IPTC completo, ID `BLOG-AAAAMMDD-…`).

### PR #1 contra o canônico v1.0.0 (commit `1f5c287`, 2026-11-02)

| ID | Veredito | Motivo |
|---|---|---|
| CANON-SEO-01 | ok | nenhum grupo Disal, mediana, embutido como dado ou Arquimedes; "Disal" aparece só como administradora na bio, e "lance embutido" só como nome de pauta, sem número |
| CANON-SEO-02 | **violado** | a abertura não tem hook com número real, fonte e data; não existe a sequência hook → oportunidade → oferta |
| CANON-SEO-03 | **violado** | os números da bio (2002, "24 anos", "mais de 15 anos") não têm fonte visível, link nem data de acesso, e "24 anos" é uma soma não identificada. Os números da lei estão ok |
| CANON-SEO-04 | **violado** | o slug `artigo-exemplo` não tem ID de criativo |
| CANON-SEO-05 | **violado** | a foto real está ok, mas a bio não tem link do Giro Automotivo nem do LinkedIn |
| CANON-SEO-06 | **pendente** | o Lighthouse não está instalado, então a verificação manual está pendente |
| CANON-SEO-07 | **violado** | as 3 capas não têm TransmissionReference=FR-001, autor, Giro e ID de criativo no XMP/IPTC; o `validate_fr.py` v1.1.0 reprova as 3; o blog cita FR-SPEC v1.0.0 |
| CANON-SEO-08 | **violado** | as proporções são 16:9, 4:3 e 1:1 (faltam 9:16 e 4:5), e as capas são placeholder |
| CANON-SEO-09 | **violado** | o post é explicativo da lei, não é notícia de oportunidade nem de mercado |
| CANON-SEO-10 | **violado** | faltam a validação do Pitágoras, o Lighthouse e o render FR-001 do Midas, e `paginas_aprovadas_wagner` está vazio. O noindex continua mantido |
| CANON-SEO-11 | ok | seção de referência; nada no PR a contradiz |

`tools/check.py` do PR #1: 307 OK, 0 falhas e 4 avisos (3 capas placeholder e o WhatsApp placeholder). O conteúdo do blog não foi alterado para passar.

## Como rodar

```
# antes de abrir/mergear PR de blog (alvo = worktree do PR, com o HTML gerado)
python3 tools/gate_seo/gate.py --alvo ../cg-blog --base origin/main --pr 1 \
    --atestado docs/seo-canonico/avaliacoes/PR1-ec01233.json --aprovacao docs/seo-canonico/aprovacoes/PR1.json \
    --registrar-readme README.md
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
tools/gate_seo/canonico.py      parser (ID / data / fonte / severidade / status / versão) + parse_secoes (## N. → CANON-SEO-NN)
tools/gate_seo/canon_checks.py  checagens automáticas parciais das seções do docs/CANONICO_SEO.md
docs/seo-canonico/canonico.meta.json   meta do canônico vigente (origem repo, sha256 v1.1.0, aprovações t69u/t71u, severidade por seção)
docs/seo-canonico/aprovacoes/   aprovação do Wagner por PR e commit (§10)
docs/seo-canonico/avaliacoes/   atestados manuais por PR e commit
tools/gate_seo/gate.py          gate: PASS ou BLOCK + IDs; registra no README
tools/gate_seo/snapshot.py      grava o .meta.json (drive_id, pasta, versão, sha256) do snapshot exportado
tools/gate_seo/mapa_checks.json ID canônico → regras do tools/check.py do blog (vazio até existirem IDs)
tools/gate_seo/test_gate.py     33 testes (parser + gate + v1.1.0)
docs/seo-canonico/candidato-DIARIO_SEO_PITAGORAS-v1.3.md (+ .meta.json)
                                snapshot do diário v1.3 (Drive 1BrYkzsmedHKHg8mp6mVPiJCK2Bkbzl--lPNXBY3sRVw,
                                modificado 2026-11-02 12:18 America/Bahia). NÃO é o canônico: está fora da pasta e sem IDs
```

## Pendências (do Pitágoras, não do gate)

- Publicar o canônico em `00_CONECTA CORTEX › 01_FONTE DA VERDADE`, com ID `SEO-xxx`, data, fonte, **severidade** e status em cada requisito.
- Dizer quais requisitos são bloqueantes. O gate não infere severidade: nada é inventado.
- (r2) O canônico vigente é o `docs/CANONICO_SEO.md` do repo. Se o Pitágoras publicar uma versão no Drive com `SEO-xxx` e severidade, ela substitui a derivação `CANON-SEO-NN`.
- (r3) Lighthouse instalado no blog (t71u). O CANON-SEO-06 passa.
- (r3) O PR #1 ainda viola CANON-SEO-07 e 08: faltam as capas finais do Midas com FR-001. A §9 foi atestada ok por interpretação, e o Wagner deve confirmar.

## Validação SEO por PR

| Data (America/Bahia) | PR | Commit | Versão do canônico lida (arquivo · sha256) | Resultado |
|---|---|---|---|---|
| 2026-11-02 12:52 | #1 blog-stripe-clone | `4f51fda` | sem versão · `ausente` · `—` | BLOCK: GATE-CANON-AUSENTE |
| 2026-11-02 12:52 | oportunidades (staged em cg-op, sem PR) | `4f51fda` | sem versão · `ausente` · `—` | BLOCK: GATE-CANON-AUSENTE |
| 2026-11-02 20:35 | #1 blog-stripe-clone | `1f5c287` | 1.0.0 · `docs/CANONICO_SEO.md` · `a6e41dd49822bdd453b5195452dc37b9202d57a54579646ae574302cfdbb1dca` | BLOCK: CANON-SEO-02, CANON-SEO-03, CANON-SEO-04, CANON-SEO-05, CANON-SEO-07, CANON-SEO-08, CANON-SEO-09, CANON-SEO-10, CANON-SEO-06 (manual pendente) |
| 2026-11-02 21:05 | #1 blog-stripe-clone | `ec01233` | 1.1.0 · `docs/CANONICO_SEO.md` · `00f85be0162fa0cea5cfc18d92553e5a16120b8f654c580083db6bdd739f9ab8` | BLOCK: CANON-SEO-07, CANON-SEO-08 · avisos (não bloqueiam): CANON-SEO-04 |

Diagnóstico das mesmas duas leituras contra o candidato `DIARIO_SEO_PITAGORAS` v1.3 (sha256 `2357f75bcd7d`). Também dá BLOCK, com `GATE-CANON-FORA-DA-PASTA`, `GATE-CANON-SEM-ID` (106/106) e `GATE-CANON-SEM-SEVERIDADE` (106/106). O `tools/check.py` dos dois alvos tem 0 FALHAS.
