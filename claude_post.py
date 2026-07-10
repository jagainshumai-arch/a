"""Claude Code × Threads 自動投稿（シロウ式：運用をClaude Codeに任せる）

autopost.py は Anthropic API を1回叩いて生成するが、こちらは `claude` CLI を
ヘッドレス（`claude -p`）で実行し、**フルのClaude Codeエージェント**にナレッジ・
テンプレ・themes を読み込ませて投稿を作らせる。生成の「頭脳」がClaude Code、
安全チェックと投稿の「手」を autopost.py の関数が担う。

    ┌─────────────┐   生成(JSON)   ┌──────────────┐  投稿  ┌─────────┐
    │ claude CLI  │ ─────────────▶ │ 安全チェック  │ ─────▶ │ Threads │
    │ (-p ヘッドレス)│ ナレッジ参照   │ (autopost)   │ 本文+リプ│  API    │
    └─────────────┘                └──────────────┘        └─────────┘

前提:
  - `claude` CLI がインストール＆ログイン済み（`npm i -g @anthropic-ai/claude-code`）
  - .env に THREADS_ACCESS_TOKEN / THREADS_USER_ID（ANTHROPIC_API_KEYはCLI側で使用）

使い方:
  python claude_post.py --dry-run     # Claude Codeに生成させて表示（投稿しない）
  python claude_post.py --now         # 生成→安全チェック→Threadsへ投稿
  python claude_post.py --draft       # 生成して下書き保存（webappの「下書き」に出る）
  python claude_post.py --now --allow-fallback   # claude CLIが無ければAPI生成に切替
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

import autopost  # 安全チェック・投稿・履歴・.env読込を再利用

autopost.load_dotenv()


# ════════════════════════════════════════════════════════
#  Claude Code（ヘッドレス）に投稿を生成させる
# ════════════════════════════════════════════════════════

GEN_PROMPT = """あなたはこのリポジトリのThreads運用担当（ポスター）です。以下を厳密に実行してください。

【手順】
1. 次のナレッジを Read で読む:
   - threads_automation/knowledge/2_writing/16_buzz_templates.md（フック型・拡散フォーマット・締め型）
   - threads_automation/knowledge/2_writing/06_references.md（具体例の型）
   - threads_automation/knowledge/5_buzz/patterns.md（勝ちパターン）
   - threads_automation/knowledge/5_buzz/themes.md（今伸びるテーマ＝あれば最優先）
   - threads_automation/knowledge/07_ng-rules.md（NG・景表法・ハッシュタグ禁止）
   - threads_automation/knowledge/1_identity/ 配下（ペルソナ・ターゲット）
2. ペルソナ「AIで実際に稼いでいる情報系の大学生（主語は僕/自分・フランク）」で、
   ターゲット「AIで稼ぎたい10代後半〜20代」向けにThreads投稿を1本作る。
3. themes.md に候補があればそのテーマを優先（＝需要の答え合わせ）。
   1行目のフック・本文の型・締めは 16_buzz_templates.md に沿う。
4. 構造（タップ経済）:
   - 本文300〜500字。1行目に固有名詞＋数字。核心はチラ見せし「リプ欄に書いた↓」で終わる
   - リプ欄200〜400字。一番有益な手順/プロンプト/裏ワザ＋最後に返信を誘う質問
5. 厳守: ハッシュタグ(#)禁止 / 景表法NG（確実に稼げる等）禁止 / AI感のある定型禁止

【出力】
説明・前置き・コードブロックを一切付けず、次のJSONオブジェクトだけを出力してください:
{"hook_line": "選んだ1行目", "text": "本文", "comment_text": "リプ欄", "post_type": "型名"}
"""


def claude_cli_available() -> bool:
    return shutil.which("claude") is not None


# 生成は読み取り専用ツールだけで足りる（投稿は autopost 側が行う）。
# 読み取りツールのみ許可すれば、ヘッドレスでも権限プロンプトで止まらず、安全。
READONLY_TOOLS = ["Read", "Grep", "Glob"]


def generate_with_claude_code(model: str | None = None,
                              timeout: int = 240) -> dict:
    """`claude -p` をヘッドレス実行し、投稿JSONを受け取る。"""
    if not claude_cli_available():
        raise FileNotFoundError(
            "`claude` CLI が見つかりません。\n"
            "  インストール: npm install -g @anthropic-ai/claude-code\n"
            "  ログイン    : claude （初回に認証）\n"
            "  または python claude_post.py --now --allow-fallback でAPI生成に切替")

    # プロンプトは標準入力から渡す（巨大＆改行・引用符を含むため、引数に載せない）。
    # 引数側には特殊文字が無いので、Windowsの .cmd シムも shell 経由で安全に起動できる。
    exe = shutil.which("claude") or "claude"
    args = ["-p", "--output-format", "json", "--allowedTools", *READONLY_TOOLS]
    if model:
        args += ["--model", model]

    run_kwargs = dict(input=GEN_PROMPT, cwd=str(autopost.BASE_DIR),
                      capture_output=True, text=True, timeout=timeout,
                      encoding="utf-8")
    if os.name == "nt":
        # npm製の claude は claude.cmd（バッチ）。CreateProcessで直接起動できないため
        # shell経由で実行する。引数に特殊文字は無く、プロンプトはstdinなので安全。
        cmdline = " ".join([f'"{exe}"'] + args)
        proc = subprocess.run(cmdline, shell=True, **run_kwargs)
    else:
        proc = subprocess.run([exe] + args, **run_kwargs)
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI がエラー終了(code={proc.returncode}):\n"
                           f"{(proc.stderr or '')[:500]}")

    raw = proc.stdout.strip()
    # `--output-format json` は {"type":"result","result":"<本文>", ...} を返す。
    # result（Claude Codeの最終テキスト）を取り出してから、その中のJSONを抽出する。
    try:
        wrapper = json.loads(raw)
        if isinstance(wrapper, dict) and "result" in wrapper:
            raw = wrapper["result"]
    except json.JSONDecodeError:
        pass  # 素のテキストが返ってきた場合はそのまま扱う

    start, end = raw.find("{"), raw.rfind("}") + 1
    if start < 0 or end <= 0:
        raise ValueError(f"Claude Codeの出力からJSONを抽出できません:\n{raw[:300]}")
    p = json.loads(raw[start:end])
    return {
        "id": _short_id(),
        "hook_line": p.get("hook_line", ""),
        "text": (p.get("text") or p.get("full_text") or "").strip(),
        "comment_text": (p.get("comment_text") or "").strip(),
        "post_type": p.get("post_type", "claude-code"),
        "generated_by": "claude-code",
    }


def _short_id() -> str:
    import uuid
    return str(uuid.uuid4())[:8]


# ════════════════════════════════════════════════════════
#  1本の生成→検査→投稿（autopost の安全装置を再利用）
# ════════════════════════════════════════════════════════

def run_once(dry_run: bool = False, save_draft: bool = False,
             model: str | None = None, allow_fallback: bool = False,
             max_retries: int = 3) -> dict | None:
    history = autopost.load_history()

    # 1日の上限チェック（実投稿時のみ）
    if (not dry_run and not save_draft and autopost.CONFIG["DAILY_LIMIT"]
            and autopost.posted_today(history) >= autopost.CONFIG["DAILY_LIMIT"]):
        print(f"  ⏸ 本日の投稿上限（{autopost.CONFIG['DAILY_LIMIT']}本）に到達。スキップ。")
        return None

    draft = None
    for attempt in range(1, max_retries + 1):
        try:
            candidate = generate_with_claude_code(model=model)
        except FileNotFoundError:
            if allow_fallback:
                print("  ↪ claude CLI 未検出 → autopost のAPI生成にフォールバック")
                candidate = autopost.generate_one_draft()
            else:
                raise
        ok, reason = autopost.vet_draft(candidate, history)
        if ok:
            draft = candidate
            break
        print(f"  ↻ 試行{attempt}: 不合格（{reason}）→ 再生成")
    if not draft:
        print("  ❌ 安全チェックを通る投稿を生成できませんでした。")
        return None

    src = draft.get("generated_by", "claude-code")
    print(f"  ┌─ [{draft['post_type']}]  (生成: {src})")
    print(f"  │ {draft['hook_line']}")
    print(f"  │ 本文 {len(draft['text'])}字 / リプ欄 {len(draft['comment_text'])}字")
    print(f"  └{'─' * 40}")

    if dry_run:
        print("  🧪 dry-run: 投稿しません。\n")
        print(draft["text"])
        print("  --- リプ欄 ---")
        print(draft["comment_text"])
        return draft

    if save_draft:
        drafts = autopost.load_drafts()
        draft.update({"status": "draft", "created_at": datetime.now().isoformat()})
        autopost.save_drafts([draft] + drafts)
        print("  💾 下書き保存しました（webappの「下書き」から確認・投稿できます）。")
        return draft

    result = autopost.post_to_threads(draft)
    draft.update({
        "status": "posted",
        "posted_at": datetime.now().isoformat(),
        "post_id": result["post_id"],
        "reply_id": result.get("reply_id"),
    })
    history.insert(0, draft)
    autopost.save_history(history)
    print(f"  ✅ 投稿完了 post_id={result['post_id']} reply_id={result.get('reply_id')}")
    return draft


# ════════════════════════════════════════════════════════
#  エントリポイント
# ════════════════════════════════════════════════════════

def main(argv=None):
    ap = argparse.ArgumentParser(description="Claude Code × Threads 自動投稿")
    ap.add_argument("--now", action="store_true", help="生成→安全チェック→投稿")
    ap.add_argument("--dry-run", action="store_true", help="生成だけして表示（投稿しない）")
    ap.add_argument("--draft", action="store_true", help="生成して下書き保存（投稿しない）")
    ap.add_argument("--count", type=int, default=1, help="--now時の投稿本数")
    ap.add_argument("--model", default=None, help="claude CLIに渡すモデル（任意）")
    ap.add_argument("--allow-fallback", action="store_true",
                    help="claude CLIが無ければ autopost のAPI生成に切り替える")
    args = ap.parse_args(argv)

    print("=" * 56)
    print("  Claude Code × Threads 自動投稿 (claude_post)")
    print("=" * 56)
    print(f"  claude CLI : {'検出' if claude_cli_available() else '未検出'}")
    print(f"  Threads API: {'設定済み' if autopost.CONFIG['THREADS_ACCESS_TOKEN'] else '未設定'}")
    print(f"  投稿時間帯 : {', '.join(autopost.CONFIG['POST_SLOTS'])} / 1日上限 {autopost.CONFIG['DAILY_LIMIT']}本")
    print("=" * 56)

    if not (args.now or args.dry_run or args.draft):
        ap.print_help()
        return 0

    n = max(1, args.count) if args.now else 1
    for i in range(n):
        print(f"\n[{i+1}/{n}]")
        try:
            run_once(dry_run=args.dry_run, save_draft=args.draft,
                     model=args.model, allow_fallback=args.allow_fallback)
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return 1
        if args.now and i < n - 1:
            import time
            print(f"  …次の投稿まで{autopost.CONFIG['POST_INTERVAL_SEC']}秒待機")
            time.sleep(autopost.CONFIG["POST_INTERVAL_SEC"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
