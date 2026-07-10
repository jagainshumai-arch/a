"""Threads × AI 投稿コンソール（webapp）

autopost.py の機能を、ブラウザの見やすいUIから操作できるようにしたWebアプリG。
Flask等は不要。Python標準ライブラリ（http.server）だけで動く。

使い方:
  python webapp.py            # http://127.0.0.1:8000 で起動
  python webapp.py --port 5000
  python webapp.py --open     # 起動後にブラウザを自動で開く

できること:
  - 生成してプレビュー（投稿せず本文＋リプ欄を確認・安全チェック表示）
  - その内容でThreadsに投稿（本文＋セルフリプライ）
  - 投稿履歴の閲覧
  - 設定（投稿時間帯・1日上限・本日の投稿数・API接続状態）の確認
"""

import argparse
import json
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import autopost   # 同じフォルダの autopost.py を再利用
import typefully  # Typefully 予約投稿連携

autopost.load_dotenv()  # .env を読み込んで CONFIG を確定させる


# ════════════════════════════════════════════════════════
#  サーバ側ロジック（autopost の関数を組み合わせる）
# ════════════════════════════════════════════════════════

def build_status() -> dict:
    history = autopost.load_history()
    cfg = autopost.CONFIG
    return {
        "claude_ready": bool(cfg["ANTHROPIC_API_KEY"]),
        "threads_ready": bool(cfg["THREADS_ACCESS_TOKEN"] and cfg["THREADS_USER_ID"]),
        "typefully_ready": typefully.is_configured(),
        "slots": cfg["POST_SLOTS"],
        "daily_limit": cfg["DAILY_LIMIT"],
        "posted_today": autopost.posted_today(history),
        "total_posts": len(history),
        "model": cfg["AI_MODEL"],
        "niche": cfg["NICHE"],
        "target": cfg["TARGET"],
    }


def generate_preview(use_sample: bool) -> dict:
    """投稿はせず、1本生成して安全チェック結果と一緒に返す。"""
    history = autopost.load_history()
    draft = autopost.sample_draft() if use_sample else autopost.generate_one_draft()
    ok, reason = autopost.vet_draft(draft, history)  # ハッシュタグ除去込み
    draft["vet_ok"] = ok
    draft["vet_reason"] = reason
    draft["text_len"] = len(draft["text"])
    draft["comment_len"] = len(draft.get("comment_text", ""))
    return draft


def post_draft(draft: dict) -> dict:
    """プレビュー済みの下書きを実際にThreadsへ投稿し、履歴に保存する。
    手動投稿（ユーザーがボタンで確認済み）なので1日上限のチェックはしない。"""
    history = autopost.load_history()
    # 投稿前に最終安全チェック（改ざん・直近重複を再確認）
    ok, reason = autopost.vet_draft(draft, history)
    if not ok:
        raise ValueError(f"安全チェック不合格のため投稿を中止: {reason}")

    result = autopost.post_to_threads(draft)
    draft.update({
        "status": "posted",
        "posted_at": datetime.now().isoformat(),
        "post_id": result["post_id"],
        "reply_id": result.get("reply_id"),
    })
    history.insert(0, draft)
    autopost.save_history(history)
    return draft


# ---- 下書き（作り置き）関連 ----

def list_drafts() -> list:
    return [d for d in autopost.load_drafts() if d.get("status") == "draft"]


def make_drafts(n: int) -> list:
    """下書きを n 本生成して保存し、作成分を返す。"""
    n = max(1, min(n, 10))
    return autopost.generate_drafts(n)


def post_saved_draft(draft_id: str) -> dict:
    """保存済み下書きを投稿し、下書きストアから取り除く。"""
    drafts = autopost.load_drafts()
    target = next((d for d in drafts if d.get("id") == draft_id), None)
    if not target:
        raise ValueError("下書きが見つかりません（既に投稿/削除済みの可能性）。")
    posted = post_draft(target)
    autopost.save_drafts([d for d in drafts if d.get("id") != draft_id])
    return posted


def delete_saved_draft(draft_id: str) -> dict:
    drafts = autopost.load_drafts()
    autopost.save_drafts([d for d in drafts if d.get("id") != draft_id])
    return {"ok": True, "removed": draft_id}


# ---- Typefully 予約投稿 ----

def schedule_preview_typefully(draft: dict, at: str = "next-free-slot") -> dict:
    """プレビュー中の下書きをTypefullyに予約下書きとして送る。"""
    draft.setdefault("hook_line", (draft.get("text", "").split("\n") or [""])[0])
    draft.setdefault("comment_text", "")
    # 送信前にハッシュタグ除去・NGチェックは通しておく（重複チェックは予約なので緩め）
    autopost.vet_draft(draft, [])
    res = typefully.create_scheduled_draft(
        draft["text"], draft.get("comment_text"), publish_at=at)
    return {"ok": True, "typefully": res}


def schedule_saved_draft_typefully(draft_id: str, at: str = "next-free-slot") -> dict:
    """保存済み下書きをTypefullyに予約し、下書きストアから取り除く。"""
    drafts = autopost.load_drafts()
    target = next((d for d in drafts if d.get("id") == draft_id), None)
    if not target:
        raise ValueError("下書きが見つかりません（既に投稿/削除済みの可能性）。")
    res = typefully.create_scheduled_draft(
        target["text"], target.get("comment_text"), publish_at=at)
    autopost.save_drafts([d for d in drafts if d.get("id") != draft_id])
    return {"ok": True, "typefully": res}


def recent_history(limit: int = 30) -> list:
    out = []
    for h in autopost.load_history()[:limit]:
        out.append({
            "hook_line": h.get("hook_line", "") or (h.get("text", "").split("\n")[0]),
            "post_type": h.get("post_type", ""),
            "posted_at": h.get("posted_at", ""),
            "text": h.get("text", ""),
            "comment_text": h.get("comment_text", ""),
            "post_id": h.get("post_id", ""),
            "reply_id": h.get("reply_id", ""),
        })
    return out


# ════════════════════════════════════════════════════════
#  HTML（1ファイルに同梱：CSS/JSも内包）
# ════════════════════════════════════════════════════════

PAGE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Threads × AI 投稿コンソール</title>
<style>
  :root{
    --bg:#0b0d12; --panel:#151922; --panel2:#1d2330; --line:#2a3240;
    --txt:#e8edf4; --muted:#8a94a6; --accent:#6d9bff; --accent2:#8b5cf6;
    --ok:#34d399; --ng:#f87171; --warn:#fbbf24;
  }
  *{box-sizing:border-box}
  body{margin:0;background:linear-gradient(160deg,#0b0d12,#10141d);color:var(--txt);
    font-family:"Hiragino Kaku Gothic ProN","Yu Gothic UI",system-ui,sans-serif;
    line-height:1.7;-webkit-font-smoothing:antialiased}
  .wrap{max-width:820px;margin:0 auto;padding:24px 18px 80px}
  header{display:flex;align-items:center;gap:12px;margin-bottom:8px}
  header h1{font-size:20px;margin:0;letter-spacing:.02em}
  header .logo{width:38px;height:38px;border-radius:11px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    display:grid;place-items:center;font-size:20px;box-shadow:0 6px 20px rgba(109,155,255,.35)}
  .sub{color:var(--muted);font-size:13px;margin:0 0 20px 50px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:16px;
    padding:18px;margin-bottom:16px;box-shadow:0 8px 30px rgba(0,0,0,.25)}
  .card h2{font-size:14px;margin:0 0 14px;color:var(--muted);font-weight:600;
    text-transform:uppercase;letter-spacing:.08em}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}
  .stat{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
  .stat .k{font-size:11px;color:var(--muted);margin-bottom:4px}
  .stat .v{font-size:18px;font-weight:700}
  .badge{display:inline-flex;align-items:center;gap:5px;font-size:12px;
    padding:3px 9px;border-radius:999px;font-weight:600}
  .badge.ok{background:rgba(52,211,153,.15);color:var(--ok)}
  .badge.ng{background:rgba(248,113,113,.15);color:var(--ng)}
  .badge.warn{background:rgba(251,191,36,.15);color:var(--warn)}
  .btn{appearance:none;border:0;border-radius:12px;padding:13px 18px;font-size:15px;
    font-weight:700;cursor:pointer;color:#fff;transition:.15s;width:100%;
    font-family:inherit}
  .btn:disabled{opacity:.45;cursor:not-allowed}
  .btn.primary{background:linear-gradient(135deg,var(--accent),var(--accent2));
    box-shadow:0 6px 18px rgba(109,155,255,.35)}
  .btn.primary:hover:not(:disabled){transform:translateY(-1px)}
  .btn.ghost{background:var(--panel2);border:1px solid var(--line)}
  .btn.danger{background:linear-gradient(135deg,#ef4444,#b91c1c)}
  .btnrow{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  @media(max-width:520px){.btnrow{grid-template-columns:1fr}}
  .preview{background:var(--panel2);border:1px solid var(--line);border-radius:14px;
    padding:16px;margin-top:14px;display:none}
  .preview.show{display:block;animation:fade .3s ease}
  @keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
  .ptype{font-size:12px;color:var(--accent);font-weight:700;margin-bottom:8px}
  .body-text{white-space:pre-wrap;background:#0d1017;border:1px solid var(--line);
    border-radius:10px;padding:13px;font-size:14.5px;margin:6px 0}
  .label{font-size:11px;color:var(--muted);margin-top:12px;display:flex;
    justify-content:space-between;align-items:center}
  .meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
  .hist-item{border-bottom:1px solid var(--line);padding:13px 0}
  .hist-item:last-child{border-bottom:0}
  .hist-hook{font-weight:600;font-size:14.5px}
  .hist-meta{font-size:11.5px;color:var(--muted);margin-top:4px;display:flex;gap:10px;flex-wrap:wrap}
  .empty{color:var(--muted);font-size:13px;text-align:center;padding:18px}
  #toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(120px);
    background:var(--panel2);border:1px solid var(--line);color:var(--txt);
    padding:12px 20px;border-radius:12px;font-size:14px;font-weight:600;
    box-shadow:0 10px 30px rgba(0,0,0,.4);transition:.3s;z-index:50;max-width:90vw}
  #toast.show{transform:translateX(-50%) translateY(0)}
  #toast.ok{border-color:var(--ok)} #toast.err{border-color:var(--ng)}
  .spinner{display:inline-block;width:15px;height:15px;border:2px solid rgba(255,255,255,.35);
    border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;vertical-align:-2px}
  @keyframes spin{to{transform:rotate(360deg)}}
  a{color:var(--accent)}
  .note{font-size:12px;color:var(--muted);margin-top:10px}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">🧵</div>
    <h1>Threads × AI 投稿コンソール</h1>
  </header>
  <p class="sub">生成 → 安全チェック → 確認して投稿。すべてブラウザから。</p>

  <!-- 設定 -->
  <div class="card">
    <h2>ステータス</h2>
    <div class="meta" id="badges"></div>
    <div class="grid" id="stats" style="margin-top:14px"></div>
    <div class="note" id="nichebox"></div>
  </div>

  <!-- 操作 -->
  <div class="card">
    <h2>投稿を作る</h2>
    <div class="btnrow">
      <button class="btn ghost" id="btnGen">🎲 生成してプレビュー</button>
      <button class="btn ghost" id="btnSample">🧪 サンプル生成（API不要）</button>
    </div>
    <div class="preview" id="preview">
      <div class="ptype" id="pType"></div>
      <div id="pVet" class="meta"></div>
      <div class="label"><span>本文</span><span id="pTextLen"></span></div>
      <div class="body-text" id="pText"></div>
      <div class="label"><span>リプ欄（セルフリプライ）</span><span id="pCommentLen"></span></div>
      <div class="body-text" id="pComment"></div>
      <div class="btnrow" style="margin-top:16px">
        <button class="btn ghost" id="btnRegen">↻ もう一度生成</button>
        <button class="btn primary" id="btnPost">🚀 今すぐThreadsに投稿</button>
      </div>
      <button class="btn ghost" id="btnSchedule" style="margin-top:10px">🗓 Typefullyで予約投稿（次の空き枠）</button>
      <div class="note">「今すぐ投稿」は本文＋リプ欄を即公開。「予約投稿」はTypefullyの次の空きスロットに予約（クラウドが自動投稿するのでPCは開いていなくてOK）。</div>
    </div>
  </div>

  <!-- 下書き（作り置き） -->
  <div class="card">
    <h2>下書き（毎朝9時に自動生成）</h2>
    <div class="btnrow" style="margin-bottom:6px">
      <button class="btn ghost" id="btnMake">📝 今すぐ5本 下書きを作る</button>
      <button class="btn ghost" id="btnReloadDrafts">↻ 再読み込み</button>
    </div>
    <div class="note">朝9時のバッチで作られた下書きがここに並びます。確認して1本ずつ投稿できます。</div>
    <div id="drafts" style="margin-top:12px"><div class="empty">読み込み中…</div></div>
  </div>

  <!-- 履歴 -->
  <div class="card">
    <h2>投稿履歴</h2>
    <div id="history"><div class="empty">読み込み中…</div></div>
  </div>
</div>

<div id="toast"></div>

<script>
let currentDraft = null;

function toast(msg, kind){
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + (kind||'');
  clearTimeout(t._t); t._t = setTimeout(()=>{t.className='';}, 3200);
}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

async function api(path, opts){
  const r = await fetch(path, opts);
  const data = await r.json().catch(()=>({}));
  if(!r.ok || data.error) throw new Error(data.error || ('HTTP '+r.status));
  return data;
}

async function loadStatus(){
  try{
    const s = await api('/api/status');
    const b = document.getElementById('badges');
    b.innerHTML =
      `<span class="badge ${s.claude_ready?'ok':'ng'}">Claude API ${s.claude_ready?'接続OK':'未設定'}</span>`+
      `<span class="badge ${s.threads_ready?'ok':'ng'}">Threads API ${s.threads_ready?'接続OK':'未設定'}</span>`+
      `<span class="badge ${s.typefully_ready?'ok':'warn'}">Typefully ${s.typefully_ready?'連携OK':'未連携'}</span>`;
    window._typefullyReady = s.typefully_ready;
    const remain = Math.max(0, s.daily_limit - s.posted_today);
    document.getElementById('stats').innerHTML =
      stat('投稿時間帯', s.slots.join(' / ')) +
      stat('1日の上限', s.daily_limit + ' 本') +
      stat('本日の投稿', s.posted_today + ' 本') +
      stat('残り投稿枠', remain + ' 本') +
      stat('累計投稿', s.total_posts + ' 本');
    document.getElementById('nichebox').textContent =
      'ジャンル: ' + s.niche + '　/　モデル: ' + s.model;
  }catch(e){ toast('ステータス取得失敗: '+e.message, 'err'); }
}
function stat(k,v){return `<div class="stat"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`;}

function renderPreview(d){
  currentDraft = d;
  document.getElementById('pType').textContent = '◆ ' + d.post_type;
  document.getElementById('pVet').innerHTML = d.vet_ok
    ? '<span class="badge ok">✓ 安全チェック合格</span>'
    : '<span class="badge ng">✗ '+esc(d.vet_reason)+'</span>';
  document.getElementById('pText').textContent = d.text;
  document.getElementById('pComment').textContent = d.comment_text || '(なし)';
  document.getElementById('pTextLen').textContent = d.text_len + ' 字';
  document.getElementById('pCommentLen').textContent = d.comment_len + ' 字';
  document.getElementById('btnPost').disabled = !d.vet_ok;
  document.getElementById('preview').classList.add('show');
  document.getElementById('preview').scrollIntoView({behavior:'smooth',block:'nearest'});
}

async function generate(sample){
  const btns = ['btnGen','btnSample','btnRegen'].map(i=>document.getElementById(i));
  btns.forEach(b=>b&&(b.disabled=true));
  const trigger = sample ? document.getElementById('btnSample') : document.getElementById('btnGen');
  const orig = trigger.innerHTML; trigger.innerHTML = '<span class="spinner"></span> 生成中…';
  try{
    const d = await api('/api/generate', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({sample: !!sample})
    });
    renderPreview(d);
    toast(d.vet_ok ? '生成しました（安全チェック合格）' : '生成しましたが要確認', d.vet_ok?'ok':'err');
  }catch(e){ toast('生成失敗: '+e.message, 'err'); }
  finally{ trigger.innerHTML = orig; btns.forEach(b=>b&&(b.disabled=false)); }
}

async function postNow(){
  if(!currentDraft){ return; }
  if(!confirm('この内容をThreadsに投稿します。よろしいですか？')) return;
  const btn = document.getElementById('btnPost');
  const orig = btn.innerHTML; btn.disabled=true; btn.innerHTML='<span class="spinner"></span> 投稿中…';
  try{
    const r = await api('/api/post', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(currentDraft)
    });
    toast('✅ 投稿完了！', 'ok');
    document.getElementById('preview').classList.remove('show');
    currentDraft = null;
    loadStatus(); loadHistory();
  }catch(e){ toast('投稿失敗: '+e.message, 'err'); btn.disabled=false; }
  finally{ btn.innerHTML = orig; }
}

async function loadHistory(){
  try{
    const items = await api('/api/history');
    const box = document.getElementById('history');
    if(!items.length){ box.innerHTML = '<div class="empty">まだ投稿はありません</div>'; return; }
    box.innerHTML = items.map(h=>{
      const dt = h.posted_at ? h.posted_at.replace('T',' ').slice(0,16) : '';
      return `<div class="hist-item">
        <div class="hist-hook">${esc(h.hook_line)}</div>
        <div class="hist-meta">
          <span>🕒 ${esc(dt)}</span>
          ${h.post_type?`<span>◆ ${esc(h.post_type)}</span>`:''}
          ${h.post_id?`<span>id: ${esc(h.post_id)}</span>`:''}
          ${h.reply_id?`<span>💬 リプ済み</span>`:''}
        </div>
      </div>`;
    }).join('');
  }catch(e){ document.getElementById('history').innerHTML =
    '<div class="empty">履歴の取得に失敗: '+esc(e.message)+'</div>'; }
}

async function scheduleCurrent(){
  if(!currentDraft) return;
  if(!window._typefullyReady){ toast('Typefully未連携（.envにTYPEFULLY_API_KEY）', 'err'); return; }
  if(!confirm('この内容をTypefullyの次の空き枠に予約します。よろしいですか？')) return;
  const btn = document.getElementById('btnSchedule');
  const orig = btn.innerHTML; btn.disabled=true; btn.innerHTML='<span class="spinner"></span> 予約中…';
  try{
    await api('/api/schedule_preview', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({...currentDraft, at:'next-free-slot'})
    });
    toast('🗓 Typefullyに予約しました', 'ok');
  }catch(e){ toast('予約失敗: '+e.message, 'err'); }
  finally{ btn.disabled=false; btn.innerHTML=orig; }
}

async function scheduleDraft(id, btn){
  if(!window._typefullyReady){ toast('Typefully未連携（.envにTYPEFULLY_API_KEY）', 'err'); return; }
  if(!confirm('この下書きをTypefullyの次の空き枠に予約します。よろしいですか？')) return;
  const orig = btn.innerHTML; btn.disabled=true; btn.innerHTML='<span class="spinner"></span> 予約中…';
  try{
    await api('/api/schedule_draft', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({id, at:'next-free-slot'})
    });
    toast('🗓 Typefullyに予約しました', 'ok');
    loadDrafts();
  }catch(e){ toast('予約失敗: '+e.message, 'err'); btn.disabled=false; btn.innerHTML=orig; }
}

async function loadDrafts(){
  try{
    const items = await api('/api/drafts');
    const box = document.getElementById('drafts');
    if(!items.length){ box.innerHTML = '<div class="empty">下書きはありません。「今すぐ5本」か、毎朝9時のバッチで作られます。</div>'; return; }
    box.innerHTML = items.map(d=>{
      const dt = (d.created_at||'').replace('T',' ').slice(0,16);
      return `<div class="hist-item" data-id="${esc(d.id)}">
        <div class="hist-hook">${esc(d.hook_line || (d.text||'').split('\n')[0])}</div>
        <div class="hist-meta">
          <span>🕒 ${esc(dt)}</span>
          ${d.post_type?`<span>◆ ${esc(d.post_type)}</span>`:''}
          <span>本文 ${(d.text||'').length}字 / リプ ${(d.comment_text||'').length}字</span>
        </div>
        <details style="margin-top:8px">
          <summary style="cursor:pointer;color:var(--accent);font-size:13px">本文とリプ欄を見る</summary>
          <div class="body-text" style="margin-top:8px">${esc(d.text)}</div>
          <div class="label"><span>リプ欄</span></div>
          <div class="body-text">${esc(d.comment_text||'(なし)')}</div>
        </details>
        <div class="btnrow" style="margin-top:10px">
          <button class="btn ghost btn-del" data-id="${esc(d.id)}">🗑 削除</button>
          <button class="btn primary btn-postdraft" data-id="${esc(d.id)}">🚀 今すぐ投稿</button>
        </div>
        <button class="btn ghost btn-scheddraft" data-id="${esc(d.id)}" style="margin-top:8px">🗓 Typefullyで予約</button>
      </div>`;
    }).join('');
    box.querySelectorAll('.btn-postdraft').forEach(b=> b.onclick = ()=>postSavedDraft(b.dataset.id, b));
    box.querySelectorAll('.btn-del').forEach(b=> b.onclick = ()=>deleteDraft(b.dataset.id));
    box.querySelectorAll('.btn-scheddraft').forEach(b=> b.onclick = ()=>scheduleDraft(b.dataset.id, b));
  }catch(e){ document.getElementById('drafts').innerHTML =
    '<div class="empty">下書きの取得に失敗: '+esc(e.message)+'</div>'; }
}

async function makeDrafts(){
  const btn = document.getElementById('btnMake');
  const orig = btn.innerHTML; btn.disabled=true; btn.innerHTML='<span class="spinner"></span> 生成中…（1分ほど）';
  try{
    const created = await api('/api/make_drafts', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({n:5})
    });
    toast(`✅ ${created.length}本の下書きを作りました`, 'ok');
    loadDrafts();
  }catch(e){ toast('生成失敗: '+e.message, 'err'); }
  finally{ btn.disabled=false; btn.innerHTML=orig; }
}

async function postSavedDraft(id, btn){
  if(!confirm('この下書きをThreadsに投稿します。よろしいですか？')) return;
  const orig = btn.innerHTML; btn.disabled=true; btn.innerHTML='<span class="spinner"></span> 投稿中…';
  try{
    await api('/api/post_draft', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id})
    });
    toast('✅ 投稿完了！', 'ok');
    loadDrafts(); loadStatus(); loadHistory();
  }catch(e){ toast('投稿失敗: '+e.message, 'err'); btn.disabled=false; btn.innerHTML=orig; }
}

async function deleteDraft(id){
  if(!confirm('この下書きを削除しますか？')) return;
  try{
    await api('/api/delete_draft', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id})
    });
    toast('削除しました', 'ok'); loadDrafts();
  }catch(e){ toast('削除失敗: '+e.message, 'err'); }
}

document.getElementById('btnGen').onclick = ()=>generate(false);
document.getElementById('btnSample').onclick = ()=>generate(true);
document.getElementById('btnRegen').onclick = ()=>generate(false);
document.getElementById('btnPost').onclick = postNow;
document.getElementById('btnSchedule').onclick = scheduleCurrent;
document.getElementById('btnMake').onclick = makeDrafts;
document.getElementById('btnReloadDrafts').onclick = loadDrafts;

loadStatus(); loadDrafts(); loadHistory();
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════
#  HTTP ハンドラ
# ════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # アクセスログは抑制（コンソールを静かに保つ）

    def _send_json(self, obj, code=200):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html):
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/" or path == "/index.html":
                self._send_html(PAGE)
            elif path == "/api/status":
                self._send_json(build_status())
            elif path == "/api/history":
                self._send_json(recent_history())
            elif path == "/api/drafts":
                self._send_json(list_drafts())
            else:
                self._send_json({"error": "not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._read_body()
            if path == "/api/generate":
                self._send_json(generate_preview(bool(body.get("sample"))))
            elif path == "/api/post":
                self._send_json(post_draft(body))
            elif path == "/api/make_drafts":
                self._send_json(make_drafts(int(body.get("n", 5))))
            elif path == "/api/post_draft":
                self._send_json(post_saved_draft(body.get("id", "")))
            elif path == "/api/delete_draft":
                self._send_json(delete_saved_draft(body.get("id", "")))
            elif path == "/api/schedule_preview":
                at = body.pop("at", "next-free-slot")
                self._send_json(schedule_preview_typefully(body, at))
            elif path == "/api/schedule_draft":
                self._send_json(schedule_saved_draft_typefully(
                    body.get("id", ""), body.get("at", "next-free-slot")))
            else:
                self._send_json({"error": "not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Threads × AI 投稿コンソール（Web UI）")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--open", action="store_true", help="起動後にブラウザを自動で開く")
    args = ap.parse_args(argv)

    url = f"http://{args.host}:{args.port}"
    st = build_status()
    print("=" * 56)
    print("  Threads × AI 投稿コンソール (webapp)")
    print("=" * 56)
    print(f"  Claude API : {'設定済み' if st['claude_ready'] else '未設定'}")
    print(f"  Threads API: {'設定済み' if st['threads_ready'] else '未設定'}")
    print(f"  投稿時間帯 : {', '.join(st['slots'])} / 1日上限 {st['daily_limit']}本")
    print("=" * 56)
    print(f"  ブラウザで開く →  {url}")
    print("  （停止するには Ctrl+C）")
    print("=" * 56)

    if args.open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました。")
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
