"""Threads × AI 全自動投稿アプリ（autopost）

人の承認を挟まず「生成 → 安全チェック → 本文＋リプ欄を自動投稿」まで一気に回す。
ナレッジ（カテゴリ別サブディレクトリ）と 5_buzz/patterns.md を参照して投稿を作る。

安全装置:
  - 景表法NG表現の自動検出（検出したら投稿せずスキップ）
  - ハッシュタグの自動除去（Threadsでは逆効果のため）
  - 直近投稿との重複チェック（同じ1行目を連投しない）
  - 1日の投稿上限（デフォルト3本）

使い方:
  python autopost.py --now                 # 今すぐ1本 生成して投稿
  python autopost.py --count 3 --now       # 今すぐ3本（間隔を空けて）投稿
  python autopost.py --loop                # 最適時間帯（朝/昼/夜）に自動投稿し続ける
  python autopost.py --now --dry-run       # 投稿せず生成結果だけ表示（API必要）
  python autopost.py --sample --dry-run    # APIなしでパイプラインだけ動作確認
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "threads_automation" / "knowledge"
HISTORY_FILE = DATA_DIR / "history.json"
DATA_DIR.mkdir(exist_ok=True)

CONFIG = {
    "THREADS_ACCESS_TOKEN": os.getenv("THREADS_ACCESS_TOKEN", ""),
    "THREADS_USER_ID": os.getenv("THREADS_USER_ID", ""),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "AI_MODEL": os.getenv("AI_MODEL", "claude-sonnet-4-20250514"),
    "NICHE": "AI活用 × 仕組み化 × 収益化（情報系大学生の視点）",
    "TARGET": "AIで稼ぎたい10代後半〜20代の大学生・専門学生・若手社会人",
    # 投稿の最適時間帯（HH:MM）。朝の通勤・昼休み・夜のゴールデンタイム
    "POST_SLOTS": ["07:30", "12:15", "20:30"],
    "DAILY_LIMIT": 3,            # 1日の最大投稿本数
    "POST_INTERVAL_SEC": 300,    # --count 連投時の投稿間隔（秒）
    "SELF_REPLY_DELAY_SEC": 3,   # 本文→リプ欄の間隔（秒）
}

# 景表法・誇大広告に該当する表現（検出したら投稿しない）
NG_PATTERNS = [
    r"確実に(稼|儲)", r"必ず(稼|儲|儲か)", r"絶対に(稼|儲|儲か)",
    r"誰でも(必ず|簡単に)?月\s*\d", r"リスク(は)?ゼロ", r"ノーリスク",
    r"\b100\s*%\s*(稼|成功|再現|儲)", r"元本保証", r"今だけ無料で\d+万",
]


# ════════════════════════════════════════════════════════
#  ナレッジ
# ════════════════════════════════════════════════════════

def load_knowledge() -> str:
    """カテゴリ別サブディレクトリを再帰的に読み込む（app.py と同じ挙動）"""
    if not KNOWLEDGE_DIR.is_dir():
        return ""
    parts = []
    for f in sorted(KNOWLEDGE_DIR.rglob("*.md"),
                    key=lambda p: p.relative_to(KNOWLEDGE_DIR).as_posix()):
        parts.append(f.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


# ════════════════════════════════════════════════════════
#  Claude API
# ════════════════════════════════════════════════════════

def call_claude(prompt: str, system: str = "", max_tokens: int = 1500) -> str:
    if not CONFIG["ANTHROPIC_API_KEY"]:
        raise ValueError("ANTHROPIC_API_KEY が未設定です。.env を確認してください。")
    body = json.dumps({
        "model": CONFIG["AI_MODEL"],
        "max_tokens": max_tokens,
        "system": system or "あなたはThreads投稿の専門家です。",
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = Request("https://api.anthropic.com/v1/messages", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", CONFIG["ANTHROPIC_API_KEY"])
    req.add_header("anthropic-version", "2023-06-01")
    with urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode())["content"][0]["text"]


# ════════════════════════════════════════════════════════
#  投稿生成
# ════════════════════════════════════════════════════════

POST_TYPES = [
    "discovery（発見・驚き型）", "before_after（Before/After時短型）",
    "comparison（比較・実験型）", "tips（知らないと損する型）",
    "paradox（逆説・意外型）", "authority（権威性・実績型）",
    "automation（仕組み化・自動化型）", "tricks（小技・裏ワザ型）",
    "problem（問題提起・悩み共感型）",
]


def build_system_prompt(knowledge: str) -> str:
    return f"""あなたはThreads投稿の専門ライターです。以下のナレッジを厳密に参照して投稿を作成してください。

=== ナレッジ ===
{knowledge[:30000]}
=== ここまで ===

【最重要ルール】
- 1行目で全てが決まる。必ず「固有名詞」（ChatGPT/Claude/Gemini/Python等）と「数字」を入れる
- AIっぽい表現禁止（「〇〇だと思っていませんか？」「いかがでしたか？」「〜と言えるでしょう」等）
- ハッシュタグ（#）は絶対に使わない（インプレッション激減するため）
- 景表法違反は厳禁（「確実に稼げます」「誰でも月○万」「リスクゼロ」「100%再現」等）
- 収益・売上の話はOK（自分の実績を語るのはOK、他人への結果保証はNG）
- バズ分析の勝ちパターン（5_buzz/patterns.md）と参考型（2_writing/06_references.md）を最優先で参照

【ペルソナ】情報系の大学生。AIで実際に稼いでいる。主語は「自分」「僕」。フランクな口調。

【本文とリプ欄の構造（タップ経済の最大化）】
- 本文: 300〜500文字。核心をチラ見せし、最後は必ず「リプ欄に書いた↓」等で終わる（完結させない）
- リプ欄: 200〜400文字。一番有益な情報（手順・プロンプト・裏ワザ）を書き、最後にCTA"""


def generate_one_draft() -> dict:
    """ナレッジ参照で本文＋リプ欄を1本生成する"""
    knowledge = load_knowledge()
    system_prompt = build_system_prompt(knowledge)
    post_type = POST_TYPES[datetime.now().microsecond % len(POST_TYPES)]

    prompt = f"""以下の条件でThreads投稿を1本作成してください。

ターゲット: {CONFIG['TARGET']}
ジャンル: {CONFIG['NICHE']}
投稿タイプ: {post_type}

【手順】
1. ナレッジからテーマを決める（AI活用/仕組み化/収益化/セキュリティ/ML/業界動向）
2. 1行目を5案考え、最も「続きが気になる」1つを選ぶ（固有名詞+数字必須）
3. 本文（300〜500文字）: 核心をチラ見せ、最後は「リプ欄に書いた↓」で終わる
4. リプ欄（200〜400文字）: 具体的な手順・プロンプト・裏ワザ + 最後にCTA
5. セルフチェック（1行目で止まるか / AI感がないか / #がないか / 景表法OKか / リプ欄誘導で終わるか）

必ず以下のJSONのみを出力:
{{"hook_line": "選んだ1行目", "full_text": "本文", "comment_text": "リプ欄", "post_type": "{post_type}"}}"""

    raw = call_claude(prompt, system=system_prompt, max_tokens=2000)
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start < 0 or end <= 0:
        raise ValueError(f"AI応答からJSONを抽出できません: {raw[:200]}")
    p = json.loads(raw[start:end])
    return {
        "id": str(uuid.uuid4())[:8],
        "hook_line": p.get("hook_line", ""),
        "text": p.get("full_text", "").strip(),
        "comment_text": p.get("comment_text", "").strip(),
        "post_type": p.get("post_type", post_type),
    }


def sample_draft() -> dict:
    """APIなしでパイプラインを試すためのダミー下書き"""
    return {
        "id": str(uuid.uuid4())[:8],
        "hook_line": "Claudeに投稿を任せたら、3時間の作業が5分で終わった",
        "text": ("Claudeに投稿作りを任せたら、3時間かかってた作業が5分で終わった。\n\n"
                 "前は1本に1時間。ネタ探し→構成→推敲で毎回ヘトヘト。\n\n"
                 "今はナレッジを読ませて指示するだけ。\n\n"
                 "やり方はリプ欄に書いた↓"),
        "comment_text": ("やってることはシンプルで、\n"
                         "「読者・型・勝ちパターン」を1枚のメモにしてClaudeに渡すだけ。\n\n"
                         "毎回ゼロから指示しないのがコツ。\n\nみんなはどう使ってる？"),
        "post_type": "before_after（サンプル）",
    }


# ════════════════════════════════════════════════════════
#  安全チェック
# ════════════════════════════════════════════════════════

def strip_hashtags(text: str) -> str:
    """ハッシュタグを除去（行末・文中どちらも）"""
    text = re.sub(r"(?:^|\s)#[^\s#]+", " ", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def check_ng(text: str) -> str | None:
    """景表法NG表現を検出。該当すれば理由を返す（なければ None）"""
    for pat in NG_PATTERNS:
        m = re.search(pat, text)
        if m:
            return f"景表法NG表現「{m.group(0)}」を検出"
    return None


def is_duplicate(draft: dict, history: list) -> bool:
    """直近20件と1行目が重複していないか"""
    hook = draft["hook_line"].strip()
    first = draft["text"].split("\n")[0].strip()
    for h in history[:20]:
        h_first = (h.get("text", "").split("\n")[0]).strip()
        if hook and (hook == h.get("hook_line", "").strip() or hook == h_first):
            return True
        if first and first == h_first:
            return True
    return False


def vet_draft(draft: dict, history: list) -> tuple[bool, str]:
    """投稿してよいか判定。ハッシュタグは自動除去してから検査する。"""
    draft["text"] = strip_hashtags(draft["text"])
    draft["comment_text"] = strip_hashtags(draft.get("comment_text", ""))

    if not draft["text"]:
        return False, "本文が空"
    reason = check_ng(draft["text"] + "\n" + draft["comment_text"])
    if reason:
        return False, reason
    if is_duplicate(draft, history):
        return False, "直近投稿と1行目が重複"
    return True, "OK"


# ════════════════════════════════════════════════════════
#  Threads API
# ════════════════════════════════════════════════════════

def threads_api(method: str, endpoint: str, params=None, data=None):
    url = f"https://graph.threads.net/v1.0/{endpoint}"
    params = dict(params or {})
    params["access_token"] = CONFIG["THREADS_ACCESS_TOKEN"]
    if method == "GET":
        req = Request(f"{url}?{urlencode(params)}", method="GET")
    else:
        data = {**(data or {}), **params}
        req = Request(url, data=urlencode(data).encode(), method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        raise Exception(f"Threads API {e.code}: {e.read().decode() if e.fp else ''}") from e


def _publish(text: str, reply_to: str | None = None) -> str:
    uid = CONFIG["THREADS_USER_ID"]
    create = {"media_type": "TEXT", "text": text}
    if reply_to:
        create["reply_to_id"] = reply_to
    container = threads_api("POST", f"{uid}/threads", data=create)
    cid = container["id"]
    for _ in range(6):
        try:
            if threads_api("GET", cid, params={"fields": "status"}).get("status") == "FINISHED":
                break
        except Exception:
            pass
        time.sleep(5)
    return threads_api("POST", f"{uid}/threads_publish", data={"creation_id": cid})["id"]


def post_to_threads(draft: dict) -> dict:
    """本文を投稿し、リプ欄をセルフリプライする"""
    if not (CONFIG["THREADS_USER_ID"] and CONFIG["THREADS_ACCESS_TOKEN"]):
        raise ValueError("Threads APIの認証情報が未設定です。")
    post_id = _publish(draft["text"])
    reply_id = None
    if draft.get("comment_text"):
        try:
            time.sleep(CONFIG["SELF_REPLY_DELAY_SEC"])
            reply_id = _publish(draft["comment_text"], reply_to=post_id)
        except Exception as e:
            print(f"    ⚠️ セルフリプライ失敗（本文は投稿済み）: {e}")
    return {"post_id": post_id, "reply_id": reply_id}


# ════════════════════════════════════════════════════════
#  履歴
# ════════════════════════════════════════════════════════

def load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(history: list):
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def posted_today(history: list) -> int:
    today = date.today().isoformat()
    return sum(1 for h in history if (h.get("posted_at", "")[:10] == today))


# ════════════════════════════════════════════════════════
#  1本の自動投稿（生成→検査→投稿→記録）
# ════════════════════════════════════════════════════════

def auto_post_one(dry_run: bool = False, use_sample: bool = False,
                  max_retries: int = 3) -> dict | None:
    history = load_history()

    if CONFIG["DAILY_LIMIT"] and posted_today(history) >= CONFIG["DAILY_LIMIT"] and not dry_run:
        print(f"  ⏸ 本日の投稿上限（{CONFIG['DAILY_LIMIT']}本）に到達。スキップ。")
        return None

    draft = None
    for attempt in range(1, max_retries + 1):
        candidate = sample_draft() if use_sample else generate_one_draft()
        ok, reason = vet_draft(candidate, history)
        if ok:
            draft = candidate
            break
        print(f"  ↻ 試行{attempt}: 不合格（{reason}）→ 再生成")
        if use_sample:  # サンプルは再生成しても同じなので打ち切り
            break
    if not draft:
        print("  ❌ 安全チェックを通る投稿を生成できませんでした。")
        return None

    print(f"  ┌─ [{draft['post_type']}]")
    print(f"  │ {draft['hook_line']}")
    print(f"  │ 本文 {len(draft['text'])}字 / リプ欄 {len(draft['comment_text'])}字")
    print(f"  └{'─' * 40}")

    if dry_run:
        print("  🧪 dry-run: 投稿はしません。\n")
        print(draft["text"])
        print("  --- リプ欄 ---")
        print(draft["comment_text"])
        return draft

    result = post_to_threads(draft)
    draft.update({
        "status": "posted",
        "posted_at": datetime.now().isoformat(),
        "post_id": result["post_id"],
        "reply_id": result.get("reply_id"),
    })
    history.insert(0, draft)
    save_history(history)
    print(f"  ✅ 投稿完了 post_id={result['post_id']} reply_id={result.get('reply_id')}")
    return draft


# ════════════════════════════════════════════════════════
#  スケジューラ（最適時間帯にループ投稿）
# ════════════════════════════════════════════════════════

def _seconds_until_next_slot() -> tuple[float, str]:
    from datetime import timedelta
    now = datetime.now()
    today_slots = []
    for s in CONFIG["POST_SLOTS"]:
        hh, mm = map(int, s.split(":"))
        today_slots.append(now.replace(hour=hh, minute=mm, second=0, microsecond=0))
    future = [t for t in today_slots if t > now]
    # 今日に残り枠があればその最初、なければ明日の最初の枠
    target = future[0] if future else today_slots[0] + timedelta(days=1)
    return (target - now).total_seconds(), target.strftime("%m/%d %H:%M")


def run_loop():
    print("🤖 全自動投稿モード開始（Ctrl+Cで停止）")
    print(f"   時間帯: {', '.join(CONFIG['POST_SLOTS'])} / 1日上限: {CONFIG['DAILY_LIMIT']}本")
    while True:
        wait, when = _seconds_until_next_slot()
        print(f"\n💤 次の投稿予定: {when}（約{int(wait/60)}分後）")
        try:
            time.sleep(max(wait, 1))
        except KeyboardInterrupt:
            print("\n停止しました。")
            return
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} 投稿サイクル")
        try:
            auto_post_one()
        except Exception as e:
            print(f"  ❌ 投稿サイクルでエラー: {e}")
        time.sleep(60)  # 同一スロットでの二重実行防止


# ════════════════════════════════════════════════════════
#  エントリポイント
# ════════════════════════════════════════════════════════

def load_dotenv():
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    for key in ("THREADS_ACCESS_TOKEN", "THREADS_USER_ID", "ANTHROPIC_API_KEY"):
        CONFIG[key] = os.getenv(key, CONFIG[key])


def main(argv=None):
    load_dotenv()
    ap = argparse.ArgumentParser(description="Threads 全自動投稿アプリ")
    ap.add_argument("--now", action="store_true", help="今すぐ投稿する")
    ap.add_argument("--loop", action="store_true", help="最適時間帯に自動投稿し続ける")
    ap.add_argument("--count", type=int, default=1, help="--now時に投稿する本数")
    ap.add_argument("--dry-run", action="store_true", help="投稿せず生成結果のみ表示")
    ap.add_argument("--sample", action="store_true", help="APIなしでパイプライン動作確認")
    args = ap.parse_args(argv)

    print("=" * 56)
    print("  Threads × AI 全自動投稿アプリ (autopost)")
    print("=" * 56)
    print(f"  Claude API : {'設定済み' if CONFIG['ANTHROPIC_API_KEY'] else '未設定'}")
    print(f"  Threads API: {'設定済み' if CONFIG['THREADS_ACCESS_TOKEN'] else '未設定'}")
    print("=" * 56)

    if args.loop:
        run_loop()
        return 0

    if args.now or args.dry_run or args.sample:
        n = max(1, args.count)
        for i in range(n):
            print(f"\n[{i+1}/{n}]")
            try:
                auto_post_one(dry_run=args.dry_run, use_sample=args.sample)
            except Exception as e:
                print(f"  ❌ エラー: {e}")
                return 1
            if not args.dry_run and i < n - 1:
                print(f"  …次の投稿まで{CONFIG['POST_INTERVAL_SEC']}秒待機")
                time.sleep(CONFIG["POST_INTERVAL_SEC"])
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
