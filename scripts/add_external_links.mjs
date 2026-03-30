/**
 * Add external authority links to CVE and tutorial articles:
 * - CVE articles: NVD entry + MITRE + CISA known exploited (where applicable)
 * - Tutorial articles: OWASP, NIST, official tool docs
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE_DIR = dirname(__dirname);

// CSS for external references box (appended once per file)
const REFS_CSS = `
    /* ── EXTERNAL REFERENCES ── */
    .ext-refs {
      max-width: 780px; margin: 0 auto 2rem;
      padding: 1.25rem 1.75rem; background: #f8fafc;
      border: 1px solid #e2e8f0; border-radius: 12px;
    }
    .ext-refs h3 {
      font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase; letter-spacing: 0.1em;
      color: #475569; margin-bottom: 0.85rem;
    }
    .ext-refs ul { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .ext-refs a {
      display: inline-flex; align-items: center; gap: 0.4rem;
      padding: 0.3rem 0.8rem; background: #fff; border: 1px solid #e2e8f0;
      border-radius: 6px; font-size: 0.8rem; color: #1d4ed8;
      text-decoration: none; font-family: 'JetBrains Mono', monospace;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .ext-refs a:hover { border-color: #1d4ed8; box-shadow: 0 2px 8px rgba(29,78,216,0.12); }
    .ext-refs a::before { content: '↗'; font-size: 0.7rem; }
`;

// ─── CVE-specific reference links ────────────────────────────────────────────
// Maps slug fragment → list of [label, url]
const CVE_REFS = {
  'cve-2024-6387': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-6387'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-6387'],
    ['Qualys Blog', 'https://blog.qualys.com/vulnerabilities-threat-research/2024/07/01/regresshion-remote-unauthenticated-code-execution-vulnerability-in-openssh-server'],
  ],
  'cve-2024-21762': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-21762'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-21762'],
    ['CISA Advisory', 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog'],
  ],
  'cve-2024-38063': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-38063'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-38063'],
    ['Microsoft Advisory', 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-38063'],
  ],
  'cve-2024-3400': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-3400'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-3400'],
    ['Palo Alto Advisory', 'https://security.paloaltonetworks.com/CVE-2024-3400'],
  ],
  'cve-2024-30078': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-30078'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-30078'],
    ['Microsoft Advisory', 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-30078'],
  ],
  'cve-2024-21413': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-21413'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-21413'],
    ['Microsoft Advisory', 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-21413'],
  ],
  'cve-2024-23897': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-23897'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-23897'],
    ['Jenkins Advisory', 'https://www.jenkins.io/security/advisory/2024-01-24/'],
  ],
  'cve-2024-27198': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-27198'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-27198'],
    ['JetBrains Advisory', 'https://www.jetbrains.com/privacy-security/issues-fixed/'],
  ],
  'cve-2024-0519': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-0519'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-0519'],
    ['Chrome Release Notes', 'https://chromereleases.googleblog.com/'],
  ],
  'cve-2024-4577': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-4577'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-4577'],
    ['PHP Security', 'https://www.php.net/ChangeLog-8.php'],
  ],
  'cve-2024-21338': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-21338'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-21338'],
    ['Microsoft Advisory', 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-21338'],
  ],
  'cve-2024-1708': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-1708'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1708'],
    ['ConnectWise Advisory', 'https://www.connectwise.com/company/trust/security-bulletins'],
  ],
  'cve-2024-20353': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-20353'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-20353'],
    ['Cisco Advisory', 'https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-asaftd-dos-X8gNucD2'],
  ],
  'cve-2024-26169': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-26169'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-26169'],
    ['Microsoft Advisory', 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-26169'],
  ],
  'cve-2024-49113': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2024-49113'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-49113'],
    ['Microsoft Advisory', 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-49113'],
  ],
  'cve-2023-20198': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2023-20198'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-20198'],
    ['Cisco Talos Blog', 'https://blog.talosintelligence.com/active-exploitation-of-cisco-ios-xe-software/'],
  ],
  'cve-2023-44487': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2023-44487'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-44487'],
    ['CISA Advisory', 'https://www.cisa.gov/news-events/alerts/2023/10/10/http2-rapid-reset-attack'],
  ],
  'cve-2023-4966': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2023-4966'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-4966'],
    ['Citrix Advisory', 'https://support.citrix.com/article/CTX579459'],
  ],
  'log4shell': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2021-44228'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-44228'],
    ['Apache Advisory', 'https://logging.apache.org/log4j/2.x/security.html'],
    ['CISA Advisory', 'https://www.cisa.gov/news-events/news/apache-log4j-vulnerability-guidance'],
  ],
  'proxylogon': [
    ['NVD Entry', 'https://nvd.nist.gov/vuln/detail/CVE-2021-26855'],
    ['MITRE CVE', 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-26855'],
    ['Microsoft Blog', 'https://www.microsoft.com/en-us/security/blog/2021/03/02/hafnium-targeting-exchange-servers/'],
    ['CISA Advisory', 'https://www.cisa.gov/news-events/alerts/2021/03/03/mitigating-microsoft-exchange-server-vulnerabilities'],
  ],
};

// ─── Tutorial/tool reference links ───────────────────────────────────────────
const TUTORIAL_REFS = {
  'sql-injection': [
    ['OWASP SQLi', 'https://owasp.org/www-community/attacks/SQL_Injection'],
    ['OWASP Top 10', 'https://owasp.org/www-project-top-ten/'],
    ['PortSwigger SQLi Labs', 'https://portswigger.net/web-security/sql-injection'],
    ['NIST CWE-89', 'https://nvd.nist.gov/vuln/categories'],
  ],
  'cross-site-scripting': [
    ['OWASP XSS', 'https://owasp.org/www-community/attacks/xss/'],
    ['OWASP Top 10', 'https://owasp.org/www-project-top-ten/'],
    ['PortSwigger XSS Labs', 'https://portswigger.net/web-security/cross-site-scripting'],
  ],
  'privilege-escalation': [
    ['MITRE ATT&CK Privilege Escalation', 'https://attack.mitre.org/tactics/TA0004/'],
    ['GTFOBins', 'https://gtfobins.github.io/'],
    ['HackTricks Linux PrivEsc', 'https://book.hacktricks.xyz/linux-hardening/privilege-escalation'],
  ],
  'buffer-overflow': [
    ['OWASP Buffer Overflow', 'https://owasp.org/www-community/vulnerabilities/Buffer_Overflow'],
    ['NIST Buffer Overflow', 'https://nvd.nist.gov/vuln/categories'],
    ['MITRE CWE-120', 'https://cwe.mitre.org/data/definitions/120.html'],
  ],
  'owasp-top-10': [
    ['OWASP Top 10 Official', 'https://owasp.org/www-project-top-ten/'],
    ['OWASP Testing Guide', 'https://owasp.org/www-project-web-security-testing-guide/'],
    ['NIST SSDF', 'https://csrc.nist.gov/projects/ssdf'],
  ],
  'social-engineering': [
    ['MITRE ATT&CK Phishing', 'https://attack.mitre.org/techniques/T1566/'],
    ['SANS Social Engineering', 'https://www.sans.org/blog/social-engineering/'],
    ['NIST SP 800-50', 'https://csrc.nist.gov/publications/detail/sp/800-50/final'],
  ],
  'penetration-test': [
    ['PTES Standard', 'http://www.pentest-standard.org/index.php/Main_Page'],
    ['OWASP Testing Guide', 'https://owasp.org/www-project-web-security-testing-guide/'],
    ['NIST SP 800-115', 'https://csrc.nist.gov/publications/detail/sp/800-115/final'],
  ],
  'nmap': [
    ['Nmap Official Docs', 'https://nmap.org/docs.html'],
    ['Nmap Reference Guide', 'https://nmap.org/book/man.html'],
  ],
  'burp-suite': [
    ['PortSwigger Docs', 'https://portswigger.net/burp/documentation'],
    ['PortSwigger Web Academy', 'https://portswigger.net/web-security'],
  ],
  'metasploit': [
    ['Metasploit Docs', 'https://docs.metasploit.com/'],
    ['Rapid7 Metasploit', 'https://www.rapid7.com/products/metasploit/'],
  ],
  'wireshark': [
    ['Wireshark Official Docs', 'https://www.wireshark.org/docs/'],
    ['Wireshark Sample Captures', 'https://wiki.wireshark.org/SampleCaptures'],
  ],
  'hydra': [
    ['THC Hydra GitHub', 'https://github.com/vanhauser-thc/thc-hydra'],
    ['OWASP Brute Force', 'https://owasp.org/www-community/attacks/Brute_force_attack'],
  ],
  'sqlmap': [
    ['SQLMap Official', 'https://sqlmap.org/'],
    ['SQLMap GitHub', 'https://github.com/sqlmapproject/sqlmap'],
    ['OWASP SQLi', 'https://owasp.org/www-community/attacks/SQL_Injection'],
  ],
  'aircrack': [
    ['Aircrack-ng Official', 'https://www.aircrack-ng.org/'],
    ['Aircrack-ng Docs', 'https://www.aircrack-ng.org/documentation.html'],
  ],
  'hashcat': [
    ['Hashcat Official', 'https://hashcat.net/hashcat/'],
    ['Hashcat Wiki', 'https://hashcat.net/wiki/'],
  ],
  'nikto': [
    ['Nikto GitHub', 'https://github.com/sullo/nikto'],
    ['OWASP Vulnerability Scanning', 'https://owasp.org/www-community/controls/Static_Code_Analysis'],
  ],
  'gobuster': [
    ['Gobuster GitHub', 'https://github.com/OJ/gobuster'],
    ['OWASP Directory Traversal', 'https://owasp.org/www-community/attacks/Path_Traversal'],
  ],
  'john-the-ripper': [
    ['John the Ripper Official', 'https://www.openwall.com/john/'],
    ['John the Ripper GitHub', 'https://github.com/openwall/john'],
  ],
  'netcat': [
    ['Netcat Man Page', 'https://www.unix.com/man-page/linux/1/nc/'],
    ['SANS Netcat Cheatsheet', 'https://www.sans.org/'],
  ],
  'docker': [
    ['Docker Security Docs', 'https://docs.docker.com/engine/security/'],
    ['OWASP Docker Security', 'https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html'],
    ['CIS Docker Benchmark', 'https://www.cisecurity.org/benchmark/docker'],
  ],
  'kubernetes': [
    ['Kubernetes Security Docs', 'https://kubernetes.io/docs/concepts/security/'],
    ['CIS Kubernetes Benchmark', 'https://www.cisecurity.org/benchmark/kubernetes'],
    ['OWASP Kubernetes Top 10', 'https://owasp.org/www-project-kubernetes-top-ten/'],
  ],
  'aws-iam': [
    ['AWS IAM Best Practices', 'https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html'],
    ['MITRE ATT&CK Cloud', 'https://attack.mitre.org/matrices/enterprise/cloud/'],
    ['CloudGoat by Rhino Security', 'https://github.com/RhinoSecurityLabs/cloudgoat'],
  ],
  'dns': [
    ['OWASP DNS Security', 'https://owasp.org/www-community/attacks/DNS_Spoofing'],
    ['MITRE DNS Attack', 'https://attack.mitre.org/techniques/T1071/004/'],
    ['NIST SP 800-81', 'https://csrc.nist.gov/publications/detail/sp/800-81/2/final'],
  ],
  'ldap': [
    ['OWASP LDAP Injection', 'https://owasp.org/www-community/attacks/LDAP_Injection'],
    ['CWE-90 LDAP Injection', 'https://cwe.mitre.org/data/definitions/90.html'],
  ],
  'saml': [
    ['OWASP SAML Security', 'https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html'],
    ['PortSwigger SAML', 'https://portswigger.net/web-security/oauth/saml'],
  ],
  'ethical-hacking': [
    ['EC-Council CEH Info', 'https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/'],
    ['NIST Cybersecurity Framework', 'https://www.nist.gov/cyberframework'],
    ['TryHackMe', 'https://tryhackme.com/'],
    ['HackTheBox', 'https://www.hackthebox.com/'],
  ],
  'kali-linux': [
    ['Kali Linux Official', 'https://www.kali.org/docs/'],
    ['Kali Tools Documentation', 'https://www.kali.org/tools/'],
  ],
  'oscp': [
    ['Offensive Security OSCP', 'https://www.offsec.com/courses/pen-200/'],
    ['OSCP Exam Guide', 'https://help.offsec.com/hc/en-us/articles/360040165632'],
  ],
  'ceh': [
    ['EC-Council CEH', 'https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/'],
    ['CEH Exam Blueprint', 'https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/'],
  ],
  'comptia': [
    ['CompTIA Security+', 'https://www.comptia.org/certifications/security'],
    ['CompTIA Exam Objectives', 'https://www.comptia.org/certifications/security#examdetails'],
  ],
  'ejpt': [
    ['eJPT by INE Security', 'https://security.ine.com/certifications/ejpt-certification/'],
    ['INE Free Starter Pass', 'https://my.ine.com/CyberSecurity/learning-paths/61f1e35e-a429-4681-88c3-bd28d5fab2aa/'],
  ],
  'cissp': [
    ['ISC2 CISSP Info', 'https://www.isc2.org/certifications/cissp'],
    ['CISSP Domains Overview', 'https://www.isc2.org/certifications/cissp/cissp-cbk'],
  ],
  'cism': [
    ['ISACA CISM Info', 'https://www.isaca.org/credentialing/cism'],
  ],
  'ctf': [
    ['CTFtime.org', 'https://ctftime.org/'],
    ['PicoCTF', 'https://picoctf.org/'],
    ['HackTheBox CTF', 'https://www.hackthebox.com/'],
  ],
  'ransomware': [
    ['CISA Ransomware Guide', 'https://www.cisa.gov/stopransomware'],
    ['MITRE ATT&CK Ransomware', 'https://attack.mitre.org/techniques/T1486/'],
    ['No More Ransom', 'https://www.nomoreransom.org/'],
  ],
  'zero-day': [
    ['MITRE CVE Program', 'https://www.cve.org/'],
    ['CISA KEV Catalog', 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog'],
    ['Zero Day Initiative', 'https://www.zerodayinitiative.com/'],
  ],
  'supply-chain': [
    ['CISA Supply Chain Guidance', 'https://www.cisa.gov/supply-chain-security'],
    ['NIST SP 800-161', 'https://csrc.nist.gov/publications/detail/sp/800-161/rev-1/final'],
    ['MITRE ATT&CK Supply Chain', 'https://attack.mitre.org/techniques/T1195/'],
  ],
  'bug-bounty': [
    ['HackerOne', 'https://www.hackerone.com/'],
    ['Bugcrowd', 'https://www.bugcrowd.com/'],
    ['Google Bug Hunters', 'https://bughunters.google.com/'],
  ],
  'powershell-empire': [
    ['MITRE ATT&CK PowerShell', 'https://attack.mitre.org/techniques/T1059/001/'],
    ['BC-Security Empire GitHub', 'https://github.com/BC-SECURITY/Empire'],
    ['MITRE ATT&CK C2', 'https://attack.mitre.org/tactics/TA0011/'],
  ],
};

function buildRefsHtml(refs) {
  const items = refs.map(([label, url]) =>
    `    <li><a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a></li>`
  ).join('\n');
  return `\n<div class="ext-refs">
  <h3>Sources &amp; Further Reading</h3>
  <ul>
${items}
  </ul>
</div>\n`;
}

function findRefs(filename, category) {
  const slug = filename.replace('.html', '');

  if (category === 'cve') {
    // Try exact CVE slug match
    for (const [key, refs] of Object.entries(CVE_REFS)) {
      if (slug.includes(key)) return refs;
    }
    // Generic NVD fallback: extract CVE-YYYY-NNNNN pattern
    const m = slug.match(/(cve-\d{4}-\d+)/i);
    if (m) {
      const cveId = m[1].replace(/-/g, '-').toUpperCase().replace('CVE-', 'CVE-');
      return [
        ['NVD Entry', `https://nvd.nist.gov/vuln/detail/${cveId}`],
        ['MITRE CVE', `https://cve.mitre.org/cgi-bin/cvename.cgi?name=${cveId}`],
      ];
    }
    return null;
  }

  // For all other categories, search TUTORIAL_REFS
  for (const [key, refs] of Object.entries(TUTORIAL_REFS)) {
    if (slug.includes(key)) return refs;
  }
  return null;
}

function processFile(filepath, category) {
  const filename = basename(filepath);
  let content = readFileSync(filepath, 'utf-8');

  // Skip if already has external refs
  if (content.includes('ext-refs')) return false;

  const refs = findRefs(filename, category);
  if (!refs) return false;

  // Add CSS
  content = content.replace('</style>', REFS_CSS + '\n  </style>');

  // Insert refs HTML just before the author-bio div (so it appears: content → refs → author → related)
  const refsHtml = buildRefsHtml(refs);
  if (content.includes('<div class="author-bio">')) {
    content = content.replace('<div class="author-bio">', refsHtml + '<div class="author-bio">');
  } else {
    content = content.replace('</article>', refsHtml + '</article>');
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
    const didUpdate = processFile(filepath, category);
    if (didUpdate) {
      console.log(`  ✓ ${name}`);
      updated++;
    } else {
      console.log(`  - ${name} (no match)`);
      skipped++;
    }
  }
}

console.log(`\n${'='.repeat(50)}`);
console.log(`Done. External refs added: ${updated}  |  No match: ${skipped}`);
