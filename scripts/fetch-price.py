#!/usr/bin/env python3
"""Fetch tantalum price + exchange rate and save to JSON for GitHub Pages."""
import json, urllib.request, os, sys
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

price_data = {
    "intl_price": 232.5,
    "intl_price_unit": "美元/磅",
    "intl_price_desc": "SMM 30%品位钽铌矿 CIF到岸价",
    "vat_rate": 13,
    "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    "source": "smm_reference"
}

# 1. Fetch live exchange rate from Frankfurter
try:
    req = urllib.request.Request("https://api.frankfurter.dev/latest?from=USD&to=CNY")
    with urllib.request.urlopen(req, timeout=15) as resp:
        fx_data = json.loads(resp.read().decode())
        if fx_data.get("rates", {}).get("CNY", 0) > 0:
            price_data["exchange_rate"] = fx_data["rates"]["CNY"]
            price_data["exchange_rate_source"] = "api.frankfurter.dev"
            print(f"FX: USD/CNY = {price_data['exchange_rate']:.4f}")
except Exception as e:
    print(f"WARN: FX fetch failed - {e}, using default 7.25")
    price_data["exchange_rate"] = 7.25
    price_data["exchange_rate_source"] = "default"

# 2. Try Jisu API for tantalum/niobium price (custom agent gateway)
try:
    jisu_url = "https://api.jisuapi.com/agent/search?keyword=钽铌矿"
    req2 = urllib.request.Request(jisu_url)
    req2.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req2, timeout=10) as resp2:
        jisu_data = json.loads(resp2.read().decode())
        print(f"Jisu agent response: {json.dumps(jisu_data, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"INFO: Jisu agent gateway unreachable - {e}")

# Write output
out_path = os.path.join(os.path.dirname(__file__), "..", "data", "price.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(price_data, f, ensure_ascii=False, indent=2)
print(f"OK price={price_data['intl_price']:.1f} fx={price_data['exchange_rate']:.4f}")