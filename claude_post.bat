@echo off
chcp 65001 >nul
REM ============================================
REM   Claude Code × Threads 自動投稿（スケジュールから実行される中身）
REM   Claude Codeに1本生成させ、安全チェック後にThreadsへ投稿する
REM ============================================
cd /d "%~dp0"

python claude_post.py --now >> "%~dp0data\claude_post.log" 2>&1
