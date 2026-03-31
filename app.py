"""Threads × AI 投稿管理アプリ

AIが自動で投稿を生成 → 人間がレビュー・編集 → 承認後にThreadsへ投稿

使い方:
  1. .env にAPIキーを設定
  2. pip install flask
  3. python app.py
  4. ブラウザで http://localhost:5000 を開く
"""

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

# ════════════════════════════════════════════════════════
#  設定
# ════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "threads_automation" / "knowledge"

DATA_DIR.mkdir(exist_ok=True)

DRAFTS_FILE = DATA_DIR / "drafts.json"
HISTORY_FILE = DATA_DIR / "history.json"

CONFIG = {
    "THREADS_ACCESS_TOKEN": os.getenv("THREADS_ACCESS_TOKEN", ""),
    "THREADS_USER_ID": os.getenv("THREADS_USER_ID", ""),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "AI_MODEL": os.getenv("AI_MODEL", "claude-sonnet-4-20250514"),
    "NICHE": "AI活用 × 気づき・知見・効率化",
    "TARGET": "AIに興味はあるが活かしきれていない20〜40代の会社員・フリーランス",
    "POSTS_PER_BATCH": 5,
}

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "threads-app-secret-key")

# ════════════════════════════════════════════════════════
#  ユーティリティ
# ════════════════════════════════════════════════════════


def load_json(path: Path) -> list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_knowledge() -> str:
    if not KNOWLEDGE_DIR.is_dir():
        return ""
    parts = []
    for f in sorted(KNOWLEDGE_DIR.iterdir()):
        if f.suffix == ".md":
            parts.append(f.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


# ════════════════════════════════════════════════════════
#  Claude API
# ════════════════════════════════════════════════════════


def call_claude(prompt: str, system: str = "", max_tokens: int = 1500) -> str:
    api_key = CONFIG["ANTHROPIC_API_KEY"]
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY が設定されていません。.env を確認してください。")

    body = json.dumps({
        "model": CONFIG["AI_MODEL"],
        "max_tokens": max_tokens,
        "system": system or "あなたはThreads投稿の専門家です。",
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = Request("https://api.anthropic.com/v1/messages", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")

    with urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        return data["content"][0]["text"]


# ════════════════════════════════════════════════════════
#  Threads API
# ════════════════════════════════════════════════════════


def threads_api(method: str, endpoint: str, params=None, data=None):
    base = "https://graph.threads.net/v1.0"
    url = f"{base}/{endpoint}"
    if params is None:
        params = {}
    params["access_token"] = CONFIG["THREADS_ACCESS_TOKEN"]

    if method == "GET":
        url = f"{url}?{urlencode(params)}"
        req = Request(url, method="GET")
    else:
        if data:
            data.update(params)
        else:
            data = params
        body = urlencode(data).encode()
        req = Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def threads_post(text: str) -> dict:
    """Threadsにテキスト投稿（2ステップ）"""
    uid = CONFIG["THREADS_USER_ID"]
    if not uid or not CONFIG["THREADS_ACCESS_TOKEN"]:
        raise ValueError("Threads APIの認証情報が設定されていません。")

    # Step 1: コンテナ作成
    container = threads_api("POST", f"{uid}/threads", data={
        "media_type": "TEXT",
        "text": text,
    })
    container_id = container["id"]

    # ステータス待ち
    for _ in range(6):
        try:
            status = threads_api("GET", container_id, params={"fields": "status"})
            if status.get("status") == "FINISHED":
                break
        except Exception:
            pass
        time.sleep(5)

    # Step 2: 公開
    result = threads_api("POST", f"{uid}/threads_publish", data={
        "creation_id": container_id,
    })
    return {"post_id": result["id"], "container_id": container_id}


# ════════════════════════════════════════════════════════
#  AI投稿生成
# ════════════════════════════════════════════════════════


def generate_drafts(count: int = None) -> list:
    """Claude APIでThreads投稿の下書きを一括生成"""
    if count is None:
        count = CONFIG["POSTS_PER_BATCH"]

    knowledge = load_knowledge()

    system_prompt = f"""あなたはThreads投稿の専門ライターです。以下のナレッジを厳密に参照して投稿を作成してください。

=== ナレッジ ===
{knowledge[:6000]}
=== ここまで ===

【最重要ルール】
- 1行目で全てが決まる。必ず「固有名詞」（ChatGPT/Claude/Perplexity/Gemini等）と「数字」を入れること
- 売上・収益・稼ぐ・副業の話は一切禁止
- 等身大の気づき・発見・効率化のトーンで書く
- AIっぽい表現禁止（「〇〇だと思っていませんか？」「いかがでしたか？」等）
- 150〜300文字
- ハッシュタグは末尾に2〜3個"""

    post_types = [
        "discovery（発見・驚き型）",
        "before_after（Before/After時短型）",
        "comparison（比較・実験型）",
        "tips（知らないと損する型）",
        "paradox（逆説・意外型）",
        "daily（日常の気づき型）",
        "tricks（小技・裏ワザ型）",
    ]

    prompt = f"""以下の条件でThreads投稿を{count}本作成してください。

ターゲット: {CONFIG['TARGET']}
ジャンル: {CONFIG['NICHE']}

投稿タイプを混ぜて作成:
{chr(10).join(f'- {pt}' for pt in post_types[:count])}

必ず以下のJSON配列のみを出力:
[
  {{"hook_line": "1行目のフック", "full_text": "投稿全文（ハッシュタグ含む）", "post_type": "タイプ名"}}
]

{count}本分の配列を出力してください。"""

    raw = call_claude(prompt, system=system_prompt, max_tokens=3000)

    # JSONを抽出
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start < 0 or end <= 0:
        raise ValueError(f"AI応答からJSONを抽出できません: {raw[:200]}")

    posts = json.loads(raw[start:end])

    drafts = []
    for p in posts:
        drafts.append({
            "id": str(uuid.uuid4())[:8],
            "hook_line": p.get("hook_line", ""),
            "text": p.get("full_text", ""),
            "post_type": p.get("post_type", ""),
            "char_count": len(p.get("full_text", "")),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "posted_at": None,
            "post_id": None,
        })

    return drafts


# ════════════════════════════════════════════════════════
#  ルーティング
# ════════════════════════════════════════════════════════


@app.route("/")
def index():
    """ダッシュボード"""
    drafts = load_json(DRAFTS_FILE)
    history = load_json(HISTORY_FILE)

    pending = [d for d in drafts if d["status"] == "pending"]
    approved = [d for d in drafts if d["status"] == "approved"]
    rejected = [d for d in drafts if d["status"] == "rejected"]

    return render_template("dashboard.html",
                           pending=pending,
                           approved=approved,
                           rejected=rejected,
                           history=history,
                           config=CONFIG)


@app.route("/generate", methods=["POST"])
def generate():
    """AI で投稿を生成"""
    count = int(request.form.get("count", CONFIG["POSTS_PER_BATCH"]))
    try:
        new_drafts = generate_drafts(count)
        drafts = load_json(DRAFTS_FILE)
        drafts.extend(new_drafts)
        save_json(DRAFTS_FILE, drafts)
        flash(f"{len(new_drafts)}件の下書きを生成しました", "success")
    except Exception as e:
        flash(f"生成エラー: {e}", "error")
    return redirect(url_for("index"))


@app.route("/approve/<draft_id>", methods=["POST"])
def approve(draft_id):
    """下書きを承認"""
    drafts = load_json(DRAFTS_FILE)
    for d in drafts:
        if d["id"] == draft_id:
            d["status"] = "approved"
            break
    save_json(DRAFTS_FILE, drafts)
    flash("承認しました", "success")
    return redirect(url_for("index"))


@app.route("/approve_all", methods=["POST"])
def approve_all():
    """全ての下書きを一括承認"""
    drafts = load_json(DRAFTS_FILE)
    count = 0
    for d in drafts:
        if d["status"] == "pending":
            d["status"] = "approved"
            count += 1
    save_json(DRAFTS_FILE, drafts)
    flash(f"{count}件を一括承認しました", "success")
    return redirect(url_for("index"))


@app.route("/reject/<draft_id>", methods=["POST"])
def reject(draft_id):
    """下書きを却下"""
    drafts = load_json(DRAFTS_FILE)
    for d in drafts:
        if d["id"] == draft_id:
            d["status"] = "rejected"
            break
    save_json(DRAFTS_FILE, drafts)
    flash("却下しました", "info")
    return redirect(url_for("index"))


@app.route("/edit/<draft_id>", methods=["POST"])
def edit(draft_id):
    """下書きを編集"""
    new_text = request.form.get("text", "").strip()
    if not new_text:
        flash("投稿文が空です", "error")
        return redirect(url_for("index"))

    drafts = load_json(DRAFTS_FILE)
    for d in drafts:
        if d["id"] == draft_id:
            d["text"] = new_text
            d["hook_line"] = new_text.split("\n")[0]
            d["char_count"] = len(new_text)
            d["edited"] = True
            break
    save_json(DRAFTS_FILE, drafts)
    flash("編集を保存しました", "success")
    return redirect(url_for("index"))


@app.route("/delete/<draft_id>", methods=["POST"])
def delete(draft_id):
    """下書きを削除"""
    drafts = load_json(DRAFTS_FILE)
    drafts = [d for d in drafts if d["id"] != draft_id]
    save_json(DRAFTS_FILE, drafts)
    flash("削除しました", "info")
    return redirect(url_for("index"))


@app.route("/post/<draft_id>", methods=["POST"])
def post_single(draft_id):
    """承認済み投稿を1件 Threads に公開"""
    drafts = load_json(DRAFTS_FILE)
    target = None
    for d in drafts:
        if d["id"] == draft_id and d["status"] == "approved":
            target = d
            break

    if not target:
        flash("承認済みの下書きが見つかりません", "error")
        return redirect(url_for("index"))

    try:
        result = threads_post(target["text"])
        target["status"] = "posted"
        target["posted_at"] = datetime.now().isoformat()
        target["post_id"] = result["post_id"]
        save_json(DRAFTS_FILE, drafts)

        # 履歴に追加
        history = load_json(HISTORY_FILE)
        history.insert(0, target)
        save_json(HISTORY_FILE, history)

        flash(f"投稿完了！ Post ID: {result['post_id']}", "success")
    except Exception as e:
        flash(f"投稿エラー: {e}", "error")

    return redirect(url_for("index"))


@app.route("/post_all", methods=["POST"])
def post_all():
    """承認済みを全件 Threads に一括公開"""
    drafts = load_json(DRAFTS_FILE)
    approved = [d for d in drafts if d["status"] == "approved"]

    if not approved:
        flash("承認済みの下書きがありません", "error")
        return redirect(url_for("index"))

    history = load_json(HISTORY_FILE)
    posted_count = 0
    errors = []

    for i, d in enumerate(approved):
        try:
            result = threads_post(d["text"])
            d["status"] = "posted"
            d["posted_at"] = datetime.now().isoformat()
            d["post_id"] = result["post_id"]
            history.insert(0, d)
            posted_count += 1

            # 投稿間隔（最後以外は5分待機）
            if i < len(approved) - 1:
                time.sleep(300)
        except Exception as e:
            errors.append(f"{d['id']}: {e}")

    save_json(DRAFTS_FILE, drafts)
    save_json(HISTORY_FILE, history)

    if posted_count > 0:
        flash(f"{posted_count}件を投稿しました", "success")
    if errors:
        flash(f"エラー: {'; '.join(errors)}", "error")

    return redirect(url_for("index"))


@app.route("/regenerate/<draft_id>", methods=["POST"])
def regenerate(draft_id):
    """1件だけ再生成"""
    drafts = load_json(DRAFTS_FILE)
    target = None
    for d in drafts:
        if d["id"] == draft_id:
            target = d
            break

    if not target:
        flash("下書きが見つかりません", "error")
        return redirect(url_for("index"))

    try:
        new = generate_drafts(1)[0]
        target["text"] = new["text"]
        target["hook_line"] = new["hook_line"]
        target["post_type"] = new["post_type"]
        target["char_count"] = new["char_count"]
        target["status"] = "pending"
        target["created_at"] = datetime.now().isoformat()
        save_json(DRAFTS_FILE, drafts)
        flash("再生成しました", "success")
    except Exception as e:
        flash(f"再生成エラー: {e}", "error")

    return redirect(url_for("index"))


@app.route("/clear_rejected", methods=["POST"])
def clear_rejected():
    """却下済みをクリア"""
    drafts = load_json(DRAFTS_FILE)
    drafts = [d for d in drafts if d["status"] != "rejected"]
    save_json(DRAFTS_FILE, drafts)
    flash("却下済みをクリアしました", "info")
    return redirect(url_for("index"))


@app.route("/api/status")
def api_status():
    """API接続ステータスを返す"""
    status = {
        "threads_configured": bool(CONFIG["THREADS_ACCESS_TOKEN"] and CONFIG["THREADS_USER_ID"]),
        "claude_configured": bool(CONFIG["ANTHROPIC_API_KEY"]),
    }

    if status["threads_configured"]:
        try:
            uid = CONFIG["THREADS_USER_ID"]
            profile = threads_api("GET", uid, params={"fields": "username,name"})
            status["threads_username"] = profile.get("username", "")
            status["threads_connected"] = True
        except Exception as e:
            status["threads_connected"] = False
            status["threads_error"] = str(e)

    return jsonify(status)


# ════════════════════════════════════════════════════════
#  メイン
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    # .env ファイルの簡易読み込み
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
        # .env読み込み後にCONFIGを再設定
        CONFIG["THREADS_ACCESS_TOKEN"] = os.getenv("THREADS_ACCESS_TOKEN", "")
        CONFIG["THREADS_USER_ID"] = os.getenv("THREADS_USER_ID", "")
        CONFIG["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")

    print("=" * 50)
    print("  Threads × AI 投稿管理アプリ")
    print("=" * 50)
    print(f"  Claude API: {'設定済み' if CONFIG['ANTHROPIC_API_KEY'] else '未設定'}")
    print(f"  Threads API: {'設定済み' if CONFIG['THREADS_ACCESS_TOKEN'] else '未設定'}")
    print(f"  ナレッジ: {KNOWLEDGE_DIR}")
    print(f"  データ: {DATA_DIR}")
    print("=" * 50)
    print("  http://localhost:5000 をブラウザで開いてください")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=True)
