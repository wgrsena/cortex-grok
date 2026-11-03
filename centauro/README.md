# centauro: atendimento no WhatsApp Business API

Persona que atende e qualifica no primeiro contato; **um humano decide e fecha**. Estado: só o contrato de fala e o fluxo em pseudocódigo. **Nada de WhatsApp está integrado.**

- Fluxo do endpoint: `../supabase/functions/atendimento/PSEUDOCODIGO.md` (a Edge Function só autentica e repassa; o cálculo está no `solver/`).
- `frases.py`: transforma a sequência W do solver em frase. A Centauro nunca diz percentual ou "probabilidade".
- A IA **não recebe** grupo, mediana nem embutido; esses dados vão para o dossiê de handoff do vendedor.
- Compliance: alerta com registro, sem bloqueio; o Wagner arbitra.
- LGPD: consentimento no primeiro contato; voz só com opt-in específico.
- Pendente: escolha do provedor (360dialog × Zenvia), persona (`playbook` do conecta-sdr, portar sem tocar naquele repo), critério de lead quente.

```
python -m pytest -q centauro
```
