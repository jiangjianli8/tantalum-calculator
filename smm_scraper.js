/**
 * SMM (Shanghai Metals Market) Tantalum-Niobium Price Scraper
 * Uses Playwright to login and extract prices.
 * Usage: node smm_scraper.js [--json]
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  username: '368732684@qq.com',
  password: 'jiang98558',
  priceUrls: [
    'https://hq.smm.cn/tantalum',
    'https://www.smm.cn/hq/tantalum',
    'https://hq.smm.cn/niobium',
  ],
  loginUrl: 'https://www.smm.cn/login',
  homeUrl: 'https://www.smm.cn/',
  cacheFile: path.join(__dirname, 'price_cache.json'),
  jsonOnly: process.argv.includes('--json'),
};

function log(msg) { if (!CONFIG.jsonOnly) console.log('[' + new Date().toLocaleTimeString() + '] ' + msg); }

async function scrapeSMM() {
  log('Launching browser...');
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const context = await browser.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport: { width: 1920, height: 1080 }, locale: 'zh-CN' });
  const page = await context.newPage();
  let priceData = null;

  try {
    log('Visiting SMM...');
    await page.goto(CONFIG.homeUrl, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    const loginBtn = await page.$('text=登录');
    if (loginBtn) {
      log('Login required...');
      await page.goto(CONFIG.loginUrl, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      try {
        const emailInput = await page.$('input[type="text"], input[placeholder*="邮"]');
        const passInput = await page.$('input[type="password"]');
        if (emailInput && passInput) {
          await emailInput.fill(CONFIG.username);
          await passInput.fill(CONFIG.password);
          await page.waitForTimeout(500);
          const submitBtn = await page.$('button[type="submit"], button:has-text("登录")');
          if (submitBtn) { await submitBtn.click(); log('Logging in...'); await page.waitForTimeout(5000); }
        }
      } catch (e) { log('Login error: ' + e.message); }
    }

    for (const url of CONFIG.priceUrls) {
      try {
        log('Trying: ' + url);
        await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
        await page.waitForTimeout(3000);
        const pageText = await page.evaluate(function() { return document.body.innerText; });

        var patterns = [
          /(\d+\.?\d*)\s*(美元|\$)\s*\/\s*(磅|lb)/g,
          /(\d+\.?\d*)\s*(元|￥)\s*\/\s*(磅|lb)/g,
          /\$\s*(\d+\.?\d*)\s*\/\s*lb/g,
        ];

        for (var i = 0; i < patterns.length; i++) {
          var m = patterns[i].exec(pageText);
          if (m) { log('Found price: ' + m[0]); priceData = { source: url, text: m[0], time: new Date().toISOString() }; break; }
          patterns[i].lastIndex = 0;
        }
        if (priceData) break;
      } catch (e) { log(url + ' failed: ' + e.message); }
    }

    if (!priceData) {
      var debugDir = path.join(__dirname, 'debug');
      if (!fs.existsSync(debugDir)) fs.mkdirSync(debugDir);
      await page.screenshot({ path: path.join(debugDir, 'smm_page.png'), fullPage: false });
      log('Debug screenshot saved.');
    }

  } catch (e) { log('Scrape error: ' + e.message); }
  finally { await browser.close(); log('Browser closed.'); }

  var result = { success: !!priceData, timestamp: new Date().toISOString(), defaultPrice: 232.5, data: priceData };
  fs.writeFileSync(CONFIG.cacheFile, JSON.stringify(result, null, 2), 'utf-8');
  if (CONFIG.jsonOnly) console.log(JSON.stringify(result));
  else { if (result.success) log('SUCCESS'); else log('Using default price 232.5 $/lb'); }
  return result;
}

scrapeSMM().catch(function(err) { console.error('Fatal:', err.message); process.exit(1); });
