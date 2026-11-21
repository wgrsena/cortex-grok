# Clone Sales Page - Two-Stage Tool

Ferramenta versionada para clonar páginas de vendas em dois estágios: Firecrawl (HTML com CSS inline) + Playwright (fontes, vídeos, imagens lazy-loaded, snapshot DOM e bundle offline).

## 🎯 Objetivo

Extrair e capturar páginas de vendas completas para **estudo local e reconstrução**. Não republique conteúdo de terceiros sem autorização.

## 📋 Pré-requisitos

- **Node.js** 18+ 
- **Firecrawl API Key** - Obtenha em [firecrawl.dev](https://firecrawl.dev)
- **Playwright Browsers** - Instalados via comando (veja abaixo)

## 🚀 Instalação

```bash
# Instalar dependências
cd tools/clone-sales-page
npm install

# Instalar navegadores do Playwright (necessário apenas uma vez)
npx playwright install chromium
```

## 🔧 Configuração

### Variável de Ambiente Obrigatória

```bash
export FIRECRAWL_API_KEY=fc-your-api-key-here
```

**⚠️ NUNCA commit chaves de API no repositório**. Use `.env` (já ignorado por `.gitignore`) ou variáveis de ambiente do sistema.

## 📖 Uso

### Comando Básico

```bash
FIRECRAWL_API_KEY=fc-xxx npm run clone -- <url> [output-dir]
```

### Exemplos

```bash
# Clone para ./output (padrão)
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://example.com/sales

# Clone para diretório específico
FIRECRAWL_API_KEY=fc-xxx npm run clone -- https://example.com/sales ./minha-saida

# Ou com tsx diretamente
FIRECRAWL_API_KEY=fc-xxx npx tsx index.ts https://example.com/sales
```

## 📂 Estrutura de Saída

```
output/
├── stage1-firecrawl/
│   ├── page.html           # HTML completo com CSS inline (Firecrawl)
│   ├── content.md          # Conteúdo em Markdown (se disponível)
│   └── metadata.json       # Metadados da página
└── stage2-playwright/
    ├── assets/             # Recursos baixados
    │   ├── image/         # Imagens
    │   ├── font/          # Fontes
    │   ├── stylesheet/    # CSS externos
    │   └── script/        # JavaScript
    ├── snapshot.html       # Snapshot DOM completo
    ├── screenshot.png      # Screenshot da página
    ├── offline-bundle.html # Bundle HTML com referências locais
    └── manifest.json       # Manifesto de recursos baixados
```

## 🔍 Estágios

### Stage 1: Firecrawl
- Extrai HTML completo com CSS inline
- Preserva estrutura e conteúdo
- Gera markdown do conteúdo
- Captura metadados

### Stage 2: Playwright
- Captura fontes externas
- Baixa vídeos e imagens lazy-loaded
- Cria snapshot DOM após carregamento completo
- Gera bundle offline navegável localmente

## 🧪 Teste Manual

Como não commitamos conteúdo de terceiros, teste localmente:

```bash
# 1. Configure a API key
export FIRECRAWL_API_KEY=sua-chave

# 2. Clone uma página de exemplo (use uma sua ou pública)
npm run clone -- https://example.com ./test-output

# 3. Verifique a saída
ls -la test-output/stage1-firecrawl/
ls -la test-output/stage2-playwright/

# 4. Abra o bundle offline no navegador
open test-output/stage2-playwright/offline-bundle.html

# 5. Limpe após o teste
rm -rf test-output/
```

## ⚖️ Aviso Legal

**IMPORTANTE**: Esta ferramenta é para **estudo local e reconstrução** apenas.

- ❌ **NÃO** republique páginas clonadas sem autorização
- ❌ **NÃO** use conteúdo de terceiros para fins comerciais sem permissão
- ❌ **NÃO** viole direitos autorais
- ✅ Use apenas para análise, aprendizado e referência local

Ao usar esta ferramenta, você concorda em respeitar os direitos autorais e termos de serviço dos sites que clonar.

## 🐛 Troubleshooting

### "FIRECRAWL_API_KEY environment variable is required"
Defina a variável de ambiente antes de executar:
```bash
export FIRECRAWL_API_KEY=fc-your-key
```

### "browserType.launch: Executable doesn't exist"
Instale os navegadores do Playwright:
```bash
npx playwright install chromium
```

### Recursos não foram baixados
Alguns recursos podem falhar por CORS, autenticação ou rate limiting. Verifique `manifest.json` para ver quais foram baixados.

## 📝 Versão

**v1.0.0** - Implementação inicial com Firecrawl + Playwright

## 🤝 Contribuindo

Este é um repositório privado do Cortex-Grok. Mudanças devem ser propostas via Pull Request e revisadas.

## 📄 Licença

MIT - Uso interno do Conecta Cortex
