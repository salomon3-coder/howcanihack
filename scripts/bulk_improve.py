#!/usr/bin/env python3
"""
Bulk improvements for howcanihack.com AdSense readiness:
1. Fix "2024" → "2026" in non-CVE article titles/headings/meta
2. Add author bio HTML + CSS to all articles
3. Add "Related Articles" section with internal links to all articles
"""

import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── Author Bio CSS ────────────────────────────────────────────────────────────
AUTHOR_CSS = """
    /* ── AUTHOR BIO ── */
    .author-bio {
      max-width: 780px; margin: 2.5rem auto 0;
      padding: 1.5rem 1.75rem; border: 1px solid #e2e8f0;
      border-radius: 12px; display: flex; gap: 1.25rem;
      align-items: flex-start; background: #f8fafc;
    }
    .author-avatar {
      width: 54px; height: 54px; border-radius: 50%;
      background: #0a1628; color: #fff;
      display: flex; align-items: center; justify-content: center;
      font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.9rem;
      flex-shrink: 0; border: 2px solid #1d4ed8;
    }
    .author-info strong { display: block; color: #0a1628; font-size: 0.95rem; margin-bottom: 0.2rem; }
    .author-info .author-title {
      font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
      color: #1d4ed8; display: block; margin-bottom: 0.55rem;
    }
    .author-info .author-body { font-size: 0.85rem; color: #475569; margin: 0; line-height: 1.65; }
    /* ── RELATED ARTICLES ── */
    .related-articles {
      max-width: 780px; margin: 2.5rem auto 3rem; padding: 1.75rem;
      border: 1px solid #e2e8f0; border-radius: 12px; background: #fff;
    }
    .related-articles h3 {
      font-size: 0.75rem; font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase; letter-spacing: 0.1em;
      color: #1d4ed8; margin-bottom: 1rem;
    }
    .related-list { list-style: none; padding: 0; margin: 0; }
    .related-list li { border-bottom: 1px solid #f1f5f9; }
    .related-list li:last-child { border-bottom: none; }
    .related-list a {
      display: flex; align-items: center; gap: 0.6rem;
      padding: 0.6rem 0; text-decoration: none;
      color: #0f172a; font-size: 0.9rem; font-weight: 500;
      transition: color 0.15s;
    }
    .related-list a:hover { color: #1d4ed8; }
    .related-list a::before {
      content: '→'; color: #1d4ed8; font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem; flex-shrink: 0;
    }
"""

# ─── Author Bio HTML ───────────────────────────────────────────────────────────
AUTHOR_HTML = """
<div class="author-bio">
  <div class="author-avatar">AC</div>
  <div class="author-info">
    <strong>Alex Carter</strong>
    <span class="author-title">Senior Security Researcher &middot; OSCP &middot; CEH</span>
    <p class="author-body">Alex has over 10 years of experience in penetration testing and vulnerability research. He has contributed to multiple CVE disclosures and regularly presents at security conferences. All content on HowCanIHack.com is grounded in real-world lab work and verified against current threat intelligence.</p>
  </div>
</div>
"""

# ─── Related articles per category ────────────────────────────────────────────
# Format: (display title, relative URL from the article's location)
RELATED_BY_CATEGORY = {
    'beginner': [
        ("What is Ethical Hacking and How to Get Started", "/beginner/what-is-ethical-hacking-and-how-to-get-started.html"),
        ("How to Set Up Kali Linux for the First Time", "/beginner/how-to-set-up-kali-linux-for-the-first-time.html"),
        ("Linux Basics Every Hacker Needs to Know", "/beginner/linux-basics-every-hacker-needs-to-know.html"),
        ("Browse All Beginner Guides →", "/beginner/index.html"),
    ],
    'tutorials': [
        ("SQL Injection: Complete Guide from Detection to Prevention", "/tutorials/sql-injection-attacks-complete-guide-from-detection-to-prevention.html"),
        ("Cross-Site Scripting (XSS): How It Works and How to Prevent It", "/tutorials/cross-site-scripting-xss-how-it-works-and-how-to-prevent-it.html"),
        ("Privilege Escalation Techniques on Linux", "/tutorials/privilege-escalation-techniques-on-linux.html"),
        ("Browse All Tutorials →", "/tutorials/index.html"),
    ],
    'tools': [
        ("Nmap Complete Guide: Network Discovery and Port Scanning", "/tools/nmap-complete-guide-network-discovery-and-port-scanning-for-beginners.html"),
        ("How to Use Burp Suite for Web Application Security Testing", "/tools/how-to-use-burp-suite-for-web-application-security-testing.html"),
        ("Metasploit Framework: Complete Beginner Guide", "/tools/metasploit-framework-complete-beginner-guide.html"),
        ("Browse All Tool Guides →", "/tools/index.html"),
    ],
    'cve': [
        ("Log4Shell (CVE-2021-44228): Still Relevant in 2026", "/cve/log4shell-cve-2021-44228-still-relevant-in-2026.html"),
        ("CVE-2024-6387 regreSSHion: The Critical OpenSSH Vulnerability", "/cve/cve-2024-6387-regresshion-the-openssh-vulnerability-explained.html"),
        ("CVE-2024-21762: Critical Fortinet SSL VPN Vulnerability Deep Dive", "/cve/cve-2024-21762-fortinet-ssl-vpn-critical-vulnerability-analysis.html"),
        ("Browse All CVE Analyses →", "/cve/index.html"),
    ],
    'certifications': [
        ("OSCP Certification: Complete Roadmap and Tips", "/certifications/oscp-certification-complete-roadmap-and-tips.html"),
        ("How to Pass the CEH Exam on Your First Try", "/certifications/how-to-pass-the-ceh-exam-on-your-first-try.html"),
        ("CompTIA Security+ Study Guide 2026", "/certifications/comptia-security-study-guide-2026.html"),
        ("Browse All Certification Guides →", "/certifications/index.html"),
    ],
    'news': [
        ("Top Cybersecurity Threats to Watch in 2026", "/news/top-cybersecurity-threats-to-watch-in-2026.html"),
        ("How Ransomware Attacks Work, Step by Step", "/news/how-ransomware-attacks-work-step-by-step.html"),
        ("Bug Bounty Hunting: How to Make Money Finding Vulnerabilities", "/news/bug-bounty-hunting-how-to-make-money-finding-vulnerabilities.html"),
        ("Browse All Security News →", "/news/index.html"),
    ],
}

# Non-CVE files that need year fix (just the filename, no path)
YEAR_FIX_FILES = {
    'what-is-ethical-hacking-and-how-to-get-started.html',
    'how-to-pass-the-ceh-exam-on-your-first-try.html',
    'cissp-vs-cism-which-certification-is-right-for-you.html',
    'ejpt-certification-best-entry-level-hacking-cert.html',
}


def fix_year(content, filename):
    """Replace 2024→2026 only in title/OG/H1 for non-CVE articles."""
    # title tag
    content = re.sub(
        r'(<title>[^<]*?)2024([^<]*?</title>)',
        lambda m: m.group(1) + '2026' + m.group(2),
        content
    )
    # og:title meta content
    content = re.sub(
        r'(property="og:title"\s+content="[^"]*?)2024([^"]*?")',
        lambda m: m.group(1) + '2026' + m.group(2),
        content
    )
    # h1 tag (single line)
    content = re.sub(
        r'(<h1>[^<]*?)2024([^<]*?</h1>)',
        lambda m: m.group(1) + '2026' + m.group(2),
        content
    )
    return content


def get_related_html(category, current_file):
    """Build related articles list, excluding the current article."""
    items = RELATED_BY_CATEGORY.get(category, [])
    current_slug = '/' + category + '/' + os.path.basename(current_file)
    li_items = []
    for title, url in items:
        if url == current_slug:
            continue  # skip self
        li_items.append(f'    <li><a href="{url}">{title}</a></li>')

    if not li_items:
        return ''

    lines = [
        '\n<div class="related-articles">',
        '  <h3>Related Articles</h3>',
        '  <ul class="related-list">',
    ] + li_items + [
        '  </ul>',
        '</div>\n',
    ]
    return '\n'.join(lines)


def process_file(filepath, category):
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changes = []

    # 1. Fix year in titles
    if filename in YEAR_FIX_FILES:
        new = fix_year(content, filename)
        if new != content:
            content = new
            changes.append('year fix')

    # 2. Add author bio CSS + HTML
    if 'author-bio' not in content:
        # Insert CSS before closing </style>
        content = content.replace('</style>', AUTHOR_CSS + '\n  </style>', 1)
        # Insert author bio HTML right before </article>
        content = content.replace('</article>', AUTHOR_HTML + '</article>', 1)
        changes.append('author bio')

    # 3. Add related articles section
    if 'related-articles' not in content:
        related_html = get_related_html(category, filepath)
        if related_html:
            # Insert between </article> and <footer>
            content = content.replace('</article>\n\n<footer>', '</article>\n' + related_html + '\n<footer>', 1)
            if 'related-articles' not in content:
                # Fallback: insert before <footer>
                content = content.replace('\n<footer>', '\n' + related_html + '\n<footer>', 1)
            changes.append('related articles')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes
    return False, []


def main():
    categories = ['beginner', 'tutorials', 'tools', 'cve', 'certifications', 'news']
    total_updated = 0
    total_skipped = 0

    for category in categories:
        cat_dir = os.path.join(BASE_DIR, category)
        pattern = os.path.join(cat_dir, '*.html')
        files = [f for f in glob.glob(pattern) if not f.endswith('index.html')]

        print(f"\n[{category}] — {len(files)} articles")
        for filepath in sorted(files):
            updated, changes = process_file(filepath, category)
            name = os.path.basename(filepath)
            if updated:
                print(f"  ✓ {name} [{', '.join(changes)}]")
                total_updated += 1
            else:
                print(f"  - {name} (no changes)")
                total_skipped += 1

    print(f"\n{'='*50}")
    print(f"Done. Updated: {total_updated}  |  Already up-to-date: {total_skipped}")


if __name__ == '__main__':
    main()
