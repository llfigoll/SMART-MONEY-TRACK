import os, requests, json, time
from datetime import datetime

HELIUS_KEY = os.getenv('HELIUS_API_KEY')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# المحافظ الذهبية - بشر حقيقي بتحتفظ
GOLDEN_WALLETS = [
    "2T5NgDDidkvhJQg8AHDi74uCFwgp25pYFMRZXBaCUNBH",  # 20min holder
    "4oYjvNib7RrKTqMSyDYU5rXAeSV955FVad9B2y4gNFXa",  # Diamond 3047min
    "57f2jG9eveivqdSvcaaKFCSW5YDECam29xwRf2gBmqVT",
    "6NktQqEjNr6mJnsr96sg7d8iYhkxthWGN2pzRWqvbCr",  # 186min
    "C3XZgqcU1U5TLTk3kYUUeoRim8bpnqwGcV9ZVMN6YWbz",  # 63 cycles active
    "6S71WKwp5YtwBuoMv5ra3cx24umAz86qxRJmPANbJvKy",  # Diamond 409min
    "BXbByWHgUeapK52LwPBH6HCDBquRmBY4ms23cLELP5Ng",
    "96Vpi8sxTwxT7vX9mwbcZf8qjqfuVbBSPbghxxfFCqa1",
    "FzttT8tzXicSQZW9nxQTwTrfhtwgFvMiA8BvXogdWDbv",
    "9d1pZHbTJzTR9oQF2rPx3Ssy5WiTD3nz2rp5PNeynf6h",  # Diamond 305min
    "GCpKsqPx6akPVqMRqCSvTmPx4Si6agZgEAxsS8xiPf1j",  # Diamond 820min
    "SKRWBceZen2XrHvMBFzkhPxSDZm8kCQRLxtwu4asMZ3",
    "4sSxgbSBhFrArbGyacm3tcrDTxbBXdFTrPJ5vCA8ZqFG",
    "3kckXQKfcByrP5whYLaakVEjA2YDyVy7KPhMt2GWZSYi",
    "AoMS3Mgky8DPXyZQpmzzGfnLdVEVytsFsw735eJJz2Nk",  # Diamond 4299min - 71 ساعة
]

def is_real_buy(amount):
    try:
        return float(amount) > 10
    except:
        return False

def send_tg(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(text)
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"TG error: {e}")

def check_wallet(wallet):
    if not HELIUS_KEY:
        print("No HELIUS_KEY")
        return
    url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions?api-key={HELIUS_KEY}&limit=20"
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
            for tr in tx.get('tokenTransfers',[]):
                if tr.get('toUserAccount') == wallet:
                    try:
                        amt = float(tr.get('tokenAmount',0))
                        if is_real_buy(amt):
                            mint = tr.get('mint','')
                            # Bot check - dust ratio
                            # اذا الشراء >100 توكن يبقى حقيقي
                            if amt > 100:
                                msg = f"🟢 *شراء حقيقي*\\nمحفظة: `{wallet[:12]}...`\\nتوكن: `{mint[:12]}...`\\nكمية: {amt:.0f}\\n[Solscan](https://solscan.io/account/{wallet})"
                                send_tg(msg)
                                print(f"Found real buy: {wallet[:12]} {mint[:12]} {amt}")
                                return True
                    except:
                        pass
    except Exception as e:
        print(f"Error {wallet[:12]}: {e}")
    return False

if __name__ == "__main__":
    print(f"Checking {len(GOLDEN_WALLETS)} golden wallets...")
    for w in GOLDEN_WALLETS:
        check_wallet(w)
        time.sleep(0.5)
    print("Done")
