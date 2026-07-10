@echo off
chcp 65001 >nul
setlocal

REM ============================================
REM   毎朝9時「下書き5本」を自動生成する予約を登録
REM   （1回ダブルクリックするだけ。管理者権限は不要）
REM ============================================
cd /d "%~dp0"

set "TASKNAME=ThreadsMorningDrafts"

echo ============================================
echo   毎朝9時 下書き自動生成のセットアップ
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

REM 既存の同名タスクがあれば消してから作り直す
schtasks /Query /TN "%TASKNAME%" >nul 2>&1
if not errorlevel 1 (
    echo 既存の予約を更新します...
    schtasks /Delete /TN "%TASKNAME%" /F >nul 2>&1
)

REM 毎日 09:00 に morning_drafts.bat を実行する予約を登録
schtasks /Create /SC DAILY /ST 09:00 /TN "%TASKNAME%" /TR "\"%~dp0morning_drafts.bat\"" /F
if errorlevel 1 (
    echo.
    echo [エラー] 予約の登録に失敗しました。
    echo 手動で登録する場合は README の「タスクスケジューラ手動設定」を参照してください。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   登録完了！
echo ============================================
echo   毎朝 09:00 に Threads の下書きが5本、自動で作られます。
echo   （PCが起動している必要があります）
echo.
echo   作られた下書きの確認・投稿は：
echo     python webapp.py --open   → 「下書き」欄
echo.
echo   予約をやめたいとき：
echo     schtasks /Delete /TN "%TASKNAME%" /F
echo.
echo   今すぐ動作テスト（5本作ってみる）：
echo     このあと Enter を押すとテスト生成します。
pause
echo.
echo テスト生成中...（1〜2分かかります）
call "%~dp0morning_drafts.bat"
echo 完了。data\drafts.json と webapp で確認してください。
echo.
pause
