@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====================================================
REM   Threads 全自動投稿 かんたんセットアップ (Windows)
REM   ダブルクリックで実行できます
REM ====================================================

REM このバッチがある場所へ移動（autopost.py と同じフォルダ前提）
cd /d "%~dp0"

echo ============================================
echo   Threads 全自動投稿 セットアップ
echo ============================================
echo.

REM ---- 1. Python の確認 ----
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Python が見つかりませんでした。
    echo.
    echo   1. https://www.python.org/downloads/ を開く
    echo   2. 「Download Python」をクリックしてインストール
    echo   3. ※最初の画面で「Add python.exe to PATH」に必ずチェック
    echo.
    echo インストール後、このバッチをもう一度ダブルクリックしてください。
    echo.
    pause
    exit /b 1
)
echo [OK] Python を確認しました：
python --version
echo.

REM ---- 2. autopost.py の存在確認 ----
if not exist "autopost.py" (
    echo [エラー] このフォルダに autopost.py が見つかりません。
    echo setup.bat は autopost.py と同じフォルダに置いて実行してください。
    echo.
    pause
    exit /b 1
)

REM ---- 3. .env の作成 ----
if exist ".env" (
    echo [情報] .env は既にあります。
    set /p RECREATE="作り直しますか？ 作り直す場合は y を入力 [y/N]: "
    if /i not "!RECREATE!"=="y" goto RUN
)

echo.
echo .env を作成します。以下を貼り付けてください（右クリックで貼り付け）。
echo （何も入力せず Enter を押すと [ ] 内の初期値が使われます）
echo.

set "DEF_UID=27230077813343339"
set /p TUID="Threads ユーザーID [!DEF_UID!]: "
if "!TUID!"=="" set "TUID=!DEF_UID!"

set /p TTOKEN="Threads アクセストークン: "
set /p AKEY="Anthropic APIキー: "

echo.
set "DEF_SLOTS=14:00,20:00"
set /p SLOTS="投稿する時間帯（カンマ区切り） [!DEF_SLOTS!]: "
if "!SLOTS!"=="" set "SLOTS=!DEF_SLOTS!"

REM スロット数から1日の本数を数える（簡易：カンマ+1）
set "TMP=!SLOTS!"
set "COUNT=1"
:countloop
echo !TMP! | findstr "," >nul
if errorlevel 1 goto countdone
set "TMP=!TMP:*,=!"
set /a COUNT+=1
goto countloop
:countdone

(
echo THREADS_USER_ID=!TUID!
echo THREADS_ACCESS_TOKEN=!TTOKEN!
echo ANTHROPIC_API_KEY=!AKEY!
echo POST_SLOTS=!SLOTS!
echo DAILY_LIMIT=!COUNT!
) > .env

echo.
echo [OK] .env を作成しました（1日 !COUNT! 本 / !SLOTS!）。
echo.

:RUN
echo ============================================
echo   テスト：生成だけ確認（実際には投稿しません）
echo ============================================
echo.
python autopost.py --now --dry-run
echo.
echo ============================================
echo   セットアップ完了
echo ============================================
echo.
echo   本番で1本投稿     ：python autopost.py --now
echo   自動投稿し続ける  ：python autopost.py --loop
echo.
pause
