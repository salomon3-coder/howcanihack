/**
 * Add a Table of Contents (TOC) to all articles.
 * Extracts H2 headings, anchors them, and inserts a TOC box
 * right after the .lead paragraph for quick navigation.
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE_DIR = dirname(__dirname);

const TOC_CSS = `
    /* ── TABLE OF CONTENTS ── */
    .toc-box {
      max-width: 780px; margin: 2rem auto;
      padding: 1.5rem 1.75rem; background: #f8fafc;
      border: 1px solid #e2e8f0; border-left: 4px solid #1d4ed8;
      border-radius: 0 12px 12px 0;
    }
    .toc-box h3 {
      font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase; letter-spacing: 0.1em;
      color: #475569; margin-bottom: 0.85rem;
    }
    .toc-list { list-style: none; padding: 0; margin: 0; counter-reset: toc; }
    .toc-list li { counter-increment: toc; }
    .toc-list a {
      display: flex; align-items: baseline; gap: 0.6rem;
      padding: 0.3rem 0; text-decoration: none;
      color: #334155; font-size: 0.875rem; line-height: 1.5;
      transition: color 0.15s;
    }
    .toc-list a:hover { color: #1d4ed8; }
    .toc-list a::before {
      content: counter(toc) ".";
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem; color: #1d4ed8;
      min-width: 1.4rem; flex-shrink: 0;
    }
`;

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/&amp;/g, 'and')
    .replace(/&[^;]+;/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

function processFile(filepath) {
  let content = readFileSync(filepath, 'utf-8');

  if (content.includes('toc-box')) return false; // already has TOC

  // Extract H2 headings
  const h2Pattern = /<h2>([^<]+)<\/h2>/g;
  const headings = [];
  let m;
  while ((m = h2Pattern.exec(content)) !== null) {
    headings.push(m[1].trim());
  }

  if (headings.length < 2) return false; // not enough headings

  // Add id anchors to each h2
  for (const heading of headings) {
    const anchor = slugify(heading);
    const original = `<h2>${heading}</h2>`;
    const anchored = `<h2 id="${anchor}">${heading}</h2>`;
    content = content.replace(original, anchored);
  }

  // Build TOC HTML
  const listItems = headings
    .map(h => {
      const anchor = slugify(h);
      return `    <li><a href="#${anchor}">${h}</a></li>`;
    })
    .join('\n');

  const tocHtml = `\n<div class="toc-box">
  <h3>In This Article</h3>
  <ol class="toc-list">
${listItems}
  </ol>
</div>\n`;

  // Add CSS
  content = content.replace('</style>', TOC_CSS + '\n  </style>');

  // Insert TOC after the .lead paragraph
  // The lead is always <p class="lead">...</p>
  const leadPattern = /(<p class="lead">[\s\S]*?<\/p>)/;
  if (leadPattern.test(content)) {
    content = content.replace(leadPattern, `$1${tocHtml}`);
  } else {
    // Fallback: after first <h1>
    content = content.replace(/(<\/h1>)/, `$1${tocHtml}`);
  }

  writeFileSync(filepath, content, 'utf-8');
  return true;
}

// ─── Main ────────────────────────────────────────────────────────────────────
const categories = ['beginner', 'tutorials', 'tools', 'cve', 'certifications', 'news'];
let updated = 0;
let skipped = 0;

for (const category of categories) {
  const catDir = join(BASE_DIR, category);
  let files;
  try {
    files = readdirSync(catDir)
      .filter(f => f.endsWith('.html') && f !== 'index.html')
      .map(f => join(catDir, f))
      .sort();
  } catch {
    continue;
  }

  console.log(`\n[${category}]`);
  for (const filepath of files) {
    const name = basename(filepath);
    const didUpdate = processFile(filepath);
    if (didUpdate) {
      console.log(`  ✓ ${name}`);
      updated++;
    } else {
      console.log(`  - ${name}`);
      skipped++;
    }
  }
}

console.log(`\n${'='.repeat(50)}`);
console.log(`Done. TOC added: ${updated}  |  Skipped: ${skipped}`);
