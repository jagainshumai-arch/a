"""Threads APIトークン取得セットアップスクリプト

ブラウザでのOAuth認証フローをガイドし、有効なアクセストークンを取得する。
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, parse_qs


REDIRECT_PORT = 8888
# Threads/Meta は http:// のリダイレクトを拒否する（error_code 1349187
# 「セキュアではないログインがブロックされました」）。必ず https:// を使う。
REDIRECT_URI = f"https://localhost:{REDIRECT_PORT}/callback"

# ── Step 1: アプリ情報の入力 ──

def get_app_credentials():
    print("=" * 60)
    print("  Threads API トークン取得セットアップ")
    print("=" * 60)
    print()
    print("【事前準備】Meta for Developers でアプリを作成してください:")
    print()
    print("  1. https://developers.facebook.com/ にアクセス")
    print("  2. 「マイアプリ」→「アプリを作成」")
    print("  3. ユースケース: 「Threads APIにアクセスする」を選択")
    print("  4. アプリタイプ: 「なし」を選択")
    print("  5. アプリ名を入力して作成")
    print("  6. アプリダッシュボード → 設定 → ベーシック")
    print("     → アプリID と app secret を確認")
    print("  7. ユースケース → Threads API → 設定")
    print(f"     → リダイレクトURI に {REDIRECT_URI} を追加")
    print()
    print("-" * 60)

    app_id = input("アプリID (App ID) を入力: ").strip()
    app_secret = input("App Secret を入力: ").strip()

    if not app_id or not app_secret:
        print("❌ アプリIDとApp Secretは必須です")
        sys.exit(1)

    return app_id, app_secret


# ── Step 2: 認証URLを生成してブラウザで開いてもらう ──

def get_authorization_code(app_id):
    scopes = "threads_basic,threads_content_publish,threads_manage_insights,threads_manage_replies"

    auth_url = (
        f"https://threads.net/oauth/authorize?"
        f"client_id={app_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scopes}"
        f"&response_type=code"
    )

    print()
    print("=" * 60)
    print("  Step 2: ブラウザで認証")
    print("=" * 60)
    print()
    print("以下のURLをブラウザで開いてThreadsアカウントを認証してください:")
    print()
    print(f"  {auth_url}")
    print()
    print(f"認証後、{REDIRECT_URI} にリダイレクトされます。")
    print()
    print("─" * 60)
    print("【重要】ブラウザは認証後、白い『このサイトにアクセスできません』")
    print("        などのエラー画面になりますが、それで正常です。")
    print("        アドレスバーに出る URL 全体（?code=... を含む）を")
    print("        コピーして、下に貼り付けてください。")
    print("─" * 60)
    print()
    redirect_url = input("リダイレクトされたURL全体を貼り付け: ").strip()

    # 貼り付けが「URL全体」でも「codeだけ」でも拾えるようにする
    code = None
    if "code=" in redirect_url:
        parsed = urlparse(redirect_url)
        code = parse_qs(parsed.query).get("code", [None])[0]
        if not code:  # クエリ抽出に失敗したら文字列から拾う
            code = redirect_url.split("code=", 1)[1].split("&", 1)[0]
    elif redirect_url:
        code = redirect_url  # code文字列そのものを貼られた場合

    if not code:
        print("❌ 認証コードが見つかりません（URL全体を貼り付けてください）")
        sys.exit(1)
    # code末尾に付くことがある #_ を除去
    return code.rstrip("#_")


class CallbackHandler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        CallbackHandler.code = params.get("code", [None])[0]
        if CallbackHandler.code:
            CallbackHandler.code = CallbackHandler.code.rstrip("#_")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if CallbackHandler.code:
            self.wfile.write("✅ 認証成功！このタブを閉じてターミナルに戻ってください。".encode())
        else:
            self.wfile.write("❌ 認証に失敗しました。".encode())

    def log_message(self, format, *args):
        pass  # ログ抑制


def _receive_code_via_server():
    print(f"ローカルサーバーをポート{REDIRECT_PORT}で起動中...")
    server = HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
    server.handle_request()
    if CallbackHandler.code:
        print("✅ 認証コードを受信しました")
        return CallbackHandler.code
    print("❌ 認証コードの受信に失敗しました")
    sys.exit(1)


# ── Step 3: 短期トークン取得 ──

def exchange_code_for_short_token(app_id, app_secret, code):
    print()
    print("短期アクセストークンを取得中...")

    data = urlencode({
        "client_id": app_id,
        "client_secret": app_secret,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }).encode()

    req = Request("https://graph.threads.net/oauth/access_token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            token = result.get("access_token")
            user_id = result.get("user_id")
            print(f"✅ 短期トークン取得成功 (user_id: {user_id})")
            return token, str(user_id)
    except Exception as e:
        print(f"❌ トークン取得に失敗: {e}")
        sys.exit(1)


# ── Step 4: 長期トークンに交換 ──

def exchange_for_long_lived_token(app_secret, short_token):
    print("長期アクセストークンに交換中...")

    params = urlencode({
        "grant_type": "th_exchange_token",
        "client_secret": app_secret,
        "access_token": short_token,
    })

    req = Request(f"https://graph.threads.net/access_token?{params}", method="GET")

    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            token = result.get("access_token")
            expires_in = result.get("expires_in", 0)
            days = expires_in // 86400
            print(f"✅ 長期トークン取得成功（有効期限: {days}日）")
            return token
    except Exception as e:
        print(f"⚠️  長期トークン交換に失敗（短期トークンを使用します）: {e}")
        return short_token


# ── Step 5: 接続テスト ──

def test_connection(token, user_id):
    print()
    print("接続テスト中...")

    params = urlencode({
        "fields": "id,username,threads_profile_picture_url,threads_biography",
        "access_token": token,
    })

    req = Request(f"https://graph.threads.net/v1.0/{user_id}?{params}", method="GET")

    try:
        with urlopen(req, timeout=30) as resp:
            profile = json.loads(resp.read().decode())
            username = profile.get("username", "不明")
            print(f"✅ 接続成功！")
            print(f"   ユーザー名: @{username}")
            print(f"   ユーザーID: {profile.get('id')}")
            return profile
    except Exception as e:
        print(f"❌ 接続テストに失敗: {e}")
        return None


# ── Step 6: .envファイルに保存 ──

def save_env(token, user_id):
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)

    lines = []
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            lines = f.readlines()

    env_vars = {
        "THREADS_ACCESS_TOKEN": token,
        "THREADS_USER_ID": user_id,
    }

    # 既存の行を更新 or 追加
    updated_keys = set()
    new_lines = []
    for line in lines:
        key = line.split("=")[0].strip()
        if key in env_vars:
            new_lines.append(f"{key}={env_vars[key]}\n")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, val in env_vars.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"✅ 保存しました: {env_path}")
    return env_path


# ── メイン ──

def main():
    app_id, app_secret = get_app_credentials()
    code = get_authorization_code(app_id)
    short_token, user_id = exchange_code_for_short_token(app_id, app_secret, code)
    long_token = exchange_for_long_lived_token(app_secret, short_token)
    profile = test_connection(long_token, user_id)

    if profile:
        print()
        print("=" * 60)
        print("  セットアップ完了！")
        print("=" * 60)
        print()

        save_choice = input(".envファイルに保存しますか？ (y/n): ").strip().lower()
        if save_choice == "y":
            env_path = save_env(long_token, user_id)
            print()
            print(f"以下のコマンドで自動化ツールを実行できます:")
            print()
            print(f'  export $(cat {env_path} | xargs)')
            print(f'  python -m threads_automation.pipeline \\')
            print(f'    --niche "あなたのニッチ" \\')
            print(f'    --target "ターゲット読者" \\')
            print(f'    --cycles 1')
        else:
            print()
            print("以下の環境変数を手動で設定してください:")
            print(f"  export THREADS_ACCESS_TOKEN={long_token}")
            print(f"  export THREADS_USER_ID={user_id}")
    else:
        print()
        print("セットアップに問題があります。上記のエラーを確認してください。")


if __name__ == "__main__":
    main()
