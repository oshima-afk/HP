# -*- coding: utf-8 -*-
"""
施工案件やスプレッドシートとは無関係な「お役立ち」記事(例: 専門家コラムなど、
一般的な豆知識・メンテナンス情報)を追加するスクリプト。ブログ(施工事例・
ボランティア活動など)とは別の棚(useful/ディレクトリ、ナビの「お役立ち」)に
記事を作成する。特定のお客様情報を扱わないため、個人情報の自動伏字チェックは
行わない。内容は投稿前に必ず目を通すこと。

使い方:
  python3 add_useful_post.py <タグ> <タイトル> <日付 YYYY-MM-DD> <本文テキストファイル> [写真...]

タグには「専門家コラム」など、記事の種類を表す短い文字列を指定する(一覧ページの
絞り込みチップに使われる)。本文テキストファイルは段落ごとに空行区切りで書き、
段落の先頭に「## 」を付けるとその段落が見出し(h2)として表示される
(「### 」でh3)。写真は省略可(汎用的な内容の記事はイラストや省略でもよい)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_blog_article as gen


def main():
    args = sys.argv[1:]
    if len(args) < 4:
        print("usage: add_useful_post.py <タグ> <タイトル> <日付> <本文テキストファイル> [写真...]")
        sys.exit(1)

    tag, title, date, body_path = args[0:4]
    photo_paths = args[4:]

    with open(body_path, encoding="utf-8") as f:
        raw = f.read()
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]

    os.makedirs(gen.USEFUL_IMAGES_DIR, exist_ok=True)
    slug_base = tag.replace(" ", "")
    existing = gen.load_useful_manifest()
    n = 1
    while any(i["slug"] == f"{slug_base}-{date}-{n}" for i in existing):
        n += 1
    slug = f"{slug_base}-{date}-{n}"

    copied = []
    for i, src in enumerate(photo_paths, start=1):
        dst_name = f"{slug}-photo{i}.jpg"
        gen.clean_and_copy_photo(src, os.path.join(gen.USEFUL_IMAGES_DIR, dst_name))
        copied.append(dst_name)

    article_html = gen.build_article_html(
        None, "", copied, title, paragraphs, "", category=tag, section="useful",
    )
    with open(os.path.join(gen.USEFUL_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(article_html)

    items = [i for i in existing if i["slug"] != slug]
    items.append({
        "slug": slug,
        "title": title,
        "date": date,
        "thumb": copied[0] if copied else "",
        "category": tag,
    })
    gen.save_useful_manifest(items)

    index_html = gen.build_useful_index_html(items)
    with open(os.path.join(gen.USEFUL_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"article: useful/{slug}.html")
    print(f"useful index updated with {len(items)} article(s)")


if __name__ == "__main__":
    main()
