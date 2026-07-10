@echo off
chcp 65001 >nul
REM ============================================
REM   毎朝の下書き自動生成（タスクスケジューラから実行される）
REM   Threadsの下書きを5本作って data/drafts.json に保存する
REM ============================================
cd /d "%~dp0"

REM ログを残しながら下書きを5本生成（投稿はしない）
python autopost.py --drafts 5 >> "%~dp0data\morning_drafts.log" 2>&1
