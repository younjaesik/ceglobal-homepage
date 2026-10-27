"""Generate one concise English PicPost article per Korea-local day."""
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.etree.ElementTree import Element, SubElement, ElementTree

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / 'picpost' / 'blog'
POSTS = BLOG / 'posts'
POSTS.mkdir(parents=True, exist_ok=True)
SITE = 'https://ceglobal.org'
APP_URL = 'https://apps.apple.com/app/id6821620482'
ANDROID_URL = 'https://play.google.com/store/apps/details?id=com.pachira.picpost'
GA_ID = 'G-4WDWDGBLQE'
TODAY = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d')
FILE = POSTS / f'{TODAY}.html'

TOPICS = [
    'How to remember the story behind a travel photo',
    'A simple way to add context to photos as you take them',
    'How to prepare a Threads photo post with less copying and pasting',
    'How to keep everyday photo memories organized',
    'How to turn several photo notes into one social media caption',
    'How to document a trip with pictures and short notes',
    'Why writing a quick note after a photo can help preserve memories',
    'How to share photos and captions without switching between note apps',
    'How to organize event photos with notes',
    'How to write useful notes for food and restaurant photos',
    'How to keep a simple photo journal on iPhone',
    'How to make photo sharing easier after a busy day',
    'How to capture the small details behind memorable moments',
    'How to prepare a multi-photo post on your iPhone',
    'How to add personal context to an existing iPhone photo',
]

INSTRUCTIONS = '''You are an English-language editorial writer for CEglobal, maker of PicPost EZ.
Write a useful, original 400-550 word article on the given topic.
Use 3-4 clear subheadings, short paragraphs, concrete tips, and one realistic example.
Be helpful even to readers who do not install the app. Avoid keyword stuffing,
unsupported research, testimonials, prices, and exaggerated marketing claims.
Mention PicPost EZ naturally once or twice in the article, with a relevant use case.

VERIFIED PICPOST FEATURES (iOS PicPost EZ and Android PicPost):
- Camera, built-in photo album, and import of existing photos from Apple Photos.
- Add text notes to individual photos.
- Select multiple photos and combine their individual notes into one text for sharing.
- Share selected photos and combined notes to Threads, with text included in the post.
- For Instagram and Facebook, share photos and copy combined notes to the clipboard
  so the user can paste them into the post.
- Share photos with messaging apps.

ACCURACY: PicPost EZ is the iOS app; PicPost is the Android app.
Both are available for their respective platforms. Avoid claiming feature parity
where not verified. Never mention Windows, Mac availability, or unverified features. Do not claim
fully automatic posting without user action, automatic publishing to Instagram
or Facebook, AI caption generation, cloud sync, or automatic handwriting recognition.
Do not invent subscription or purchase terms.

Return ONLY a JSON object with exactly these string keys:
"title", "description", "article_html".
Description must be under 160 characters. article_html must contain only
h2, h3, p, ul, ol, li, strong, em tags; no links, images, scripts, or wrappers.
Write all content in English.'''

ALLOWED_TAGS = {'h2', 'h3', 'p', 'ul', 'ol', 'li', 'strong', 'em'}

def validate(data):
    if not isinstance(data, dict) or set(data) != {'title', 'description', 'article_html'}:
        raise ValueError('Incorrect JSON fields')
    if any(not isinstance(v, str) or not v.strip() for v in data.values()):
        raise ValueError('Empty or non-string field')
    title, description, article = (data[k].strip() for k in ('title', 'description', 'article_html'))
    if len(title) > 120 or len(description) > 160:
        raise ValueError('Title or description too long')
    # Reject all tags not on the allowlist, and remove all attributes from allowed tags.
    for match in re.finditer(r'<[^>]*>', article):
        if not re.fullmatch(r'<\s*/?\s*(?:h2|h3|p|ul|ol|li|strong|em)\s*>', match.group(), re.I):
            raise ValueError('Unsupported HTML tag or attribute')
    plain = html.unescape(re.sub(r'<[^>]+>', ' ', article))
    count = len(re.findall(r"\b[\w'-]+\b", plain))
    if not 350 <= count <= 600:
        raise ValueError(f'Article length {count}, expected 350-600 words')
    if 'PicPost EZ' not in plain:
        raise ValueError('App not mentioned')
    if re.search(r'\b(Windows|MacOS|macOS)\b', plain, re.I):
        raise ValueError('Unsupported platform mentioned')
    return title, description, article


def analytics():
    return f'''<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('js',new Date());gtag('config','{GA_ID}');</script>'''


def page_style():
    return '''<style>
body{margin:0;background:#f7f8fa;color:#202631;font:16px/1.75 system-ui,-apple-system,sans-serif}
main{max-width:780px;margin:36px auto;padding:32px;background:white;border-radius:14px}
h1{line-height:1.3}h2{margin-top:30px}a{color:#1557b0}
.cta{background:#eef4ff;border-radius:12px;padding:20px;margin-top:32px}
.download-row{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:14px 0}
.download-row p{margin:0}
.download-qr{display:none;width:100px;height:100px;object-fit:contain;flex-shrink:0}
@media screen and (min-width:1025px) and (hover:hover) and (pointer:fine){
html:not(.mobile-device) .download-qr{display:block}
}
@media(max-width:820px){main{margin:12px;padding:20px}}
</style>'''




def add_promo_images():
    """Insert the linked promo image into today's new article only."""
    promo = (
        f'<a href="{APP_URL}" target="_blank" rel="noopener noreferrer" '
        'aria-label="Get PicPost EZ on the App Store">\n'
        '<img src="/blog/images/picpost_ad.png" '
        'alt="PicPost EZ: take photos, add notes, and share" '
        'loading="lazy" '
        'style="display:block;width:100%;height:auto;margin:30px auto;border-radius:12px;">\n'
        '</a>'
    )
    for post in [FILE] if FILE.exists() else []:
        body = post.read_text(encoding='utf-8')
        if '/blog/images/picpost_ad.png' not in body and '</article>' in body:
            body = body.replace('</article>', '</article>\n' + promo, 1)
            post.write_text(body, encoding='utf-8')
            print(f'Added promo image to {post.name}')

def write_index_and_sitemap():
    posts = sorted(POSTS.glob('*.html'), reverse=True)
    items = []
    for post in posts:
        body = post.read_text(encoding='utf-8')
        m = re.search(r'<h1>(.*?)</h1>', body, re.S)
        title = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))) if m else post.stem
        items.append(f'<li><a href="/picpost/blog/posts/{post.name}">{html.escape(title)}</a> <small>({post.stem})</small></li>')
    index = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Photo Notes & Sharing Tips | CEglobal</title>
<meta name="description" content="Practical iPhone photo journaling, note-taking and sharing guides from CEglobal.">
<link rel="canonical" href="{SITE}/picpost/blog/">
{analytics()}{page_style()}</head><body><main>
<p><a href="/">CEglobal Home</a></p><h1>Photo Notes & Sharing Tips</h1>
<p>Simple guides for capturing photos, remembering their stories, and sharing them.</p>
<ul>{''.join(items)}</ul>
<p><a href="{APP_URL}">Get PicPost EZ for iPhone on the App Store</a></p>
<p><a href="{ANDROID_URL}">Get PicPost for Android on Google Play</a></p>
</main></body></html>'''
    (BLOG / 'index.html').write_text(index, encoding='utf-8')
    sitemap = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in [BLOG / 'index.html', *posts]:
        url = SubElement(sitemap, 'url')
        suffix = '/picpost/blog/' if path.name == 'index.html' else f'/picpost/blog/posts/{path.name}'
        SubElement(url, 'loc').text = SITE + suffix
        if path == FILE:
            SubElement(url, 'lastmod').text = TODAY
    ElementTree(sitemap).write(BLOG / 'sitemap.xml', encoding='utf-8', xml_declaration=True)


def main():
    if FILE.exists():
        print(f'Article for {TODAY} already exists; updating index only.')
        write_index_and_sitemap()
        return
    topic = TOPICS[len(list(POSTS.glob('*.html'))) % len(TOPICS)]
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    error = ''
    for attempt in range(3):
        request = (
            f'Write an original English article about: {topic}. '
            'Keep it concise (400-550 words). '
            'Return the complete article as a valid JSON object.'
        )
        if error:
            request += f' The previous draft failed validation: {error}. Correct it.'
        response = client.responses.create(
            model='gpt-4.1-mini', instructions=INSTRUCTIONS, input=request,
            text={'format': {'type': 'json_object'}}, max_output_tokens=3000)
        try:
            title, description, article = validate(json.loads(response.output_text))
            break
        except (ValueError, json.JSONDecodeError) as exc:
            error = str(exc)
            print(f'Validation attempt {attempt+1} failed: {error}')
    else:
        raise RuntimeError(f'Failed to generate a valid article after 3 tries: {error}')

    # New articles only: do not rewrite previously published article HTML.
    page = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | CEglobal</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{SITE}/picpost/blog/posts/{TODAY}.html">
{analytics()}{page_style()}
<script>
(function(){{
  var ua=navigator.userAgent||'';
  var mobile=/Android|iPhone|iPad|iPod|Mobile|Tablet|Silk|Kindle/i.test(ua)
    ||(navigator.platform==='MacIntel' && navigator.maxTouchPoints>1)
    ||(navigator.maxTouchPoints>1 && screen.width<=1366);
  if(mobile)document.documentElement.classList.add('mobile-device');
}})();
</script>
</head><body><main>
<nav><a href="/">CEglobal</a> / <a href="/picpost/blog/">PicPost EZ Blog</a></nav>
<h1>{html.escape(title)}</h1><p><small>Published {TODAY}</small></p>
<article>{article}</article>
<div class="cta"><h2>Capture, Note &amp; Share with PicPost EZ</h2>
<p>Take photos, add notes to individual pictures, and combine notes when sharing multiple photos.
Share to Threads, or copy your notes for pasting into Instagram and Facebook posts.</p>
<div class="download-row">
<p><a href="{APP_URL}">Get PicPost EZ for iPhone on the App Store</a></p>
<img class="download-qr" src="/picpostEZios.png" alt="PicPost EZ iOS App Store QR code" loading="lazy">
</div>
<div class="download-row">
<p><a href="{ANDROID_URL}">Get PicPost for Android on Google Play</a></p>
<img class="download-qr" src="/picpostEZand.png" alt="PicPost Android Google Play QR code" loading="lazy">
</div>
</div>
<footer><small>© CEglobal</small></footer></main></body></html>'''
    FILE.write_text(page, encoding='utf-8')
    add_promo_images()
    write_index_and_sitemap()
    print(f'Created {FILE.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
