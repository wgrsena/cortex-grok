#!/usr/bin/env node

/**
 * Two-Stage Sales Page Cloner
 * Version: 1.0.0
 * 
 * Stage 1: Firecrawl - Extract HTML with inline CSS, structure, and content
 * Stage 2: Playwright - Capture fonts, videos, lazy-loaded images, DOM snapshot, offline bundle
 * 
 * Usage:
 *   FIRECRAWL_API_KEY=your_key tsx index.ts <url> [output-dir]
 * 
 * Environment Variables:
 *   FIRECRAWL_API_KEY - Required. Your Firecrawl API key
 * 
 * Legal Notice:
 *   This tool is for LOCAL STUDY AND REBUILD purposes only.
 *   Do not republish copyrighted third-party content without permission.
 *   Cloning is for analysis and learning, not redistribution.
 */

import * as fs from 'fs';
import * as path from 'path';
import { chromium, Browser, Page } from 'playwright';

interface FirecrawlResponse {
  success: boolean;
  data?: {
    html: string;
    markdown?: string;
    metadata?: Record<string, any>;
  };
  error?: string;
}

interface CloneResult {
  stage1: {
    success: boolean;
    htmlPath?: string;
    error?: string;
  };
  stage2: {
    success: boolean;
    assetsDir?: string;
    snapshotPath?: string;
    offlineBundlePath?: string;
    error?: string;
  };
}

class SalesPageCloner {
  private url: string;
  private outputDir: string;
  private firecrawlApiKey: string;

  constructor(url: string, outputDir: string = './output') {
    this.url = url;
    this.outputDir = path.resolve(outputDir);
    
    const apiKey = process.env.FIRECRAWL_API_KEY;
    if (!apiKey) {
      throw new Error('FIRECRAWL_API_KEY environment variable is required');
    }
    this.firecrawlApiKey = apiKey;
  }

  async clone(): Promise<CloneResult> {
    console.log('🚀 Starting two-stage sales page clone...');
    console.log(`📍 URL: ${this.url}`);
    console.log(`📁 Output: ${this.outputDir}\n`);

    // Create output directory
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    const result: CloneResult = {
      stage1: { success: false },
      stage2: { success: false }
    };

    // Stage 1: Firecrawl
    try {
      console.log('🔥 Stage 1: Firecrawl extraction...');
      result.stage1 = await this.stage1Firecrawl();
      if (result.stage1.success) {
        console.log(`✅ Stage 1 complete: ${result.stage1.htmlPath}\n`);
      }
    } catch (error) {
      result.stage1.error = error instanceof Error ? error.message : String(error);
      console.error(`❌ Stage 1 failed: ${result.stage1.error}\n`);
    }

    // Stage 2: Playwright
    try {
      console.log('🎭 Stage 2: Playwright capture...');
      result.stage2 = await this.stage2Playwright();
      if (result.stage2.success) {
        console.log(`✅ Stage 2 complete:`);
        console.log(`   Assets: ${result.stage2.assetsDir}`);
        console.log(`   Snapshot: ${result.stage2.snapshotPath}`);
        console.log(`   Offline bundle: ${result.stage2.offlineBundlePath}`);
      }
    } catch (error) {
      result.stage2.error = error instanceof Error ? error.message : String(error);
      console.error(`❌ Stage 2 failed: ${result.stage2.error}`);
    }

    return result;
  }

  /**
   * Stage 1: Use Firecrawl API to extract complete HTML with inline CSS
   */
  private async stage1Firecrawl(): Promise<{
    success: boolean;
    htmlPath?: string;
    error?: string;
  }> {
    const stage1Dir = path.join(this.outputDir, 'stage1-firecrawl');
    if (!fs.existsSync(stage1Dir)) {
      fs.mkdirSync(stage1Dir, { recursive: true });
    }

    try {
      // Call Firecrawl API using standard fetch
      const response = await fetch('https://api.firecrawl.dev/v1/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.firecrawlApiKey}`
        },
        body: JSON.stringify({
          url: this.url,
          formats: ['html', 'markdown'],
          onlyMainContent: false,
          includeTags: ['style', 'script', 'link'],
          waitFor: 2000
        })
      });

      if (!response.ok) {
        throw new Error(`Firecrawl API error: ${response.status} ${response.statusText}`);
      }

      const data: FirecrawlResponse = await response.json();
      
      if (!data.success || !data.data?.html) {
        throw new Error(data.error || 'No HTML content returned from Firecrawl');
      }

      // Save HTML
      const htmlPath = path.join(stage1Dir, 'page.html');
      fs.writeFileSync(htmlPath, data.data.html, 'utf-8');

      // Save markdown if available
      if (data.data.markdown) {
        const mdPath = path.join(stage1Dir, 'content.md');
        fs.writeFileSync(mdPath, data.data.markdown, 'utf-8');
      }

      // Save metadata
      if (data.data.metadata) {
        const metaPath = path.join(stage1Dir, 'metadata.json');
        fs.writeFileSync(metaPath, JSON.stringify(data.data.metadata, null, 2), 'utf-8');
      }

      return {
        success: true,
        htmlPath
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Stage 2: Use Playwright to capture what Firecrawl misses
   * - External fonts
   * - Videos
   * - Lazy-loaded images
   * - Full DOM snapshot
   * - Downloadable offline bundle
   */
  private async stage2Playwright(): Promise<{
    success: boolean;
    assetsDir?: string;
    snapshotPath?: string;
    offlineBundlePath?: string;
    error?: string;
  }> {
    const stage2Dir = path.join(this.outputDir, 'stage2-playwright');
    const assetsDir = path.join(stage2Dir, 'assets');
    
    if (!fs.existsSync(stage2Dir)) {
      fs.mkdirSync(stage2Dir, { recursive: true });
    }
    if (!fs.existsSync(assetsDir)) {
      fs.mkdirSync(assetsDir, { recursive: true });
    }

    let browser: Browser | null = null;

    try {
      // Launch browser
      browser = await chromium.launch({ headless: true });
      const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      });
      const page = await context.newPage();

      // Track downloaded resources
      const downloadedResources: string[] = [];

      // Intercept and save resources
      await page.route('**/*', async (route) => {
        const request = route.request();
        const resourceType = request.resourceType();
        
        // Continue the request normally
        await route.continue();

        // Track important resources
        if (['font', 'image', 'media'].includes(resourceType)) {
          downloadedResources.push(request.url());
        }
      });

      // Navigate and wait for everything to load
      console.log('   Loading page...');
      await page.goto(this.url, { 
        waitUntil: 'networkidle',
        timeout: 60000 
      });

      // Scroll to trigger lazy loading
      console.log('   Triggering lazy loading...');
      await this.scrollPage(page);

      // Wait for any dynamic content
      await page.waitForTimeout(3000);

      // Take full-page screenshot
      console.log('   Capturing screenshot...');
      const screenshotPath = path.join(stage2Dir, 'screenshot.png');
      await page.screenshot({ 
        path: screenshotPath, 
        fullPage: true 
      });

      // Get complete DOM HTML
      console.log('   Extracting DOM snapshot...');
      const html = await page.content();
      const snapshotPath = path.join(stage2Dir, 'snapshot.html');
      fs.writeFileSync(snapshotPath, html, 'utf-8');

      // Download all resources for offline bundle
      console.log('   Downloading resources...');
      const resourcesInfo = await this.downloadResources(page, assetsDir);

      // Create offline bundle with resource references updated
      console.log('   Creating offline bundle...');
      const offlineBundlePath = await this.createOfflineBundle(
        html, 
        stage2Dir, 
        resourcesInfo
      );

      // Save resource manifest
      const manifestPath = path.join(stage2Dir, 'manifest.json');
      fs.writeFileSync(manifestPath, JSON.stringify({
        url: this.url,
        timestamp: new Date().toISOString(),
        resources: downloadedResources,
        downloadedFiles: resourcesInfo
      }, null, 2), 'utf-8');

      await browser.close();

      return {
        success: true,
        assetsDir,
        snapshotPath,
        offlineBundlePath
      };
    } catch (error) {
      if (browser) {
        await browser.close();
      }
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Scroll page to trigger lazy loading
   */
  private async scrollPage(page: Page): Promise<void> {
    await page.evaluate(async () => {
      const distance = 100;
      const delay = 100;
      
      while (window.scrollY + window.innerHeight < document.body.scrollHeight) {
        window.scrollBy(0, distance);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      // Scroll back to top
      window.scrollTo(0, 0);
    });
  }

  /**
   * Download all page resources (images, fonts, CSS, JS)
   */
  private async downloadResources(page: Page, assetsDir: string): Promise<Record<string, string>> {
    const resourceMap: Record<string, string> = {};

    // Get all images
    const images = await page.$$eval('img', imgs => 
      imgs.map(img => ({
        src: img.src,
        alt: img.alt || ''
      }))
    );

    // Get all stylesheets
    const stylesheets = await page.$$eval('link[rel="stylesheet"]', links =>
      links.map(link => (link as HTMLLinkElement).href)
    );

    // Get all scripts
    const scripts = await page.$$eval('script[src]', scripts =>
      scripts.map(script => (script as HTMLScriptElement).src)
    );

    // Get font URLs from CSS
    const fonts = await page.evaluate(() => {
      const fontUrls: string[] = [];
      for (const sheet of Array.from(document.styleSheets)) {
        try {
          for (const rule of Array.from(sheet.cssRules)) {
            if (rule instanceof CSSFontFaceRule) {
              const src = rule.style.getPropertyValue('src');
              const urlMatches = src.match(/url\(['"]?([^'"]+)['"]?\)/g);
              if (urlMatches) {
                urlMatches.forEach(match => {
                  const url = match.match(/url\(['"]?([^'"]+)['"]?\)/)?.[1];
                  if (url) fontUrls.push(url);
                });
              }
            }
          }
        } catch (e) {
          // Cross-origin stylesheet, skip
        }
      }
      return fontUrls;
    });

    // Download each resource type
    const allResources = [
      ...images.map(img => ({ url: img.src, type: 'image' })),
      ...stylesheets.map(href => ({ url: href, type: 'stylesheet' })),
      ...scripts.map(src => ({ url: src, type: 'script' })),
      ...fonts.map(url => ({ url, type: 'font' }))
    ];

    for (const resource of allResources) {
      try {
        const url = new URL(resource.url);
        const fileName = this.sanitizeFileName(path.basename(url.pathname) || 'resource');
        const typeDir = path.join(assetsDir, resource.type);
        
        if (!fs.existsSync(typeDir)) {
          fs.mkdirSync(typeDir, { recursive: true });
        }

        const filePath = path.join(typeDir, fileName);
        
        // Use page.request to fetch (respects cookies, auth, etc.)
        const response = await page.request.fetch(resource.url);
        if (response.ok()) {
          const buffer = await response.body();
          fs.writeFileSync(filePath, buffer);
          resourceMap[resource.url] = path.relative(
            path.dirname(filePath), 
            filePath
          );
        }
      } catch (error) {
        // Resource download failed, continue with others
        console.warn(`   Failed to download: ${resource.url}`);
      }
    }

    return resourceMap;
  }

  /**
   * Create an offline HTML bundle with local resource references
   */
  private async createOfflineBundle(
    html: string,
    outputDir: string,
    resourceMap: Record<string, string>
  ): Promise<string> {
    let bundleHtml = html;

    // Replace resource URLs with local paths
    for (const [originalUrl, localPath] of Object.entries(resourceMap)) {
      const escapedUrl = originalUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      bundleHtml = bundleHtml.replace(
        new RegExp(escapedUrl, 'g'),
        localPath
      );
    }

    const bundlePath = path.join(outputDir, 'offline-bundle.html');
    fs.writeFileSync(bundlePath, bundleHtml, 'utf-8');

    return bundlePath;
  }

  /**
   * Sanitize filename for safe filesystem use
   */
  private sanitizeFileName(fileName: string): string {
    return fileName
      .replace(/[^a-zA-Z0-9._-]/g, '_')
      .substring(0, 255);
  }
}

// CLI Entry Point
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.log(`
Two-Stage Sales Page Cloner v1.0.0

Usage:
  FIRECRAWL_API_KEY=your_key tsx index.ts <url> [output-dir]

Arguments:
  url         - The URL of the sales page to clone (required)
  output-dir  - Output directory (default: ./output)

Environment Variables:
  FIRECRAWL_API_KEY - Your Firecrawl API key (required)

Example:
  FIRECRAWL_API_KEY=fc-xxx tsx index.ts https://example.com/sales ./my-output

Legal Notice:
  This tool is for LOCAL STUDY AND REBUILD purposes only.
  Do not republish copyrighted third-party content without permission.
    `);
    process.exit(0);
  }

  const url = args[0];
  const outputDir = args[1] || './output';

  try {
    const cloner = new SalesPageCloner(url, outputDir);
    const result = await cloner.clone();

    console.log('\n' + '='.repeat(60));
    console.log('📊 Clone Summary:');
    console.log('='.repeat(60));
    console.log(`Stage 1 (Firecrawl): ${result.stage1.success ? '✅ Success' : '❌ Failed'}`);
    if (result.stage1.error) {
      console.log(`  Error: ${result.stage1.error}`);
    }
    console.log(`Stage 2 (Playwright): ${result.stage2.success ? '✅ Success' : '❌ Failed'}`);
    if (result.stage2.error) {
      console.log(`  Error: ${result.stage2.error}`);
    }
    console.log('='.repeat(60));

    if (!result.stage1.success && !result.stage2.success) {
      process.exit(1);
    }
  } catch (error) {
    console.error('\n❌ Fatal error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

export { SalesPageCloner };
