
#!/usr/bin/env python3
"""
Auto-generates a cybersecurity article using Claude API
and saves it as HTML ready for Netlify.
"""

import anthropic
import json
import os
import re
from datetime import datetime
from slugify import slugify

# Categories that hold article HTML (exclude index.html)
ARTICLE_CATEGORIES = [
    "tutorials", "beginner", "tools", "certifications", "news", "cve",
]

# English stopwords + site-specific noise for title tokenization
_STOPWORDS_RAW = """
a an the and or for to of in on at by from with without is are was were be been being
as if this that these those it its into about how what when where why who which than
then not no nor only own same so such some any both each few more most other such
than too very can will just should now do does did doing done use using used also
your you we they our their them one two first new make made way may might must
shall could would need like get got go going went work works working learn learning
guide complete tutorial introduction basics explained explain understanding step tips
tricks best free beginners beginner intermediate advanced real world hands practical
security cybersecurity cyber attack attacks hacking hacker hackers vulnerability
threat threats protect protection prevent network web application
cve
""".split()
STOPWORDS = frozenset(w.lower() for w in _STOPWORDS_RAW if w)

# Tools / vuln “anchors”: if a new title shares any with an existing title, reject
STRONG_SINGLE = frozenset({
    "nmap", "wireshark", "burp", "sqlmap", "metasploit", "nikto", "gobuster",
    "hashcat", "hydra", "netcat", "aircrack", "nessus", "openvas", "bloodhound",
    "mimikatz", "snort", "suricata", "zeek", "masscan", "rustscan", "amass",
    "subfinder", "ffuf", "feroxbuster", "wpscan", "enum4linux", "responder",
    "impacket", "covenant", "sliver", "chisel", "proxychains", "tor",
})

JACCARD_MAX = 0.35
PROMPT_TITLES_MAX_CHARS = 12000
AI_TOPIC_ATTEMPTS = 12

# Last-resort topics if the model keeps colliding (must be distinct angles)
EMERGENCY_TOPICS = [
    ("Kubernetes security basics for self-hosters", "tutorials"),
    ("Introduction to threat modeling with STRIDE", "tutorials"),
    ("Secure software supply chain: SBOMs and signing", "news"),
    ("Windows Event Log hunting for incident responders", "tutorials"),
    ("Email authentication: SPF, DKIM, and DMARC explained", "beginner"),
    ("Introduction to cloud IAM misconfiguration risks", "tutorials"),
    ("Basics of digital forensics and disk imaging ethics", "tutorials"),
    ("OPSEC for researchers: separating identity from work", "beginner"),
    ("Secure coding review checklist for web developers", "tutorials"),
    ("Introduction to purple teaming and detection engineering", "tutorials"),
    ("Smart contract security pitfalls for beginners", "tutorials"),
    ("ICS/OT network segmentation fundamentals", "tutorials"),
]

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
    ("CVE-2024-49113 Windows LDAP critical vulnerability explained", "cve"),
    ("CVE-2024-38063 Windows TCP/IP remote code execution", "cve"),
    ("CVE-2024-30078 Windows WiFi driver remote code execution", "cve"),
    ("CVE-2024-21338 Windows kernel privilege escalation", "cve"),
    ("CVE-2024-0519 Google Chrome V8 engine zero-day", "cve"),
    ("CVE-2024-4577 PHP CGI argument injection on Windows", "cve"),
    ("CVE-2024-23897 Jenkins arbitrary file read vulnerability", "cve"),
    ("CVE-2024-21413 Microsoft Outlook NTLM leak vulnerability", "cve"),
    ("CVE-2024-20353 Cisco ASA denial of service vulnerability", "cve"),
    ("CVE-2024-26169 Windows Error Reporting privilege escalation", "cve"),
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
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4579344894934796" crossorigin="anonymous"></script>
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


def normalize_meta_title(s):
    s = (s or "").strip()
    s = re.sub(r"\s*\|\s*HowCanIHack\.com\s*$", "", s, flags=re.I)
    return s.strip()


def extract_title_from_html_file(filepath):
    """Read <title> from article HTML, else first <h1>."""
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            chunk = f.read(32768)
    except OSError:
        return None
    m = re.search(r"<title>\s*([^<]+?)\s*</title>", chunk, re.I | re.S)
    if m:
        return normalize_meta_title(m.group(1))
    m = re.search(r"<h1>\s*([^<]+?)\s*</h1>", chunk, re.I | re.S)
    if m:
        return m.group(1).strip()
    return None


def collect_published_slugs():
    published_slugs = set()
    for cat in ARTICLE_CATEGORIES:
        if not os.path.isdir(cat):
            continue
        for f in os.listdir(cat):
            if f.endswith(".html") and f != "index.html":
                published_slugs.add(f.replace(".html", ""))
    return published_slugs


def collect_existing_titles():
    """Titles from on-disk HTML plus articles.json (deduped by normalized string)."""
    titles = []
    seen = set()

    def add_title(t):
        if not t:
            return
        key = t.lower().strip()
        if key in seen:
            return
        seen.add(key)
        titles.append(t)

    for cat in ARTICLE_CATEGORIES:
        if not os.path.isdir(cat):
            continue
        for f in os.listdir(cat):
            if not f.endswith(".html") or f == "index.html":
                continue
            path = os.path.join(cat, f)
            t = extract_title_from_html_file(path)
            if t:
                add_title(t)

    index_path = "articles.json"
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as fp:
                articles = json.load(fp)
            for a in articles:
                add_title(a.get("title") or "")
        except Exception:
            pass

    return titles


def tokenize_title(title):
    """Significant word tokens for similarity (lowercase alnum words)."""
    title = (title or "").lower()
    title = title.replace("cve-", "cve-").replace("cve ", "cve ")
    words = re.findall(r"[a-z0-9]+", title)
    return frozenset(w for w in words if len(w) > 2 and w not in STOPWORDS)


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def strong_signature(title):
    """Concept/tool anchors that should not repeat across articles."""
    tokens = tokenize_title(title)
    sig = set(tokens & STRONG_SINGLE)
    tl = (title or "").lower()
    if "sql" in tl and "injection" in tl:
        sig.add("__sqli__")
    if "xss" in tl or "cross-site" in tl or "cross site" in tl:
        sig.add("__xss__")
    if "buffer" in tl and "overflow" in tl:
        sig.add("__buffer_overflow__")
    return frozenset(sig)


def max_jaccard_against(candidate_tokens, existing_token_sets):
    if not existing_token_sets or not candidate_tokens:
        return 0.0
    return max(jaccard(candidate_tokens, ts) for ts in existing_token_sets)


def strong_token_conflict(candidate_title, existing_titles):
    c_sig = strong_signature(candidate_title)
    if not c_sig:
        return False
    for ex in existing_titles:
        if c_sig & strong_signature(ex):
            return True
    return False


def topic_too_similar(topic, existing_titles, existing_token_sets):
    """
    True if topic is too close to any existing title (Jaccard on tokens)
    or shares a strong tool/vuln anchor with an existing title.
    """
    cand_tokens = tokenize_title(topic)
    mj = max_jaccard_against(cand_tokens, existing_token_sets)
    if mj > JACCARD_MAX:
        return True, f"jaccard={mj:.2f}"
    if strong_token_conflict(topic, existing_titles):
        return True, "strong_token_overlap"
    return False, None


def build_title_block_for_prompt(existing_titles, max_chars=PROMPT_TITLES_MAX_CHARS):
    lines = []
    total = 0
    for i, t in enumerate(existing_titles, start=1):
        line = f"{i}. {t}"
        if total + len(line) + 1 > max_chars:
            lines.append(f"... ({len(existing_titles) - i + 1} more titles omitted)")
            break
        lines.append(line)
        total += len(line) + 1
    return "\n".join(lines) if lines else "(none yet)"


def generate_new_topic(published_slugs, existing_titles, existing_token_sets):
    """
    Ask Claude for a topic that is new by slug and not semantically similar
    to existing article titles on disk / in the index.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    titles_block = build_title_block_for_prompt(existing_titles)
    slug_sample = ", ".join(sorted(published_slugs)[:40])
    rejection_note = ""

    topic, category = None, "tutorials"

    for attempt in range(AI_TOPIC_ATTEMPTS):
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=220,
            messages=[{
                "role": "user",
                "content": f"""Suggest ONE new cybersecurity article topic for howcanihack.com.

Already published article titles (do NOT repeat the same tool, vulnerability, or core concept as any of these — pick a genuinely different angle, e.g. another protocol, cloud/identity/OT, forensics, detection, hardening, architecture, governance, etc.):
{titles_block}

Existing URL slugs (sample; your title must produce a NEW slug not in this set): {slug_sample}

{rejection_note}
Requirements:
- Must not overlap semantically with any title above (not another "Nmap guide", "SQL injection guide", "Wireshark tutorial", etc. if those themes already appear).
- Useful for beginner to intermediate cybersecurity learners.
- Topic title in clear, natural English only (no other languages).
- category must be one of: beginner, tutorials, tools, certifications, news, cve
- Return ONLY valid JSON, nothing else:
{{"topic": "Your topic title here", "category": "beginner|tutorials|tools|certifications|news|cve"}}"""
            }]
        )

        try:
            raw = message.content[0].text.strip()
            # tolerate markdown fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)
            topic = data["topic"].strip()
            category = data["category"].strip()
        except Exception:
            rejection_note = "Your last reply was not valid JSON. Reply with ONLY the JSON object.\n"
            continue

        if category not in (
            "beginner", "tutorials", "tools", "certifications", "news", "cve",
        ):
            category = "tutorials"

        if slugify(topic) in published_slugs:
            rejection_note = "Last suggestion collided with an existing URL slug. Choose a completely different subject and title.\n"
            continue

        bad, reason = topic_too_similar(topic, existing_titles, existing_token_sets)
        if bad:
            rejection_note = (
                f"Last title was rejected ({reason}): too close to an existing article. "
                "Pick a different primary tool/concept and a fresh angle.\n"
            )
            continue

        return topic, category

    # Emergency static topics (still respect slug + similarity)
    for em_topic, em_cat in EMERGENCY_TOPICS:
        if slugify(em_topic) in published_slugs:
            continue
        bad, _ = topic_too_similar(em_topic, existing_titles, existing_token_sets)
        if not bad:
            print("⚠️  Using emergency topic list (AI suggestions kept colliding)")
            return em_topic, em_cat

    # Final fallback: unique slug via suffix (rare)
    base = topic or "Advanced cybersecurity deep dive"
    suffix = 2
    topic = base
    while slugify(topic) in published_slugs or topic_too_similar(
        topic, existing_titles, existing_token_sets
    )[0]:
        topic = f"{base} (Part {suffix})"
        suffix += 1
    print("⚠️  Fallback: suffix topic to satisfy uniqueness")
    return topic, category


def pick_unused_topic():
    """Pick a topic not yet published, checking slugs on disk and semantic overlap."""
    published_slugs = collect_published_slugs()
    existing_titles = collect_existing_titles()
    existing_token_sets = [tokenize_title(t) for t in existing_titles]

    print(f"📂 Found {len(published_slugs)} existing articles on disk")
    print(f"📚 Indexed {len(existing_titles)} titles for similarity checks")

    unused = [t for t in TOPICS if slugify(t[0]) not in published_slugs]
    unused = [
        t for t in unused
        if not topic_too_similar(t[0], existing_titles, existing_token_sets)[0]
    ]

    if unused:
        print(f"📋 {len(unused)} topics remaining in list (after semantic filter)")
        return unused[0]

    print("⚠️  All curated topics used or blocked by similarity; generating with AI")
    return generate_new_topic(published_slugs, existing_titles, existing_token_sets)

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

    # Remove any existing entry for this slug so we don't duplicate
    articles = [a for a in articles if a.get("slug") != slug]

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
        f"  <url><loc>{base}/about.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>",
        f"  <url><loc>{base}/contact.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>",
        f"  <url><loc>{base}/editorial-policy.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>",
        f"  <url><loc>{base}/write-for-us.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>",
        f"  <url><loc>{base}/privacy.html</loc><changefreq>monthly</changefreq><priority>0.4</priority></url>",
        f"  <url><loc>{base}/disclaimer.html</loc><changefreq>monthly</changefreq><priority>0.4</priority></url>",
    ]

    if os.path.exists("articles.json"):
        with open("articles.json", "r") as f:
            try:
                articles = json.load(f)
                # Deduplicate by canonical URL; keep latest lastmod
                url_lastmod = {}
                for a in articles:
                    url = base + (a.get("url") or "")
                    if not url or url == base:
                        continue
                    lastmod = a.get("date") or datetime.now().strftime("%Y-%m-%d")
                    prev = url_lastmod.get(url)
                    if prev is None or lastmod > prev:
                        url_lastmod[url] = lastmod
                for url in sorted(url_lastmod.keys()):
                    lastmod = url_lastmod[url]
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
