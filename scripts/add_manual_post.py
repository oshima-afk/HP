# -*- coding: utf-8 -*-
"""
スプレッドシート(施工案件)に紐づかない記事(例: ボランティア活動、社員の日常)を
手動で追加するためのスクリプト。写真はExifを除去して取り込む。個人情報の自動伏字
チェックは行わない(お客様情報を扱わない記事のため)ので、内容は投稿前に目を通すこと。

使い方:
  python3 add_manual_post.py <category> <title> <date YYYY-MM-DD> <body_text_file> [photo1 photo2 ...]

body_text_file は、段落ごとに空行区切りで書いたテキストファイル。
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_blog_article as gen


def main():
    if len(sys.argv) < 5:
        print("usage: add_manual_post.py <category> <title> <date> <body_text_file> [photos...]")
        sys.exit(1)

    category, title, date, body_path = sys.argv[1:5]
    photo_paths = sys.argv[5:]

    with open(body_path, encoding="utf-8") as f:
        raw = f.read()
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]

    os.makedirs(gen.IMAGES_DIR, exist_ok=True)
    slug_base = category.replace(" ", "")
    # 同じカテゴリ・日付の記事が複数ある場合のため、連番を振る
    existing = gen.load_manifest()
    n = 1
    while any(i["slug"] == f"{slug_base}-{date}-{n}" for i in existing):
        n += 1
    slug = f"{slug_base}-{date}-{n}"

    copied = []
    for i, src in enumerate(photo_paths, start=1):
        dst_name = f"{slug}-photo{i}.jpg"
        gen.clean_and_copy_photo(src, os.path.join(gen.IMAGES_DIR, dst_name))
        copied.append(dst_name)

    article_html = gen.build_article_html(
        None, "", copied, title, paragraphs, "", category=category,
    )
    with open(os.path.join(gen.BLOG_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(article_html)

    items = [i for i in existing if i["slug"] != slug]
    items.append({
        "slug": slug,
        "title": title,
        "date": date,
        "thumb": copied[0] if copied else "",
        "category": category,
    })
    gen.save_manifest(items)

    index_html = gen.build_index_html(items)
    with open(os.path.join(gen.BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"article: blog/{slug}.html")
    print(f"index updated with {len(items)} article(s)")


if __name__ == "__main__":
    main()
