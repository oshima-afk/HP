# -*- coding: utf-8 -*-
"""
rewrite_old_articles.py が blog/_rewrite_drafts/<slug>.html に用意した下書きを、
人が内容を確認したうえで本番の blog/<slug>.html に反映するスクリプト。
Git操作・Cloudflareへの公開は行わない(それは別途、通常の公開フローで行う)。

使い方:
  python3 apply_rewrite.py <slug1> [<slug2> ...]
  python3 apply_rewrite.py --all   # 下書きが存在する記事を全て反映
"""
import datetime
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_blog_article as gen

STATE_PATH = os.path.expanduser("~/.blog_rewrite_state.json")


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    args = sys.argv[1:]
    if not args:
        print("使い方: python3 apply_rewrite.py <slug1> [<slug2> ...] または --all")
        sys.exit(1)

    draft_dir = os.path.join(gen.BLOG_DIR, "_rewrite_drafts")

    if args == ["--all"]:
        if not os.path.isdir(draft_dir):
            print("下書きフォルダがありません。")
            return
        slugs = [fn[:-5] for fn in os.listdir(draft_dir) if fn.endswith(".html")]
    else:
        slugs = args

    state = load_state()
    today = datetime.date.today().isoformat()
    applied = []
    for slug in slugs:
        draft = os.path.join(draft_dir, f"{slug}.html")
        live = os.path.join(gen.BLOG_DIR, f"{slug}.html")
        if not os.path.exists(draft):
            print(f"[skip] {slug}: 下書きが見つかりません({draft})")
            continue
        shutil.copy(draft, live)
        os.remove(draft)
        state.setdefault(slug, {})["last_rewritten"] = today
        state[slug].pop("last_notified", None)
        applied.append(slug)
        print(f"[applied] {slug}")

    save_state(state)
    if applied:
        print(f"{len(applied)}件を本番ファイルに反映しました。この後、通常のGit公開フロー"
              f"(コミット→demoブランチpush→本番ブランチへマージ→push→反映確認)で公開してください。")


if __name__ == "__main__":
    main()
