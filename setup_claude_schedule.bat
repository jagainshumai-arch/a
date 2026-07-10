@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================
REM   Claude Code自動投稿を毎日決めた時刻に走らせる予約を登録
REM   （1回ダブルクリックするだけ。管理者権限は不要）
REM ============================================
cd /d "%~dp0"

echo ============================================
echo   Claude Code × Threads 自動投稿スケジュール登録
echo ============================================
echo.

REM Python の確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりません。先に Python を入れてください。
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

REM claude CLI の確認（無くても登録は可能だが警告する）
where claude >nul 2>&1
if errorlevel 1 (
    echo [注意] claude CLI が見つかりません。
    echo   Claude Code運用には claude CLI が必要です:
    echo     npm install -g @anthropic-ai/claude-code
    echo     claude   ^(初回にログイン^)
    echo   ※ claude CLI 無しで動かすなら claude_post.bat の中身を
    echo     「python claude_post.py --now --allow-fallback」に変えてください。
    echo.
)

echo 投稿する時刻をカンマ区切りで入力してください。
set /p TIMES="投稿時刻 [14:00,20:00]: "
if "!TIMES!"=="" set "TIMES=14:00,20:00"

REM 既存の同名タスクを一旦削除（作り直し）
for /L %%i in (1,1,10) do schtasks /Delete /TN "ThreadsClaudePost_%%i" /F >nul 2>&1

REM 時刻ごとにタスクを作成（カンマ→スペースに変換して回す）
set IDX=0
for %%T in (!TIMES:,= !) do (
    set /a IDX+=1
    schtasks /Create /SC DAILY /ST %%T /TN "ThreadsClaudePost_!IDX!" /TR "\"%~dp0claude_post.bat\"" /F
    if errorlevel 1 (
        echo [エラー] %%T の登録に失敗しました。
    ) else (
        echo   ✓ 毎日 %%T に自動投稿を登録しました。
    )
)

echo.
echo ============================================
echo   登録完了！（PCが起動している必要があります）
echo ============================================
echo   予約を止めるとき（例）:
echo     schtasks /Delete /TN "ThreadsClaudePost_1" /F
echo.
echo   今すぐ動作テスト（1本 生成→投稿）:
echo     このあと Enter でテスト実行します。投稿したくない場合は閉じてください。
pause
echo.
echo テスト実行中...（Claude Codeが生成するので30秒〜数分かかります）
call "%~dp0claude_post.bat"
echo 完了。data\claude_post.log と Threads を確認してください。
echo.
pause
