
#!/usr/bin/env python3
"""
Auto-generates a cybersecurity article using Claude API
and saves it as HTML ready for Netlify.
"""

import anthropic
import json
import os
import random
from datetime import datetime
from slugify import slugify

# ── TOPIC LIST ──────────────────────────────────────────────────────────────
TOPICS = [
    # Beginner
    ("What is ethical hacking and how to get started", "beginner"),
    ("How to use Nmap for network scanning — beginner guide", "beginner"),
    ("Linux basics every hacker needs to know", "beginner"),
    ("What is a VPN and does it really protect you", "beginner"),
    ("How to set up Kali Linux for the first time", "beginner"),
    ("Understanding firewalls: how they work and how to bypass them", "beginner"),
    ("What is social engineering and how to protect yourself", "beginner"),
    ("How to use Wireshark to analyze network traffic", "beginner"),
    ("Password cracking 101: how hackers break your passwords", "beginner"),
    ("What is a man-in-the-middle attack and how to prevent it", "beginner"),

    # Tools
    ("Metasploit Framework: complete beginner guide", "tools"),
    ("Burp Suite for web application testing", "tools"),
    ("How to use Hydra for brute force attacks ethically", "tools"),
    ("John the Ripper: password cracking tutorial", "tools"),
    ("Aircrack-ng: WiFi security testing guide", "tools"),
    ("Sqlmap tutorial: automated SQL injection testing", "tools"),
    ("Nikto web scanner: find vulnerabilities in minutes", "tools"),
    ("How to use Gobuster for directory enumeration", "tools"),
    ("Hashcat GPU password cracking guide", "tools"),
    ("Netcat: the swiss army knife of networking", "tools"),

    # Certifications
    ("CompTIA Security+ study guide 2026", "certifications"),
    ("How to pass the CEH exam on your first try", "certifications"),
    ("OSCP certification: complete roadmap and tips", "certifications"),
    ("eJPT certification: best entry-level hacking cert", "certifications"),
    ("CISSP vs CISM: which certification is right for you", "certifications"),

    # News & concepts
    ("Top cybersecurity threats to watch in 2026", "news"),
    ("How ransomware attacks work step by step", "news"),
    ("What is zero-day vulnerability and why it matters", "news"),
    ("Supply chain attacks: how hackers target software vendors", "news"),
    ("Bug bounty hunting: how to make money finding vulnerabilities", "news"),

    # CVE
    ("CVE-2024-6387 regreSSHion: the OpenSSH vulnerability explained", "cve"),
    ("CVE-2024-3400 Palo Alto PAN-OS command injection breakdown", "cve"),
    ("CVE-2024-21762 Fortinet SSL VPN critical vulnerability analysis", "cve"),
    ("CVE-2023-44487 HTTP/2 Rapid Reset attack explained", "cve"),
    ("CVE-2023-20198 Cisco IOS XE privilege escalation deep dive", "cve"),
    ("CVE-2023-4966 Citrix Bleed session hijacking vulnerability", "cve"),
    ("CVE-2024-1708 ConnectWise ScreenConnect path traversal", "cve"),
    ("CVE-2024-27198 JetBrains TeamCity authentication bypass", "cve"),
    ("Log4Shell CVE-2021-44228 still relevant in 2026", "cve"),
    ("ProxyLogon CVE-2021-26855 Microsoft Exchange explained", "cve"),

    # CVE / Advanced
    ("SQL injection explained: from basics to exploitation", "tutorials"),
    ("Cross-site scripting (XSS): how it works and how to prevent it", "tutorials"),
    ("How buffer overflow attacks work", "tutorials"),
    ("Understanding OWASP Top 10 vulnerabilities 2026", "tutorials"),
    ("How to do a basic penetration test on your own network", "tutorials"),
    ("Privilege escalation techniques on Linux", "tutorials"),
    ("Windows privilege escalation for beginners", "tutorials"),
    ("How to stay anonymous online: Tor, proxychains and more", "tutorials"),
    ("CTF competitions: how to get started and win", "tutorials"),
    ("How to build a home hacking lab for free", "tutorials"),
]

# ── TEMPLATE ────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-047Q5LKQHS"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{ dataLayer.push(arguments); }}
    gtag('js', new Date());
    gtag('config', 'G-047Q5LKQHS');
  </script>

  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | HowCanIHack.com</title>
  <meta name="description" content="{meta_description}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{meta_description}" />
  <meta property="og:type" content="article" />
  <link rel="canonical" href="https://howcanihack.com/{category}/{slug}.html" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --navy: #0a1628; --blue: #1d4ed8; --sky: #dbeafe;
      --gray50: #f8fafc; --gray100: #f1f5f9; --gray200: #e2e8f0;
      --gray600: #475569; --text: #0f172a;
      --mono: 'JetBrains Mono', monospace;
      --serif: 'DM Serif Display', serif;
      --sans: 'DM Sans', sans-serif;
    }}
    body {{ font-family: var(--sans); color: var(--text); background: #fff; }}
    nav {{
      position: sticky; top: 0; z-index: 100;
      background: rgba(255,255,255,0.92); backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--gray200);
      padding: 0 2rem; display: flex; align-items: center;
      justify-content: space-between; height: 64px;
    }}
    .nav-logo {{
      font-family: var(--mono); font-size: 1rem; font-weight: 600;
      color: var(--navy); text-decoration: none;
    }}
    .nav-logo span {{ color: var(--blue); }}
    .nav-home {{ font-size: 0.875rem; color: var(--gray600); text-decoration: none; }}
    .nav-home:hover {{ color: var(--blue); }}
    .article-wrap {{ max-width: 780px; margin: 0 auto; padding: 3rem 1.5rem 5rem; }}
    .article-meta {{
      display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;
      margin-bottom: 2rem;
    }}
    .tag {{
      display: inline-block; background: var(--sky); color: var(--blue);
      font-size: 0.7rem; font-weight: 600; font-family: var(--mono);
      padding: 0.2rem 0.6rem; border-radius: 4px; text-transform: uppercase;
    }}
    .date {{ font-family: var(--mono); font-size: 0.78rem; color: var(--gray600); }}
    h1 {{
      font-family: var(--serif); font-size: clamp(2rem, 5vw, 3rem);
      color: var(--navy); line-height: 1.15; margin-bottom: 1.5rem;
    }}
    .lead {{
      font-size: 1.15rem; color: var(--gray600); line-height: 1.8;
      margin-bottom: 2.5rem; border-left: 3px solid var(--blue);
      padding-left: 1.25rem;
    }}
    h2 {{
      font-family: var(--serif); font-size: 1.6rem; color: var(--navy);
      margin: 2.5rem 0 1rem;
    }}
    h3 {{ font-size: 1.1rem; font-weight: 600; color: var(--navy); margin: 1.5rem 0 0.75rem; }}
    p {{ line-height: 1.8; color: #334155; margin-bottom: 1.25rem; }}
    pre {{
      background: var(--navy); color: #e2e8f0; border-radius: 10px;
      padding: 1.5rem; overflow-x: auto; margin: 1.5rem 0;
      font-family: var(--mono); font-size: 0.85rem; line-height: 1.7;
    }}
    code {{ font-family: var(--mono); font-size: 0.875em; background: var(--sky); color: var(--blue); padding: 0.1em 0.4em; border-radius: 3px; }}
    pre code {{ background: none; color: inherit; padding: 0; }}
    ul, ol {{ padding-left: 1.5rem; margin-bottom: 1.25rem; }}
    li {{ line-height: 1.8; color: #334155; margin-bottom: 0.4rem; }}
    .cta-box {{
      background: var(--navy); border-radius: 12px; padding: 2rem;
      text-align: center; margin: 3rem 0;
    }}
    .cta-box p {{ color: #94a3b8; margin-bottom: 1rem; }}
    .cta-box a {{
      background: var(--blue); color: #fff; text-decoration: none;
      padding: 0.75rem 1.75rem; border-radius: 8px; font-weight: 600;
      font-size: 0.95rem;
    }}
    footer {{
      background: var(--navy); color: #94a3b8;
      text-align: center; padding: 2rem;
      font-size: 0.82rem;
    }}
    footer a {{ color: #94a3b8; text-decoration: none; }}
  </style>
</head>
<body>
<nav>
  <a href="/" class="nav-logo"><span>[</span>howcanihack<span>]</span></a>
  <a href="/" class="nav-home">← Back to Home</a>
</nav>

<article class="article-wrap">
  <div class="article-meta">
    <span class="tag">{category}</span>
    <span class="date">{date}</span>
    <span class="date">{read_time} min read</span>
  </div>

  {article_html}

  <div class="cta-box">
    <p>Want more cybersecurity tutorials delivered to your inbox?</p>
    <a href="/#newsletter">Subscribe Free →</a>
  </div>
</article>

<footer>
  <p>© 2026 <a href="/">HowCanIHack.com</a> — For educational purposes only. Always obtain proper authorization before testing any system.</p>
</footer>
</body>
</html>
"""

# ── MAIN ────────────────────────────────────────────────────────────────────
def count_words(text):
    return len(text.split())

def estimate_read_time(text):
    return max(1, count_words(text) // 200)


def generate_new_topic(published_slugs):
    """Ask Claude to suggest a fresh topic not yet covered."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    existing = ", ".join(list(published_slugs)[:30])

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Suggest ONE new cybersecurity article topic for the site howcanihack.com.

Already covered topics (slugs): {existing}

Requirements:
- Must be different from all topics above
- Must be useful for beginner to intermediate cybersecurity learners
- Return ONLY this JSON, nothing else:
{{"topic": "Your topic title here", "category": "beginner|tutorials|tools|certifications|news|cve"}}"""
        }]
    )

    data = json.loads(message.content[0].text.strip())
    return data["topic"], data["category"]


def pick_unused_topic():
    """Pick a topic not yet published, tracking by slug."""
    published_slugs = set()

    # Read already published slugs from articles.json
    if os.path.exists("articles.json"):
        with open("articles.json", "r") as f:
            try:
                articles = json.load(f)
                for a in articles:
                    published_slugs.add(a.get("slug", ""))
            except Exception:
                pass

    # Filter out already published topics
    unused = [t for t in TOPICS if slugify(t[0]) not in published_slugs]

    if not unused:
        # All topics used — ask Claude for a new topic
        print("⚠️  All topics used, generating new topic with AI")
        return generate_new_topic(published_slugs)

    # Pick sequentially, not randomly, to avoid repetition
    return unused[0]

def generate_article(topic, category):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Write a comprehensive, SEO-optimized cybersecurity article for howcanihack.com.

Topic: {topic}
Category: {category}
Target audience: Beginners to intermediate cybersecurity enthusiasts
Target length: 1200-1800 words

Requirements:
- Write in clear, engaging English
- Include practical examples and real commands where relevant
- Use proper HTML formatting with these tags only: <h1>, <h2>, <h3>, <p>, <ul>, <ol>, <li>, <pre><code>, <strong>, <em>
- Start with an <h1> title tag
- Add a compelling introduction paragraph right after h1 with class "lead": <p class="lead">
- Include at least 3 H2 sections
- Add real terminal commands in <pre><code> blocks where appropriate
- End with a practical "Next Steps" or "Conclusion" section
- Make it genuinely useful and accurate

Also provide at the very end, after the HTML, a JSON block like this (on its own line):
METADATA: {{"meta_description": "155 char max description here", "read_time": 8}}

Write the full HTML article now:"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def parse_response(raw):
    """Split article HTML from metadata JSON."""
    meta = {"meta_description": "", "read_time": 6}
    html = raw

    if "METADATA:" in raw:
        parts = raw.split("METADATA:")
        html = parts[0].strip()
        try:
            meta = json.loads(parts[1].strip())
        except Exception:
            pass

    return html, meta

def save_article(html_content, meta, topic, category, slug):
    os.makedirs(category, exist_ok=True)

    # Extract title from h1
    title = topic
    if "<h1>" in html_content:
        start = html_content.index("<h1>") + 4
        end = html_content.index("</h1>")
        title = html_content[start:end]

    page = HTML_TEMPLATE.format(
        title=title,
        meta_description=meta.get("meta_description", topic),
        category=category,
        slug=slug,
        date=datetime.now().strftime("%B %d, %Y"),
        read_time=meta.get("read_time", estimate_read_time(html_content)),
        article_html=html_content,
    )

    filepath = os.path.join(category, f"{slug}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"✅ Article saved: {filepath}")
    return filepath

def update_index(topic, category, slug, meta):
    """Append new article to a simple articles index JSON."""
    index_path = "articles.json"
    articles = []

    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            try:
                articles = json.load(f)
            except Exception:
                articles = []

    articles.insert(0, {
        "title": topic,
        "slug": slug,
        "category": category,
        "url": f"/{category}/{slug}.html",
        "description": meta.get("meta_description", ""),
        "date": datetime.now().strftime("%Y-%m-%d"),
    })

    with open(index_path, "w") as f:
        json.dump(articles[:200], f, indent=2)

    print(f"📋 Index updated ({len(articles)} articles)")


def update_sitemap():
    """Regenerate sitemap.xml from articles.json so new pages are included for SEO."""
    base = "https://howcanihack.com"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <url><loc>{base}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
        f"  <url><loc>{base}/tutorials/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{base}/news/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
        f"  <url><loc>{base}/cve/</loc><changefreq>daily</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{base}/certifications/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{base}/tools/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>",
        f"  <url><loc>{base}/beginner/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>",
    ]

    if os.path.exists("articles.json"):
        with open("articles.json", "r") as f:
            try:
                articles = json.load(f)
                for a in articles:
                    url = base + a.get("url", "")
                    if not url or url == base:
                        continue
                    lastmod = a.get("date", datetime.now().strftime("%Y-%m-%d"))
                    lines.append(
                        f'  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>'
                    )
            except Exception:
                pass

    lines.append("</urlset>")
    with open("sitemap.xml", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("🗺️  Sitemap updated")


def main():
    topic, category = pick_unused_topic()
    slug = slugify(topic)

    print(f"🔄 Generating: {topic} [{category}]")

    raw = generate_article(topic, category)
    html_content, meta = parse_response(raw)
    save_article(html_content, meta, topic, category, slug)
    update_index(topic, category, slug, meta)
    update_sitemap()

    print("🚀 Done! Netlify will deploy automatically.")

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for i in range(count):
        print(f"\n--- Article {i+1}/{count} ---")
        main()
