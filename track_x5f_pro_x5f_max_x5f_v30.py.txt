"""
PRO MAX V30 - 30 محفظة ذهبية + 3 طبقات فلترة بشر + سكام + عنقود
نسخة موسعة من 15 لـ 30 محفظة
"""

import os, requests, time
from datetime import datetime
from collections import defaultdict

HELIUS_KEY = os.getenv('HELIUS_API_KEY')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 30 محفظة ذهبية موسعة - بشر حقيقي فقط
GOLDEN_WALLETS = [
    # الـ 15 الأصلية LEHR
    "2T5NgDDidkvhJQg8AHDi74uCFwgp25pYFMRZXBaCUNBH",
    "4oYjvNib7RrKTqMSyDYU5rXAeSV955FVad9B2y4gNFXa",
    "57f2jG9eveivqdSvcaaKFCSW5YDECam29xwRf2gBmqVT",
    "6NktQqEjNr6mJnsr96sg7d8iYhkxthWGN2pzRWqvbCr",
    "C3XZgqcU1U5TLTk3kYUUeoRim8bpnqwGcV9ZVMN6YWbz",
    "6S71WKwp5YtwBuoMv5ra3cx24umAz86qxRJmPANbJvKy",
    "BXbByWHgUeapK52LwPBH6HCDBquRmBY4ms23cLELP5Ng",
    "96Vpi8sxTwxT7vX9mwbcZf8qjqfuVbBSPbghxxfFCqa1",
    "FzttT8tzXicSQZW9nxQTwTrfhtwgFvMiA8BvXogdWDbv",
    "9d1pZHbTJzTR9oQF2rPx3Ssy5WiTD3nz2rp5PNeynf6h",
    "GCpKsqPx6akPVqMRqCSvTmPx4Si6agZgEAxsS8xiPf1j",
    "SKRWBceZen2XrHvMBFzkhPxSDZm8kCQRLxtwu4asMZ3",
    "4sSxgbSBhFrArbGyacm3tcrDTxbBXdFTrPJ5vCA8ZqFG",
    "3kckXQKfcByrP5whYLaakVEjA2YDyVy7KPhMt2GWZSYi",
    "AoMS3Mgky8DPXyZQpmzzGfnLdVEVytsFsw735eJJz2Nk",
    # 15 الجديدة - Diamond + بشر
    "215nhcAHjQQGgwpQSJQ7zR26etbjjtVdW74NLzwEgQjP",  # OGAntD انت
    "6kbwsSY4hL6WVadLRLnWV2irkMN2AvFZVAS8McKJmAtJ",  # $1.3M smart
    "BKVaB3eNrGUVRCj3M4LiodKypBTzrpatoo7VBhmdv3eY",  # AI specialist $990k
    "5hAgYC8TJCcEZV7LTXAzkTrm7YL29YXyQQJPCNrG84zM",  # Schoen 71% WR
    "muDJGhd84zZsPUX16REawGUUWRaRV9Zrs2TkNzc213Th",
    "BUEZoTy9yhnncGMk2XUTRCnhBzKp6HX6Sgsi29jwK8db",
    "yhituu4c2PMGz7V9GXa4YGA3r2Rgwr6q5JUZgp28ciYA",
    "dPFteZFTM14oAz4MryK1PLofeSep37vbW5tEuYjdckRm",
    "6z1JxzoMJLPMGr4g7X4BxghrBXTtcBAdee8hQ2Hs1Ay2",
    "pUBnLni4tAVCEAUPigBKgvCVffAokNQ2b2htBg8rcu5p",
    "veu3Wh1jSNxUUrjpYnq2zT7b1MYdv7pBsZVDxwydHwLo",
    "BkGkxf75bfD7PVjETXCuGRage5DKSHjvUVTXdZVD6QdF",
    "6h1rYhLyY23jepQaBkyfhhpGhEt1AM18J7Hzjfrt5zRS",
    "Qf3wwhrKbVfVfxoBHr5AUEE3PMypE2hY2rFntqbrzdPM",
    "aaLP9RbzwqeDm7HVJY3TTQQEjN63VrqCexyya5Ux3kAv",
]

RECENT_BUYS = defaultdict(list)

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(text)
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=12)
    except Exception as e:
        print(f"TG error: {e}")

def check_token_rugcheck(mint):
    score = 0
    warnings = []
    details = {}
    try:
        r = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report/summary", timeout=10)
        if r.status_code == 200:
            data = r.json()
            rug_score = data.get('score_normalised') or data.get('score') or 0
            risks = data.get('risks', [])
            details['rugcheck_score'] = rug_score
            if rug_score > 60:
                score += 40
                warnings.append(f"RugCheck {rug_score}/100 عالي")
            elif rug_score > 40:
                score += 20
                warnings.append(f"RugCheck {rug_score}/100 متوسط")
            for risk in risks:
                name = risk.get('name','') if isinstance(risk, dict) else str(risk)
                if name in ['HONEYPOT','RUG_PULL','HIGH_TAXES']:
                    score += 30
                    warnings.append(f"خطر: {name}")
        r2 = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report", timeout=10)
        if r2.status_code == 200:
            data = r2.json()
            mint_auth = data.get('token',{}).get('mintAuthority') or data.get('mintAuthority')
            freeze_auth = data.get('token',{}).get('freezeAuthority') or data.get('freezeAuthority')
            details['mintAuthority'] = mint_auth
            details['freezeAuthority'] = freeze_auth
            if mint_auth:
                score += 30
                warnings.append("يقدر يطبع توكنات")
            if freeze_auth:
                score += 25
                warnings.append("يقدر يجمد محافظ")
            top_holders = data.get('topHolders',[]) or data.get('holders',[])
            if top_holders:
                try:
                    top_pct = float(top_holders[0].get('pct',0) or top_holders[0].get('percentage',0) or 0)
                    details['top_holder_pct'] = top_pct
                    if top_pct > 50:
                        score += 25
                        warnings.append(f"محفظة واحدة {top_pct:.1f}%")
                    elif top_pct > 35:
                        score += 15
                        warnings.append(f"تركيز عالي {top_pct:.1f}%")
                except: pass
    except Exception as e:
        warnings.append(f"RugCheck خطأ: {e}")
    return score, warnings, details

def check_token_dex(mint):
    score = 0
    warnings = []
    details = {}
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            pairs = data.get('pairs',[])
            if not pairs:
                return 80, ["مفيش سيولة"], {}
            pair = sorted(pairs, key=lambda x: float(x.get('liquidity',{}).get('usd',0) or 0), reverse=True)[0]
            liquidity = float(pair.get('liquidity',{}).get('usd',0) or 0)
            volume_24h = float(pair.get('volume',{}).get('h24',0) or 0)
            fdv = float(pair.get('fdv',0) or 0)
            ch24 = float(pair.get('priceChange',{}).get('h24',0) or 0)
            ch1h = float(pair.get('priceChange',{}).get('h1',0) or 0)
            details.update({
                'liquidity': liquidity,
                'volume_24h': volume_24h,
                'fdv': fdv,
                'price_change_24h': ch24,
                'price_change_1h': ch1h,
                'symbol': pair.get('baseToken',{}).get('symbol','UNKNOWN'),
                'price_usd': pair.get('priceUsd','0')
            })
            if liquidity < 5000:
                score += 40
                warnings.append(f"سيولة ضعيفة ${liquidity:.0f}")
            elif liquidity < 10000:
                score += 25
                warnings.append(f"سيولة قليلة ${liquidity:.0f}")
            if volume_24h < 1000:
                score += 20
                warnings.append(f"حجم ضعيف ${volume_24h:.0f}")
            if fdv>0 and liquidity>0 and fdv/liquidity>200:
                score += 20
                warnings.append(f"FDV/Liq عالي {fdv/liquidity:.0f}x")
            if ch24>1000:
                score += 25
                warnings.append(f"صعود {ch24:.0f}% pump محتمل")
            if ch1h < -80:
                score += 30
                warnings.append(f"نزل {ch1h:.0f}% rug محتمل")
    except Exception as e:
        warnings.append(f"Dex خطأ: {e}")
    return score, warnings, details

def is_token_safe(mint):
    total=0
    warns=[]
    det={}
    s1,w1,d1=check_token_rugcheck(mint)
    s2,w2,d2=check_token_dex(mint)
    total=s1+s2
    warns=w1+w2
    det={**d1,**d2}
    critical = any("يطبع" in w or "يجمد" in w or "HONEYPOT" in w for w in warns)
    safe = total<60 and not critical
    return safe,total,warns,det

def check_wallet(wallet):
    if not HELIUS_KEY:
        return
    url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_KEY}&limit=25"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code!=200:
            return
        txs=r.json()
        cutoff=datetime.now().timestamp()-6*3600
        for tx in txs:
            if tx.get('timestamp',0)<cutoff:
                continue
            if tx.get('type')=='CREATE':
                continue
            sig=tx.get('signature','')
            for tr in tx.get('tokenTransfers',[]):
                try:
                    amt=float(tr.get('tokenAmount',0))
                    if amt<100:
                        continue
                    mint=tr.get('mint','')
                    if not mint:
                        continue
                    to_acc=tr.get('toUserAccount')
                    from_acc=tr.get('fromUserAccount')
                    if to_acc==from_acc:
                        continue
                    if to_acc==wallet:
                        safe, risk, warnings, details = is_token_safe(mint)
                        symbol=details.get('symbol','UNKNOWN')
                        price=details.get('price_usd','0')
                        liq=details.get('liquidity',0)
                        RECENT_BUYS[mint].append((wallet, tx.get('timestamp',0), amt))
                        RECENT_BUYS[mint]=[(w,t,a) for w,t,a in RECENT_BUYS[mint] if datetime.now().timestamp()-t<3600]
                        cluster=len(RECENT_BUYS[mint])
                        cluster_wallets=[w[:6] for w,_,_ in RECENT_BUYS[mint]]
                        if safe:
                            vol24=details.get('price_change_24h',0)
                            if abs(vol24)>50:
                                tp,sl,strat=30,15,"⚡ متقلب TP 30%"
                            elif abs(vol24)>20:
                                tp,sl,strat=50,20,"📈 متوسط TP 50%"
                            else:
                                tp,sl,strat=100,25,"💎 هادي Diamond TP 100%"
                            cluster_msg=""
                            if cluster>=2:
                                cluster_msg=f"\n🔥 *عنقود ذهبي!* {cluster} محافظ اشتروا نفس التوكن: {', '.join(cluster_wallets)}"
                            msg=f"""🟢 *شراء حقيقي - بشر + آمن* ✅
محفظة: `{wallet[:12]}...`
توكن: `{symbol}` `{mint[:12]}...`
كمية: {amt:,.0f} | سعر ${price}
سيولة ${liq:,.0f} | Risk {risk}/100
{strat} TP {tp}% SL {sl}%
[Solscan](https://solscan.io/account/{wallet}) | [Dex](https://dexscreener.com/solana/{mint}){cluster_msg}"""
                            send_tg(msg)
                            print(f"BUY SAFE {wallet[:8]} {symbol} Risk {risk}")
                        else:
                            print(f"REJECTED RISKY {wallet[:8]} {mint[:8]} Risk {risk} {warnings[:2]}")
                        return True
                    elif from_acc==wallet:
                        msg=f"""🔴 *بيع حقيقي - خروج!*
محفظة: `{wallet[:12]}...` باعت
توكن: `{mint[:12]}...`
كمية {amt:,.0f}
[Solscan](https://solscan.io/account/{wallet})"""
                        send_tg(msg)
                        print(f"SELL {wallet[:8]} {mint[:8]}")
                        return True
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Error {wallet[:12]} {e}")

if __name__=="__main__":
    print(f"=== PRO MAX V30 - {len(GOLDEN_WALLETS)} wallets - Human + Safe Token + Cluster ===")
    for w in GOLDEN_WALLETS:
        check_wallet(w)
        time.sleep(0.7)
    print("Done")
