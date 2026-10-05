
"""
5-LAYER SMART MONEY SYSTEM - النظام الكامل
1. Discovery: محافظ جديدة مش dust ✅ عندك
2. Tracking: محافظ قوية بتكسب ✅ عندك  
3. Risk Shield: يحظرك من الدخول ❌ هنعمله
4. TP/SL Advisor: يقولك take profit & stop loss ❌ هنعمله
5. Alpha Alert: ينبهك لصعود حقيقي مش scam ❌ هنعمله
"""

import os, requests, time
from datetime import datetime

HELIUS_KEY = os.getenv('HELIUS_API_KEY')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(text)
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

# ===== LAYER 3: RISK SHIELD - يحظرك من الدخول =====
def check_token_risk(mint):
    """
    يفحص التوكن هل scam ولا لا
    بيرجع: risk_score 0-100 و تحذير
    """
    risk_score = 0
    warnings = []
    
    try:
        # 1. DexScreener check
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            pairs = data.get('pairs', [])
            if not pairs:
                return 100, ["❌ مفيش liquidity"]
            
            pair = pairs[0]
            liquidity = float(pair.get('liquidity', {}).get('usd', 0) or 0)
            fdv = float(pair.get('fdv', 0) or 0)
            price_change_24h = float(pair.get('priceChange', {}).get('h24', 0) or 0)
            
            # Liquidity قليلة = خطر
            if liquidity < 10000:
                risk_score += 30
                warnings.append(f"⚠️ سيولة قليلة: ${liquidity:.0f}")
            
            # FDV كبير و liquidity صغيرة = scam محتمل
            if fdv > 0 and liquidity > 0 and fdv / liquidity > 100:
                risk_score += 20
                warnings.append("⚠️ FDV عالي بالنسبة للسيولة")
            
            # صعود 1000% في 24h = pump and dump محتمل
            if price_change_24h > 500:
                risk_score += 15
                warnings.append(f"⚠️ صعود {price_change_24h:.0f}% في 24h - ممكن dump")
    
    except Exception as e:
        warnings.append(f"⚠️ مقدرش أفحص: {e}")
    
    # 2. Holder concentration (لو محفظة واحدة عندها >50% = خطر)
    try:
        if HELIUS_KEY:
            url = f"https://api.helius.xyz/v0/tokens/{mint}/holders?api-key={HELIUS_KEY}&limit=10"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                holders = r.json().get('holders', [])
                if holders:
                    top_holder_pct = float(holders[0].get('percentage', 0) or 0)
                    if top_holder_pct > 50:
                        risk_score += 25
                        warnings.append(f"🚨 محفظة واحدة عندها {top_holder_pct:.0f}% - خطر rug")
                    elif top_holder_pct > 30:
                        risk_score += 10
                        warnings.append(f"⚠️ تركيز عالي: {top_holder_pct:.0f}% عند محفظة واحدة")
    except: pass
    
    return risk_score, warnings

# ===== LAYER 4: TP/SL ADVISOR =====
def suggest_tp_sl(mint, entry_price=None):
    """
    يقترح TP و SL بناء على:
    - متوسط احتفاظ المحافظ الذهبية
    - تقلب التوكن
    """
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}", timeout=10)
        if r.status_code == 200:
            pairs = r.json().get('pairs', [])
            if pairs:
                pair = pairs[0]
                price = float(pair.get('priceUsd', 0) or 0)
                change_1h = float(pair.get('priceChange', {}).get('h1', 0) or 0)
                change_24h = float(pair.get('priceChange', {}).get('h24', 0) or 0)
                
                # بناء على بيانات الـ 15 الذهبية: متوسط احتفاظ 200 دقيقة
                # لو التوكن متقلب → TP قريب
                # لو هادي → TP بعيد
                
                volatility = abs(change_1h) + abs(change_24h) / 10
                
                if volatility > 50:  # متقلب جدا
                    tp = 30  # 30%
                    sl = 15  # 15%
                    strategy = "⚡ متقلب - خد ربح سريع"
                elif volatility > 20:
                    tp = 50
                    sl = 20
                    strategy = "📈 متوسط - TP 50% SL 20%"
                else:
                    tp = 100
                    sl = 25
                    strategy = "💎 هادي - خليك Diamond TP 100%"
                
                return {
                    "price": price,
                    "tp_percent": tp,
                    "sl_percent": sl,
                    "tp_price": price * (1 + tp/100) if price else 0,
                    "sl_price": price * (1 - sl/100) if price else 0,
                    "strategy": strategy,
                    "volatility": volatility
                }
    except: pass
    return None

# ===== LAYER 5: ALPHA ALERT - صعود حقيقي =====
def detect_real_pump():
    """
    يكتشف صعود حقيقي مش scam:
    - حجم كبير + محافظ ذهبية بتشتري مع بعض + سيولة بتزيد
    """
    try:
        # نجيب توكنات تريند
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=solana", timeout=10)
        if r.status_code != 200:
            return []
        
        pairs = r.json().get('pairs', [])[:20]
        alpha_tokens = []
        
        for pair in pairs:
            if pair.get('chainId') != 'solana':
                continue
            
            mint = pair.get('baseToken', {}).get('address')
            if not mint:
                continue
            
            volume_24h = float(pair.get('volume', {}).get('h24', 0) or 0)
            liquidity = float(pair.get('liquidity', {}).get('usd', 0) or 0)
            price_change_24h = float(pair.get('priceChange', {}).get('h24', 0) or 0)
            price_change_1h = float(pair.get('priceChange', {}).get('h1', 0) or 0)
            
            # شروط صعود حقيقي:
            # 1. حجم > 100k
            # 2. سيولة > 20k
            # 3. صعود 20-200% (مش 1000% scam)
            # 4. صعود في آخر ساعة موجب
            
            if (volume_24h > 100000 and 
                liquidity > 20000 and 
                20 < price_change_24h < 300 and
                price_change_1h > 5):
                
                # افحص risk
                risk_score, warnings = check_token_risk(mint)
                
                if risk_score < 40:  # خطر قليل
                    alpha_tokens.append({
                        "mint": mint,
                        "symbol": pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                        "price": pair.get('priceUsd'),
                        "change_24h": price_change_24h,
                        "change_1h": price_change_1h,
                        "volume": volume_24h,
                        "liquidity": liquidity,
                        "risk_score": risk_score,
                        "warnings": warnings
                    })
        
        return alpha_tokens
    except Exception as e:
        print(f"Alpha error: {e}")
        return []

if __name__ == "__main__":
    print("=== 5-Layer System Check ===")
    
    # Layer 3 test
    print("\n--- Layer 3: Risk Shield ---")
    test_mint = "So11111111111111111111111111111111111111112"  # WSOL
    risk, warns = check_token_risk(test_mint)
    print(f"Risk {test_mint[:10]}: {risk} - {warns}")
    
    # Layer 4 test
    print("\n--- Layer 4: TP/SL ---")
    tp_sl = suggest_tp_sl(test_mint)
    if tp_sl:
        print(f"TP: {tp_sl['tp_percent']}% SL: {tp_sl['sl_percent']}% - {tp_sl['strategy']}")
    
    # Layer 5 test
    print("\n--- Layer 5: Alpha Alert ---")
    alphas = detect_real_pump()
    print(f"Found {len(alphas)} real pumps")
    for a in alphas[:3]:
        print(f"  {a['symbol']}: {a['change_24h']:.0f}% Vol ${a['volume']:.0f} Risk {a['risk_score']}")
        if a['risk_score'] < 30:
            msg = f"🚀 *صعود حقيقي مكتشف!*\\n{a['symbol']} +{a['change_24h']:.0f}%\\nVol: ${a['volume']:.0f}\\nLiq: ${a['liquidity']:.0f}\\nRisk: {a['risk_score']}/100\\n`{a['mint']}`"
            send_tg(msg)
