# -*- coding: utf-8 -*-
"""
施工情報一覧シートの1件分のデータから、ブログ記事ページ(blog/<slug>.html)と
一覧ページ(blog/index.html)を自動生成する。

安全策: 本文・タイトルに「お客様氏名(苗字+名前)」「市+番地の組み合わせ」が
そのまま出てきた場合は自動的に伏字にする(人が確認する代わりの機械的なブロック)。
"""
import html
import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(REPO, "blog")
IMAGES_DIR = os.path.join(BLOG_DIR, "images")
MANIFEST = os.path.join(BLOG_DIR, "articles.json")


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_manifest(items):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def redact(text, job):
    """お客様名・住所の断片が混入していたら伏字にする。何を伏せたか返す。"""
    if not text:
        return text, []
    redactions = []
    full_name_variants = [
        f"{job['last']}{job['first']}",
        f"{job['last']} {job['first']}",
        f"{job['last']}様{job['first']}",
    ]
    addr = f"{job['city']}{job['banchi']}"
    patterns = set(full_name_variants + ([addr] if job.get("banchi") else []))
    out = text
    for p in patterns:
        if p and p in out:
            out = out.replace(p, "〇" * len(p))
            redactions.append(p)
    return out, redactions


def build_article_html(job, memo, image_files, title, body_paragraphs):
    nav_header = NAV_HEADER
    footer = FOOTER
    imgs_html = ""
    for img in image_files:
        imgs_html += (
            f'<div class="ph-slot" style="aspect-ratio: 4 / 3; border-radius: var(--radius-md); overflow: hidden;">'
            f'<img src="images/{html.escape(img)}" alt="施工の様子" style="width:100%;height:100%;object-fit:cover;display:block;"></div>\n        '
        )
    body_html = "\n        ".join(f"<p style=\"margin:0 0 1.4em; line-height:2;\">{html.escape(p)}</p>" for p in body_paragraphs)
    memo_html = ""
    if memo:
        memo_html = f'<p style="margin: 1.6em 0 0; padding: 16px; background: var(--color-accent-100); border-radius: var(--radius-md); line-height:1.9;">現場より: {html.escape(memo)}</p>'

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}｜大嶋塗装株式会社</title>
<meta name="description" content="大嶋塗装株式会社の施工事例です。">
<link rel="stylesheet" href="../assets/styles.css">
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --font-heading: "Cormorant Garamond", "Shippori Mincho B1", serif;
    --font-body: "Lora", "Shippori Mincho B1", serif;
  }}
  body {{ margin: 0; -webkit-font-smoothing: antialiased; }}
  a {{ color: var(--color-accent-700); }}
  a:hover {{ color: var(--color-accent); }}
  h1, h2, h3, h4 {{ font-weight: 400; }}
</style>
</head>
<body>
<div style="background: var(--color-bg); color: var(--color-text); min-height: 100%;">
{nav_header}
  <section style="padding: clamp(36px, 5vw, 64px) clamp(20px, 5vw, 64px) clamp(16px, 3vw, 32px); max-width: 760px; margin: 0 auto;">
    <p style="margin: 0 0 10px; font-size: 12px; letter-spacing: 0.12em; color: var(--color-neutral-600);"><a href="index.html" style="color: var(--color-neutral-600);">ブログ</a> / 施工事例</p>
    <h1 style="font-size: clamp(24px, 3.4vw, 34px); letter-spacing: 0.06em; margin: 0 0 24px;">{html.escape(title)}</h1>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); gap: 14px; margin-bottom: 28px;">
        {imgs_html}
    </div>
    {body_html}
    {memo_html}
  </section>
  <section style="padding: clamp(32px, 5vw, 64px) clamp(20px, 5vw, 64px); border-top: 1px solid var(--color-divider); display: grid; justify-items: center; gap: 20px; text-align: center;">
    <div style="display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;">
      <a class="btn btn-primary" href="../index.html#contact">お問合せ・お見積もり</a>
      <a class="btn btn-secondary" href="index.html">ブログ一覧へ戻る</a>
    </div>
  </section>
{footer}
</div>
<script src="../assets/site.js"></script>
</body>
</html>
"""


def build_index_html(items):
    cards = ""
    for item in sorted(items, key=lambda x: x["date"], reverse=True):
        cards += (
            '<a href="{slug}.html" style="display:block; text-decoration:none; color:var(--color-text); '
            'border:1px solid var(--color-divider); border-radius:var(--radius-md); overflow:hidden;">'
            '<div class="ph-slot" style="aspect-ratio:16/10;"><img src="images/{thumb}" alt="" '
            'style="width:100%;height:100%;object-fit:cover;display:block;"></div>'
            '<div style="padding:14px 16px;">'
            '<p style="margin:0 0 6px; font-size:11.5px; letter-spacing:0.08em; color:var(--color-neutral-600);">{date}</p>'
            '<p style="margin:0; font-size:15px; letter-spacing:0.04em;">{title}</p>'
            '</div></a>\n        '
        ).format(slug=item["slug"], thumb=item["thumb"], date=item["date"], title=html.escape(item["title"]))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>施工ブログ｜大嶋塗装株式会社</title>
<meta name="description" content="大嶋塗装株式会社の施工事例・現場ブログです。">
<link rel="stylesheet" href="../assets/styles.css">
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho+B1:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --font-heading: "Cormorant Garamond", "Shippori Mincho B1", serif;
    --font-body: "Lora", "Shippori Mincho B1", serif;
  }}
  body {{ margin: 0; -webkit-font-smoothing: antialiased; }}
  a {{ color: var(--color-accent-700); }}
  a:hover {{ color: var(--color-accent); }}
  h1, h2, h3, h4 {{ font-weight: 400; }}
</style>
</head>
<body>
<div style="background: var(--color-bg); color: var(--color-text); min-height: 100%;">
{NAV_HEADER}
  <section style="padding: clamp(36px, 5vw, 64px) clamp(20px, 5vw, 64px) clamp(16px, 3vw, 32px); max-width: 1000px; margin: 0 auto;">
    <h1 style="font-size: clamp(26px, 3.8vw, 38px); letter-spacing: 0.1em; margin: 0 0 28px;">施工ブログ</h1>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap:20px;">
        {cards if cards else '<p>まだ記事がありません。</p>'}
    </div>
  </section>
{FOOTER}
</div>
<script src="../assets/site.js"></script>
</body>
</html>
"""


NAV_HEADER = """  <header style="position: sticky; top: 0; z-index: 20; background: var(--color-bg); border-bottom: 1px solid var(--color-divider); padding: 18px clamp(16px, 4vw, 56px) 10px;">
    <a href="../index.html#top" style="display: grid; justify-items: center; gap: 4px; text-decoration: none; color: var(--color-text); margin-bottom: 14px;">
      <span style="font-family: var(--font-heading); font-size: clamp(22px, 3.2vw, 32px); letter-spacing: 0.14em;">大嶋塗装株式会社</span>
      <span style="font-size: 10px; letter-spacing: 0.2em; color: var(--color-neutral-600); text-transform: uppercase; text-align: center;">Oshima Tosou Co., Ltd. — Since 1977</span>
    </a>
    <nav style="display: flex; justify-content: center; flex-wrap: wrap; gap: clamp(4px, 1.6vw, 22px);">
        <a href="../index.html#top" style="display: grid; justify-items: center; gap: 8px; text-decoration: none; color: var(--color-text); padding: 6px 10px;">ホーム</a>
        <a href="../works.html" style="display: grid; justify-items: center; gap: 8px; text-decoration: none; color: var(--color-text); padding: 6px 10px;">施工実績</a>
        <a href="index.html" aria-current="page" style="display: grid; justify-items: center; gap: 8px; text-decoration: none; color: var(--color-accent); padding: 6px 10px;">ブログ</a>
        <a href="../contact.html" style="display: grid; justify-items: center; gap: 8px; text-decoration: none; color: var(--color-text); padding: 6px 10px;">お問合せ</a>
    </nav>
  </header>"""

FOOTER = """  <footer style="border-top: 1px solid var(--color-divider); background: var(--color-neutral-100); padding: 24px; text-align: center;">
    <p style="margin: 0; font-size: 11px; letter-spacing: 0.1em; color: var(--color-neutral-700);">© 大嶋塗装株式会社</p>
  </footer>"""


def main():
    job_path, memo, out_root = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # --- demo用の写真(実写真が無いため、既存の実験フォルダのサンプル画像を使う) ---
    src_images_dir = out_root
    src_files = ["sns_square_1080x1080.jpg", "sns_beforeafter_1080x1080.jpg"]
    copied = []
    for fn in src_files:
        src = os.path.join(src_images_dir, fn)
        if os.path.exists(src):
            dst_name = f"{job['no'].zfill(2)}-{fn}"
            shutil.copy(src, os.path.join(IMAGES_DIR, dst_name))
            copied.append(dst_name)

    work = job.get("work") or "塗装工事"
    title = f"施工事例：{job['city']}エリアの{work}"
    title, redacted_title = redact(title, job)

    body_paragraphs = [
        f"{job['city']}エリアにて{work}を行いました。担当は{job['staff']}です。",
        f"工期は{job['start']}〜{job['end']}でした。",
    ]
    clean_paragraphs = []
    all_redactions = list(redacted_title)
    for p in body_paragraphs:
        clean, red = redact(p, job)
        clean_paragraphs.append(clean)
        all_redactions += red

    clean_memo, red_memo = redact(memo, job)
    all_redactions += red_memo

    slug = f"{job['no'].zfill(2)}-{job['end']}"
    article_html = build_article_html(job, clean_memo, copied, title, clean_paragraphs)
    with open(os.path.join(BLOG_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(article_html)

    items = load_manifest()
    items = [i for i in items if i["slug"] != slug]
    items.append({
        "slug": slug,
        "title": title,
        "date": job["end"],
        "thumb": copied[0] if copied else "",
    })
    save_manifest(items)

    index_html = build_index_html(items)
    with open(os.path.join(BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"article: blog/{slug}.html")
    print(f"index updated with {len(items)} article(s)")
    if all_redactions:
        print(f"[safety] redacted: {all_redactions}")
    else:
        print("[safety] no customer name/address fragments found in generated text")


if __name__ == "__main__":
    main()
