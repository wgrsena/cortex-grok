---
name: clone-sales-page
description: >-
  Use quando precisar clonar uma página de vendas completa para estudo local e 
  reconstrução. Extrai HTML, CSS, fontes, imagens, vídeos e gera bundle offline 
  navegável. Duas etapas: Firecrawl (estrutura) + Playwright (recursos dinâmicos).
---
# Clone Sales Page - Clonar Página de Vendas

## Quando usar
- Estudar estrutura e design de páginas de vendas (VSLs, landing pages, etc.)
- Reconstruir páginas de referência localmente
- Analisar recursos (fontes, imagens, vídeos) de uma sales page
- Criar backup offline de páginas próprias
- Desenvolver páginas similares com base em exemplos

## ⚠️ NÃO use para
- Republicar conteúdo de terceiros sem autorização
- Copiar páginas protegidas por direitos autorais para uso comercial
- Violar termos de serviço de sites
- Qualquer uso que viole propriedade intelectual alheia

## Fluxo de duas etapas

### Stage 1: Firecrawl
**O que faz:**
- Extrai HTML completo com CSS inline
- Preserva estrutura semântica e conteúdo
- Gera markdown do texto principal
- Captura metadados (título, descrição, OG tags)

**Saída:**
- `stage1-firecrawl/page.html` - HTML com estilos inline
- `stage1-firecrawl/content.md` - Conteúdo em markdown
- `stage1-firecrawl/metadata.json` - Metadados estruturados

### Stage 2: Playwright
**O que faz:**
- Renderiza página em navegador real (Chromium)
- Baixa fontes externas (Google Fonts, custom fonts)
- Captura vídeos e imagens lazy-loaded
- Faz scroll automático para disparar lazy loading
- Cria snapshot DOM completo após carregamento
- Gera bundle HTML offline com referências locais

**Saída:**
- `stage2-playwright/assets/` - Recursos organizados por tipo
  - `image/` - Todas as imagens
  - `font/` - Fontes externas
  - `stylesheet/` - CSS externos
  - `script/` - JavaScript
- `stage2-playwright/snapshot.html` - DOM completo
- `stage2-playwright/screenshot.png` - Screenshot full-page
- `stage2-playwright/offline-bundle.html` - Bundle navegável localmente
- `stage2-playwright/manifest.json` - Lista de recursos baixados

## Pré-requisitos

### 1. Instalar dependências
```bash
cd tools/clone-sales-page
npm install
```

### 2. Instalar navegadores Playwright (uma vez)
```bash
npx playwright install chromium
```

### 3. Configurar API Key (obrigatório)
```bash
export FIRECRAWL_API_KEY=fc-sua-chave-aqui
```

⚠️ **NUNCA commit a API key**. Use variável de ambiente ou `.env` local.

Como obter: [firecrawl.dev](https://firecrawl.dev) → Sign up → API Keys

## Como executar

### Sintaxe
```bash
FIRECRAWL_API_KEY=fc-xxx npm run clone -- <url> [diretorio-saida]
```

### Exemplos
```bash
# Clone para ./output (padrão)
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://example.com/vsl

# Clone para diretório específico
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://example.com/vsl ./analise-concorrente

# Usando tsx diretamente
FIRECRAWL_API_KEY=fc-xxx npx tsx index.ts https://example.com/vsl
```

## Contrato de entrada/saída

### Entrada
- **URL** (obrigatório): URL completa da página a clonar
- **Output dir** (opcional): Diretório de saída (default: `./output`)
- **FIRECRAWL_API_KEY** (obrigatório): Variável de ambiente

### Saída
Estrutura de diretórios:
```
[output-dir]/
├── stage1-firecrawl/
│   ├── page.html
│   ├── content.md
│   └── metadata.json
└── stage2-playwright/
    ├── assets/
    │   ├── image/
    │   ├── font/
    │   ├── stylesheet/
    │   └── script/
    ├── snapshot.html
    ├── screenshot.png
    ├── offline-bundle.html
    └── manifest.json
```

### Códigos de saída
- `0` - Sucesso (pelo menos um estágio completou)
- `1` - Falha (ambos os estágios falharam ou erro fatal)

## Troubleshooting

### ❌ "FIRECRAWL_API_KEY environment variable is required"
**Causa**: Variável de ambiente não definida  
**Solução**: 
```bash
export FIRECRAWL_API_KEY=fc-sua-chave
```

### ❌ "browserType.launch: Executable doesn't exist"
**Causa**: Navegadores Playwright não instalados  
**Solução**:
```bash
npx playwright install chromium
```

### ❌ "Firecrawl API error: 401"
**Causa**: API key inválida ou expirada  
**Solução**: Verifique a chave em [firecrawl.dev/dashboard](https://firecrawl.dev/dashboard)

### ❌ "Firecrawl API error: 429"
**Causa**: Rate limit excedido  
**Solução**: Aguarde ou upgrade do plano Firecrawl

### ⚠️ Alguns recursos não foram baixados
**Causa**: CORS, autenticação, rate limiting  
**Solução**: Normal para alguns sites. Verifique `manifest.json` para lista de recursos baixados.

## Casos de uso recomendados

### 1. Análise de concorrente
```bash
# Clone VSL do concorrente para análise local
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://concorrente.com/vsl ./analise-concorrente
# Estude: estrutura, copy, elementos visuais, funil
```

### 2. Backup de página própria
```bash
# Backup antes de mudanças
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://meuproduto.com/vsl ./backup-$(date +%Y%m%d)
```

### 3. Desenvolvimento baseado em referência
```bash
# Clone referência, estude offline, desenvolva similar
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://referencia.com/sales ./ref-desenvolvimento
# Use como guia visual, não copie código diretamente
```

## Avisos legais e éticos

### ✅ Uso permitido (local, estudo, reconstrução)
- Análise de estrutura e design
- Estudo de copy e elementos persuasivos
- Referência para desenvolver página própria
- Backup de páginas próprias

### ❌ Uso proibido
- Republicar páginas clonadas sem autorização
- Hospedar cópias de páginas de terceiros
- Uso comercial de conteúdo alheio sem licença
- Violação de direitos autorais ou marcas registradas

### 🧑‍⚖️ Disclaimer
Esta skill é para **estudo e desenvolvimento local apenas**. Você é responsável por:
- Respeitar direitos autorais
- Cumprir termos de serviço dos sites
- Não republicar conteúdo sem autorização
- Usar o conteúdo clonado de forma ética e legal

## Limitações conhecidas

1. **Recursos protegidos**: Alguns sites bloqueiam scraping via Cloudflare, captcha, etc.
2. **Conteúdo dinâmico complexo**: SPAs com estado complexo podem não capturar tudo
3. **Vídeos hospedados**: Vídeos de plataformas externas (YouTube, Vimeo) podem não ser baixados
4. **Rate limits**: Firecrawl tem limites de requisições por minuto/dia
5. **Tamanho**: Páginas muito grandes podem exceder timeouts

## Versão
**v1.0.0** - Implementação inicial (Nov 2026)

## Manutenção
- Localização: `tools/clone-sales-page/`
- Dependências: Playwright 1.48.2, tsx 4.19.2
- Linguagem: TypeScript/Node.js
- Atualização de navegadores: `npx playwright install chromium`

## Ver também
- [Firecrawl Docs](https://docs.firecrawl.dev)
- [Playwright Docs](https://playwright.dev)
- README: `tools/clone-sales-page/README.md`
