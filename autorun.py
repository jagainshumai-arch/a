"""Threads × AI 完全自動化パイプライン（スタンドアロン版）

リサーチ → 分析 → 投稿作成 → Threads投稿 → インサイト取得 → スーパーバイザー
の全6ステップを自動実行する。

使い方:
  1. .envファイルにAPIキーを設定（autorun.bat が自動読み込み）
  2. autorun.bat をダブルクリックで実行
"""

import json
import os
import time
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

# ════════════════════════════════════════════════════════
#  設定（ここを自分の情報に書き換える）
# ════════════════════════════════════════════════════════

CONFIG = {
    # Threads API（.envファイルまたは環境変数で設定）
    "THREADS_ACCESS_TOKEN": os.getenv("THREADS_ACCESS_TOKEN", ""),
    "THREADS_USER_ID": os.getenv("THREADS_USER_ID", ""),

    # Anthropic API（.envファイルまたは環境変数で設定）
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "AI_MODEL": "claude-sonnet-4-20250514",

    # パイプライン設定
    "NICHE": "AI活用 × 気づき・知見・効率化",
    "TARGET": "AIに興味はあるが活かしきれていない20〜40代の会社員・フリーランス",
    "POSTS_PER_CYCLE": 3,          # 1サイクルで投稿する本数
    "POST_INTERVAL_SEC": 300,      # 投稿間隔（秒）= 5分
    "CYCLE_INTERVAL_MIN": 60,      # サイクル間隔（分）
    "MAX_CYCLES": 1,               # 実行サイクル数（0=無限ループ）

    # データ保存先
    "DATA_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "threads_automation", "data"),
    "KNOWLEDGE_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "threads_automation", "knowledge"),
}

# ════════════════════════════════════════════════════════
#  ナレッジ読み込み
# ════════════════════════════════════════════════════════

def load_knowledge():
    """knowledgeディレクトリから全ナレッジを読み込む"""
    kdir = CONFIG["KNOWLEDGE_DIR"]
    if not os.path.isdir(kdir):
        return ""
    parts = []
    for fname in sorted(os.listdir(kdir)):
        if fname.endswith(".md"):
            with open(os.path.join(kdir, fname), encoding="utf-8") as f:
                parts.append(f.read())
    return "\n\n---\n\n".join(parts)

# ════════════════════════════════════════════════════════
#  Claude API
# ════════════════════════════════════════════════════════

def call_claude(prompt, system="", max_tokens=1500):
    """Claude APIを呼び出す"""
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

    with urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        return data["content"][0]["text"]

# ════════════════════════════════════════════════════════
#  Threads API
# ════════════════════════════════════════════════════════

def threads_api(method, endpoint, params=None, data=None):
    """Threads Graph APIリクエスト"""
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


def threads_post(text):
    """Threadsにテキスト投稿する（2ステップ）"""
    uid = CONFIG["THREADS_USER_ID"]

    # Step 1: コンテナ作成
    container = threads_api("POST", f"{uid}/threads", data={
        "media_type": "TEXT",
        "text": text,
    })
    container_id = container["id"]
    print(f"    コンテナ作成: {container_id}")

    # 処理待ち
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
    return result["id"]


def threads_get_posts(limit=25):
    """自分の投稿一覧を取得"""
    uid = CONFIG["THREADS_USER_ID"]
    result = threads_api("GET", f"{uid}/threads", params={
        "fields": "id,text,timestamp,permalink",
        "limit": str(limit),
    })
    return result.get("data", [])


def threads_get_insights(post_id):
    """投稿のインサイトを取得"""
    result = threads_api("GET", f"{post_id}/insights", params={
        "metric": "views,likes,replies,reposts,quotes",
    })
    insights = {"post_id": post_id, "views": 0, "likes": 0, "replies": 0, "reposts": 0, "quotes": 0}
    for item in result.get("data", []):
        name = item.get("name", "")
        values = item.get("values", [{}])
        value = values[0].get("value", 0) if values else 0
        if name in insights:
            insights[name] = value
    return insights

# ════════════════════════════════════════════════════════
#  データ保存/読み込み
# ════════════════════════════════════════════════════════

def save_json(filename, data):
    os.makedirs(CONFIG["DATA_DIR"], exist_ok=True)
    path = os.path.join(CONFIG["DATA_DIR"], filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_json(filename):
    path = os.path.join(CONFIG["DATA_DIR"], filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

# ════════════════════════════════════════════════════════
#  Step 1: フェッチ（インサイト取得）
# ════════════════════════════════════════════════════════

def step_fetch():
    print("\n  [1/6] 📊 インサイト取得（Fetcher）")
    print("  " + "-" * 50)

    posts = threads_get_posts(limit=20)
    all_insights = []

    for p in posts:
        try:
            ins = threads_get_insights(p["id"])
            ins["text"] = p.get("text", "")
            ins["timestamp"] = p.get("timestamp", "")
            ins["permalink"] = p.get("permalink", "")
            all_insights.append(ins)

            er = (ins["likes"] + ins["replies"] + ins["reposts"]) / max(ins["views"], 1) * 100
            tag = "🔥" if ins["views"] > 10000 else "✅" if ins["views"] > 3000 else "⚠️" if ins["views"] > 500 else "❌"
            line1 = ins["text"].split("\n")[0][:35] if ins["text"] else ""
            print(f"    {tag} views={ins['views']:>6,}  likes={ins['likes']:>3}  ER={er:.1f}%  {line1}")
        except Exception as e:
            print(f"    ⚠️ {p['id']}: {e}")

    save_json("insights_history.json", all_insights)
    print(f"  ✅ {len(all_insights)}件のインサイトを取得・保存")
    return all_insights

# ════════════════════════════════════════════════════════
#  Step 2: 分析（Analyst）
# ════════════════════════════════════════════════════════

def step_analyze(insights):
    print("\n  [2/6] 📈 パフォーマンス分析（Analyst）")
    print("  " + "-" * 50)

    if not insights:
        print("  ⚠️ 分析対象の投稿がありません")
        return [], []

    for ins in insights:
        views = max(ins.get("views", 1), 1)
        ins["er"] = (ins.get("likes", 0) + ins.get("replies", 0) + ins.get("reposts", 0)) / views * 100

    insights.sort(key=lambda x: x["er"], reverse=True)
    avg_er = sum(i["er"] for i in insights) / len(insights)

    top = [i for i in insights if i.get("views", 0) > 3000]
    low = [i for i in insights if i.get("views", 0) < 1000 and i.get("likes", 0) < 10]

    print(f"  平均ER: {avg_er:.2f}%  |  投稿数: {len(insights)}")
    print(f"  🏆 高パフォーマンス: {len(top)}件")
    print(f"  ❌ 低パフォーマンス: {len(low)}件")

    # 低パフォーマンス投稿のAI分析
    if low:
        print("  🤖 失敗要因をClaude APIで分析中...")
        for p in low[:3]:
            try:
                analysis = call_claude(
                    f"以下のThreads投稿が伸びませんでした。失敗の原因を3つ、各1行で簡潔に。\n\n"
                    f"投稿文: {p.get('text', '')}\nviews: {p.get('views', 0)}  likes: {p.get('likes', 0)}",
                    max_tokens=300,
                )
                print(f"    📋 分析: {p.get('text', '')[:30]}...")
                for line in analysis.strip().split("\n")[:3]:
                    if line.strip():
                        print(f"       {line.strip()}")
            except Exception as e:
                print(f"    ⚠️ AI分析エラー: {e}")

    return top, low

# ════════════════════════════════════════════════════════
#  Step 3: リサーチ（Researcher）
# ════════════════════════════════════════════════════════

def step_research(top_posts):
    print("\n  [3/6] 🔍 トレンドリサーチ（Researcher）")
    print("  " + "-" * 50)

    competitor_data = load_json("competitor_posts.json")
    if competitor_data:
        print(f"  競合データ: {len(competitor_data)}件読み込み")

    top_texts = [p.get("text", "")[:200] for p in top_posts[:5]]

    print("  🤖 Claude APIでトレンド分析中...")
    try:
        raw = call_claude(f"""あなたはThreads×AI運用の専門家です。

【ニッチ】{CONFIG['NICHE']}
【ターゲット】{CONFIG['TARGET']}
【高パフォーマンス投稿】{json.dumps(top_texts, ensure_ascii=False)}

今すぐThreadsに投稿すべきトピック5つと切り口3つを提案。
JSON形式のみで出力:
{{"trending_topics": ["...", "..."], "recommended_angles": ["...", "..."], "analysis": "30文字以内"}}""",
            max_tokens=500)

        start = raw.find("{")
        end = raw.rfind("}") + 1
        research = json.loads(raw[start:end]) if start >= 0 else {"trending_topics": [], "recommended_angles": []}
    except Exception as e:
        print(f"  ⚠️ リサーチエラー: {e}")
        research = {"trending_topics": ["ChatGPT活用術", "AI時短テクニック", "Claude vs ChatGPT"],
                    "recommended_angles": ["発見・驚き型", "Before/After型", "小技・裏ワザ型"]}

    print("  🔥 トレンドトピック:")
    for i, t in enumerate(research.get("trending_topics", []), 1):
        print(f"     {i}. {t}")
    print("  💡 おすすめの切り口:")
    for i, a in enumerate(research.get("recommended_angles", []), 1):
        print(f"     {i}. {a}")

    save_json(f"research_report_{datetime.now().strftime('%Y%m%d')}.json", research)
    return research

# ════════════════════════════════════════════════════════
#  Step 4: 投稿作成（Writer）
# ════════════════════════════════════════════════════════

def step_compose(research):
    print("\n  [4/6] ✍️  投稿作成（Writer）")
    print("  " + "-" * 50)

    knowledge = load_knowledge()
    system_prompt = f"""あなたはThreads投稿の専門家です。以下のナレッジを参照して投稿を作成してください。

=== ナレッジ（重要部分のみ） ===
{knowledge[:4000]}
=== ここまで ===

【最重要：タップ経済の原則】
1行目で全てが決まる。必ず「固有名詞」（ChatGPT/Claude/Perplexity等）と「数字」を入れること。

【ルール】
1. 1行目は固有名詞+数字でベネフィット提示
2. 気づき→理由→具体例→結論で構成
3. 150〜300文字
4. AIっぽい表現禁止（「〇〇だと思っていませんか？」「いかがでしたか？」等）
5. 具体的な数字・体験を入れる
6. ハッシュタグは末尾に2〜3個
7. 売上・収益・稼ぐ・副業の話は一切禁止
8. 等身大の体験・気づきトーンで書く"""

    topics = research.get("trending_topics", []) + research.get("recommended_angles", [])
    post_types = ["benefit", "list", "story", "how_to", "before_after"]
    count = CONFIG["POSTS_PER_CYCLE"]

    drafts = []
    print(f"  🤖 Claude APIで{count}本の投稿を生成中...\n")

    for i in range(min(count, len(topics) if topics else count)):
        topic = topics[i] if i < len(topics) else f"{CONFIG['NICHE']}について"
        pt = post_types[i % len(post_types)]

        try:
            raw = call_claude(f"""以下の条件でThreads投稿を1つ作成。

トピック: {topic}
ターゲット: {CONFIG['TARGET']}
投稿タイプ: {pt}

JSON形式のみで出力:
{{"hook_line": "1行目", "full_text": "投稿全文"}}""",
                system=system_prompt, max_tokens=500)

            start = raw.find("{")
            end = raw.rfind("}") + 1
            parsed = json.loads(raw[start:end])

            draft = {
                "text": parsed["full_text"],
                "topic": topic,
                "post_type": pt,
                "hook_line": parsed["hook_line"],
                "created_at": datetime.now().isoformat(),
            }
            drafts.append(draft)

            print(f"  ┌─── 投稿 {i+1} [{pt}] ───")
            print(f"  │ フック: {parsed['hook_line']}")
            for line in parsed["full_text"].split("\n"):
                print(f"  │ {line}")
            print(f"  │ 文字数: {len(parsed['full_text'])}字")
            print(f"  └{'─' * 45}\n")
        except Exception as e:
            print(f"  ⚠️ 投稿{i+1}生成エラー: {e}")

    save_json(f"drafts_{datetime.now().strftime('%Y%m%d_%H%M')}.json", drafts)
    print(f"  ✅ {len(drafts)}本の下書きを生成")
    return drafts

# ════════════════════════════════════════════════════════
#  Step 5: Threads投稿（Poster）
# ════════════════════════════════════════════════════════

def step_post(drafts):
    print("\n  [5/6] 📤 投稿公開（Poster）")
    print("  " + "-" * 50)

    published = []
    for i, draft in enumerate(drafts):
        try:
            post_id = threads_post(draft["text"])
            entry = {
                "post_id": post_id,
                "text": draft["text"],
                "topic": draft.get("topic", ""),
                "post_type": draft.get("post_type", ""),
                "hook_line": draft.get("hook_line", ""),
                "published_at": datetime.now().isoformat(),
            }
            published.append(entry)
            print(f"  ✅ 投稿{i+1} 公開完了: {post_id}")

            # 投稿間隔を空ける（最後以外）
            if i < len(drafts) - 1:
                wait = CONFIG["POST_INTERVAL_SEC"]
                print(f"     次の投稿まで{wait}秒待機...")
                time.sleep(wait)
        except Exception as e:
            print(f"  ❌ 投稿{i+1} 失敗: {e}")

    # 履歴に追加保存
    history = load_json("publish_history.json")
    history.extend(published)
    save_json("publish_history.json", history)

    print(f"\n  ✅ {len(published)}/{len(drafts)}件の投稿を公開")
    return published

# ════════════════════════════════════════════════════════
#  Step 6: スーパーバイザーレポート
# ════════════════════════════════════════════════════════

def step_supervisor(insights, top, low, research, drafts, published):
    print("\n  [6/6] 🎯 スーパーバイザーレポート")
    print("  " + "-" * 50)

    avg_er = sum(i.get("er", 0) for i in insights) / max(len(insights), 1) if insights else 0
    low_rate = len(low) / max(len(insights), 1) * 100 if insights else 0

    print()
    print("  ┌──────────────────────────────────────────┐")
    print("  │          サイクル完了サマリー              │")
    print("  ├──────────────────┬───────┬────────────────┤")
    print(f"  │ 分析した投稿     │ {len(insights):>5} │ ─              │")
    print(f"  │ 高パフォーマンス │ {len(top):>5} │ ─              │")
    print(f"  │ 低パフォーマンス │ {len(low):>5} │ {'✅ 正常' if len(low) < 3 else '⚠️  要改善'}         │")
    print(f"  │ 平均ER           │ {avg_er:>4.1f}% │ {'✅ 良好' if avg_er > 2 else '⚠️  要改善'}         │")
    print(f"  │ 生成した下書き   │ {len(drafts):>5} │ ─              │")
    print(f"  │ 投稿公開         │ {len(published):>5} │ ✅ 完了         │")
    print("  └──────────────────┴───────┴────────────────┘")

    # AI による次回アクション提案
    print("\n  🤖 次回アクション提案:")
    try:
        suggestion = call_claude(
            f"Threads運用のスーパーバイザーとして、以下の状況から次にやるべきことを3つ提案（各1行）。\n\n"
            f"平均ER: {avg_er:.2f}%、高パフォ: {len(top)}件、低パフォ: {len(low)}件、"
            f"今回投稿: {len(published)}件、トレンド: {json.dumps(research.get('trending_topics', [])[:3], ensure_ascii=False)}",
            max_tokens=200,
        )
        for line in suggestion.strip().split("\n")[:5]:
            if line.strip():
                print(f"     {line.strip()}")
    except Exception as e:
        print(f"     ⚠️ 提案生成エラー: {e}")

    # レポート保存
    report = {
        "cycle_time": datetime.now().isoformat(),
        "niche": CONFIG["NICHE"],
        "target": CONFIG["TARGET"],
        "posts_analyzed": len(insights),
        "avg_er": round(avg_er, 2),
        "top_performers": len(top),
        "low_performers": len(low),
        "drafts_generated": len(drafts),
        "posts_published": len(published),
        "published_ids": [p["post_id"] for p in published],
        "trending_topics": research.get("trending_topics", []),
    }
    os.makedirs(os.path.join(CONFIG["DATA_DIR"], "reports"), exist_ok=True)
    report_path = os.path.join(CONFIG["DATA_DIR"], "reports",
                               f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 レポート保存: {report_path}")

# ════════════════════════════════════════════════════════
#  メインパイプライン
# ════════════════════════════════════════════════════════

def run_cycle():
    """1サイクル分のパイプラインを実行"""
    print()
    print("=" * 60)
    print("  Threads × AI 完全自動パイプライン")
    print("=" * 60)
    print(f"  ニッチ      : {CONFIG['NICHE']}")
    print(f"  ターゲット  : {CONFIG['TARGET']}")
    print(f"  投稿数/回   : {CONFIG['POSTS_PER_CYCLE']}本")
    print(f"  開始時刻    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: フェッチ
    insights = step_fetch()

    # Step 2: 分析
    top, low = step_analyze(insights)

    # Step 3: リサーチ
    research = step_research(top)

    # Step 4: 投稿作成
    drafts = step_compose(research)

    # Step 5: 投稿公開
    published = step_post(drafts)

    # Step 6: スーパーバイザー
    step_supervisor(insights, top, low, research, drafts, published)

    print("\n" + "=" * 60)
    print("  パイプライン完了")
    print("=" * 60)


def main():
    print("╔══════════════════════════════════════════════╗")
    print("║  Threads × AI 完全自動化システム 起動        ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"  サイクル数: {CONFIG['MAX_CYCLES'] or '無限ループ'}")
    print(f"  間隔: {CONFIG['CYCLE_INTERVAL_MIN']}分")

    cycle = 0
    max_cycles = CONFIG["MAX_CYCLES"]

    while max_cycles == 0 or cycle < max_cycles:
        cycle += 1
        print(f"\n{'━' * 60}")
        print(f"  サイクル {cycle} 開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'━' * 60}")

        try:
            run_cycle()
        except Exception as e:
            print(f"\n  ❌ サイクル{cycle}でエラー: {e}")
            import traceback
            traceback.print_exc()

        if max_cycles == 0 or cycle < max_cycles:
            wait = CONFIG["CYCLE_INTERVAL_MIN"] * 60
            print(f"\n  💤 次のサイクルまで{CONFIG['CYCLE_INTERVAL_MIN']}分待機...")
            time.sleep(wait)

    print(f"\n✅ 全{cycle}サイクル完了")


if __name__ == "__main__":
    main()
