#!/usr/bin/env python3
"""
Deduplicate articles.json (by canonical URL / slug) and regenerate sitemap.xml.
Stdlib only — no API keys. Run from repo root:
  python scripts/refresh_index_and_sitemap.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    deduped = deduped[:200]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2)
        f.write("\n")

    write_sitemap(deduped)
    print(f"📋 articles.json: {before} → {len(deduped)} rows (deduped by URL/slug)")
    print("🗺️  sitemap.xml regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
