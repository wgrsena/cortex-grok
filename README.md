# cortex-grok
Repositório próprio do Grok/Ara no Conecta Cortex. Escrita livre. Leitura do CONECTACORTEX (Claude/Codex) via acesso de leitor.

## Backtest rolante da sequência (01/11/2026)

**Estado:** o backtest foi executado sobre o cofre real e as evidências estão em `artifacts/backtest-rolante/`. Detalhes em [`docs/backtest-rolante.md`](docs/backtest-rolante.md).

**Método**
- **Cofre:** planilha WebDisal "webdisal_resultados_assembleia_2026-10-25", com 57.239 linhas.
  - É lida a partir de uma cópia local só-leitura, fora do repositório.
  - CSV sha256 `352363b1dfc3e6493affa1d74c3d8278ad1fd866b951569261885b4c9f74d910`; o script aborta se o hash divergir.
- **Corte rolante mensal, sem look-ahead:** a entrada usa só assembleias anteriores a D.
- **Sequência:** W = assembleias consecutivas com lance livre contemplado, dentre as 6 anteriores a D (de 2 a 6).
  - Lance previsto = maior menor lance livre dessas W.
  - p = W/6 (`solver/niveis.py::niveis_livres`).
- **Mediana:** só desempate no ranking.

**Decisão Wagner 01/11: empate exato = contemplação.**
- Acerto = lance previsto >= menor lance livre contemplado real.
- Comparação em `Decimal` exato, sem float.
- 20 empates no histórico.

**Premissas adotadas como default**
1. Data de referência = dia 1 de cada mês; alvo = primeira assembleia após D, dentro do mês.
2. Assembleia-alvo sem lance livre contemplado fica fora da conta.
3. O grupo existe em D se já teve assembleia antes de D.
4. Os grupos 003/004/006 entram porque o tipo de bem vem vazio no cofre.

**Números**
- 162 grupos e 7.670 avaliações em 147 cortes, de 2014-09-01 a 2026-10-01.
- Geral: **81,7%** (6.263/7.670), contra 91,4% previsto.
- Últimos 12 meses: **88,6%** (1.458 avaliações).

| W | p | n | taxa |
|---|---|---|---|
| 2 | 0,33 | 452 | 59,7% |
| 3 | 0,50 | 392 | 62,0% |
| 4 | 0,67 | 334 | 72,2% |
| 5 | 0,83 | 292 | 77,7% |
| 6 | 1,00 | 6.200 | 85,2% |

**Como rodar** (só stdlib, testado em Python 3.13; os testes rodam com `python -m unittest discover -s scrap` ou com `pytest`):
```
python scrap/backtest_rolante.py --cofre /caminho/copia-so-leitura.csv --sha256 <hash> --saida backtest_saida
python -m pytest -q scrap        # 9 testes
```

**Origem do código portado:** conecta-cortex, branch `cortex/revisao-reviewer`, commit `8bfd5d4511c2132b18708f4c73f38097e86481cc`.

| arquivo | origem | sha256 |
|---|---|---|
| `solver/niveis.py` | copiado sem alteração | `eedb51d474557e9380a0d7f640cf12bf12fe346b9a934b1564ffe6926c015af6` |
| `solver/modelos.py` | copiado sem alteração | `0db8c5d2fc95303ae69164e892993ccdd5c786b701b71290236be5881321f3d8` |
| `scrap/cofre.py` | copiado sem alteração | `074bc3349b5adf313baea4b6993709f8222683ccb6504fc4b93adfcbb49a0879` |
| `scrap/conftest.py` | copiado sem alteração | `53001fcd530d5cbf556e9c47cc7cb28799cb3da00a81521dae97b548e15b6277` |
| `scrap/backtest_rolante.py` | novo (branch local `cortex/backtest-rolante` do conecta-cortex) | `939a846fce60c559722bbf5fd59083eb13811f6fbf0cc02e713c75affe5272a8` |
| `scrap/test_backtest_rolante.py` | novo (idem) | `128e3c33b76b51fc71ef98942f52dec1900f71fe1b427b36fbcb2bc32b083818` |

**Dependências:** nenhuma nova. O script e os módulos portados usam só a stdlib, por isso não há `requirements.txt`. O pytest é opcional; no conecta-cortex é usado `pytest==9.1.1`.
