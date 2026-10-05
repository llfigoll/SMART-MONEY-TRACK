PRO MAX SMART MONEY TRACKER - نظام فلترة احترافي 3 طبقات
- بشر فقط (مش بوتات)
- توكن مش scam
- عنقود ذهبي
Built from RugCheck.xyz + DexScreener + Helius research
"""

import os, requests, time, json
from datetime import datetime
from collections import defaultdict

HELIUS_KEY = os.getenv('HELIUS_API_KEY')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# المحافظ الذهبية المفلترة (15 محفظة بشر حقيقي من 173 محفظة)
GOLDEN_WALLETS = [
    "2T5NgDDidkvhJQg8AHDi74uCFwgp25pYFMRZXBaCUNBH", # LEHR_1 - 20min holder - 1669 SOL
    "4oYjvNib7RrKTqMSyDYU5rXAeSV955FVad9B2y4gNFXa", # LEHR_2 - DIAMOND 3047min (50h) - 17 cycles
    "57f2jG9eveivqdSvcaaKFCSW5YDECam29xwRf2gBmqVT", # LEHR_3 - 16min
    "6NktQqEjNr6mJnsr96sg7d8iYhkxthWGN2pzRWqvbCr", # LEHR_4 - 186min - 27 cycles
    "C3XZgqcU1U5TLTk3kYUUeoRim8bpnqwGcV9ZVMN6YWbz", # LEHR_5 - 63 cycles ACTIVE
    "6S71WKwp5YtwBuoMv5ra3cx24umAz86qxRJmPANbJvKy", # LEHR_6 - DIAMOND 409min
    "BXbByWHgUeapK52LwPBH6HCDBquRmBY4ms23cLELP5Ng", # LEHR_7 - 37 cycles
    "96Vpi8sxTwxT7vX9mwbcZf8qjqfuVbBSPbghxxfFCqa1", # LEHR_8
    "FzttT8tzXicSQZW9nxQTwTrfhtwgFvMiA8BvXogdWDbv", # LEHR_9 - 21 cycles
    "9d1pZHbTJzTR9oQF2rPx3Ssy5WiTD3nz2rp5PNeynf6h", # LEHR_10 - DIAMOND 305min
    "GCpKsqPx6akPVqMRqCSvTmPx4Si6agZgEAxsS8xiPf1j", # LEHR_11 - DIAMOND 820min (13h)
    "SKRWBceZen2XrHvMBFzkhPxSDZm8kCQRLxtwu4asMZ3", # LEHR_12
    "4sSxgbSBhFrArbGyacm3tcrDTxbBXdFTrPJ5vCA8ZqFG", # LEHR_13
    "3kckXQKfcByrP5whYLaakVEjA2YDyVy7KPhMt2GWZSYi", # LEHR_14
    "AoMS3Mgky8DPXyZQpmzzGfnLdVEVytsFsw735eJJz2Nk", # LEHR_15 - DIAMOND 4299min (71h) - أقوى واحد
]

# ذاكرة مؤقتة للعنقود الذهبي - لو 2 محافظ اشتروا نفس التوكن في ساعة
RECENT_BUYS = defaultdict(list) # mint -> [(wallet, timestamp, amount)]

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(text)
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID, 
            "text": text, 
            "parse_mode": "Markdown", 
            "disable_web_page_preview": True
        }, timeout=10)
    except Exception as e:
        print(f"TG error: {e}")

# ===== الطبقة 1: فلتر البشر - هل المحفظة دي بشر ولا بوت؟ =====
def is_human_wallet(wallet, quick_check=True):
    """
    من V8_BOT_DETECTOR + تطوير:
    البوت بيتعرف من 4 حاجات:
    1. Dust: بيشتري 1-10 توكن كتير (40 نقطة)
    2. سرعة: بين كل شراء أقل من 2 دقيقة (30 نقطة)
    3. كميات صغيرة كتير (20 نقطة)
    4. بيشتري توكنات كتير مختلفة بسرعة (10 نقاط)
    لو جمع 50+ = بوت
    
    للذهبية: احنا عارفين انهم بشر (bot_score 0-10) ف بنعمل quick_check
    """
    if quick_check and wallet in GOLDEN_WALLETS:
        return True, 0, "ذهبية مؤكدة بشر"
    
    if not HELIUS_KEY:
        return True, 0, "No key - افتراض بشر"
    
    try:
        url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_KEY}&limit=50"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return True, 0, "مقدرش أفحص - افتراض بشر"
        
        txs = r.json()
        buys = []
        times = []
        amounts = []
        mints = set()
        
        for tx in txs:
            ts = tx.get('timestamp',0)
            for tr in tx.get('tokenTransfers',[]):
                if tr.get('toUserAccount') == wallet:
                    try:
                        amt = float(tr.get('tokenAmount',0))
                        buys.append(amt)
                        times.append(ts)
                        amounts.append(amt)
                        mints.add(tr.get('mint',''))
                    except:
                        pass
        
        if len(buys) < 3:
            return True, 0, f"مشتريات قليلة ({len(buys)}) - بشر محتمل"
        
        times_sorted = sorted(times)
        intervals = [times_sorted[i+1]-times_sorted[i] for i in range(len(times_sorted)-1)]
        avg_interval = sum(intervals)/len(intervals) if intervals else 9999
        dust_count = sum(1 for a in amounts if a <= 10)
        dust_ratio = dust_count / len(buys) if buys else 0
        avg_amount = sum(amounts)/len(amounts) if amounts else 0
        
        bot_score = 0
        reasons = []
        
        if dust_ratio > 0.5: # شروط أشد من الأول (كان 70%)
            bot_score += 40
            reasons.append(f"Dust {dust_ratio:.0%}")
        if avg_interval < 120: # أقل من دقيقتين
            bot_score += 30
            reasons.append(f"سريع {avg_interval:.0f}ث")
        if len(buys) > 30 and avg_amount < 15:
            bot_score += 20
            reasons.append("كميات صغيرة")
        if len(mints) > 30 and len(buys) > 30:
            bot_score += 10
            reasons.append("توكنات كتير")
        
        is_human = bot_score < 30 # أشد من 50
        status = f"بشر ✅ Score {bot_score}" if is_human else f"بوت 🤖 Score {bot_score} ({', '.join(reasons)})"
        return is_human, bot_score, status
        
    except Exception as e:
        return True, 0, f"خطأ فحص: {e}"

# ===== الطبقة 2: فلتر السكام - هل التوكن نصاب ولا لا؟ =====
def check_token_rugcheck(mint):
    """
    من بحث RugCheck.xyz:
    Base: https://api.rugcheck.xyz/v1/tokens/{mint}/report/summary + /report
    - score_normalised: 0=آمن 100=خطر
    - mintAuthority == null = كويس (مايقدرش يطبع)
    - freezeAuthority == null = كويس (مايقدرش يجمد)
    - topHolders % < 35% = كويس
    - lpLocked > 50% = كويس
    - risks: HONEYPOT, RUG_PULL, HIGH_TAXES
    """
    score = 0
    warnings = []
    details = {}
    
    try:
        # 1. تقرير سريع
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report/summary", timeout=10)
        if r.status_code == 200:
            data = r.json()
            # API بيرجع score بأسماء مختلفة
            rug_score = data.get('score_normalised') or data.get('score') or 0
            risks = data.get('risks', [])
            
            details['rugcheck_score'] = rug_score
            details['risks'] = risks
            
            if rug_score > 60:
                score += 40
                warnings.append(f"🚨 RugCheck {rug_score}/100 خطر عالي")
            elif rug_score > 40:
                score += 20
                warnings.append(f"⚠️ RugCheck {rug_score}/100 متوسط")
            
            # فحص المخاطر الخطيرة
            for risk in risks:
                name = risk.get('name','') if isinstance(risk, dict) else str(risk)
                level = risk.get('level','') if isinstance(risk, dict) else ''
                if name in ['HONEYPOT', 'RUG_PULL', 'HIGH_TAXES', 'PROXY_CONTRACT']:
                    score += 30
                    warnings.append(f"🚨 خطر: {name}")
        
        # 2. تقرير مفصل للـ authorities
        r2 = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=10)
        if r2.status_code == 200:
            data = r2.json()
            
            # mint authority
            mint_auth = data.get('token', {}).get('mintAuthority') or data.get('mintAuthority')
            freeze_auth = data.get('token', {}).get('freezeAuthority') or data.get('freezeAuthority')
            
            details['mintAuthority'] = mint_auth
            details['freezeAuthority'] = freeze_auth
            
            if mint_auth:
                score += 30
                warnings.append("🚨 يقدر يطبع توكنات جديدة (mint authority موجود)")
            if freeze_auth:
                score += 25
                warnings.append("🚨 يقدر يجمد محافظ (freeze authority موجود)")
            
            # Top holders
            top_holders = data.get('topHolders', []) or data.get('holders', [])
            if top_holders:
                try:
                    top_pct = float(top_holders[0].get('pct', 0) or top_holders[0].get('percentage', 0) or 0)
                    if top_pct > 50:
                        score += 25
                        warnings.append(f"🚨 محفظة واحدة عندها {top_pct:.1f}%")
                    elif top_pct > 35:
                        score += 15
                        warnings.append(f"⚠️ تركيز عالي {top_pct:.1f}% عند حوت واحد")
                    details['top_holder_pct'] = top_pct
                except:
                    pass
            
            # LP lock
            markets = data.get('markets', [])
            if markets:
                try:
                    lp_locked = markets[0].get('lp', {}).get('lpLockedPct', 0) or markets[0].get('lpLockedPct', 0)
                    if lp_locked < 50 and lp_locked != 0:
                        score += 15
                        warnings.append(f"⚠️ سيولة مش مقفولة كويس {lp_locked:.0f}%")
                    details['lp_locked_pct'] = lp_locked
                except:
                    pass
                    
    except Exception as e:
        warnings.append(f"⚠️ مقدرش أفحص RugCheck: {e}")
    
    return score, warnings, details

def check_token_dexscreener(mint):
    """
    فحص DexScreener:
    - liquidity > $10k
    - volume 24h > $5k
    - fdv/liquidity < 100
    - priceChange 24h < 500% (تجنب pump مضروب)
    - holders > 50 (لو متاح)
    """
    score = 0
    warnings = []
    details = {}
    
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            pairs = data.get('pairs', [])
            if not pairs:
                return 80, ["❌ مفيش سيولة على DexScreener"], {}
            
            # خد أفضل pair (أكبر سيولة)
            pair = sorted(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0), reverse=True)[0]
            
            liquidity = float(pair.get('liquidity', {}).get('usd', 0) or 0)
            volume_24h = float(pair.get('volume', {}).get('h24', 0) or 0)
            fdv = float(pair.get('fdv', 0) or 0)
            price_change_24h = float(pair.get('priceChange', {}).get('h24', 0) or 0)
            price_change_1h = float(pair.get('priceChange', {}).get('h1', 0) or 0)
            
            details['liquidity'] = liquidity
            details['volume_24h'] = volume_24h
            details['fdv'] = fdv
            details['price_change_24h'] = price_change_24h
            details['price_change_1h'] = price_change_1h
            details['symbol'] = pair.get('baseToken', {}).get('symbol', 'UNKNOWN')
            details['price_usd'] = pair.get('priceUsd', '0')
            
            if liquidity < 5000:
                score += 40
                warnings.append(f"❌ سيولة ضعيفة جدا ${liquidity:.0f}")
            elif liquidity < 10000:
                score += 25
                warnings.append(f"⚠️ سيولة قليلة ${liquidity:.0f}")
            
            if volume_24h < 1000:
                score += 20
                warnings.append(f"⚠️ حجم تداول ضعيف ${volume_24h:.0f}")
            
            if fdv > 0 and liquidity > 0:
                ratio = fdv / liquidity
                if ratio > 200:
                    score += 20
                    warnings.append(f"⚠️ FDV عالي جدا بالنسبة للسيولة ({ratio:.0f}x)")
                details['fdv_liq_ratio'] = ratio
            
            if price_change_24h > 1000:
                score += 25
                warnings.append(f"🚨 صعود {price_change_24h:.0f}% في 24h - Pump & Dump محتمل")
            elif price_change_24h > 500:
                score += 15
                warnings.append(f"⚠️ صعود كبير {price_change_24h:.0f}%")
            
            # لو نزل 90% في ساعة = rug
            if price_change_1h < -80:
                score += 30
                warnings.append(f"🚨 نزل {price_change_1h:.0f}% في ساعة - Rug محتمل")
    
    except Exception as e:
        warnings.append(f"⚠️ DexScreener خطأ: {e}")
    
    return score, warnings, details

def is_token_safe(mint):
    """
    يجمع كل فحوصات السكام ويرجع True لو آمن
    """
    total_score = 0
    all_warnings = []
    all_details = {}
    
    # 1. RugCheck
    rug_score, rug_warns, rug_details = check_token_rugcheck(mint)
    total_score += rug_score
    all_warnings.extend(rug_warns)
    all_details.update(rug_details)
    
    # 2. DexScreener
    dex_score, dex_warns, dex_details = check_token_dexscreener(mint)
    total_score += dex_score
    all_warnings.extend(dex_warns)
    all_details.update(dex_details)
    
    # قرار نهائي
    is_safe = total_score < 60 # أقل من 60 = آمن نسبيا
    # لو فيه خطر قاتل واحد (mint auth + top holder >50%) ارفض حتى لو Score قليل
    has_critical = any("يقدر يطبع" in w or "يقدر يجمد" in w or "HONEYPOT" in w or "RUG_PULL" in w for w in all_warnings)
    if has_critical:
        is_safe = False
    
    return is_safe, total_score, all_warnings, all_details

# ===== الطبقة 3: تتبع المحافظ مع كل الفلاتر =====
def check_wallet_with_filters(wallet):
    if not HELIUS_KEY:
        print("No HELIUS_KEY")
        return
    
    # فلتر بشر؟
    is_human, bot_score, human_status = is_human_wallet(wallet, quick_check=True)
    if not is_human:
        print(f"تجاهل {wallet[:8]} - {human_status}")
        return
    
    url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_KEY}&limit=25"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return
        txs = r.json()
        cutoff = datetime.now().timestamp() - 6*3600
        
        for tx in txs:
            ts = tx.get('timestamp',0)
            if ts < cutoff:
                continue
            
            if tx.get('type') == 'CREATE':
                continue
            
            signature = tx.get('signature','')
            
            for tr in tx.get('tokenTransfers',[]):
                try:
                    amt = float(tr.get('tokenAmount',0))
                    if amt < 100: # dust filter
                        continue
                    
                    mint = tr.get('mint','')
                    if not mint:
                        continue
                    
                    to_acc = tr.get('toUserAccount')
                    from_acc = tr.get('fromUserAccount')
                    
                    if to_acc == from_acc:
                        continue
                    
                    # ===== شراء =====
                    if to_acc == wallet:
                        # فلتر التوكن scam؟
                        is_safe, risk_score, warnings, details = is_token_safe(mint)
                        
                        symbol = details.get('symbol', 'UNKNOWN')
                        price = details.get('price_usd', '0')
                        liquidity = details.get('liquidity', 0)
                        
                        # سجل للعنقود الذهبي
                        RECENT_BUYS[mint].append((wallet, ts, amt))
                        # نظف القديم (أكتر من ساعة)
                        RECENT_BUYS[mint] = [(w,t,a) for w,t,a in RECENT_BUYS[mint] if datetime.now().timestamp() - t < 3600]
                        
                        cluster_count = len(RECENT_BUYS[mint])
                        cluster_wallets = [w[:6] for w,_ ,_ in RECENT_BUYS[mint]]
                        
                        if is_safe:
                            # TP/SL suggestion
                            vol_24 = details.get('price_change_24h', 0)
                            if abs(vol_24) > 50:
                                tp, sl, strategy = 30, 15, "⚡ متقلب - TP 30% سريع"
                            elif abs(vol_24) > 20:
                                tp, sl, strategy = 50, 20, "📈 متوسط - TP 50%"
                            else:
                                tp, sl, strategy = 100, 25, "💎 هادي - Diamond TP 100%"
                            
                            cluster_msg = ""
                            if cluster_count >= 2:
                                cluster_msg = f"\n🔥 *عنقود ذهبي!* {cluster_count} محافظ ذهبية اشتروا نفس التوكن في ساعة: {', '.join(cluster_wallets)}"
                            
                            msg = f"""🟢 *شراء حقيقي - بشر مؤكد* ✅
محفظة: `{wallet[:12]}...` ({human_status})
توكن: `{symbol}` `{mint[:12]}...`
كمية: {amt:,.0f} | سعر: ${price}
سيولة: ${liquidity:,.0f} | Risk: {risk_score}/100 آمن
{strategy} TP {tp}% SL {sl}%
[Solscan](https://solscan.io/account/{wallet}) | [DexScreener](https://dexscreener.com/solana/{mint}) | [Tx](https://solscan.io/tx/{signature}){cluster_msg}"""
                            send_tg(msg)
                            print(f"BUY SAFE: {wallet[:8]} {symbol} {amt} Risk {risk_score}")
                        else:
                            # توكن خطر - نبعت تحذير بس مش توصية
                            warn_text = "\\n".join(warnings[:3])
                            msg = f"""⚠️ *شراء لكن توكن خطر - لا تدخل* 
محفظة بشر: `{wallet[:12]}...`
توكن: `{mint[:12]}...`
Risk: {risk_score}/100 - مرفوض
الأسباب:
{warn_text}
[فحص RugCheck](https://rugcheck.xyz/tokens/{mint})"""
                            # ما نبعتش التحذير للعامة، نطبعه بس عشان ما نزعجش
                            print(f"BUY RISKY REJECTED: {wallet[:8]} {mint[:8]} Risk {risk_score} {warnings}")
                            # send_tg(msg) # اختياري - لو عايز تحذيرات السكام كمان
                        
                        return True
                    
                    # ===== بيع =====
                    elif from_acc == wallet:
                        msg = f"""🔴 *بيع حقيقي - خروج!* 
محفظة: `{wallet[:12]}...` باعت
توكن: `{mint[:12]}...`
كمية: {amt:,.0f}
[Solscan](https://solscan.io/account/{wallet}) | [Tx](https://solscan.io/tx/{signature})"""
                        send_tg(msg)
                        print(f"SELL: {wallet[:8]} {mint[:8]} {amt}")
                        return True
                        
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"Error {wallet[:12]}: {e}")
    return False

if __name__ == "__main__":
    print(f"=== PRO MAX TRACKER ===")
    print(f"Checking {len(GOLDEN_WALLETS)} golden HUMAN wallets...")
    print(f"Filters: Human only (bot_score<30) + Token safe (RugCheck+DexScreener) + Golden Cluster")
    
    for w in GOLDEN_WALLETS:
        is_human, bot_score, status = is_human_wallet(w, quick_check=False)
        print(f"{w[:12]}...: {status}")
        check_wallet_with_filters(w)
        time.sleep(0.8)
    
    print("Done - Recent buys cluster:", dict(RECENT_BUYS))
