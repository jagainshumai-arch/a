"""バズ収集・分析モジュール — 影響力のある投稿を蓄積し、勝ちパターンを抽出する

Threads API には他者投稿の検索機能がないため、収集自体は手動（または競合データの
取り込み）で行い、「蓄積 → 構造化 → AI抽出」を自動化する。

シロウ式の sns-research/outputs/buzz/ 構造を再現:

    data/buzz/                      ← 生データ（収集したバズ投稿。1投稿1ファイル）
      _counter.txt                    連番カウンタ
      _index.md                       収集済み一覧（自動生成）
      NNN_{slug}.md                   YAMLフロントマター付きの投稿レコード

    knowledge/5_buzz/patterns.md    ← AIで抽出した最新の勝ちパターン（writerが読む）

CLI:
    python -m threads_automation.buzz import   # competitor_posts.json を取り込む
    python -m threads_automation.buzz list     # 蓄積済みバズ投稿を一覧表示
    python -m threads_automation.buzz analyze  # 勝ちパターンを抽出して patterns.md を更新
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BuzzPost:
    """収集した1件のバズ投稿"""
    text: str
    account: str = ""
    source: str = "threads"
    url: str = ""
    views: int = 0
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    niche: str = ""
    notes: str = ""
    captured_at: str = ""
    seq: int = 0

    @property
    def engagement_rate(self) -> float:
        return (self.likes + self.replies + self.reposts) / max(self.views, 1)


class BuzzLibrary:
    """バズ投稿の蓄積庫。生データの保存・索引・AI抽出を担う。"""

    def __init__(self, data_dir: str = "data", knowledge_dir: str | None = None):
        self.buzz_dir = Path(data_dir) / "buzz"
        self.counter_file = self.buzz_dir / "_counter.txt"
        self.index_file = self.buzz_dir / "_index.md"
        # 抽出結果の出力先（ナレッジ側）。writer がここを読む。
        if knowledge_dir is None:
            knowledge_dir = Path(__file__).resolve().parent / "knowledge"
        self.patterns_file = Path(knowledge_dir) / "5_buzz" / "patterns.md"

    # ── 収集 ──────────────────────────────────────────────

    def add(self, post: BuzzPost) -> Path:
        """バズ投稿を1件追加。連番ファイルを作り、索引を更新する。"""
        self.buzz_dir.mkdir(parents=True, exist_ok=True)
        seq = self._next_seq()
        post.seq = seq
        post.captured_at = post.captured_at or datetime.now().isoformat(timespec="seconds")

        path = self.buzz_dir / f"{seq:03d}_{self._slug(post)}.md"
        path.write_text(self._to_markdown(post), encoding="utf-8")
        self.rebuild_index()
        logger.info("Added buzz post #%d → %s", seq, path.name)
        return path

    def import_legacy(self, json_path: str | Path) -> int:
        """旧 competitor_posts.json を新構造へ取り込む。重複（本文一致）はスキップ。"""
        json_path = Path(json_path)
        if not json_path.exists():
            logger.info("No legacy file at %s", json_path)
            return 0
        records = json.loads(json_path.read_text(encoding="utf-8"))
        existing = {p.text.strip() for p in self.list_posts()}
        added = 0
        for r in records:
            text = (r.get("text") or "").strip()
            if not text or text in existing:
                continue
            self.add(BuzzPost(
                text=text,
                account=r.get("account", ""),
                source=r.get("source", "threads"),
                url=r.get("url", ""),
                views=int(r.get("estimated_views") or r.get("views") or 0),
                likes=int(r.get("estimated_likes") or r.get("likes") or 0),
                replies=int(r.get("replies") or 0),
                reposts=int(r.get("reposts") or 0),
                niche=r.get("niche", ""),
                notes=r.get("notes", ""),
            ))
            existing.add(text)
            added += 1
        logger.info("Imported %d legacy buzz posts", added)
        return added

    # ── 読み出し ──────────────────────────────────────────

    def list_posts(self) -> list[BuzzPost]:
        """蓄積済みのバズ投稿を連番順で返す。"""
        if not self.buzz_dir.is_dir():
            return []
        posts = []
        for f in sorted(self.buzz_dir.glob("[0-9]*.md")):
            try:
                posts.append(self._from_markdown(f.read_text(encoding="utf-8")))
            except Exception as e:  # 壊れたファイルは握りつぶして続行
                logger.warning("Skipping unreadable buzz file %s: %s", f.name, e)
        posts.sort(key=lambda p: p.seq)
        return posts

    def top_posts(self, n: int = 20) -> list[BuzzPost]:
        """エンゲージメント率の高い順に上位を返す。"""
        return sorted(self.list_posts(), key=lambda p: p.engagement_rate, reverse=True)[:n]

    # ── 索引 ──────────────────────────────────────────────

    def rebuild_index(self) -> Path:
        """_index.md を全レコードから再生成する。"""
        posts = self.list_posts()
        lines = [
            "# バズ投稿インデックス（自動生成）",
            "",
            f"> 最終更新: {datetime.now().isoformat(timespec='seconds')} / 収集数: {len(posts)}件",
            "> このファイルは `buzz.py` が自動生成する。手で編集しない。",
            "",
            "| # | アカウント | ニッチ | 表示 | いいね | ER | メモ |",
            "|---|----------|-------|-----:|------:|----:|------|",
        ]
        for p in posts:
            lines.append(
                f"| {p.seq:03d} | {p.account or '—'} | {p.niche or '—'} | "
                f"{p.views:,} | {p.likes:,} | {p.engagement_rate*100:.1f}% | "
                f"{(p.notes or '')[:30]} |"
            )
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.index_file

    # ── AI抽出 ────────────────────────────────────────────

    def analyze(self, ai, niche: str = "AI活用×仕組み化×収益化") -> Path:
        """蓄積したバズ投稿を AI に分析させ、勝ちパターンを patterns.md に書き出す。"""
        posts = self.top_posts(30)
        if not posts:
            raise ValueError("バズ投稿が0件です。先に /buzz add か import で収集してください。")

        dataset = [
            {
                "account": p.account,
                "niche": p.niche,
                "views": p.views,
                "likes": p.likes,
                "engagement_rate": round(p.engagement_rate, 4),
                "text": p.text,
                "notes": p.notes,
            }
            for p in posts
        ]

        prompt = f"""あなたはThreads×AI運用のバズ分析専門家です。
以下は実際に伸びた投稿の収集データ（エンゲージメント率の高い順）です。
これらを分析し、再現可能な「勝ちパターン」を抽出してください。

【発信ニッチ】{niche}

【収集データ】
{json.dumps(dataset, ensure_ascii=False, indent=2)}

以下のMarkdown構成で、そのままナレッジファイルに保存できる形で出力してください
（コードブロックで囲まず、見出しから直接書く）:

## 共通する勝ちの要素
- 伸びた投稿に共通する構造・1行目・テーマ・感情トリガーを箇条書きで5〜8個

## 抽出した型（再現テンプレート）
型ごとに「### 型名」「**使う場面**」「**1行目のテンプレ**」「**構成**」を書く。3〜5型。

## 数字・固有名詞の使われ方
- どんな数字/固有名詞がフックに効いているかの分析

## このニッチで避けるべきこと
- データから見えるスベりやすいパターン（景表法NG表現は別途 07_ng-rules.md 参照）

事実に基づき、抽象論を避け、すぐ使える具体性で書くこと。"""

        body = ai.generate(prompt, max_tokens=3000)
        header = (
            "# 5_buzz パターン（バズ分析の抽出結果）\n\n"
            f"> `buzz.py analyze` が自動生成。最終更新: "
            f"{datetime.now().isoformat(timespec='seconds')} / 分析対象: {len(posts)}件\n"
            "> writer はこの「実データから抽出した型」を最優先で参照する。\n"
            "> 手で編集せず、再収集→再分析で更新する。\n\n"
            "---\n\n"
        )
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)
        self.patterns_file.write_text(header + body.strip() + "\n", encoding="utf-8")
        logger.info("Wrote buzz patterns → %s", self.patterns_file)
        return self.patterns_file

    # ── 内部ヘルパ ────────────────────────────────────────

    def _next_seq(self) -> int:
        n = 0
        if self.counter_file.exists():
            n = int(self.counter_file.read_text(encoding="utf-8").strip() or "0")
        n += 1
        self.counter_file.write_text(str(n), encoding="utf-8")
        return n

    @staticmethod
    def _slug(post: BuzzPost) -> str:
        base = post.account.lstrip("@") or post.niche or post.text
        slug = re.sub(r"[^\w぀-ヿ一-鿿]+", "-", base).strip("-")
        return (slug[:24] or "post")

    @staticmethod
    def _to_markdown(post: BuzzPost) -> str:
        fm = {
            "seq": post.seq,
            "account": post.account,
            "source": post.source,
            "url": post.url,
            "views": post.views,
            "likes": post.likes,
            "replies": post.replies,
            "reposts": post.reposts,
            "engagement_rate": round(post.engagement_rate, 4),
            "niche": post.niche,
            "captured_at": post.captured_at,
            "notes": post.notes,
        }
        lines = ["---"]
        for k, v in fm.items():
            lines.append(f'{k}: {json.dumps(v, ensure_ascii=False)}')
        lines.append("---")
        lines.append("")
        lines.append(post.text)
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _from_markdown(content: str) -> BuzzPost:
        meta: dict = {}
        body = content
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", content, re.DOTALL)
        if m:
            for line in m.group(1).splitlines():
                if ":" not in line:
                    continue
                key, _, raw = line.partition(":")
                key = key.strip()
                raw = raw.strip()
                try:
                    meta[key] = json.loads(raw)
                except json.JSONDecodeError:
                    meta[key] = raw.strip('"')
            body = m.group(2).strip()
        return BuzzPost(
            text=body,
            account=meta.get("account", ""),
            source=meta.get("source", "threads"),
            url=meta.get("url", ""),
            views=int(meta.get("views", 0) or 0),
            likes=int(meta.get("likes", 0) or 0),
            replies=int(meta.get("replies", 0) or 0),
            reposts=int(meta.get("reposts", 0) or 0),
            niche=meta.get("niche", ""),
            notes=meta.get("notes", ""),
            captured_at=meta.get("captured_at", ""),
            seq=int(meta.get("seq", 0) or 0),
        )


def _main(argv: list[str]) -> int:
    import os

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cmd = argv[0] if argv else "list"
    data_dir = os.getenv("DATA_DIR", str(Path(__file__).resolve().parent / "data"))
    lib = BuzzLibrary(data_dir=data_dir)

    if cmd == "import":
        legacy = Path(data_dir) / "competitor_posts.json"
        n = lib.import_legacy(legacy)
        print(f"取り込み完了: {n}件")
    elif cmd == "list":
        posts = lib.top_posts(50)
        if not posts:
            print("バズ投稿はまだありません。`import` か `/buzz add` で収集してください。")
        for p in posts:
            print(f"#{p.seq:03d} ER={p.engagement_rate*100:5.1f}% "
                  f"views={p.views:>7,} {p.account or '—':<16} {p.text[:40]!r}")
    elif cmd == "analyze":
        from .ai_client import AIClient
        from .config import load_config
        cfg = load_config()
        if not (cfg.ai.anthropic_api_key or cfg.ai.openai_api_key):
            print("APIキーが未設定です（ANTHROPIC_API_KEY / OPENAI_API_KEY）。")
            return 1
        ai = AIClient(cfg.ai)
        out = lib.analyze(ai)
        print(f"勝ちパターンを書き出しました → {out}")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
