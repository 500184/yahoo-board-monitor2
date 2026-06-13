import os
import re
import json
import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


JST = ZoneInfo("Asia/Tokyo")
STATE_PATH = "data/state.json"

IFTTT_KEY = os.environ.get("IFTTT_KEY", "")
IFTTT_EVENT = os.environ.get("IFTTT_EVENT", "yahoo_board_spike")

# 市場時間内の通知基準
MARKET_LAST5_THRESHOLD = 15
MARKET_SURGE_THRESHOLD = 15

# 市場時間外の通知基準
OFF_LAST5_THRESHOLD = 5
OFF_SURGE_THRESHOLD = 5

# 同じ銘柄の重複通知を防ぐ時間
ALERT_COOLDOWN_MINUTES = 15

# Yahoo側に負荷をかけすぎないため、銘柄ごとに少し待つ
MIN_SLEEP_SEC = 1.5
MAX_SLEEP_SEC = 3.5

BOARDS = [
    {"name": "オンコリス", "code": "4588", "url": "https://finance.yahoo.co.jp/quote/4588.T/forum"},
    {"name": "ステラファーマ", "code": "4888", "url": "https://finance.yahoo.co.jp/quote/4888.T/forum"},
    {"name": "ブライトパス", "code": "4594", "url": "https://finance.yahoo.co.jp/quote/4594.T/forum"},
    {"name": "ヘリオス", "code": "4593", "url": "https://finance.yahoo.co.jp/quote/4593.T/forum"},
    {"name": "レナサイエンス", "code": "4889", "url": "https://finance.yahoo.co.jp/quote/4889.T/forum"},
    {"name": "ケイファーマ", "code": "4896", "url": "https://finance.yahoo.co.jp/quote/4896.T/forum"},
    {"name": "サンバイオ", "code": "4592", "url": "https://finance.yahoo.co.jp/quote/4592.T/forum"},
    {"name": "ファンヘップ", "code": "4881", "url": "https://finance.yahoo.co.jp/quote/4881.T/forum"},
    {"name": "リボミック", "code": "4591", "url": "https://finance.yahoo.co.jp/quote/4591.T/forum"},
    {"name": "ハートシード", "code": "219A", "url": "https://finance.yahoo.co.jp/quote/219A.T/forum"},
    {"name": "コーディア", "code": "190A", "url": "https://finance.yahoo.co.jp/quote/190A.T/forum"},
    {"name": "クオリプス", "code": "4894", "url": "https://finance.yahoo.co.jp/quote/4894.T/forum"},
    {"name": "メドレックス", "code": "4586", "url": "https://finance.yahoo.co.jp/quote/4586.T/forum"},
    {"name": "ジーエヌアイ", "code": "2160", "url": "https://finance.yahoo.co.jp/quote/2160.T/forum"},
    {"name": "スリーディー", "code": "7777", "url": "https://finance.yahoo.co.jp/quote/7777.T/forum"},
    {"name": "セルシード", "code": "7776", "url": "https://finance.yahoo.co.jp/quote/7776.T/forum"},
    {"name": "デウエスタン", "code": "4576", "url": "https://finance.yahoo.co.jp/quote/4576.T/forum"},
    {"name": "デルタフライ", "code": "4598", "url": "https://finance.yahoo.co.jp/quote/4598.T/forum"},
    {"name": "ノイルイミューン", "code": "4893", "url": "https://finance.yahoo.co.jp/quote/4893.T/forum"},
    {"name": "モダリス", "code": "4883", "url": "https://finance.yahoo.co.jp/quote/4883.T/forum"},
    {"name": "キャンバス", "code": "4575", "url": "https://finance.yahoo.co.jp/quote/4575.T/forum"},
    {"name": "カイオム", "code": "4583", "url": "https://finance.yahoo.co.jp/quote/4583.T/forum"},
    {"name": "ペルセウス", "code": "4882", "url": "https://finance.yahoo.co.jp/quote/4882.T/forum"},
    {"name": "カルナバイオ", "code": "4572", "url": "https://finance.yahoo.co.jp/quote/4572.T/forum"},
    {"name": "キッズウェル", "code": "4584", "url": "https://finance.yahoo.co.jp/quote/4584.T/forum"},
    {"name": "シンバイオ", "code": "4582", "url": "https://finance.yahoo.co.jp/quote/4582.T/forum"},
    {"name": "クリングル", "code": "4884", "url": "https://finance.yahoo.co.jp/quote/4884.T/forum"},
    {"name": "ティムス", "code": "4891", "url": "https://finance.yahoo.co.jp/quote/4891.T/forum"},
    {"name": "ステムリム", "code": "4599", "url": "https://finance.yahoo.co.jp/quote/4599.T/forum"},
    {"name": "ラクオリア", "code": "4579", "url": "https://finance.yahoo.co.jp/quote/4579.T/forum"},
    {"name": "ソレイジア", "code": "4597", "url": "https://finance.yahoo.co.jp/quote/4597.T/forum"},
    {"name": "nano", "code": "4571", "url": "https://finance.yahoo.co.jp/quote/4571.T/forum"},
    {"name": "オンコセラピー", "code": "4564", "url": "https://finance.yahoo.co.jp/quote/4564.T/forum"},
    {"name": "リプロセル", "code": "4978", "url": "https://finance.yahoo.co.jp/quote/4978.T/forum"},
    {"name": "ネクセラ", "code": "4565", "url": "https://finance.yahoo.co.jp/quote/4565.T/forum"},
    {"name": "ペプチドリーム", "code": "4587", "url": "https://finance.yahoo.co.jp/quote/4587.T/forum"},
    {"name": "プリズム", "code": "206A", "url": "https://finance.yahoo.co.jp/quote/206A.T/forum"},
    {"name": "ベリタス", "code": "130A", "url": "https://finance.yahoo.co.jp/quote/130A.T/forum"},
    {"name": "アンジェス", "code": "4563", "url": "https://finance.yahoo.co.jp/quote/4563.T/forum"},
    {"name": "坪田ラボ", "code": "4890", "url": "https://finance.yahoo.co.jp/quote/4890.T/forum"},
    {"name": "フェニックスバイオ", "code": "6190", "url": "https://finance.yahoo.co.jp/quote/6190.T/forum"},
    {"name": "ジェイファーマ", "code": "520A", "url": "https://finance.yahoo.co.jp/quote/520A.T/forum"},
]


def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def is_market_open(now):
    # 土日除外。祝日は未対応。
    if now.weekday() >= 5:
        return False

    minutes = now.hour * 60 + now.minute

    morning_open = 9 * 60
    morning_close = 11 * 60 + 30
    afternoon_open = 12 * 60 + 30
    afternoon_close = 15 * 60 + 30

    return (
        morning_open <= minutes < morning_close
        or afternoon_open <= minutes < afternoon_close
    )


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }

    last_error = None

    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            print(f"  fetch attempt={attempt + 1} status={r.status_code}")

            if r.status_code == 200 and r.text:
                return r.text

            last_error = f"status={r.status_code}"

        except Exception as e:
            last_error = str(e)
            print(f"  fetch error attempt={attempt + 1}: {e}")

        time.sleep(3 + attempt * 3)

    raise RuntimeError(f"fetch failed: {last_error}")


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")
    text = re.sub(r"\n+", "\n", text)
    return text


def extract_post_dates(html, now):
    text = html_to_text(html)

    patterns = [
        r"(\d{4})/(\d{1,2})/(\d{1,2})\s+([0-2]?\d):([0-5]\d)",
        r"(\d{4})-(\d{1,2})-(\d{1,2})\s+([0-2]?\d):([0-5]\d)",
        r"(\d{4})年(\d{1,2})月(\d{1,2})日\s+([0-2]?\d):([0-5]\d)",
    ]

    results = []
    seen = set()

    for pat in patterns:
        for m in re.finditer(pat, text):
            y, mo, d, h, mi = map(int, m.groups())
            dt = datetime(y, mo, d, h, mi, tzinfo=JST)

            if dt > now + timedelta(minutes=1):
                continue

            key = dt.isoformat()
            if key not in seen:
                seen.add(key)
                results.append(dt)

    results.sort(reverse=True)
    return results


def judge_spike(post_dates, now, market_open):
    last5 = 0
    prev5 = 0

    for dt in post_dates[:80]:
        diff_min = (now - dt).total_seconds() / 60

        if 0 <= diff_min < 5:
            last5 += 1
        elif 5 <= diff_min < 10:
            prev5 += 1

    surge = last5 - prev5

    if market_open:
        should_alert = last5 >= MARKET_LAST5_THRESHOLD or surge >= MARKET_SURGE_THRESHOLD
    else:
        should_alert = last5 >= OFF_LAST5_THRESHOLD or surge >= OFF_SURGE_THRESHOLD

    return should_alert, last5, prev5, surge


def send_ifttt(name, code, last5, prev5, surge, market_open):
    if not IFTTT_KEY:
        print("  IFTTT_KEY not set. skip notification.")
        return

    mode = "市場時間内" if market_open else "市場時間外"

    url = f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}"

    payload = {
        "value1": f"{name} 掲示板急増",
        "value2": f"{mode} / {code} / 直近5分:{last5}",
        "value3": f"前5分:{prev5} / 差:{surge:+d}",
    }

    try:
        r = requests.post(url, data=payload, timeout=20)
        print(f"  IFTTT status={r.status_code} body={r.text[:120]}")
    except Exception as e:
        print(f"  IFTTT error: {e}")


def main():
    now = datetime.now(JST)
    market_open = is_market_open(now)

    print(f"start now={now.isoformat()} market_open={market_open}")
    print(f"boards={len(BOARDS)}")

    state = load_state()
    alerts = state.setdefault("alerts", {})

    checked = 0
    failed = 0
    alerted = 0

    for board in BOARDS:
        name = board["name"]
        code = board["code"]
        url = board["url"]

        print(f"\n{name} {code}")

        try:
            html = fetch_html(url)
            post_dates = extract_post_dates(html, now)

            if not post_dates:
                print("  post date not found")
                failed += 1
                continue

            should_alert, last5, prev5, surge = judge_spike(post_dates, now, market_open)

            print(
                f"  dates={len(post_dates)} "
                f"last5={last5} prev5={prev5} surge={surge}"
            )

            last_alert_iso = alerts.get(code)
            cooldown_ok = True

            if last_alert_iso:
                try:
                    last_alert = datetime.fromisoformat(last_alert_iso)
                    minutes_since = (now - last_alert).total_seconds() / 60
                    if minutes_since < ALERT_COOLDOWN_MINUTES:
                        cooldown_ok = False
                        print(f"  cooldown skip minutes_since={minutes_since:.1f}")
                except Exception:
                    pass

            if should_alert and cooldown_ok:
                send_ifttt(name, code, last5, prev5, surge, market_open)
                alerts[code] = now.isoformat()
                alerted += 1

            checked += 1

        except Exception as e:
            print(f"  error: {e}")
            failed += 1

        time.sleep(random.uniform(MIN_SLEEP_SEC, MAX_SLEEP_SEC))

    state["last_run"] = now.isoformat()
    state["last_result"] = {
        "checked": checked,
        "failed": failed,
        "alerted": alerted,
        "market_open": market_open,
    }

    save_state(state)

    print("\nfinished")
    print(f"checked={checked} failed={failed} alerted={alerted}")


if __name__ == "__main__":
    main()
