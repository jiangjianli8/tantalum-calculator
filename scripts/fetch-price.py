#!/usr/bin/env python3
"""Fetch tantalum/niobium ore price from SMM AJAX API + live exchange rate.
   Called by: GitHub Actions (every 2 hours) or manually.
"""
import json, urllib.request, os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

end_date = now.strftime("%Y-%m-%d")
start_date = (now - timedelta(days=60)).strftime("%Y-%m-%d")

SMM_PRODUCT_ID = "202504100001"
SMM_API_URL = f"https://hq.smm.cn/ajax/spot/history/{SMM_PRODUCT_ID}/{start_date}/{end_date}"

price_data = {
    "intl_price": 232.5,
    "intl_price_unit": "美元/磅",
    "intl_price_desc": "SMM 30%品位钽铌矿 CIF到岸价(每日更新)",
    "vat_rate": 13,
    "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
    "source": "smm_reference",
}

# 1. Live exchange rate from open.er-api.com
try:
    req = urllib.request.Request(
        "https://open.er-api.com/v6/latest/USD",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        fx = json.loads(resp.read().decode())
        rate = fx.get("rates", {}).get("CNY", 0)
        if rate > 0:
            price_data["exchange_rate"] = round(rate, 4)
            price_data["exchange_rate_source"] = "open.er-api.com"
            print(f"FX: USD/CNY = {rate:.4f}")
except Exception as e:
    print(f"WARN: FX fetch failed - {e}")
    price_data["exchange_rate"] = 7.25
    price_data["exchange_rate_source"] = "default"

# 2. Tantalum price from SMM AJAX API (no login needed)
try:
    req = urllib.request.Request(
        SMM_API_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"https://hq.smm.cn/other-minor-metals/category/{SMM_PRODUCT_ID}",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        smm = json.loads(resp.read().decode())
        if smm.get("code") == 0 and smm.get("data"):
            latest = smm["data"][-1]
            avg = latest.get("average", 0)
            if avg > 0:
                price_data["intl_price"] = avg
                price_data["source"] = "smm_ajax"
                price_data["smm_renew_date"] = latest.get("renew_date", "")
                price_data["smm_high"] = latest.get("high_show", "")
                price_data["smm_low"] = latest.get("low_show", "")
                print(f"SMM Price: ${avg}/lb (updated: {latest.get('renew_date','')})")
        else:
            print(f"WARN: SMM API code={smm.get('code')}")
except Exception as e:
    print(f"WARN: SMM fetch failed - {e}")

out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "price.json"), "w", encoding="utf-8") as f:
    json.dump(price_data, f, ensure_ascii=False, indent=2)

print(f"OK price=${price_data['intl_price']:.1f}/lb fx={price_data.get('exchange_rate','N/A')}")
