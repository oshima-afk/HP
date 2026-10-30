# -*- coding: utf-8 -*-
"""
スプレッドシート(施工案件)に紐づかない記事(例: ボランティア活動、社員の日常)を
手動で追加するためのスクリプト。写真はExifを除去して取り込む。個人情報の自動伏字
チェックは行わない(お客様情報を扱わない記事のため)ので、内容は投稿前に目を通すこと。

使い方:
  python3 add_manual_post.py <category> <title> <date YYYY-MM-DD> <body_text_file> [--region 地域名] [photo1 photo2 ...]

body_text_file は、段落ごとに空行区切りで書いたテキストファイル。
--region を指定すると、写真の下に「エリア：<地域名>」と表示され、ブログ一覧の
「地域から探す」フィルタにもそのカテゴリの記事が出るようになる(省略可)。
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_blog_article as gen


def main():
    args = sys.argv[1:]
    region = ""
    if "--region" in args:
        idx = args.index("--region")
        if idx + 1 >= len(args):
            print("usage: --region の後に地域名を指定してください")
            sys.exit(1)
        region = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if len(args) < 4:
        print("usage: add_manual_post.py <category> <title> <date> <body_text_file> [--region 地域名] [photos...]")
        sys.exit(1)

    category, title, date, body_path = args[0:4]
    photo_paths = args[4:]

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

    area_caption = f"エリア：{region}" if region else ""
    article_html = gen.build_article_html(
        None, "", copied, title, paragraphs, area_caption, category=category,
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
        "region": region,
    })
    gen.save_manifest(items)

    index_html = gen.build_index_html(items)
    with open(os.path.join(gen.BLOG_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"article: blog/{slug}.html")
    print(f"index updated with {len(items)} article(s)")


if __name__ == "__main__":
    main()
