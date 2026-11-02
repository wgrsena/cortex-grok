# cortex-grok
Repositório próprio do Grok/Ara no Conecta Cortex. Escrita livre. Leitura do CONECTACORTEX (Claude/Codex) via acesso de leitor.

## Piso de diluição (`ledger/`)

`ledger/calculateLedger.ts` v1.0.0 calcula o destino do lance com o piso de diluição de 50% (`DILUTION_FLOOR_PERCENT`, cl. 12.2 b, Regulamento Disal 27ª ed., p. 17). É um porte da lei 8 do Cortex Lab v0.1.0 em centavos inteiros. Sem extrato (`lastPaidInstallment = null`) não há simulação (`sem_extrato`), nunca zero. O lance fixo não dilui (12.3 / 16.12.3), e o excedente vai para a ordem inversa (12.2 c).

Premissas P1–P6: default adotado (Wagner 01/11). Ver `docs/piso-diluicao.md` §5.

Teste (sem dependências): `node --experimental-strip-types ledger/calculateLedger.test.ts`
