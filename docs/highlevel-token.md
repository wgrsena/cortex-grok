# HighLevel: o que falta para destravar o PR 18 (`HIGHLEVEL_TOKEN`)

Status em 01/11/2026 (America/Bahia): **bloqueado por token**. Nenhuma chamada à HighLevel foi feita para escrever este documento.

## 1. Situação

- O PR 18 (HighLevel v3, plano de 42 chamadas) **não está visível** daqui. Não está em `wgrsena/conecta-cortex` (só PRs #1 e #2) nem em `wgrsena/cortex-grok`. Provavelmente está em `wgrsena/CONECTACORTEX`, que está sem acesso. Por isso o plano das 42 chamadas **não foi lido**.
- A lista de escopos abaixo vem do roteiro do Cortex Lab (`highlevel/fluxo-comercial-teste.md`, v0.1, 01/11/2026). É preciso conferir contra as 42 chamadas do PR 18 antes de gerar o token.
- Segundo esse roteiro, o token do lab que existia respondia 401 em location info, pipelines, calendars, users, conversations, forms, funnels e blogs. Falta escopo, não falta autenticação.

## 2. O que o Wagner precisa fazer

1. **Criar uma Private Integration** na subconta. Na HighLevel: Settings › Private Integrations › "Create new Integration". Se o item não aparecer, habilitar em Labs.
   - Nome sugerido: `cortex-pr18-lab`.
   - Descrição: "Cortex: PR 18, só subconta de laboratório".
2. **Marcar só os escopos necessários** (tabela da seção 3).
3. **Copiar o token**, que só aparece uma vez.
4. **Colar o token como variável de ambiente secreta `HIGHLEVEL_TOKEN`** no ambiente dos agentes, pelo mesmo mecanismo do `GH_TOKEN_CORTEX_GROK`. **Não colar em chat, arquivo, issue, commit ou log.**
5. **Informar o Location ID da subconta** em `HIGHLEVEL_LOCATION_ID`. Não é segredo. O roteiro do Lab usa `huMcM926VaTDELzSRQEc` (laboratório). Confirmar se o PR 18 aponta para essa ou para outra subconta.
6. **Autorizar explicitamente a 1ª chamada.** Até lá, a regra é "nenhuma chamada à HighLevel". Sugestão de 1ª chamada, só leitura: `GET /locations/{HIGHLEVEL_LOCATION_ID}`.

## 3. Escopos (Private Integration, API v2)

Nomes conferidos na lista oficial `GoHighLevel/highlevel-api-docs › docs/oauth/Scopes.md` (lida em 01/11/2026):

| Escopo | Para quê (roteiro do Lab) | Endpoint de referência |
|---|---|---|
| `locations.readonly` | ler a subconta | `GET /locations/:locationId` |
| `locations/tags.readonly`, `locations/tags.write` | tags `lab-teste`, `lgpd-*`, `cortex-quente/frio` | `GET/POST /locations/:locationId/tags` |
| `locations/customFields.readonly`, `locations/customFields.write` | campos `cortex_lead_id`, `cortex_tipo_bem`, `cortex_valor_credito`, `cortex_resumo_handoff` | `/locations/:locationId/customFields` |
| `contacts.readonly`, `contacts.write` | contatos de teste e tags no contato | `/contacts/` |
| `opportunities.readonly`, `opportunities.write` | pipeline `Lab — Comercial Teste` e mover a oportunidade no handoff | `GET /opportunities/pipelines`, `/opportunities/` |
| `users.readonly` | dono da tarefa de handoff | `GET /users/` |
| `conversations.readonly` | conferir que nenhuma mensagem sai da HighLevel | `GET /conversations/:id` |
| `workflows.readonly` | conferir os workflows em Draft. A API **não cria** workflow; o editor é manual | `GET /workflows/` |

**Fora da lista** até o PR 18 pedir: `conversations/message.write` (envio de mensagem), `calendars.*`, `forms.readonly`, `funnels/*`, `blogs/*`, `medias.*`, `users.write`, `locations.write`.

## 4. Como o código deve usar o token

Formato oficial (marketplace.gohighlevel.com › Authorization › Private Integrations):

```
Authorization: Bearer $HIGHLEVEL_TOKEN
Version: 2021-07-28
Accept: application/json
Base URL: https://services.leadconnectorhq.com
```

Regras:
- O token é lido **só de `process.env.HIGHLEVEL_TOKEN`** (ou equivalente). Nunca em arquivo, fixture ou log, e o header `Authorization` deve ser mascarado nos logs.
- **"v3" e o header `Version`.** Segundo o guia de migração da HighLevel, a API atual usa o header `Version` e APIs mais novas podem usar versões nomeadas (ex.: v3). Cada uma das 42 chamadas deve usar a versão que a documentação do endpoint indica. Não assumir `2021-07-28` para todas.
- **Rotação.** A HighLevel recomenda rotacionar a cada 90 dias. Na rotação, o token antigo e o novo valem juntos por 7 dias. Editar os escopos **não** muda o token.
- **Vazamento.** Usar "Rotate and expire this token now" e trocar a variável.

## 5. Checklist de desbloqueio

- [ ] Acesso de leitura ao repositório do PR 18 (ou o plano das 42 chamadas colado num doc), para conferir os escopos.
- [ ] Private Integration criada com os escopos da seção 3, ajustados ao plano.
- [ ] `HIGHLEVEL_TOKEN` no ambiente (secreto).
- [ ] `HIGHLEVEL_LOCATION_ID` confirmado.
- [ ] OK explícito do Wagner para a 1ª chamada (leitura) e, depois, para as de escrita.

## Fontes

- HighLevel, Private Integrations: https://marketplace.gohighlevel.com/docs/Authorization/PrivateIntegrationsToken (acesso em 01/11/2026).
- HighLevel, lista de escopos: https://github.com/GoHighLevel/highlevel-api-docs/blob/main/docs/oauth/Scopes.md (acesso em 01/11/2026).
- HighLevel Support, guia de migração para Private Integrations: https://help.gohighlevel.com/support/solutions/articles/155000008488 (acesso em 01/11/2026).
- Cortex Lab, `highlevel/fluxo-comercial-teste.md` v0.1 (01/11/2026), local no box, fora de repositório.
