
import os
import json
import html
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
POSTS = BLOG / "posts"
POSTS.mkdir(parents=True, exist_ok=True)

SITE = "https://ceglobal.org"
APP_URL = "https://apps.apple.com/app/id6779927785"
ANDROID_URL = "https://play.google.com/store/apps/details?id=com.pachira.recallnote"
WINDOWS_URL = "https://apps.microsoft.com/detail/9P3MRK8KNDL8"

TOPICS = [
    "How to organize study notes for exam preparation",
    "How to use flashcards for active recall before exams",
    "How to study effectively with PDF textbooks and annotations",
    "How to build a practical weekly revision routine",
    "How to use digital practice notebooks for exam preparation",
    "How to remember difficult concepts with question-and-answer cards",
    "How to study across iPhone, iPad and Mac with iCloud sync",
    "How to make the most of a 20-minute study session",
    "How to plan spaced review sessions without complicated tools",
    "How to prepare a focused final review before an exam",
    "How to organize revision cards by subject and importance",
    "How to study from lecture PDFs and handwritten notes",
    "How to share revision cards with classmates",
    "How to create an exam-day revision checklist",
    "How to review large amounts of study material efficiently",
    "How to combine PDF reading, flashcards and practice notebooks",
    "How to identify weak topics before a major exam",
    "How to use active recall when studying law or other complex subjects",
    "How to review key definitions and formulas before an exam",
    "How to build a sustainable study system with digital tools"
]

today = datetime.now(
    ZoneInfo("Asia/Seoul")
).strftime("%Y-%m-%d")

filename = POSTS / f"{today}.html"

# Existing published posts are intentionally left unchanged.

if filename.exists():
    print("Today's article already exists. Skipping.")
    raise SystemExit(0)

existing = len(list(POSTS.glob("*.html")))
topic = TOPICS[existing % len(TOPICS)]

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

INSTRUCTIONS = """
You are a professional educational writer for CEglobal,
the independent developer of RecallNote.

Your job is to publish useful, original English-language
study guides for students and exam candidates.

EDITORIAL REQUIREMENTS

1. Write an original article of 400-650 English words.
2. Focus on solving one specific study problem.
3. Give concrete, actionable steps and realistic examples.
4. Use clear, natural English suitable for US and UK readers.
5. Avoid generic motivational filler and repetitive advice. Keep the article concise.
6. Explain why each recommended study technique is useful.
7. Include at least one practical study workflow.
8. Include examples relevant to real exam preparation.
9. Use 3-4 informative headings and short paragraphs.
10. Never fabricate scientific findings, statistics or citations.

RECALLNOTE: VERIFIED FEATURES

RecallNote is a study and revision application.

The following features are supported:

- Flashcards for reviewing questions and answers.
- Spaced repetition review using revision cards.
- Question-first flashcard review with answer reveal.
- Exam-focused quick review mode for rapid revision.
- Review selection by subject and importance in
  exam-focused review mode.
- PDF study material viewing.
- PDF annotation and handwriting where supported.
- PDF bookmarks and document navigation where supported.
- Practice notebooks for writing and reviewing notes.
- Sharing revision cards with other learners.
- iCloud synchronization between supported Apple devices:
  iPhone, iPad and Mac.
- Google Drive synchronization between supported Android and
  Windows devices when using the same Google account.
- Available on iPhone, iPad, Mac, Android and Windows.
- Offline study capabilities.

IMPORTANT ACCURACY RULES

Do not claim RecallNote:
- Creates PDF documents from arbitrary source files.
- Converts Word, PowerPoint or other files to PDF.
- Automatically generates flashcards using AI.
- Provides AI tutoring or AI-generated summaries.
- Predicts the exact moment a learner will forget something.
- Automatically grades exams.
- Offers OCR or text recognition.
- Supports real-time collaborative editing.
- Synchronizes Apple and Android devices through iCloud.
- Synchronizes Apple and Android/Windows devices with each other.
- Offers identical PDF annotation features on every platform.
- Offers any unverified feature.

Do not invent subscription prices, purchase requirements,
free-trial conditions, ratings or testimonials.

Do not assume every PDF annotation feature is available
on every platform. Explain that iCloud sync is for Apple devices
and Google Drive sync is for Android and Windows devices.
Do not imply synchronization between these two groups.

When describing a feature, explain how a student can use it
in a practical study scenario.

RECALLNOTE PROMOTION RULES

The article must remain genuinely useful even if the reader
does not install RecallNote.

Introduce RecallNote naturally where it can help with
the specific problem being discussed.

Include one realistic example of a study session using
RecallNote's verified features.

Avoid repeatedly mentioning the app name.
Do not write exaggerated marketing claims.
Do not compare RecallNote with competitors without evidence.

ARTICLE STRUCTURE

- Start with a concise, engaging introduction.
- Explain the study problem.
- Provide practical, numbered or clearly structured steps.
- Include a realistic worked example.
- Explain how to review progress or avoid common mistakes.
- Finish with a concise, actionable conclusion.

SEARCH QUALITY

Use a descriptive title matching the topic.
Write a natural meta description of 120-145 characters, including spaces.
Use meaningful headings.
Avoid keyword stuffing and repetitive SEO phrases.
Do not invent author credentials or external references.

OUTPUT FORMAT

Return ONLY a valid JSON object with exactly these keys:

"title"
"description"
"article_html"

article_html must use only:
h2, h3, p, ul, ol, li, strong, em

MANDATORY OUTPUT RULES:
- Mention the exact name RecallNote naturally in the article body at least once.
- Keep description at most 145 characters including spaces.
- Never output <br>, <br/>, <br />, or any HTML tag outside the allowed list.
- Use separate <p> paragraphs instead of HTML line breaks.

Do not include:
- h1
- Markdown
- JavaScript
- CSS
- hyperlinks
- images
- code blocks
- HTML document wrappers

Write the entire article in English.
"""

FORBIDDEN_PATTERNS = [
    r"\bAI[- ]generated flashcards\b",
    r"\bAI[- ]powered (?:tutor|summar(?:y|ies|ization))\b",
    r"\bautomatically (?:generate|create) (?:PDFs?|flashcards)\b",
    r"\bconvert(?:s|ing)? (?:Word|PowerPoint|documents?) to PDF\b",
    r"\bOCR\b",
    r"\boptical character recognition\b",
    r"\breal[- ]time collaborat(?:ion|ive editing)\b",
    r"\bautomatically grad(?:e|es|ing) exams?\b"
]

ALLOWED_TAGS = {
    "h2", "h3", "p", "ul", "ol", "li", "strong", "em"
}


def validate_article(data):
    if not isinstance(data, dict):
        raise ValueError("AI response is not a JSON object.")

    required = {"title", "description", "article_html"}

    if set(data.keys()) != required:
        raise ValueError(
            "AI response has missing or unexpected fields."
        )

    for key in required:
        if not isinstance(data[key], str):
            raise ValueError(f"Invalid field type: {key}")

        if not data[key].strip():
            raise ValueError(f"Empty field: {key}")

    title = data["title"].strip()
    description = data["description"].strip()
    article = data["article_html"].strip()

    if len(title) > 120:
        raise ValueError("Article title is too long.")

    if len(description) > 160:
        description = description[:157].rstrip(" ,;:-") + "..."

    plain_text = re.sub(r"<[^>]+>", " ", article)
    plain_text = html.unescape(plain_text)
    words = re.findall(r"\b[\w'-]+\b", plain_text)

    if not 300 <= len(words) <= 900:
        raise ValueError(
            f"Unexpected article length: {len(words)} words."
        )

    if "RecallNote" not in plain_text:
        raise ValueError(
            "Article body must mention the exact app name RecallNote at least once."
        )

    combined = title + " " + description + " " + plain_text

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, combined, flags=re.I):
            raise ValueError(
                f"Potential unsupported feature: {pattern}"
            )

    # Normalize harmless line-break tags before checking the strict allowlist.
    article = re.sub(r"<\s*br\s*/?\s*>", "</p><p>", article, flags=re.I)

    tags = re.findall(
        r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>",
        article
    )

    for tag in tags:
        if tag.lower() not in ALLOWED_TAGS:
            raise ValueError(
                f"Disallowed HTML tag: {tag}"
            )

    if re.search(
        r"<\s*(script|style|iframe|svg|img|a)\b",
        article,
        flags=re.I
    ):
        raise ValueError("Unsafe HTML element detected.")

    return title, description, article, len(words)


# Retry when the generated article fails validation. Never publish invalid content.
MAX_ARTICLE_ATTEMPTS = 3
validation_feedback = ""

for attempt in range(1, MAX_ARTICLE_ATTEMPTS + 1):
    print(f"Generating article (attempt {attempt}/{MAX_ARTICLE_ATTEMPTS})")
    request_text = (
        f"Write a detailed, original educational article about this topic: {topic}. "
        "Return the complete article as a valid JSON object. "
        "Follow all accuracy, structure and formatting rules. "
        "RecallNote supports spaced repetition with revision cards. "
        "You may describe spaced repetition as a supported feature. "
        "Do not invent unrelated features or claim exact forgetting-time prediction. "
        "Mention RecallNote in the article body. Keep the meta description under 145 characters. "
        "Do not use br tags; use p tags for paragraphs."
    )
    if validation_feedback:
        request_text += (
            " The previous draft failed validation for this reason: "
            + validation_feedback
            + ". Rewrite the article to correct the issue."
        )

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=INSTRUCTIONS,
        input=request_text,
        text={"format": {"type": "json_object"}},
        max_output_tokens=4500
    )

    try:
        if not response.output_text:
            raise ValueError("AI returned no article content.")
        data = json.loads(response.output_text)
        title, description, article, word_count = validate_article(data)
        break
    except (ValueError, json.JSONDecodeError) as exc:
        validation_feedback = str(exc)
        print(f"Article validation failed (attempt {attempt}): {exc}")
        if attempt == MAX_ARTICLE_ATTEMPTS:
            raise RuntimeError(
                f"Article generation failed after {MAX_ARTICLE_ATTEMPTS} attempts. "
                f"Last validation error: {exc}"
            ) from exc

print(f"Validated article: {title}")
print(f"Word count: {word_count}")

safe_title = html.escape(title)
safe_description = html.escape(description, quote=True)

# Strip unexpected attributes from permitted tags.
article = re.sub(
    r"<\s*(/?)\s*(h2|h3|p|ul|ol|li|strong|em)\b[^>]*>",
    lambda m: f"<{m.group(1)}{m.group(2).lower()}>",
    article,
    flags=re.I
)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4WDWDGBLQE"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-4WDWDGBLQE');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>
(function() {{
    var ua = navigator.userAgent || "";
    var mobile = /Android|iPhone|iPad|iPod|Mobile|Tablet|Silk|Kindle/i.test(ua)
        || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
        || (navigator.maxTouchPoints > 1 && screen.width <= 1366);
    if (mobile) document.documentElement.classList.add("mobile-device");
}})();
</script>
<title>{safe_title} | CEglobal</title>
<meta name="description" content="{safe_description}">
<link rel="canonical" href="{SITE}/blog/posts/{today}.html">
<style>
body{{
    font-family:system-ui,-apple-system,sans-serif;
    line-height:1.8;
    margin:0;
    background:#f7f8fa;
    color:#202631;
}}
main{{
    max-width:780px;
    margin:40px auto;
    padding:35px;
    background:white;
    border-radius:14px;
}}
h1{{
    font-size:2rem;
    line-height:1.3;
}}
h2{{
    margin-top:32px;
}}
h3{{
    margin-top:24px;
}}
a{{
    color:#1557b0;
}}
.cta{{
    padding:20px;
    background:#eef4ff;
    border-radius:12px;
    margin-top:36px;
}}
.download-row{{
    display:flex;
    align-items:center;
    gap:16px;
    flex-wrap:wrap;
    margin:12px 0;
}}
.download-row .download-qr{{
    display:none;
}}
@media screen and (min-width:1025px) and (hover:hover) and (pointer:fine){{
    html:not(.mobile-device) .download-row .download-qr{{
        display:block;
        width:100px;
        height:100px;
        object-fit:contain;
    }}
}}
.recallnote-banner{{
    display:block;
    width:100%;
    max-width:500px;
    height:auto;
    margin:24px auto 0;
    border-radius:12px;
}}
footer{{
    margin-top:36px;
    font-size:14px;
    color:#666;
}}
@media(max-width:820px){{
    main{{
        margin:12px;
        padding:20px;
    }}
}}
</style>
</head>
<body>
<main>
<nav>
<a href="/">CEglobal</a> /
<a href="/blog/">Study Blog</a>
</nav>

<h1>{safe_title}</h1>
<p><small>Published {today}</small></p>

<article>
{article}
</article>

<div class="cta">
<h2>Study with RecallNote</h2>
<p>
Organize study materials, review flashcards with spaced repetition,
annotate supported PDF documents and use
practice notebooks with RecallNote.
</p>
<p>
Sync across supported Apple devices with iCloud,
or between Android and Windows with Google Drive.
These are separate synchronization systems.
</p>
<div class="download-row">
<a href="{APP_URL}">
Download for iPhone, iPad and Mac (App Store)
</a>
<img class="download-qr" src="/recallnoteios.png" alt="RecallNote App Store QR code" loading="lazy">
</div>
<div class="download-row">
<a href="{ANDROID_URL}">
Download for Android (Google Play)
</a>
<img class="download-qr" src="/recallnoteand.png" alt="RecallNote Google Play QR code" loading="lazy">
</div>
<p>
<a href="{WINDOWS_URL}">
Download for Windows (Microsoft Store)
</a>
</p>
<p>
<a href="/recallnote/">
Learn more about RecallNote
</a>
</p>
<p>
<a href="/recallnote/" aria-label="Explore RecallNote and download for your device">
<img class="recallnote-banner" src="/blog/images/recallnote_ad.png" alt="RecallNote: Stop forgetting. Start RecallNote. Download now." loading="lazy">
</a>
</p>
</div>

<footer>© CEglobal</footer>
</main>
</body>
</html>"""

# Write only after article validation succeeds.
filename.write_text(page, encoding="utf-8")

# Do not modify previously published articles.

posts = sorted(
    POSTS.glob("*.html"),
    reverse=True
)

items = []

for post in posts:
    content = post.read_text(encoding="utf-8")

    match = re.search(
        r"<h1>(.*?)</h1>",
        content,
        flags=re.S
    )

    if match:
        post_title = re.sub(
            r"<[^>]+>",
            "",
            match.group(1)
        )
        post_title = html.unescape(post_title)
    else:
        post_title = post.stem

    items.append(
        f'<li><a href="/blog/posts/{post.name}">'
        f'{html.escape(post_title)}</a>'
        f' <small>({post.stem})</small></li>'
    )

index = f"""<!DOCTYPE html>
<html lang="en">
<head>
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4WDWDGBLQE"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-4WDWDGBLQE');
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Study Tips &amp; Guides | CEglobal</title>
<meta name="description"
content="Practical study techniques, flashcard guides,
PDF annotation tips and exam preparation
articles from CEglobal.">
<style>
body{{
    font-family:system-ui,-apple-system,sans-serif;
    line-height:1.8;
    max-width:800px;
    margin:50px auto;
    padding:20px;
    color:#202631;
}}
a{{
    color:#1557b0;
}}
li{{
    padding:12px 0;
}}
@media(max-width:820px){{
    body{{
        margin:12px;
        padding:15px;
    }}
}}
</style>
</head>
<body>

<p><a href="/">← CEglobal Home</a></p>

<h1>Study Tips &amp; Guides</h1>

<p>
Practical study strategies, exam preparation
guides and digital note-taking tips.
</p>

<ul>
{''.join(items)}
</ul>

<p>
<a href="/recallnote/">
Discover RecallNote
</a>
</p>
<p>
Get RecallNote:
<a href="{APP_URL}">App Store</a> ·
<a href="{ANDROID_URL}">Google Play</a> ·
<a href="{WINDOWS_URL}">Microsoft Store</a>
</p>

</body>
</html>"""

(BLOG / "index.html").write_text(
    index,
    encoding="utf-8"
)

print(f"Created: {filename.relative_to(ROOT)}")
print("Blog index updated successfully.")


# Automatically update the blog sitemap.
from xml.etree.ElementTree import Element, SubElement, ElementTree

sitemap = Element(
    "urlset",
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
)

blog_urls = [BLOG / "index.html"] + sorted(
    POSTS.glob("*.html"),
    reverse=True
)

for file in blog_urls:
    relative_path = file.relative_to(ROOT).as_posix()

    if relative_path.endswith("/index.html"):
        url = f"{SITE}/{relative_path[:-10]}"
    else:
        url = f"{SITE}/{relative_path}"

    entry = SubElement(sitemap, "url")
    SubElement(entry, "loc").text = url

    if file == filename:
        SubElement(entry, "lastmod").text = today

ElementTree(sitemap).write(
    ROOT / "sitemap.xml",
    encoding="utf-8",
    xml_declaration=True
)

print("Sitemap updated successfully.")
