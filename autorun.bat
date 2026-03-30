@echo off
chcp 65001 >nul
echo ========================================
echo  Threads x AI 自動化パイプライン 起動
echo ========================================
echo.

cd /d "%~dp0"

REM .envファイルから環境変数を読み込む
if exist .env (
    echo .envファイルを読み込み中...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
    echo 読み込み完了
    echo.
) else (
    echo [エラー] .envファイルが見つかりません
    echo .env.example をコピーして .env を作成してください
    pause
    exit /b 1
)

python autorun.py

echo.
echo 完了しました。
pause
