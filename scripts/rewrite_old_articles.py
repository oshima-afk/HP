# -*- coding: utf-8 -*-
"""
公開から一定期間(既定14日)経った「施工事例」記事を、現在の本文生成ロジック
(generate_blog_article.build_body_paragraphs/build_article_html)で書き直した
「下書き」を作成するスクリプト。

重要: 記事本体(blog/<slug>.html)は直接上書きしない。下書きは
blog/_rewrite_drafts/<slug>.html に書き出すだけなので、実際に公開するか
どうかは人が内容を確認してから apply_rewrite.py で反映する(このスクリプト
自体はGit操作もCloudflareへの公開も一切行わない)。

対象は「施工事例」カテゴリのみ(案件スプレッドシート駆動でテンプレート生成
された記事のみ、本文の構造が一定のため)。ボランティア活動・社員の日常・
表彰・お役立ちは、記事ごとに書かれた独自の文章のため対象外。

案件の元データ(氏名・住所・工種・工期・担当者・現場メモ)はお客様の個人情報
保護のため記事生成後は保存していない(redact()で伏字化される前提のデータは
どこにも残していない)ので、既存の公開済みHTML自体から
city/work/start/end/staff/memoを正規表現で読み取って job dict を復元する。
氏名・番地(last/first/banchi)は本文に含まれないため復元不要(空文字のまま)。

使い方:
  python3 rewrite_old_articles.py [--min-days 14] [--state ~/.blog_rewrite_state.json] [--notify-cooldown-days 5]
"""
import argparse
import datetime
import html as htmlmod
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_blog_article as gen

TITLE_RE = re.compile(r"^施工事例：(?P<city>.+?)エリアの(?P<work>.+)$")
PERIOD_RE_NEW = re.compile(
    r"工期は(?P<start>\d{4}年\d{1,2}月\d{1,2}日)から(?P<end>\d{4}年\d{1,2}月\d{1,2}日)までで、"
    r"担当は(?P<staff>.+?)が務めさせていただきました。"
)
PERIOD_RE_OLD = re.compile(
    r"(?P<start>\d{4}年\d{1,2}月\d{1,2}日)から(?P<end>\d{4}年\d{1,2}月\d{1,2}日)にかけて、.+?にて.+?を行いました。"
)
STAFF_RE_OLD = re.compile(r"担当は(?P<staff>.+?)。")
MEMO_RE = re.compile(r"現場では、「(?P<memo>.+?)」とのことでした。")
PHOTO_RE = re.compile(r'src="images/([^"]+)"')


def parse_jp_date(s):
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
    if not m:
        return None
    y, mo, d = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def extract_job_from_html(path):
    """既存の公開済み記事HTMLから、テンプレート再生成に必要な事実だけを復元する。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()

    title_m = re.search(r"<h1[^>]*>(.+?)</h1>", text)
    city = work = None
    if title_m:
        tm = TITLE_RE.match(htmlmod.unescape(strip_tags(title_m.group(1))))
        if tm:
            city, work = tm.group("city"), tm.group("work")

    start = end = staff = None
    pm = PERIOD_RE_NEW.search(text)
    if pm:
        start = parse_jp_date(pm.group("start"))
        end = parse_jp_date(pm.group("end"))
        staff = pm.group("staff")
    else:
        pm_old = PERIOD_RE_OLD.search(text)
        if pm_old:
            start = parse_jp_date(pm_old.group("start"))
            end = parse_jp_date(pm_old.group("end"))
        sm = STAFF_RE_OLD.search(text)
        if sm:
            staff = sm.group("staff")

    memo_m = MEMO_RE.search(text)
    memo = memo_m.group("memo") if memo_m else ""
    photos = PHOTO_RE.findall(text)

    if not all([city, work, start, end, staff]):
        return None, None, None

    job = {
        "no": "", "last": "", "first": "",
        "city": city, "banchi": "",
        "start": start, "end": end,
        "staff": staff, "work": work,
    }
    return job, memo, photos


def load_state(state_path):
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state_path, state):
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-days", type=int, default=14)
    ap.add_argument("--state", default=os.path.expanduser("~/.blog_rewrite_state.json"))
    ap.add_argument("--notify-cooldown-days", type=int, default=5)
    args = ap.parse_args()

    items = gen.load_manifest()
    state = load_state(args.state)
    today = datetime.date.today()

    draft_dir = os.path.join(gen.BLOG_DIR, "_rewrite_drafts")
    os.makedirs(draft_dir, exist_ok=True)

    candidates = []
    skipped = []
    for item in items:
        if item.get("category") != "施工事例":
            continue
        slug = item["slug"]
        pub_date = item.get("date")
        if not pub_date:
            continue
        try:
            pub = datetime.date.fromisoformat(pub_date)
        except ValueError:
            continue

        rec = state.get(slug, {})
        base_str = rec.get("last_rewritten") or pub_date
        try:
            base_date = datetime.date.fromisoformat(base_str)
        except ValueError:
            base_date = pub
        elapsed = (today - base_date).days
        if elapsed < args.min_days:
            continue

        last_notified = rec.get("last_notified")
        if last_notified:
            try:
                ln = datetime.date.fromisoformat(last_notified)
                if (today - ln).days < args.notify_cooldown_days:
                    continue
            except ValueError:
                pass

        article_path = os.path.join(gen.BLOG_DIR, f"{slug}.html")
        if not os.path.exists(article_path):
            continue

        job, memo, photos = extract_job_from_html(article_path)
        if not job:
            skipped.append(slug)
            continue

        new_title = f"施工事例：{job['city']}エリアの{job['work']}"
        new_body = gen.build_body_paragraphs(job, memo)
        clean_body = []
        for p in new_body:
            clean, _ = gen.redact(p, job)
            clean_body.append(clean)
        new_html = gen.build_article_html(
            job, "", photos, new_title, clean_body, f"施工エリア：{job['city']}"
        )
        draft_path = os.path.join(draft_dir, f"{slug}.html")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(new_html)

        state.setdefault(slug, {})["last_notified"] = today.isoformat()
        candidates.append({
            "slug": slug, "title": item.get("title"),
            "elapsed_days": elapsed, "draft": draft_path,
        })

    save_state(args.state, state)

    if skipped:
        print(f"[warn] 本文から案件データを復元できず、スキップした記事: {skipped}")
    if not candidates:
        print("見直し対象の記事はありませんでした。")
        return
    print(f"見直し候補: {len(candidates)}件")
    for c in candidates:
        print(f" - {c['slug']} (前回更新/公開から{c['elapsed_days']}日) -> 下書き: {c['draft']}")


if __name__ == "__main__":
    main()
