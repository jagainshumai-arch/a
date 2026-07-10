"""Typefully 連携（予約投稿）

生成した投稿（本文＋リプ欄）を Typefully に「予約下書き」として送り、
Typefully のクラウド側でスケジュール投稿する。これにより自分のPCが
起動していなくても、決めた時間にThreadsへ自動投稿できる。

Typefully API v2 を使用（v1は2026-06-15で終了）。
  - 認証   : Authorization: Bearer <TYPEFULLY_API_KEY>
  - social : GET  /v2/social-sets              … 投稿先セット一覧
  - 下書き : POST /v2/social-sets/{id}/drafts   … 予約下書き作成

前提:
  1. Typefully の有料プラン（APIアクセス可）
  2. Typefully に Threads アカウントを連携済み
  3. .env に TYPEFULLY_API_KEY を設定（任意で TYPEFULLY_SOCIAL_SET_ID）

使い方（単体）:
  python typefully.py --check                 # 接続確認＆social set一覧
  python typefully.py --sample                # サンプル投稿を次の空き枠に予約
  python typefully.py --drafts                # data/drafts.json の下書きを全部 予約送信
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
API_BASE = "https://api.typefully.com/v2"


# ── 設定読み込み（autopost と同じ .env を共有） ──────────────
def load_dotenv():
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _api_key() -> str:
    key = os.getenv("TYPEFULLY_API_KEY", "").strip()
    if not key:
        raise ValueError("TYPEFULLY_API_KEY が未設定です。.env に追加してください。")
    return key


def is_configured() -> bool:
    return bool(os.getenv("TYPEFULLY_API_KEY", "").strip())


# ── 低レベルHTTP ──────────────────────────────────────────
def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = API_BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_api_key()}")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8") if e.fp else ""
        except Exception:
            pass
        raise Exception(f"Typefully API エラー {e.code}: {detail[:300]}") from e


# ── Social sets（投稿先） ─────────────────────────────────
def list_social_sets() -> list:
    """アクセスできる social set（Threads等を束ねた投稿先）の一覧。"""
    res = _request("GET", "/social-sets")
    if isinstance(res, dict):
        return res.get("results", res.get("data", []))
    return res or []


def resolve_social_set_id(explicit: str | None = None) -> str:
    """使用する social_set_id を決める。env指定 > 一覧の先頭。"""
    sid = (explicit or os.getenv("TYPEFULLY_SOCIAL_SET_ID", "")).strip()
    if sid:
        return sid
    sets = list_social_sets()
    if not sets:
        raise ValueError("Typefully に social set がありません。先にThreadsアカウントを連携してください。")
    return str(sets[0]["id"])


# ── 下書き作成（予約投稿） ────────────────────────────────
def create_scheduled_draft(text: str, comment_text: str | None = None,
                           publish_at: str = "next-free-slot",
                           social_set_id: str | None = None) -> dict:
    """本文（＋リプ欄）を Threads 向け予約下書きとして作成する。

    publish_at:
      - "next-free-slot" : Typefullyで設定した次の空きスロット（既定）
      - "now"            : すぐ公開
      - ISO8601日時       : 例 "2026-07-11T09:00:00Z"（指定時刻に予約）
    posts配列の1件目=本文、2件目=リプ欄（スレッド＝セルフリプライになる）
    """
    sid = resolve_social_set_id(social_set_id)
    posts = [{"text": text.strip()}]
    if comment_text and comment_text.strip():
        posts.append({"text": comment_text.strip()})
    body = {
        "platforms": {"threads": {"enabled": True, "posts": posts}},
        "publish_at": publish_at,
    }
    return _request("POST", f"/social-sets/{sid}/drafts", body)


# ── CLI ───────────────────────────────────────────────────
def _cmd_check():
    print("Typefully 接続確認中…")
    sets = list_social_sets()
    if not sets:
        print("⚠️ social set が見つかりません。Threadsアカウントを連携してください。")
        return 1
    print(f"✅ 接続OK。利用可能な social set: {len(sets)}件")
    for s in sets:
        print(f"   id={s.get('id')}  name={s.get('name','')}  username={s.get('username','')}")
    print("\n（複数ある場合は .env の TYPEFULLY_SOCIAL_SET_ID で固定できます）")
    return 0


def _cmd_sample(publish_at: str):
    draft = {
        "text": ("Typefully連携のテスト投稿です。\n\n"
                 "これが予約通りに公開されれば、PCを開いていなくても\n"
                 "クラウドから自動投稿できる状態になっています。"),
        "comment": "詳しい仕組みはこのリプ欄に続きます（テスト）。",
    }
    res = create_scheduled_draft(draft["text"], draft["comment"], publish_at=publish_at)
    print("✅ 予約下書きを作成しました:")
    print(json.dumps(res, ensure_ascii=False, indent=2)[:800])
    return 0


def _cmd_drafts(publish_at: str):
    import autopost  # data/drafts.json を読むため
    autopost.load_dotenv()
    drafts = [d for d in autopost.load_drafts() if d.get("status") == "draft"]
    if not drafts:
        print("送信する下書きがありません（data/drafts.json）。")
        return 0
    print(f"{len(drafts)}本の下書きを Typefully に予約送信します…")
    sent = 0
    for d in drafts:
        try:
            create_scheduled_draft(d["text"], d.get("comment_text"), publish_at=publish_at)
            print(f"  ✓ {d.get('hook_line','')[:36]}…")
            sent += 1
        except Exception as e:
            print(f"  ✗ 失敗: {e}")
    print(f"\n完了: {sent}/{len(drafts)}本を予約しました。")
    return 0


def main(argv=None):
    load_dotenv()
    ap = argparse.ArgumentParser(description="Typefully 連携（予約投稿）")
    ap.add_argument("--check", action="store_true", help="接続確認＆social set一覧")
    ap.add_argument("--sample", action="store_true", help="サンプルを予約")
    ap.add_argument("--drafts", action="store_true", help="data/drafts.jsonを全部予約送信")
    ap.add_argument("--at", default="next-free-slot",
                    help='予約時刻: next-free-slot（既定）/ now / ISO日時（例 2026-07-11T09:00:00Z）')
    args = ap.parse_args(argv)

    if not is_configured():
        print("TYPEFULLY_API_KEY が未設定です。Typefullyの Settings → API でキーを取得し .env に追加してください。")
        return 1
    try:
        if args.check:
            return _cmd_check()
        if args.sample:
            return _cmd_sample(args.at)
        if args.drafts:
            return _cmd_drafts(args.at)
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
