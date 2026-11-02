# Midas — cards de oportunidade v0.8.0 (com dados reais)

## Estado (01/11/2026, horário da Bahia)

- 9 cards gerados: faixas 50, 100 e 200 mil × 16:9, 4:3 e 1:1, 1200 px de largura.
- FR-SPEC v1.0.0: os 9 PASSARAM nos critérios A, M e T (`validate_fr.py`); S1 ok nos 3 lotes; S2 ok, sha256 local igual ao da cópia no Drive. Revisão visual V1–V7 feita imagem por imagem.
- No Drive: `Midas - Blog / cards-oportunidade v0.8.0`. São arquivos NOVOS; a v0.7.0 continua lá, sem alteração.
- Sem deploy, sem dependência nova e sem chamada a nenhuma API externa na geração.

| Faixa | Combinação | Carta de crédito | Parcela (1ª, com seguro) | Próxima assembleia | Entrada | Lance |
|---|---|---|---|---|---|---|
| 50 mil | F50-1 (1 carta) | R$ 55.000,00 | R$ 2.408,79 | 26/11/2026 | dado não disponível | dado não disponível |
| 100 mil | F100-1 (2 cartas) | R$ 110.000,00 | R$ 5.472,36 | 26/11/2026 | dado não disponível | dado não disponível |
| 200 mil | F200-1 (1 carta) | R$ 236.973,00 | R$ 8.958,06 | 26/11/2026 | dado não disponível | dado não disponível |

Os valores vêm da coleta de 25/10/2026. É a mesma rodada e o mesmo card F<faixa>-1 das páginas `/oportunidades/50/`, `/100/` e `/200/`. Crédito e parcela saem do portal da administradora; a assembleia sai do calendário WebDisal. A coleta vale por 8 dias (`max_dias_coleta`): até 02/11 gera, a partir de 03/11 não gera nada.

## Causa (v0.7.0, local em `/workspace/midas/blog/cards-oportunidade/`, fora de qualquer branch do cortex-grok)

1. **As imagens não tinham texto nenhum.** Em `tools/gen_imgs.py`, linhas 7–9 e 18–21, as 9 imagens são só recortes (`crop(...).save(...)`) das fotos raw 001–003. Nenhuma linha desenha os campos.
2. **O HTML lia uma fonte estática vazia.** Em `data/oportunidades.json`, linhas 12, 14 e 16, `entrada`, `parcela`, `data_assembleia` e `fonte_valores` estão como `null`. Em `tools/gen_cards.py`, linha 11, o script lê só esse JSON. A função `valor()` (linhas 29–32) troca o `null` pelo marcador literal, e as linhas 41, 56 e 58 colocam `[data da assembleia]`, `[entrada]` e `[parcela]`.
3. **Nada ligava os cards ao motor.** O resultado do Arquimedes e da coleta só existia no gerador da rota (`tools/oportunidades/gerar.py`, staged em `cg-op`). Os cards do Midas nunca o chamaram.
4. **O template não tinha o campo lance.**

## Como funciona agora

```
python3 midas/cards/injetar.py --hoje 2026-11-01   # gerar.rodar() + gerar.card() -> midas/cards/dados-cards.json (stdlib)
python3 midas/cards/compor.py                      # dados-cards.json + foto da faixa -> midas/cards/saida/*.jpg + XMP/IPTC
python3 midas/cards/test_injetar.py                # 5 testes
```

- `injetar.py` não recalcula nada. Ele roda o gerador da rota (`gerar.rodar`) e renderiza o MESMO card da página (`gerar.card`, posição 1 da faixa). Depois lê os `data-campo` desse HTML: `credito`, `parcela`, `assembleia` e `entrada`. Assim o texto do card é idêntico ao da página, e uma mudança na rota passa direto para os cards.
- Se a coleta estiver vencida, o script para e não gera card (o teste cobre isso).
- `compor.py` desenha o painel sobre `oportunidades/assets/img/faixa-<N>-<prop>.jpg`, a mesma foto ilustrativa da rota. O painel tem: crédito, os 4 campos, a data da coleta, o CTA com FR-001 dentro da frase, o aviso e "imagem ilustrativa gerada por IA". Ele usa o Pillow que já está na box e já é usado pelo Midas (`compose.py`, `gen_imgs.py`). Os metadados vão com exiftool (`$EXIFTOOL`).
- IDs: `BLOG-20261101-oportunidade-<N>mil-v08-{16x9-001,4x3-002,1x1-003}`. Há um lote por faixa (S1). O sufixo `v08` existe porque o ID não aceita ponto. O script não sobrescreve um arquivo que já existe.

## Lacunas

- **Entrada e lance: "dado não disponível".** Não há base verificada. A mediana de lance livre e o % de embutido servem só para ordenar as combinações no Arquimedes; nunca são publicados, e o teste `test_nada_interno` garante isso.
- **Postgres / tabela fato não está deployado.** A fonte é a coleta CSV do Drive de 25/10 (`dados/oportunidades/coleta-2026-10-25/`, com `fontes.json` apontando os IDs no Drive). Também não existe coluna de parcela pré/pós-contemplação versionada.
- **A coleta vence em 03/11/2026.** Depois disso é preciso uma nova coleta para regerar os cards, e o lote ganha um ID novo.
- **O HTML dos cards v0.7** (`partials/cards-oportunidade.html`, local no Midas) continua com os marcadores. Esta branch corrige as imagens. O HTML da rota já traz os mesmos campos preenchidos (`gerar.card`).
- **A parcela é a 1ª, com seguro**, como o portal publica. Não é a parcela média nem a pós-contemplação.

## Arquivos trazidos do `cg-op` (rota /oportunidades, ainda sem commit)

O injetor depende do gerador da rota, que ainda não está em `main`. Esta branch traz o mínimo para rodar, **com bytes idênticos** aos de `cg-op` e do blog (`4f51fda`). Assim, quando a branch da rota entrar, o merge não tem conflito:

- `tools/oportunidades/gerar.py`, `tools/oportunidades/entrada.py` (sem nenhuma alteração)
- `vendor/arquimedes/` (`__init__`, `grid`, `modelos`, `ranking`, `VENDOR.md`)
- `config/oportunidades.json`; `config/site.json` (blob do blog `4f51fda`)
- `dados/oportunidades/coleta-2026-10-25/` (`grupos_a_venda.csv`, `cotas_disponiveis.csv`, `calendario.csv`, `fontes.json`)
- `oportunidades/assets/img/faixa-{50,100,200}-{16x9,4x3,1x1}.jpg` (mesmos bytes dos recortes da v0.7)
- `.gitignore` (igual ao do `cg-op`)

O restante da rota (páginas, CSS/JS, testes da rota) fica de fora e continua só staged em `cg-op`.
