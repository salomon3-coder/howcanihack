#!/usr/bin/env python3
"""
Deduplicate articles.json (by canonical URL / slug) and regenerate sitemap.xml.
Stdlib only — no API keys. Run from repo root:
  python scripts/refresh_index_and_sitemap.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_ARTICLES = 140

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in",
    "into", "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
    "guide", "tutorial", "complete", "explained", "basics", "beginner", "beginners",
    "cybersecurity", "security", "attack", "attacks", "vulnerability", "vulnerabilities",
    "learn", "using", "use", "what", "why", "works",
}

STRONG_TOKENS = {
    "nmap", "wireshark", "burp", "sqlmap", "metasploit", "hydra", "hashcat", "aircrack",
    "gobuster", "netcat", "nikto", "john", "password", "social", "engineering",
    "owasp", "ctf", "kali", "firewalls", "firewall", "tor", "proxychains",
}


def _article_key(a: dict) -> str:
    url = (a.get("url") or "").strip()
    if url:
        return url
    slug = (a.get("slug") or "").strip()
    cat = (a.get("category") or "").strip()
    if slug and cat:
        return f"/{cat}/{slug}.html"
    return slug


def dedupe_articles(articles: list) -> list[dict]:
    """One entry per URL/slug; keep the row with the latest date string."""
    best: dict[str, dict] = {}
    for a in articles:
        if not isinstance(a, dict):
            continue
        key = _article_key(a)
        if not key:
            continue
        d = a.get("date") or ""
        prev = best.get(key)
        if prev is None or d >= (prev.get("date") or ""):
            best[key] = a
    out = sorted(best.values(), key=lambda x: x.get("date", ""), reverse=True)
    return out


def _tokens(title: str) -> set[str]:
    raw = re.findall(r"[a-z0-9]+", (title or "").lower())
    return {t for t in raw if len(t) > 2 and t not in STOPWORDS}


def _strong_signature(title: str) -> set[str]:
    t = (title or "").lower()
    tokens = _tokens(t)
    sig = set(tokens & STRONG_TOKENS)
    if "sql" in t and "injection" in t:
        sig.add("__sqli__")
    if "xss" in t or "cross-site" in t or "cross site" in t:
        sig.add("__xss__")
    if "home" in t and "lab" in t:
        sig.add("__home_lab__")
    if "social" in t and "engineering" in t:
        sig.add("__social_engineering__")
    return sig


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def prune_similar_articles(articles: list[dict]) -> list[dict]:
    """
    Keep one canonical piece per repeated concept for non-CVE categories.
    Preference order: has description -> newest date.
    """
    ranked = sorted(
        articles,
        key=lambda a: (1 if (a.get("description") or "").strip() else 0, a.get("date", "")),
        reverse=True,
    )

    kept: list[dict] = []
    by_cat_tokens: dict[str, list[set[str]]] = {}
    by_cat_sig: dict[str, set[str]] = {}

    for a in ranked:
        cat = (a.get("category") or "").strip().lower()
        title = (a.get("title") or "").strip()
        if not title:
            continue

        # CVE items are naturally distinct by CVE ID; keep all.
        if cat == "cve":
            kept.append(a)
            continue

        tset = _tokens(title)
        sig = _strong_signature(title)
        seen_sig = by_cat_sig.setdefault(cat, set())
        seen_tokens = by_cat_tokens.setdefault(cat, [])

        if sig and (sig & seen_sig):
            continue
        if any(_jaccard(tset, prev) >= 0.58 for prev in seen_tokens):
            continue

        kept.append(a)
        seen_sig.update(sig)
        seen_tokens.append(tset)

    # Freshest first in resulting index
    kept.sort(key=lambda x: x.get("date", ""), reverse=True)
    return kept


def write_sitemap(articles: list[dict]) -> None:
    """Same structure as generate_article.update_sitemap (dedupe by loc)."""
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

    url_lastmod: dict[str, str] = {}
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
            f'  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod>'
            f'<changefreq>weekly</changefreq><priority>0.7</priority></url>'
        )

    lines.append("</urlset>")
    out_path = os.path.join(REPO_ROOT, "sitemap.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    os.chdir(REPO_ROOT)
    path = os.path.join(REPO_ROOT, "articles.json")
    if not os.path.isfile(path):
        print("No articles.json — writing sitemap with section pages only.")
        write_sitemap([])
        print("🗺️  sitemap.xml updated")
        return 0

    with open(path, encoding="utf-8") as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return 1

    if not isinstance(raw, list):
        print("articles.json must be a list")
        return 1

    before = len(raw)
    deduped = dedupe_articles(raw)
    curated = prune_similar_articles(deduped)
    curated = curated[:MAX_ARTICLES]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(curated, f, indent=2)
        f.write("\n")

    write_sitemap(curated)
    print(
        f"📋 articles.json: {before} → {len(deduped)} rows (exact dedupe)"
        f" → {len(curated)} rows (semantic curation)"
    )
    print("🗺️  sitemap.xml regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
