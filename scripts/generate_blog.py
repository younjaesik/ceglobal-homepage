
import os
import json
import html
import re
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
POSTS = BLOG / "posts"
POSTS.mkdir(parents=True, exist_ok=True)

SITE = "https://ceglobal.org"
APP_URL = "https://apps.apple.com/app/id6779927785"

TOPICS = [
    "How to organize study notes for exam preparation",
    "How flashcards can improve active recall",
    "Practical ways to review PDF study materials",
    "How to create a consistent revision routine",
    "How to prepare for exams using digital notebooks",
    "Study techniques for remembering difficult concepts",
    "How to review notes across iPhone, iPad and Mac",
    "How to make the most of short study sessions",
    "Why spaced repetition matters for learning",
    "How to build better study habits"
]

today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
filename = POSTS / f"{today}.html"

if filename.exists():
    print("Today's article already exists. Skipping.")
    raise SystemExit(0)

existing = len(list(POSTS.glob("*.html")))
topic = TOPICS[existing % len(TOPICS)]

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.responses.create(
    model="gpt-4.1-mini",
    instructions=(
        "You write accurate, useful, original English study guides "
        "for the CEglobal website. Return only a JSON object with "
        "keys title, description, and article_html. "
        "article_html must contain only h2, h3, p, ul, ol, li, "
        "strong and em tags. No links, scripts, styles or markdown. "
        "Write 600-900 words of genuinely helpful educational content. "
        "Avoid keyword stuffing, exaggerated claims and fabricated research. "
        "Mention RecallNote naturally near the end, not repeatedly. "
        "RecallNote supports flashcards, PDF study materials, "
        "practice notebooks and iCloud synchronization across "
        "iPhone, iPad and Mac. Do not invent features, pricing, "
        "testimonials or scientific citations."
    ),
    input=f"Write an original study guide about: {topic}. Return the result as a valid JSON object.",
    text={"format": {"type": "json_object"}}
)

data = json.loads(response.output_text)
title = html.escape(data["title"])
description = html.escape(data["description"][:160], quote=True)
article = data["article_html"]

# Allow only a limited set of formatting tags.
article = re.sub(
    r"<(?!/?(?:h2|h3|p|ul|ol|li|strong|em)\s*>)[^>]*>",
    "",
    article,
    flags=re.I
)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | CEglobal</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{SITE}/blog/posts/{today}.html">
<style>
body{{font-family:system-ui,-apple-system,sans-serif;line-height:1.8;
margin:0;background:#f7f8fa;color:#202631}}
main{{max-width:780px;margin:40px auto;padding:35px;
background:white;border-radius:14px}}
h1{{font-size:2rem;line-height:1.3}}
h2{{margin-top:32px}}
a{{color:#1557b0}}
.cta{{padding:20px;background:#eef4ff;border-radius:12px;margin-top:36px}}
footer{{margin-top:36px;font-size:14px;color:#666}}
@media(max-width:820px){{main{{margin:12px;padding:20px}}}}
</style>
</head>
<body>
<main>
<nav><a href="/">CEglobal</a> / <a href="/blog/">Study Blog</a></nav>
<h1>{title}</h1>
<p><small>Published {today}</small></p>
<article>{article}</article>
<div class="cta">
<h2>Study with RecallNote</h2>
<p>Organize your study materials, review flashcards and use practice
notebooks with RecallNote for iPhone, iPad and Mac.</p>
<p><a href="{APP_URL}">View RecallNote on the App Store</a></p>
<p><a href="/recallnote/">Learn more about RecallNote</a></p>
</div>
<footer>© CEglobal</footer>
</main>
</body>
</html>"""

filename.write_text(page, encoding="utf-8")

posts = sorted(POSTS.glob("*.html"), reverse=True)
items = []
for post in posts:
    content = post.read_text(encoding="utf-8")
    match = re.search(r"<h1>(.*?)</h1>", content, re.S)
    post_title = re.sub(r"<[^>]+>", "", match.group(1)) if match else post.stem
    items.append(
        f'<li><a href="/blog/posts/{post.name}">'
        f'{html.escape(html.unescape(post_title))}</a>'
        f' <small>({post.stem})</small></li>'
    )

index = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Study Tips & Guides | CEglobal</title>
<meta name="description" content="Study techniques, flashcard guides,
PDF note-taking tips and exam preparation articles from CEglobal.">
<style>
body{{font-family:system-ui,-apple-system,sans-serif;line-height:1.8;
max-width:800px;margin:50px auto;padding:20px;color:#202631}}
a{{color:#1557b0}}
li{{padding:12px 0}}
</style>
</head>
<body>
<p><a href="/">← CEglobal Home</a></p>
<h1>Study Tips & Guides</h1>
<p>Helpful study techniques, exam preparation guides and digital
note-taking tips.</p>
<ul>{''.join(items)}</ul>
<p><a href="/recallnote/">Discover RecallNote</a></p>
</body>
</html>"""

(BLOG / "index.html").write_text(index, encoding="utf-8")
print(f"Created: {filename.relative_to(ROOT)}")
