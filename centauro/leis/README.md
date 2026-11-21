# centauro/leis: leis executáveis e persona do Centauro

**Estado: BLOQUEADO — sem acesso a `conecta-sdr` e `conecta-captacao`.**

Tarefa (pendente desde 26/10, Cortex Lab): absorver `compliance.mts` e `playbook.mts` do `conecta-sdr` e o `CLAUDE.md` do `conecta-captacao`, reescrever como leis executáveis (`centauro/leis/`) e persona (`centauro/persona.md`), **sem alterar os repositórios originais**.

## O que foi tentado (somente leitura, 28/10/2026) e o erro exato
1. `git clone --depth 1 https://github.com/wgrsena/conecta-sdr.git` (e `conecta-captacao`), sem credencial:
   `fatal: could not read Username for 'https://github.com': terminal prompts disabled`
2. Ferramenta GitHub conectada (`get_file_contents`, `wgrsena/conecta-sdr` e `wgrsena/conecta-captacao`):
   `scm_repo_not_accessible` — "GitHub cannot see repository wgrsena/conecta-sdr with the connected account: it may not be granted to Cursor's GitHub App, be private, or not exist." (mesma resposta para `conecta-captacao`).
3. `gh auth status`: "You are not logged into any GitHub hosts."

Nenhum token foi usado ou gravado. Nenhuma lei foi escrita de memória.

## O que falta para destravar (uma das opções)
- Token com **acesso de leitura** a `wgrsena/conecta-sdr` e `wgrsena/conecta-captacao` (até agora o token só enxergava `conecta-cortex` e `dialogflow-webhook`), colado pelo Wagner em campo seguro; **ou**
- Conceder os dois repos ao app GitHub do Cursor (https://github.com/apps/cursor/installations/new); **ou**
- O Wagner (ou o Cortex Lab) enviar o conteúdo de `compliance.mts`, `playbook.mts` e `CLAUDE.md`.

## Referência já no repo (não substitui as fontes)
`centauro/README.md` e `docs/arquitetura.md` descrevem apenas o que se sabe: compliance = **alerta com registro, sem bloqueio**; a IA não recebe grupo/mediana/embutido; a Centauro nunca diz percentual ou "probabilidade" (`centauro/frases.py`).
