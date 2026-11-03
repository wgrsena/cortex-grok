# Fluxo em cascata

Regra: **só se renderiza cartaz/tabela de grupo que o Wagner escolheu**. Evita gerar PDF de grupo que não será usado.

```mermaid
flowchart TD
  A["Coleta semanal (scrap/)<br/>tabela fato ~70 grupos vivos"] --> B["Arquimedes Disal<br/>compila e aplica a regra"]
  B --> C["Tabela ranqueada COMPLETA<br/>(branch separada + diff)"]
  C --> D{"Wagner escolhe<br/>as melhores oportunidades"}
  D -- "não escolheu" --> E["Nada é renderizado"]
  D -- "escolheu grupos" --> F["Dispara criação de<br/>cartazes / tabelas / PDF"]
  F --> G["Marketing (futuro) cria<br/>Comercial (futuro) vende"]
  C -. "commit só com 'manda' do Wagner" .-> H["Cortex Build commita"]
```
*(Mermaid não validado: sem mermaid-cli. Conferir em https://mermaid.live.)*

## Passos
1. Arquimedes entrega a tabela ranqueada completa (todos os grupos vivos, não só o Top 5).
2. Wagner escolhe as melhores oportunidades (limites de entrada, ex.: 10 a 24/11).
3. Só então dispara cartaz/tabela, para os grupos escolhidos.
4. Commit da tabela: só o Cortex Build, só com aprovação do Wagner.

Validade: dado com mais de 8 dias de coleta sai `desatualizada` (solver v1.1); cartaz de grupo com dado vencido deve esperar a coleta seguinte.
