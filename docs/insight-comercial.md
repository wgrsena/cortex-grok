# Insight comercial: lance coberto pelo embutido

**Ideia (Wagner):** se a **mediana do lance livre** do grupo for **menor que o `pct_embutido_max`** (em % da categoria), o lance vencedor típico pode ser **coberto integralmente pelo embutido**. O cliente contempla **sem recurso próprio**.

## No solver v1.1
- `mediana_lance_livre`: fração da categoria; **dado comercial**, calculado pelo job a partir do cofre. Nunca entra em probabilidade nem em ranking.
- `embutido_cobre_mediana`: `mediana <= pct_embutido_max` (o embutido que iguala a mediana cobre o lance); `null` se a mediana é desconhecida.
- Unidade e comparação alinhadas na revisão I2 (01/11/2026): tudo em fração da categoria, solver e view `grupos_disal_faixa` com `<=` (migration `0003`). Ver `solver/NOTAS_DUVIDAS.md`.
- Ressalva: o lance **fixo** não usa mediana (chance = 1/n_ofertantes, V1).

## Pontos a conferir
1. **Unidade das medianas do Wagner (45,56 a 54): NÃO verificada.** Pode ser % da categoria, % do crédito ou outra base. Pendência.
2. **Se for %** (da categoria), a mediana de **45–54%** **excede** o embutido de **25%** (e o de 10%). Então `embutido_cobre_mediana` seria **falso** para os cinco do Top 5, e o insight **não se aplicaria** a eles: o cliente precisaria de recurso próprio. Ex. (suposição, mediana % da categoria): 3301 → lance 45,56% × 70.800 = 32.256,48; embutido máx. 25% × 70.800 = 17.700; recurso próprio mínimo ≈ 14.556,48. 3314 → 54% × 70.800 = 38.232; embutido 17.700; recurso ≈ 20.532.
3. **Se for fração** (0,4556) o resultado é o mesmo (45,56% ≫ 25%). Só se a unidade for outra (ex.: % de outra base, ou valor em R$ mil) a conclusão muda.
4. Em que grupos o insight vale (mediana <= teto de embutido) só se sabe com os dados reais da planilha mestra; **não verificado**.
5. Casca comercial: mesmo quando vale, o número sai embalado ("nas últimas assembleias o lance vencedor cabia no embutido"), nunca como percentual frio.
