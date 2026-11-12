# -*- coding: utf-8 -*-
"""
施工情報一覧シートの1件分のデータから、ブログ記事ページ(blog/<slug>.html)と
一覧ページ(blog/index.html)を自動生成する。

安全策: 本文・タイトルに「お客様氏名(苗字+名前)」「市+番地の組み合わせ」が
そのまま出てきた場合は自動的に伏字にする(人が確認する代わりの機械的なブロック)。
写真は「Claude 実験用」フォルダ内の当該案件フォルダから実写真を探し、
Exif(位置情報含む)を除去して書き出す。見つからない場合のみデモ画像で代用する。
"""
import html
import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(REPO, "blog")
IMAGES_DIR = os.path.join(BLOG_DIR, "images")
MANIFEST = os.path.join(BLOG_DIR, "articles.json")

USEFUL_DIR = os.path.join(REPO, "useful")
USEFUL_IMAGES_DIR = os.path.join(USEFUL_DIR, "images")
USEFUL_MANIFEST = os.path.join(USEFUL_DIR, "articles.json")


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_manifest(items):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def load_useful_manifest():
    if os.path.exists(USEFUL_MANIFEST):
        with open(USEFUL_MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_useful_manifest(items):
    os.makedirs(USEFUL_DIR, exist_ok=True)
    with open(USEFUL_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def redact(text, job):
    """お客様名・住所の断片が混入していたら伏字にする。何を伏せたか返す。

    last/first/banchiのいずれかが空(苗字・名前が分からない場合。例えば
    rewrite_old_articles.pyのように、個人情報を保存していない公開済み記事
    から再構成したjob dictを扱うとき)は、1文字や空白1つのような意味のない
    パターンが生まれて無関係な単語(「様子」「ご予約」等)を誤って伏字にして
    しまうため、氏名・住所のパターン自体を作らない。"""
    if not text:
        return text, []
    redactions = []
    last = job.get("last") or ""
    first = job.get("first") or ""
    banchi = job.get("banchi") or ""
    full_name_variants = []
    if last and first:
        full_name_variants = [
            f"{last}{first}",
            f"{last} {first}",
            f"{last}様{first}",
        ]
    addr = f"{job['city']}{banchi}"
    patterns = set(full_name_variants + ([addr] if banchi else []))
    out = text
    for p in patterns:
        if p and len(p) >= 2 and p in out:
            out = out.replace(p, "〇" * len(p))
            redactions.append(p)
    return out, redactions

    return out, redactions


WORK_DETAILS = {
    "壁塗り": (
        "外壁の塗り替えは、建物を雨風や紫外線から守るだけでなく、街並みの印象も大きく変える大切な工事です。",
        "まずは高圧洗浄で古い汚れやコケをしっかり洗い流し、ひび割れがあればシーリングの打ち替えなどで下地から補修。そのうえで下塗り・中塗り・上塗りと3回に分けて塗料を重ねていくことで、見た目の美しさと長持ちする塗膜を両立させています。",
        "塗料もシリコン・ラジカル制御・フッ素・無機など複数の選択肢があり、ご予算や求める耐用年数に応じてご提案しています。一般的な戸建住宅であれば工期は2週間前後(天候により変動)で、乾燥時間をしっかり確保しながら塗り重ねることが、仕上がりだけでなく将来の耐久性にも大きく影響します。",
    ),
    "外壁塗装": (
        "外壁の塗り替えは、建物を雨風や紫外線から守るだけでなく、街並みの印象も大きく変える大切な工事です。",
        "まずは高圧洗浄で古い汚れやコケをしっかり洗い流し、ひび割れがあればシーリングの打ち替えなどで下地から補修。そのうえで下塗り・中塗り・上塗りと3回に分けて塗料を重ねていくことで、見た目の美しさと長持ちする塗膜を両立させています。",
        "塗料もシリコン・ラジカル制御・フッ素・無機など複数の選択肢があり、ご予算や求める耐用年数に応じてご提案しています。一般的な戸建住宅であれば工期は2週間前後(天候により変動)で、乾燥時間をしっかり確保しながら塗り重ねることが、仕上がりだけでなく将来の耐久性にも大きく影響します。",
    ),
    "屋根塗装": (
        "屋根の塗装は、普段なかなか目にする機会がない分、劣化に気づきにくい箇所のひとつです。",
        "強い日差しや雨風を直接受け続ける屋根は、外壁以上に傷みが進みやすい場所。下地の状態を一つひとつ確認しながら下塗りを行い、耐候性の高い塗料で仕上げることで、住まい全体を長く守ります。",
        "外壁と同様、塗料はシリコン・ラジカル制御・フッ素・無機などから、ご予算と求める耐用年数に合わせてお選びいただけます。屋根は特に乾燥時間の確保が仕上がりを左右するため、天候を見ながら無理のない工程で進めています。",
    ),
    "屋根工事": (
        "屋根まわりの工事は、普段なかなか目にする機会がない分、劣化に気づきにくい箇所のひとつです。",
        "強い日差しや雨風を直接受け続ける屋根は、外壁以上に傷みが進みやすい場所。下地の状態を一つひとつ確認しながら、しっかりとした工事で住まい全体を長く守ります。",
        "見えない部分だからこそ、下地の状態を一つひとつ確認しながら、天候を見て無理のない工程で進めることを大切にしています。",
    ),
    "大規模修繕": (
        "大規模修繕は、建物全体の資産価値を長く保つために欠かせない工事です。",
        "外壁や屋根はもちろん、タイルの補修・シーリングの打ち替え・鉄部塗装・屋上防水・共用部の内装まで含めて、建物調査と報告書の作成→修繕計画と概算のご提示→住民説明→施工→完了報告という流れで計画的に進めていきます。",
        "大規模修繕でいちばん大事なのは、居住者の皆様の生活を止めないことだと考えています。作業時間や動線、洗濯物、駐車場の使い方まで事前に調整したうえで着工し、安心して長く住み続けていただける住環境を整えます。",
    ),
    "防水工事": (
        "防水工事は、雨漏りを未然に防ぎ、建物の寿命を延ばすうえで欠かせない工事です。",
        "ベランダや屋上、共用廊下など、水が溜まりやすい場所を中心に、下地の状態を一つひとつ確認しながら防水層を丁寧に仕上げていきます。",
        "ウレタン防水・シート防水・FRP防水など、場所や既存の状態に合わせて適した工法をご提案しています。見えなくなる下地の工程にこそ手間をかけることが、数年後の雨漏りを防ぐ一番の近道です。",
    ),
}
DEFAULT_DETAIL = (
    "住まいを長く大切に使っていただけるよう、今回も一つひとつの工程を丁寧に進めました。",
    "お客様の大切な住まいだからこそ、小さな工程にも手を抜かず、確認を重ねながら仕上げていくことを大切にしています。",
    "塗り替えや修繕は、仕上げたその日ではなく数年先に評価が出る仕事だと考えています。見えなくなる部分の工程にこそ手間をかける姿勢を、今回も大切にしました。",
)


def pick_work_detail(work):
    for key, triple in WORK_DETAILS.items():
        if key and key in work:
            return triple
    return DEFAULT_DETAIL


def format_date_jp(date_str):
    """'2026-10-30' のようなISO形式の日付を '2026年10月30日' に整える。"""
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", (date_str or "").strip())
    if not m:
        return date_str
    y, mo, d = m.groups()
    return f"{y}年{int(mo)}月{int(d)}日"


def format_month_jp(yyyy_mm):
    """'2026-11' のような年月を '2026年11月' に整える。"""
    m = re.match(r"^(\d{4})-(\d{1,2})$", (yyyy_mm or "").strip())
    if not m:
        return yyyy_mm
    y, mo = m.groups()
    return f"{y}年{int(mo)}月"


def build_body_paragraphs(job, memo):
    """案件データから、より具体的でお客様目線の、親しみやすいブログ口調の本文を組み立てる(テンプレートベースの自動生成)。"""
    work = job.get("work") or "塗装工事"
    city = job["city"]
    staff = job["staff"]
    start = format_date_jp(job["start"])
    end = format_date_jp(job["end"])
    intro_text, detail_text, extra_text = pick_work_detail(work)

    paragraphs = []
    paragraphs.append(f"みなさまこんにちは！{city}にて、{work}の工事をさせていただきましたので、現場の様子とあわせてご紹介します。")
    paragraphs.append(f"工期は{start}から{end}までで、担当は{staff}が務めさせていただきました。")
    paragraphs.append("## 今回の工事について")
    paragraphs.append(intro_text)
    paragraphs.append(detail_text)
    paragraphs.append(extra_text)
    memo_line = quote_field_memo(memo)
    if memo_line:
        paragraphs.append("## 現場担当より")
        paragraphs.append(memo_line)
        paragraphs.append("現場では、こうした細かな状況も見逃さず、必要な対応をそのつど確認しながら作業を進めています。")
    paragraphs.append("## おわりに")
    paragraphs.append("ご依頼くださり、本当にありがとうございました！これからも、お客様の大切な住まいを長く守るお手伝いができるよう、一つひとつの工事を丁寧に進めてまいります。")
    paragraphs.append("現地調査・お見積もりは無料で承っております。外壁や屋根のことで気になる点がございましたら、どんな小さなことでもお気軽にご相談くださいm(__)m")
    return paragraphs


def quote_field_memo(memo):
    """現場メモの内容は書き換えず、親しみやすい一文に整える。"""
    memo = (memo or "").strip()
    if not memo:
        return ""
    if not memo.endswith(("。", "！", "？")):
        memo += "。"
    return f"現場では、「{memo}」とのことでした。"


def find_job_folder(job, experiment_root):
    """撮影ガイド機能で作成される案件フォルダ(例: 01_大嶋俊介様邸)を探す。"""
    if not experiment_root or not os.path.isdir(experiment_root):
        return None
    folder_name = f"{job['no'].zfill(2)}_{job['last']}{job['first']}様邸"
    path = os.path.join(experiment_root, folder_name)
    return path if os.path.isdir(path) else None


def collect_real_photos(job, experiment_root):
    """案件フォルダ配下(日付サブフォルダ含む)の画像ファイルを全て集める。"""
    folder = find_job_folder(job, experiment_root)
    if not folder:
        return []
    photos = []
    for root, dirs, files in os.walk(folder):
        for fn in sorted(files):
            if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                photos.append(os.path.join(root, fn))
    return photos


def find_useful_topic_folder(no, topic, experiment_root):
    """「お役立ちコラム_投稿用」配下の、お題キューの行(No./お題)に対応するフォルダを探す。"""
    if not experiment_root or not os.path.isdir(experiment_root):
        return None
    base = os.path.join(experiment_root, "お役立ちコラム_投稿用")
    folder_name = f"{str(no).zfill(2)}_{topic}"
    path = os.path.join(base, folder_name)
    return path if os.path.isdir(path) else None


def collect_useful_photos(no, topic, experiment_root):
    """お題フォルダ配下の画像ファイルを全て集める(collect_real_photosのお役立ち版)。"""
    folder = find_useful_topic_folder(no, topic, experiment_root)
    if not folder:
        return []
    photos = []
    for root, dirs, files in os.walk(folder):
        for fn in sorted(files):
            if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                photos.append(os.path.join(root, fn))
    return photos


def clean_and_copy_photo(src, dst):
    """Exif(位置情報含む)を一切付与せずJPEGとして書き出す。"""
    from PIL import Image
    img = Image.open(src)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.save(dst, "JPEG", quality=92, exif=b"")


def build_article_html(job, memo_sentence, image_files, title, body_paragraphs, city_caption, category="施工事例", section="blog"):
    nav_header = build_nav_header(section)
    footer = FOOTER
    crumb_label = "ブログ" if section == "blog" else "お役立ち"
    back_link_text = "ブログ一覧へ戻る" if section == "blog" else "お役立ち一覧へ戻る"
    alt_text = "施工の様子" if category == "施工事例" else f"{category}の様子"
    imgs_html = ""
    for img in image_files:
        imgs_html += (
            f'<div class="ph-slot" style="position: static; aspect-ratio: 4 / 3; border-radius: var(--radius-md); overflow: hidden;">'
            f'<img src="images/{html.escape(img)}" alt="{html.escape(alt_text)}" style="width:100%;height:100%;object-fit:cover;display:block;"></div>\n        '
        )
    body_parts = []
    for p in body_paragraphs:
        if p.startswith("## "):
            body_parts.append(
                f"<h2 style=\"margin:1.8em 0 0.8em; font-size:20px; letter-spacing:0.04em; "
                f"border-left:4px solid var(--color-accent); padding-left:12px;\">{html.escape(p[3:])}</h2>"
            )
        elif p.startswith("### "):
            body_parts.append(
                f"<h3 style=\"margin:1.4em 0 0.6em; font-size:16px; letter-spacing:0.03em; "
                f"color: var(--color-neutral-700);\">{html.escape(p[4:])}</h3>"
            )
        else:
            body_parts.append(f"<p style=\"margin:0 0 1.4em; line-height:2;\">{html.escape(p)}</p>")
    body_html = "\n        ".join(body_parts)
    caption_html = ""
    if city_caption:
        caption_html = f'<p style="margin: 0 0 24px; font-size: 13px; letter-spacing: 0.08em; color: var(--color-neutral-600);">{html.escape(city_caption)}</p>'
    memo_html = ""
    if memo_sentence:
        memo_html = f'<p style="margin: 1.6em 0 0; padding: 16px; background: var(--color-accent-100); border-radius: var(--radius-md); line-height:1.9;">{html.escape(memo_sentence)}</p>'

    meta_desc = "大嶋塗装株式会社の施工事例です。" if category == "施工事例" else f"大嶋塗装株式会社の{category}の記事です。"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}｜大嶋塗装株式会社</title>
<meta name="description" content="{meta_desc}">
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
    <p style="margin: 0 0 10px; font-size: 12px; letter-spacing: 0.12em; color: var(--color-neutral-600);"><a href="index.html" style="color: var(--color-neutral-600);">{crumb_label}</a> / {html.escape(category)}</p>
    <h1 style="font-size: clamp(24px, 3.4vw, 34px); letter-spacing: 0.06em; margin: 0 0 24px;">{html.escape(title)}</h1>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 190px)); gap: 12px; margin-bottom: 12px; justify-content: start;">
        {imgs_html}
    </div>
    {caption_html}
    {body_html}
    {memo_html}
  </section>
  <section style="padding: clamp(32px, 5vw, 64px) clamp(20px, 5vw, 64px); border-top: 1px solid var(--color-divider); display: grid; justify-items: center; gap: 20px; text-align: center;">
    <div style="display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;">
      <a class="btn btn-primary" href="../index.html#contact">お問合せ・お見積もり</a>
      <a class="btn btn-secondary" href="index.html">{back_link_text}</a>
    </div>
  </section>
{footer}
</div>
<script src="../assets/site.js"></script>
</body>
</html>
"""


CATEGORIES = ["施工事例", "ボランティア活動", "社員の日常", "表彰"]


def build_index_html(items):
    cards = ""
    for item in sorted(items, key=lambda x: x["date"], reverse=True):
        category = item.get("category") or "施工事例"
        region = item.get("region") or ""
        month = (item.get("date") or "")[:7]
        cards += (
            '<a href="{slug}.html" data-category="{category_attr}" data-region="{region_attr}" '
            'data-month="{month_attr}" class="blog-card" '
            'style="display:block; text-decoration:none; color:var(--color-text); '
            'border:1px solid var(--color-divider); border-radius:var(--radius-md); overflow:hidden;">'
            '<div class="ph-slot" style="position:static; aspect-ratio:16/10;"><img src="images/{thumb}" alt="" '
            'style="width:100%;height:100%;object-fit:cover;display:block;"></div>'
            '<div style="padding:14px 16px;">'
            '<p style="margin:0 0 6px; font-size:11px; letter-spacing:0.08em; color:var(--color-accent-700);">{category}</p>'
            '<p style="margin:0 0 6px; font-size:11.5px; letter-spacing:0.08em; color:var(--color-neutral-600);">{date}</p>'
            '<p style="margin:0; font-size:15px; letter-spacing:0.04em;">{title}</p>'
            '</div></a>\n        '
        ).format(
            slug=item["slug"], thumb=item["thumb"], date=item["date"],
            title=html.escape(item["title"]), category=html.escape(category),
            category_attr=html.escape(category), region_attr=html.escape(region),
            month_attr=html.escape(month),
        )

    filter_buttons = '<button type="button" class="blog-filter-btn is-active" data-filter="all" onclick="filterBlog(this, \'category\', \'all\')" style="padding:8px 16px; border-radius:999px; border:1px solid var(--color-divider); background:var(--color-accent); color:#fff; font-size:13px; cursor:pointer;">\u3059\u3079\u3066</button>\n        '
    for cat in CATEGORIES:
        filter_buttons += (
            '<button type="button" class="blog-filter-btn" data-filter="{cat}" onclick="filterBlog(this, \'category\', \'{cat}\')" '
            'style="padding:8px 16px; border-radius:999px; border:1px solid var(--color-divider); background:transparent; color:var(--color-text); font-size:13px; cursor:pointer;">{cat}</button>\n        '
        ).format(cat=html.escape(cat))

    regions = sorted({item.get("region") for item in items if item.get("region")})
    region_buttons = ""
    for region in regions:
        region_buttons += (
            '<button type="button" class="blog-filter-btn" data-filter-region="{region}" onclick="filterBlog(this, \'region\', \'{region}\')" '
            'style="padding:8px 16px; border-radius:999px; border:1px solid var(--color-divider); background:transparent; color:var(--color-text); font-size:13px; cursor:pointer;">{region}</button>\n        '
        ).format(region=html.escape(region))

    if region_buttons:
        region_row = (
            '<div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-bottom:24px;">'
            '<span style="font-size:12px; color:var(--color-neutral-600); letter-spacing:0.08em;">地域から探す：</span>'
            f'{region_buttons}'
            '</div>'
        )
    else:
        region_row = ""

    months = sorted({(item.get("date") or "")[:7] for item in items if item.get("date")}, reverse=True)
    archive_buttons = ""
    for month in months:
        archive_buttons += (
            '<button type="button" class="blog-filter-btn" data-filter-month="{month}" onclick="filterBlog(this, \'month\', \'{month}\')" '
            'style="padding:8px 16px; border-radius:999px; border:1px solid var(--color-divider); background:transparent; color:var(--color-text); font-size:13px; cursor:pointer;">{label}</button>\n        '
        ).format(month=html.escape(month), label=html.escape(format_month_jp(month)))

    if archive_buttons:
        archive_row = (
            '<div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-bottom:24px;">'
            '<span style="font-size:12px; color:var(--color-neutral-600); letter-spacing:0.08em;">アーカイブ：</span>'
            f'{archive_buttons}'
            '</div>'
        )
    else:
        archive_row = ""

    region_row_margin = "12px" if (region_row or archive_row) else "24px"

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
{build_nav_header('blog')}
  <section style="padding: clamp(36px, 5vw, 64px) clamp(20px, 5vw, 64px) clamp(16px, 3vw, 32px); max-width: 1000px; margin: 0 auto;">
    <h1 style="font-size: clamp(26px, 3.8vw, 38px); letter-spacing: 0.1em; margin: 0 0 28px;">施工ブログ</h1>
    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:{region_row_margin};">
        {filter_buttons}
    </div>
    {region_row}
    {archive_row}
    <div id="blog-card-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap:20px;">
        {cards if cards else '<p>まだ記事がありません。</p>'}
    </div>
    <p id="blog-empty-msg" style="display:none; color:var(--color-neutral-600); margin-top:20px;">このカテゴリの記事はまだありません。</p>
  </section>
{FOOTER}
<script>
function filterBlog(btn, group, value) {{
  document.querySelectorAll('.blog-filter-btn').forEach(function(b) {{
    b.classList.remove('is-active');
    b.style.background = 'transparent';
    b.style.color = 'var(--color-text)';
  }});
  btn.classList.add('is-active');
  btn.style.background = 'var(--color-accent)';
  btn.style.color = '#fff';
  var any = false;
  document.querySelectorAll('.blog-card').forEach(function(card) {{
    var show;
    if (group === 'category') {{
      show = (value === 'all' || card.getAttribute('data-category') === value);
    }} else if (group === 'region') {{
      show = (card.getAttribute('data-region') === value);
    }} else {{
      show = (card.getAttribute('data-month') === value);
    }}
    card.style.display = show ? '' : 'none';
    if (show) any = true;
  }});
  document.getElementById('blog-empty-msg').style.display = any ? 'none' : 'block';
}}
</script>
</div>
<script src="../assets/site.js"></script>
</body>
</html>
"""


def build_useful_index_html(items):
    cards = ""
    for item in sorted(items, key=lambda x: x["date"], reverse=True):
        tag = item.get("category") or "お役立ち"
        cards += (
            '<a href="{slug}.html" data-category="{tag_attr}" class="useful-card" '
            'style="display:block; text-decoration:none; color:var(--color-text); '
            'border:1px solid var(--color-divider); border-radius:var(--radius-md); overflow:hidden;">'
            '<div class="ph-slot" style="position:static; aspect-ratio:16/10;"><img src="images/{thumb}" alt="" '
            'style="width:100%;height:100%;object-fit:cover;display:block;"></div>'
            '<div style="padding:14px 16px;">'
            '<p style="margin:0 0 6px; font-size:11px; letter-spacing:0.08em; color:var(--color-accent-700);">{tag}</p>'
            '<p style="margin:0 0 6px; font-size:11.5px; letter-spacing:0.08em; color:var(--color-neutral-600);">{date}</p>'
            '<p style="margin:0; font-size:15px; letter-spacing:0.04em;">{title}</p>'
            '</div></a>\n        '
        ).format(
            slug=item["slug"], thumb=item["thumb"], date=item["date"],
            title=html.escape(item["title"]), tag=html.escape(tag), tag_attr=html.escape(tag),
        )

    tags = sorted({item.get("category") for item in items if item.get("category")})
    filter_buttons = '<button type="button" class="useful-filter-btn is-active" data-filter="all" onclick="filterUseful(this, \'all\')" style="padding:8px 16px; border-radius:999px; border:1px solid var(--color-divider); background:var(--color-accent); color:#fff; font-size:13px; cursor:pointer;">すべて</button>\n        '
    for tag in tags:
        filter_buttons += (
            '<button type="button" class="useful-filter-btn" data-filter="{tag}" onclick="filterUseful(this, \'{tag}\')" '
            'style="padding:8px 16px; border-radius:999px; border:1px solid var(--color-divider); background:transparent; color:var(--color-text); font-size:13px; cursor:pointer;">{tag}</button>\n        '
        ).format(tag=html.escape(tag))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>お役立ち｜大嶋塗装株式会社</title>
<meta name="description" content="大嶋塗装株式会社がお届けする、外壁塗装や住まいのメンテナンスに関するお役立ち情報です。">
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
{build_nav_header('useful')}
  <section style="padding: clamp(36px, 5vw, 64px) clamp(20px, 5vw, 64px) clamp(16px, 3vw, 32px); max-width: 1000px; margin: 0 auto;">
    <h1 style="font-size: clamp(26px, 3.8vw, 38px); letter-spacing: 0.1em; margin: 0 0 12px;">お役立ち</h1>
    <p style="margin: 0 0 28px; color: var(--color-neutral-700); line-height: 1.9;">外壁塗装や住まいのメンテナンスに関する、ちょっとしたお役立ち情報をお届けします。</p>
    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px;">
        {filter_buttons}
    </div>
    <div id="useful-card-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap:20px;">
        {cards if cards else '<p>まだ記事がありません。</p>'}
    </div>
    <p id="useful-empty-msg" style="display:none; color:var(--color-neutral-600); margin-top:20px;">このカテゴリの記事はまだありません。</p>
  </section>
{FOOTER}
<script>
function filterUseful(btn, value) {{
  document.querySelectorAll('.useful-filter-btn').forEach(function(b) {{
    b.classList.remove('is-active');
    b.style.background = 'transparent';
    b.style.color = 'var(--color-text)';
  }});
  btn.classList.add('is-active');
  btn.style.background = 'var(--color-accent)';
  btn.style.color = '#fff';
  var any = false;
  document.querySelectorAll('.useful-card').forEach(function(card) {{
    var show = (value === 'all' || card.getAttribute('data-category') === value);
    card.style.display = show ? '' : 'none';
    if (show) any = true;
  }});
  document.getElementById('useful-empty-msg').style.display = any ? 'none' : 'block';
}}
</script>
</div>
<script src="../assets/site.js"></script>
</body>
</html>
"""


def build_nav_header(active="blog"):
    """blog/ 配下とuseful/ 配下、どちらもルートから1階層下にあるので相対パスは共通。
    active には "blog" か "useful" を渡す(どちらのナビ項目をハイライトするか)。"""
    def item(href, label, key):
        is_active = (key == active)
        color = "var(--color-accent)" if is_active else "var(--color-text)"
        current = ' aria-current="page"' if is_active else ""
        return (
            f'<a href="{href}"{current} style="display: grid; justify-items: center; gap: 8px; '
            f'text-decoration: none; color: {color}; padding: 6px 10px;">{label}</a>'
        )

    blog_href = "index.html" if active == "blog" else "../blog/index.html"
    useful_href = "index.html" if active == "useful" else "../useful/index.html"

    nav_items = "\n        ".join([
        item("../index.html#top", "ホーム", "home"),
        item("../works.html", "施工実績", "works"),
        item(blog_href, "ブログ", "blog"),
        item(useful_href, "お役立ち", "useful"),
        item("../contact.html", "お問合せ", "contact"),
    ])

    return f"""  <header style="position: sticky; top: 0; z-index: 20; background: var(--color-bg); border-bottom: 1px solid var(--color-divider); padding: 18px clamp(16px, 4vw, 56px) 10px;">
    <a href="../index.html#top" style="display: grid; justify-items: center; gap: 4px; text-decoration: none; color: var(--color-text); margin-bottom: 14px;">
      <span style="font-family: var(--font-heading); font-size: clamp(22px, 3.2vw, 32px); letter-spacing: 0.14em;">大嶋塗装株式会社</span>
      <span style="font-size: 10px; letter-spacing: 0.2em; color: var(--color-neutral-600); text-transform: uppercase; text-align: center;">Oshima Tosou Co., Ltd. — Since 1977</span>
    </a>
    <nav style="display: flex; justify-content: center; flex-wrap: wrap; gap: clamp(4px, 1.6vw, 22px);">
        {nav_items}
    </nav>
  </header>"""

FOOTER = """  <footer style="border-top: 1px solid var(--color-divider); background: var(--color-neutral-100); padding: 24px; text-align: center;">
    <p style="margin: 0; font-size: 11px; letter-spacing: 0.1em; color: var(--color-neutral-700);">© 大嶋塗装株式会社</p>
  </footer>"""


def main():
    job_path, memo, out_root = sys.argv[1], sys.argv[2], sys.argv[3]
    experiment_root = sys.argv[4] if len(sys.argv) > 4 else None
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    copied = []
    real_photos = collect_real_photos(job, experiment_root) if experiment_root else []
    if real_photos:
        for i, src in enumerate(real_photos, start=1):
            dst_name = f"{job['no'].zfill(2)}-photo{i}.jpg"
            clean_and_copy_photo(src, os.path.join(IMAGES_DIR, dst_name))
            copied.append(dst_name)
        print(f"[photos] real photo(s) used: {len(copied)} (from {find_job_folder(job, experiment_root)})")
    else:
        # フォールバック: 実写真が見つからない場合のみ、以前の実験フォルダのサンプル画像を使う
        src_images_dir = out_root
        src_files = ["sns_square_1080x1080.jpg", "sns_beforeafter_1080x1080.jpg"]
        for fn in src_files:
            src = os.path.join(src_images_dir, fn)
            if os.path.exists(src):
                dst_name = f"{job['no'].zfill(2)}-{fn}"
                shutil.copy(src, os.path.join(IMAGES_DIR, dst_name))
                copied.append(dst_name)
        print("[photos] no real photos found; used demo images as fallback")

    work = job.get("work") or "塗装工事"
    title = f"施工事例：{job['city']}エリアの{work}"
    title, redacted_title = redact(title, job)

    body_paragraphs = build_body_paragraphs(job, memo)
    clean_paragraphs = []
    all_redactions = list(redacted_title)
    for p in body_paragraphs:
        clean, red = redact(p, job)
        clean_paragraphs.append(clean)
        all_redactions += red

    slug = f"{job['no'].zfill(2)}-{job['end']}"
    city_caption = f"施工エリア：{job['city']}"
    article_html = build_article_html(job, "", copied, title, clean_paragraphs, city_caption)
    with open(os.path.join(BLOG_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(article_html)

    items = load_manifest()
    items = [i for i in items if i["slug"] != slug]
    items.append({
        "slug": slug,
        "title": title,
        "date": job["end"],
        "thumb": copied[0] if copied else "",
        "category": "施工事例",
        "region": job["city"],
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
