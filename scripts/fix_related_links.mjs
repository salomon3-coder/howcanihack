/**
 * Fix: add related articles HTML to all articles that have the CSS but not the HTML.
 * The bulk_improve.mjs script had a bug where it checked content.includes('related-articles')
 * but the CSS already contained that string, so the HTML was never inserted.
 * Also handles CRLF line endings properly.
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE_DIR = dirname(__dirname);

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

function getRelatedHtml(category, filename) {
  const items = RELATED_BY_CATEGORY[category] || [];
  const currentUrl = `/${category}/${filename}`;
  const liItems = items
    .filter(([, url]) => url !== currentUrl)
    .map(([title, url]) => `    <li><a href="${url}">${title}</a></li>`)
    .join('\n');
  if (!liItems) return '';
  return `\n<div class="related-articles">\n  <h3>Related Articles</h3>\n  <ul class="related-list">\n${liItems}\n  </ul>\n</div>\n`;
}

function processFile(filepath, category) {
  const filename = basename(filepath);
  let content = readFileSync(filepath, 'utf-8');

  // Check if HTML element (not just CSS) is already present
  if (content.includes('<div class="related-articles">')) return false;

  const related = getRelatedHtml(category, filename);
  if (!related) return false;

  // Normalize: handle both CRLF and LF by replacing with LF for matching, then restore
  const hasCRLF = content.includes('\r\n');
  const normalized = hasCRLF ? content.replace(/\r\n/g, '\n') : content;

  let updated = normalized;

  // Insert after </article>, before <footer>
  if (normalized.includes('</article>\n\n<footer>')) {
    updated = normalized.replace('</article>\n\n<footer>', `</article>\n${related}\n<footer>`);
  } else if (normalized.includes('</article>\n<footer>')) {
    updated = normalized.replace('</article>\n<footer>', `</article>\n${related}\n<footer>`);
  } else {
    // Last resort: insert just before <footer>
    const footerIdx = normalized.lastIndexOf('\n<footer>');
    if (footerIdx !== -1) {
      updated = normalized.slice(0, footerIdx) + '\n' + related + normalized.slice(footerIdx);
    }
  }

  if (updated === normalized) return false;

  // Restore CRLF if original had it
  const final = hasCRLF ? updated.replace(/\n/g, '\r\n') : updated;
  writeFileSync(filepath, final, 'utf-8');
  return true;
}

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
  } catch { continue; }

  console.log(`\n[${category}]`);
  for (const filepath of files) {
    const name = basename(filepath);
    const did = processFile(filepath, category);
    if (did) { console.log(`  ✓ ${name}`); updated++; }
    else { console.log(`  - ${name}`); skipped++; }
  }
}

console.log(`\n${'='.repeat(50)}`);
console.log(`Done. Related links added: ${updated}  |  Already had it: ${skipped}`);
