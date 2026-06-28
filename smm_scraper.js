/**
 * SMM (Shanghai Metals Market) Price Scraper - Optimized v2
 * Logs into SMM, searches for tantalum/niobium ore prices.
 * Usage: node smm_scraper.js [--json]
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  username: '368732684@qq.com',
  password: 'jiang98558',
  jsonOnly: process.argv.includes('--json'),
  dataFile: path.join(__dirname, 'data', 'price.json'),
};

function log(msg) {
  if (!CONFIG.jsonOnly) console.log('[' + new Date().toLocaleTimeString() + '] ' + msg);
}

function savePrice(priceData) {
  const base = {
    intl_price: 232.5,
    intl_price_unit: "美元/磅",
    intl_price_desc: "SMM 30%品位钽铌矿 CIF到岸价",
    vat_rate: 13,
    source: "smm_reference"
  };
  const merged = Object.assign({}, base, priceData);
  
  const dir = path.dirname(CONFIG.dataFile);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(CONFIG.dataFile, JSON.stringify(merged, null, 2), 'utf-8');
  log('Saved: ' + CONFIG.dataFile);
  return merged;
}

async function loginToSMM(page) {
  log('Attempting SMM login...');
  
  // SMM uses popup login dialog on homepage
  await page.goto('https://www.smm.cn/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  
  // Click login button to trigger popup
  const loginSelectors = [
    'text=登录',
    'a:has-text("登录")',
    '.login-btn',
    'span:has-text("登录")',
  ];
  
  let clicked = false;
  for (const sel of loginSelectors) {
    const btn = await page.$(sel);
    if (btn) {
      log('Clicking login: ' + sel);
      await btn.click();
      await page.waitForTimeout(2000);
      clicked = true;
      break;
    }
  }
  
  if (!clicked) {
    log('No login button found, trying login page URLs...');
    const loginUrls = [
      'https://www.smm.cn/member/login',
      'https://passport.smm.cn/login',
    ];
    for (const url of loginUrls) {
      try {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
        const text = await page.evaluate(function() { return document.body.innerText; });
        if (text.includes('登录') && text.includes('密码')) {
          log('Found login page: ' + url);
          clicked = true;
          break;
        }
      } catch(e) {}
    }
  }
  
  if (!clicked) {
    log('Could not find login form - continuing without login');
    return false;
  }
  
  await page.waitForTimeout(1000);
  
  // Handle login in main frame or iframe
  async function fillLogin(frame) {
    const emailSelectors = [
      'input[type="text"]',
      'input[placeholder*="手机"]',
      'input[placeholder*="邮"]',
      'input[placeholder*="账号"]',
      'input[name*="user"]',
      'input[name*="email"]',
      'input[name*="account"]',
    ];
    let emailInput = null;
    for (const s of emailSelectors) {
      emailInput = await frame.$(s);
      if (emailInput) break;
    }
    const passInput = await frame.$('input[type="password"]');
    return emailInput && passInput;
  }
  
  let emailInput = null;
  let passInput = null;
  
  // Try main frame first
  const mainHasForm = await fillLogin(page);
  if (mainHasForm) {
    emailInput = await page.$('input[type="text"], input:not([type="password"])');
    passInput = await page.$('input[type="password"]');
  } else {
    // Try iframes
    const frames = page.frames();
    for (const frame of frames) {
      const hasForm = await fillLogin(frame);
      if (hasForm) {
        log('Found login form in iframe');
        emailInput = await frame.$('input[type="text"], input:not([type="password"])');
        passInput = await frame.$('input[type="password"]');
        break;
      }
    }
  }
  
  if (emailInput && passInput) {
    await emailInput.fill(CONFIG.username);
    await passInput.fill(CONFIG.password);
    await page.waitForTimeout(500);
    
    const submitBtn = await page.$('button[type="submit"], button:has-text("登录"), input[type="submit"]');
    if (submitBtn) {
      await submitBtn.click();
      log('Submitted login, waiting...');
      await page.waitForTimeout(5000);
      return true;
    }
  }
  
  log('Login form fields not found');
  return false;
}

async function searchPrice(page) {
  log('Searching for tantalum/niobium prices...');
  
  const searchUrls = [
    'https://www.smm.cn/search?keyword=%E9%92%BD%E9%93%8C',
    'https://hq.smm.cn/search?keyword=%E9%92%BD',
    'https://hq.smm.cn/search?keyword=%E9%93%8C',
  ];
  
  for (const url of searchUrls) {
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });
      await page.waitForTimeout(3000);
      
      const pageText = await page.evaluate(function() { return document.body.innerText; });
      
      // Find price patterns
      const priceMatch = pageText.match(/\$?\s*(\d{2,4}(?:\.\d{1,2})?)\s*(?:美元|\$)?\s*\/\s*(?:磅|lb)/gi);
      if (priceMatch) {
        log('Price found: ' + JSON.stringify(priceMatch));
        const numMatch = pageText.match(/\$?\s*(\d{2,4}(?:\.\d{1,2})?)\s*(?:美元|\$)?\s*\/\s*(?:磅|lb)/i);
        if (numMatch) {
          const price = parseFloat(numMatch[1] || numMatch[0].replace(/[^\\d.]/g, ''));
          if (price > 0) {
            return { intl_price: price, source: url };
          }
        }
      }
      
      // Look for SMM price table data
      if (pageText.includes('钽铌') || pageText.includes('Tantalum') || pageText.includes('Niobium')) {
        log('Tantalum/niobium content found on page');
        // Try to find structured data
        const rows = await page.evaluate(function() {
          const cells = document.querySelectorAll('td, .price-value, .value');
          return Array.from(cells).map(function(c) { return c.textContent; }).join('|');
        });
        log('Table data: ' + rows.substring(0, 300));
      }
    } catch(e) {
      log(url + ': ' + e.message);
    }
  }
  
  return null;
}

async function main() {
  log('=== SMM Tantalum/Niobium Price Scraper ===');
  
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 },
    locale: 'zh-CN',
  });
  
  const page = await context.newPage();
  let scrapedPrice = null;
  
  try {
    await loginToSMM(page);
    scrapedPrice = await searchPrice(page);
    
    if (!scrapedPrice) {
      log('No tantalum/niobium price found on SMM');
      const debugDir = path.join(__dirname, 'debug');
      if (!fs.existsSync(debugDir)) fs.mkdirSync(debugDir, { recursive: true });
      await page.screenshot({ path: path.join(debugDir, 'smm_result.png'), fullPage: false });
      log('Debug screenshot saved');
    }
  } catch(e) {
    log('Error: ' + e.message);
  } finally {
    await browser.close();
  }
  
  const now = new Date();
  const cstTime = new Date(now.getTime() + 8*60*60*1000).toISOString().replace('T',' ').substring(0,19);
  
  const finalData = savePrice({
    updated_at: cstTime,
    exchange_rate_source: 'open.er-api.com',
    source: scrapedPrice ? 'smm_scraped' : 'smm_reference',
    source_url: scrapedPrice ? scrapedPrice.source : undefined,
  });
  
  if (scrapedPrice && scrapedPrice.intl_price) {
    finalData.intl_price = scrapedPrice.intl_price;
  }
  
  if (CONFIG.jsonOnly) {
    console.log(JSON.stringify(finalData));
  } else {
    log('Done. Price: $' + finalData.intl_price + '/lb');
  }
  
  return finalData;
}

main().catch(function(err) {
  console.error('Fatal:', err.message);
  process.exit(1);
});