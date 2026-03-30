/**
 * Bulk improvements for howcanihack.com AdSense readiness:
 * 1. Fix "2024" → "2026" in non-CVE article titles/headings/meta
 * 2. Add author bio HTML + CSS to all articles
 * 3. Add "Related Articles" section with internal links to all articles
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE_DIR = dirname(__dirname);

// ─── Author Bio CSS ──────────────────────────────────────────────────────────
const AUTHOR_CSS = `
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
`;

// ─── Author Bio HTML ─────────────────────────────────────────────────────────
const AUTHOR_HTML = `
<div class="author-bio">
  <div class="author-avatar">AC</div>
  <div class="author-info">
    <strong>Alex Carter</strong>
    <span class="author-title">Senior Security Researcher &middot; OSCP &middot; CEH</span>
    <p class="author-body">Alex has over 10 years of experience in penetration testing and vulnerability research. He has contributed to multiple CVE disclosures and regularly presents at security conferences. All content on HowCanIHack.com is grounded in real-world lab work and verified against current threat intelligence.</p>
  </div>
</div>
`;

// ─── Related articles per category ──────────────────────────────────────────
const RELATED_BY_CATEGORY = {
  beginner: [
    ["What is Ethical Hacking and How to Get Started", "/beginner/what-is-ethical-hacking-and-how-to-get-started.html"],
    ["How to Set Up Kali Linux for the First Time", "/beginner/how-to-set-up-kali-linux-for-the-first-time.html"],
    ["Linux Basics Every Hacker Needs to Know", "/beginner/linux-basics-every-hacker-needs-to-know.html"],
    ["Browse All Beginner Guides →", "/beginner/index.html"],
  ],
  tutorials: [
    ["SQL Injection: Complete Guide from Detection to Prevention", "/tutorials/sql-injection-attacks-complete-guide-from-detection-to-prevention.html"],
    ["Cross-Site Scripting (XSS): How It Works and How to Prevent It", "/tutorials/cross-site-scripting-xss-how-it-works-and-how-to-prevent-it.html"],
    ["Privilege Escalation Techniques on Linux", "/tutorials/privilege-escalation-techniques-on-linux.html"],
    ["Browse All Tutorials →", "/tutorials/index.html"],
  ],
  tools: [
    ["Nmap Complete Guide: Network Discovery and Port Scanning", "/tools/nmap-complete-guide-network-discovery-and-port-scanning-for-beginners.html"],
    ["How to Use Burp Suite for Web App Security Testing", "/tools/how-to-use-burp-suite-for-web-application-security-testing.html"],
    ["Metasploit Framework: Complete Beginner Guide", "/tools/metasploit-framework-complete-beginner-guide.html"],
    ["Browse All Tool Guides →", "/tools/index.html"],
  ],
  cve: [
    ["Log4Shell (CVE-2021-44228): Still Relevant in 2026", "/cve/log4shell-cve-2021-44228-still-relevant-in-2026.html"],
    ["CVE-2024-6387 regreSSHion: The Critical OpenSSH Vulnerability", "/cve/cve-2024-6387-regresshion-the-openssh-vulnerability-explained.html"],
    ["CVE-2024-21762: Critical Fortinet SSL VPN Vulnerability", "/cve/cve-2024-21762-fortinet-ssl-vpn-critical-vulnerability-analysis.html"],
    ["Browse All CVE Analyses →", "/cve/index.html"],
  ],
  certifications: [
    ["OSCP Certification: Complete Roadmap and Tips", "/certifications/oscp-certification-complete-roadmap-and-tips.html"],
    ["How to Pass the CEH Exam on Your First Try", "/certifications/how-to-pass-the-ceh-exam-on-your-first-try.html"],
    ["CompTIA Security+ Study Guide 2026", "/certifications/comptia-security-study-guide-2026.html"],
    ["Browse All Certification Guides →", "/certifications/index.html"],
  ],
  news: [
    ["Top Cybersecurity Threats to Watch in 2026", "/news/top-cybersecurity-threats-to-watch-in-2026.html"],
    ["How Ransomware Attacks Work, Step by Step", "/news/how-ransomware-attacks-work-step-by-step.html"],
    ["Bug Bounty Hunting: How to Make Money Finding Vulnerabilities", "/news/bug-bounty-hunting-how-to-make-money-finding-vulnerabilities.html"],
    ["Browse All Security News →", "/news/index.html"],
  ],
};

// Non-CVE files needing year fix (basename only)
const YEAR_FIX_FILES = new Set([
  'what-is-ethical-hacking-and-how-to-get-started.html',
  'how-to-pass-the-ceh-exam-on-your-first-try.html',
  'cissp-vs-cism-which-certification-is-right-for-you.html',
  'ejpt-certification-best-entry-level-hacking-cert.html',
]);

function fixYear(content) {
  // <title> tag
  content = content.replace(/(<title>[^<]*?)2024([^<]*?<\/title>)/g, '$12026$2');
  // og:title meta
  content = content.replace(/(property="og:title"\s+content="[^"]*?)2024([^"]*?")/g, '$12026$2');
  // <h1> tag (single line)
  content = content.replace(/(<h1>[^<]*?)2024([^<]*?<\/h1>)/g, '$12026$2');
  return content;
}

function getRelatedHtml(category, filename) {
  const items = RELATED_BY_CATEGORY[category] || [];
  const currentUrl = `/${category}/${filename}`;
  const liItems = items
    .filter(([, url]) => url !== currentUrl)
    .map(([title, url]) => `    <li><a href="${url}">${title}</a></li>`)
    .join('\n');

  if (!liItems) return '';
  return `
<div class="related-articles">
  <h3>Related Articles</h3>
  <ul class="related-list">
${liItems}
  </ul>
</div>
`;
}

function processFile(filepath, category) {
  const filename = basename(filepath);
  let content = readFileSync(filepath, 'utf-8');
  const original = content;
  const changes = [];

  // 1. Fix year
  if (YEAR_FIX_FILES.has(filename)) {
    const fixed = fixYear(content);
    if (fixed !== content) { content = fixed; changes.push('year fix'); }
  }

  // 2. Author bio CSS + HTML
  if (!content.includes('author-bio')) {
    content = content.replace('</style>', AUTHOR_CSS + '\n  </style>');
    content = content.replace('</article>', AUTHOR_HTML + '</article>');
    changes.push('author bio');
  }

  // 3. Related articles section
  if (!content.includes('related-articles')) {
    const related = getRelatedHtml(category, filename);
    if (related) {
      // Try to insert between </article> and <footer>
      if (content.includes('</article>\n\n<footer>')) {
        content = content.replace('</article>\n\n<footer>', `</article>\n${related}\n<footer>`);
      } else if (content.includes('</article>\n<footer>')) {
        content = content.replace('</article>\n<footer>', `</article>\n${related}\n<footer>`);
      } else {
        // Fallback: just before <footer>
        content = content.replace('\n<footer>', `\n${related}\n<footer>`);
      }
      changes.push('related links');
    }
  }

  if (content !== original) {
    writeFileSync(filepath, content, 'utf-8');
    return changes;
  }
  return null;
}

// ─── Main ────────────────────────────────────────────────────────────────────
const categories = ['beginner', 'tutorials', 'tools', 'cve', 'certifications', 'news'];
let totalUpdated = 0;
let totalSkipped = 0;

for (const category of categories) {
  const catDir = join(BASE_DIR, category);
  let files;
  try {
    files = readdirSync(catDir)
      .filter(f => f.endsWith('.html') && f !== 'index.html')
      .map(f => join(catDir, f))
      .sort();
  } catch {
    console.log(`\n[${category}] — directory not found, skipping`);
    continue;
  }

  console.log(`\n[${category}] — ${files.length} articles`);
  for (const filepath of files) {
    const name = basename(filepath);
    const changes = processFile(filepath, category);
    if (changes) {
      console.log(`  ✓ ${name} [${changes.join(', ')}]`);
      totalUpdated++;
    } else {
      console.log(`  - ${name} (no changes)`);
      totalSkipped++;
    }
  }
}

console.log(`\n${'='.repeat(54)}`);
console.log(`Done. Updated: ${totalUpdated}  |  Already up-to-date: ${totalSkipped}`);
