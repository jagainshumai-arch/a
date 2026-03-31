#!/bin/bash
# Threads × AI 投稿管理アプリ 起動スクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  Threads × AI 投稿管理アプリ 起動"
echo "========================================"
echo ""

# .env 読み込み
ENV_FILE="$SCRIPT_DIR/../.env"
if [ -f "$ENV_FILE" ]; then
    echo ".env ファイルを読み込み中..."
    set -a
    source "$ENV_FILE"
    set +a
    echo ""
fi

# Flask インストール確認
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Flask をインストール中..."
    pip3 install flask
    echo ""
fi

echo "ブラウザで http://localhost:5000 を開いてください"
echo "終了するには Ctrl+C を押してください"
echo ""

python3 "$SCRIPT_DIR/app.py"
