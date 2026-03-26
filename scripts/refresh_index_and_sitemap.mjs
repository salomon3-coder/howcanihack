import { readFileSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..");
const MAX_ARTICLES = 140;

const STOPWORDS = new Set([
  "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in",
  "into", "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
  "guide", "tutorial", "complete", "explained", "basics", "beginner", "beginners",
  "cybersecurity", "security", "attack", "attacks", "vulnerability", "vulnerabilities",
  "learn", "using", "use", "what", "why", "works"
]);

const STRONG_TOKENS = new Set([
  "nmap", "wireshark", "burp", "sqlmap", "metasploit", "hydra", "hashcat", "aircrack",
  "gobuster", "netcat", "nikto", "john", "password", "social", "engineering",
  "owasp", "ctf", "kali", "firewalls", "firewall", "tor", "proxychains"
]);

const articleKey = (a) => {
  const url = (a.url || "").trim();
  if (url) return url;
  const slug = (a.slug || "").trim();
  const cat = (a.category || "").trim();
  if (slug && cat) return `/${cat}/${slug}.html`;
  return slug;
};

const tokens = (title) => {
  const raw = (title || "").toLowerCase().match(/[a-z0-9]+/g) || [];
  return new Set(raw.filter((t) => t.length > 2 && !STOPWORDS.has(t)));
};

const strongSignature = (title) => {
  const t = (title || "").toLowerCase();
  const tok = tokens(t);
  const sig = new Set([...tok].filter((x) => STRONG_TOKENS.has(x)));
  if (t.includes("sql") && t.includes("injection")) sig.add("__sqli__");
  if (t.includes("xss") || t.includes("cross-site") || t.includes("cross site")) sig.add("__xss__");
  if (t.includes("home") && t.includes("lab")) sig.add("__home_lab__");
  if (t.includes("social") && t.includes("engineering")) sig.add("__social_engineering__");
  return sig;
};

const jaccard = (a, b) => {
  if (!a.size || !b.size) return 0;
  const inter = [...a].filter((x) => b.has(x)).length;
  const union = new Set([...a, ...b]).size;
  return union ? inter / union : 0;
};

const dedupeExact = (rows) => {
  const best = new Map();
  for (const a of rows) {
    if (!a || typeof a !== "object") continue;
    const key = articleKey(a);
    if (!key) continue;
    const prev = best.get(key);
    if (!prev || (a.date || "") >= (prev.date || "")) best.set(key, a);
  }
  return [...best.values()].sort((x, y) => (y.date || "").localeCompare(x.date || ""));
};

const curateSemantic = (rows) => {
  const ranked = [...rows].sort((a, b) => {
    const ad = (a.description || "").trim() ? 1 : 0;
    const bd = (b.description || "").trim() ? 1 : 0;
    if (bd !== ad) return bd - ad;
    return (b.date || "").localeCompare(a.date || "");
  });

  const kept = [];
  const byCatTokens = new Map();
  const byCatSig = new Map();

  for (const a of ranked) {
    const cat = (a.category || "").trim().toLowerCase();
    const title = (a.title || "").trim();
    if (!title) continue;
    if (cat === "cve") {
      kept.push(a);
      continue;
    }

    const tset = tokens(title);
    const sig = strongSignature(title);
    const seenSig = byCatSig.get(cat) || new Set();
    const seenTokens = byCatTokens.get(cat) || [];

    if (sig.size && [...sig].some((x) => seenSig.has(x))) continue;
    if (seenTokens.some((p) => jaccard(tset, p) >= 0.58)) continue;

    kept.push(a);
    for (const s of sig) seenSig.add(s);
    seenTokens.push(tset);
    byCatSig.set(cat, seenSig);
    byCatTokens.set(cat, seenTokens);
  }

  return kept.sort((x, y) => (y.date || "").localeCompare(x.date || "")).slice(0, MAX_ARTICLES);
};

const writeSitemap = (articles) => {
  const base = "https://howcanihack.com";
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    `  <url><loc>${base}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>`,
    `  <url><loc>${base}/tutorials/</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>`,
    `  <url><loc>${base}/news/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>`,
    `  <url><loc>${base}/cve/</loc><changefreq>daily</changefreq><priority>0.8</priority></url>`,
    `  <url><loc>${base}/certifications/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>`,
    `  <url><loc>${base}/tools/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>`,
    `  <url><loc>${base}/beginner/</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>`,
    `  <url><loc>${base}/about.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>`,
    `  <url><loc>${base}/contact.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>`,
    `  <url><loc>${base}/editorial-policy.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>`,
    `  <url><loc>${base}/write-for-us.html</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>`,
    `  <url><loc>${base}/privacy.html</loc><changefreq>monthly</changefreq><priority>0.4</priority></url>`,
    `  <url><loc>${base}/disclaimer.html</loc><changefreq>monthly</changefreq><priority>0.4</priority></url>`
  ];

  const urlLastmod = {};
  const today = new Date().toISOString().slice(0, 10);
  for (const a of articles) {
    const url = base + (a.url || "");
    if (!url || url === base) continue;
    const lastmod = a.date || today;
    if (!urlLastmod[url] || lastmod > urlLastmod[url]) urlLastmod[url] = lastmod;
  }
  for (const url of Object.keys(urlLastmod).sort()) {
    lines.push(
      `  <url><loc>${url}</loc><lastmod>${urlLastmod[url]}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>`
    );
  }
  lines.push("</urlset>");
  writeFileSync(join(REPO_ROOT, "sitemap.xml"), lines.join("\n") + "\n", "utf8");
};

const path = join(REPO_ROOT, "articles.json");
const raw = JSON.parse(readFileSync(path, "utf8"));
const exact = dedupeExact(raw);
const curated = curateSemantic(exact);
writeFileSync(path, JSON.stringify(curated, null, 2) + "\n", "utf8");
writeSitemap(curated);
console.log(`articles.json: ${raw.length} -> ${exact.length} (exact) -> ${curated.length} (semantic)`);
console.log("sitemap.xml regenerated");
