#!/usr/bin/env python3
"""Fetch tantalum/niobium ore price + live exchange rate for GitHub Pages.
   Called by: GitHub Actions (every 2 hours) or manually.
   Price source: SMM reference $232.5/lb (updated via smm_scraper.js locally).
"""
import json, urllib.request, os, sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

# Default price data (overridden if smm_scraper.js found price)
price_data = {
    "intl_price": 232.5,
    "intl_price_unit": "美元/磅",
    "intl_price_desc": "SMM 30%品位钽铌矿 CIF到岸价",
    "vat_rate": 13,
    "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    "source": "smm_reference",
}

# 1. Fetch live exchange rate from open.er-api.com (free, no key)
try:
    req = urllib.request.Request(
        "https://open.er-api.com/v6/latest/USD",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        fx_data = json.loads(resp.read().decode())
        if fx_data.get("rates", {}).get("CNY", 0) > 0:
            price_data["exchange_rate"] = round(fx_data["rates"]["CNY"], 4)
            price_data["exchange_rate_source"] = "open.er-api.com"
            print(f"FX: USD/CNY = {price_data['exchange_rate']:.4f}")
except Exception as e:
    print(f"WARN: FX fetch failed - {e}")
    if "exchange_rate" not in price_data:
        price_data["exchange_rate"] = 7.25
        price_data["exchange_rate_source"] = "default"

# 2. Try to read any scraped price from smm_scraper.js output
scraper_file = os.path.join(os.path.dirname(__file__), "..", "price_cache.json")
if os.path.exists(scraper_file):
    try:
        with open(scraper_file, "r", encoding="utf-8") as f:
            scraped = json.load(f)
            if scraped.get("success") and scraped.get("data"):
                scraped_price = scraped["data"]
                if "intl_price" in scraped_price and scraped_price["intl_price"] > 0:
                    price_data["intl_price"] = scraped_price["intl_price"]
                    price_data["source"] = "smm_scraped"
                    price_data["source_url"] = scraped_price.get("source")
                    print(f"Price from scraper: ${price_data['intl_price']:.1f}/lb")
    except Exception as e:
        print(f"INFO: Could not read scraper cache - {e}")

# Write output
out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "price.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(price_data, f, ensure_ascii=False, indent=2)
    
print(f"OK price=${price_data['intl_price']:.1f}/lb fx={price_data.get('exchange_rate', 'N/A')}")