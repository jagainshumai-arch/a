@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Threads x AI 投稿管理アプリ 起動
echo ========================================
echo.

REM .envファイル読み込み
if exist "%~dp0..\.env" (
    echo .env ファイルを読み込み中...
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0..\.env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
    echo.
)

REM Flaskインストール確認
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Flask をインストール中...
    pip install flask
    echo.
)

echo ブラウザで http://localhost:5000 を開いてください
echo 終了するには Ctrl+C を押してください
echo.

python "%~dp0app.py"
pause
