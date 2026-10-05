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
    except Exception as e:
        print(f"TG error: {e}")

def get_trending_mints():
    """يجيب توكنات تريند من DexScreener"""
    try:
        url = "https://api.dexscreener.com/latest/dex/tokens/trending"
        # بديل: نجيب توكنات Solana الجديدة
        r = requests.get("https://api.dexscreener.com/latest/dex/search/?q=solana", timeout=10)
        if r.status_code == 200:
            data = r.json()
            mints = []
            for pair in data.get('pairs',[])[:10]:
                if pair.get('chainId') == 'solana':
                    mints.append(pair.get('baseToken',{}).get('address'))
            return [m for m in mints if m][:5]
    except Exception as e:
        print(f"Dex error: {e}")
    # fallback mints معروفة
    return [
        "So11111111111111111111111111111111111111112",  # WSOL
    ]

def get_holders_for_mint(mint):
    """يجيب اكبر حاملي التوكن"""
    if not HELIUS_KEY:
        return []
    try:
        # نستخدم Helius للحصول على holders
        url = f"https://api.helius.xyz/v0/tokens/{mint}/holders?api-key={HELIUS_KEY}&limit=20"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json().get('holders', [])[:10]
    except:
        pass
    return []

def check_if_real_buyer(wallet):
    """يفحص هل المحفظة بتشتري حقيقي ولا dust"""
    if not HELIUS_KEY:
        return None
    url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_KEY}&limit=50"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        txs = r.json()
        buys = []
        real = []
        cutoff = datetime.now().timestamp() - 24*3600
        for tx in txs:
            if tx.get('timestamp',0) < cutoff:
                continue
            for tr in tx.get('tokenTransfers',[]):
                if tr.get('toUserAccount') == wallet:
                    try:
                        amt = float(tr.get('tokenAmount',0))
                        buys.append(amt)
                        if amt > 10:
                            real.append(amt)
                    except:
                        pass
        if not buys:
            return None
        dust_ratio = len([a for a in buys if a <= 10]) / len(buys)
        avg = sum(buys)/len(buys) if buys else 0
        bot_score = 0
        if dust_ratio > 0.7:
            bot_score += 40
        if len(buys) > 30 and avg < 20:
            bot_score += 30
        is_bot = bot_score >= 50
        is_real = len(real) >= 3 and not is_bot and dust_ratio < 0.5
        return {
            "total": len(buys),
            "real": len(real),
            "dust_ratio": dust_ratio,
            "bot_score": bot_score,
            "is_bot": is_bot,
            "is_real": is_real,
            "max_buy": max(real) if real else 0
        }
    except Exception as e:
        print(f"Check error {wallet[:8]}: {e}")
        return None

if __name__ == "__main__":
    print("=== بوت اكتشاف محافظ جديدة مش dust ===")
    # للتجربة: نفحص محافظ عشوائية من التريند
    # في النسخة الكاملة هنفحص holders التوكنات الجديدة
    
    # محافظ للتجربة من LEHR (هنكتشف زيها)
    test_wallets = [
        "2T5NgDDidkvhJQg8AHDi74uCFwgp25pYFMRZXBaCUNBH",
        "4oYjvNib7RrKTqMSyDYU5rXAeSV955FVad9B2y4gNFXa",
    ]
    
    new_real_wallets = []
    for wallet in test_wallets:
        res = check_if_real_buyer(wallet)
        if res and res['is_real']:
            print(f"✅ محفظة حقيقية جديدة: {wallet[:12]} Real:{res['real']} Max:{res['max_buy']:.0f} Dust:{res['dust_ratio']:.0%}")
            new_real_wallets.append((wallet, res))
            msg = f"💎 *محفظة جديدة مش dust!*\\n`{wallet[:12]}...`\\nصفقات حقيقية: {res['real']}\\nأكبر صفقة: {res['max_buy']:.0f}\\nDust: {res['dust_ratio']:.0%}\\n[Solscan](https://solscan.io/account/{wallet})"
            send_tg(msg)
        elif res and res['is_bot']:
            print(f"🤖 بوت dust: {wallet[:12]} Dust:{res['dust_ratio']:.0%}")
        time.sleep(0.5)
    
    print(f"\\nFound {len(new_real_wallets)} new real wallets")
    # حفظ
    if new_real_wallets:
        with open("new_real_wallets.txt","w") as f:
            for w, r in new_real_wallets:
                f.write(f"{w} - Real:{r['real']} Max:{r['max_buy']:.0f}\\n")
