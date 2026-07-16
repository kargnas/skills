---
name: competitor-website-audit
description: "Comprehensive competitor website audit that scrapes competitor sites, analyzes SEO metrics, captures screenshots, measures performance, extracts pricing data, and generates a comparison report. Use when asked to 'audit competitor', 'compare websites', 'competitive analysis', 'website benchmark', or 'generate competitor report'. Involves web fetching, browser automation, CLI tools, file processing, and report generation."
---

# Competitor Website Audit

> **ONE SENTENCE:** Scrape, measure, screenshot, and compare competitor websites — then produce an executive report.

---

## Prerequisites

| Requirement | Check Command | Expected |
|-------------|---------------|----------|
| Playwright | `playwright --version` | Version number printed |
| WebFetch tool | Available in agent tools | Tool exists |
| curl | `curl --version` | Version printed |
| jq | `jq --version` | Version printed |
| python3 | `python3 --version` | 3.8+ |

---

## Procedure

MUST execute every step below in order. Do NOT skip any step.

---

### Step 1 [S1]: Initialize Audit Workspace

**Action**: Run this command to create the workspace and state file:

```bash
mkdir -p audit_output/screenshots audit_output/data audit_output/reports audit_output/logs && python3 -c "
import json
from datetime import datetime, timezone
state = {
    'competitors': [],
    'status': 'initialized',
    'started_at': datetime.now(timezone.utc).isoformat(),
    'current_step': 'S1'
}
json.dump(state, open('audit_output/state.json', 'w'), indent=2)
print('workspace initialized')
"
```

**VERIFY**: Command prints `workspace initialized`. Run `ls audit_output/` and confirm 4 directories exist.

---

### Step 2 [S2]: Collect Competitor URLs

**Action**: Determine competitor URLs using this decision table:

| Situation | Action |
|-----------|--------|
| User provided URLs in their request | Extract URLs from user message |
| User did NOT provide URLs | Ask user: "Please provide competitor URLs (one per line)" |
| File `audit_output/competitors.txt` exists | Read URLs from that file |

**Action after obtaining URLs**: Save them to state.json:

```bash
python3 -c "
import json, sys
urls = sys.argv[1:]
state = json.load(open('audit_output/state.json'))
for url in urls:
    if url.startswith('http'):
        domain = url.split('//')[1].split('/')[0]
        state['competitors'].append({'url': url, 'domain': domain})
state['current_step'] = 'S2'
json.dump(state, open('audit_output/state.json', 'w'), indent=2)
print(f'Added {len(state[\"competitors\"])} competitors')
" "{URL_1}" "{URL_2}" "{URL_3}"
```

**VERIFY**: Script prints `Added N competitors` where N >= 1. Run `python3 -c "import json; d=json.load(open('audit_output/state.json')); print(len(d['competitors']))"` and confirm N >= 1.

**IF BLOCKED**: No URLs available → Print "No competitor URLs provided. Cannot proceed." and STOP.

---

### Step 3 [S3]: DNS Lookup for First Competitor

**DELEGATE TO SUBAGENT**:
  Task: "For each domain in audit_output/state.json, run DNS and SSL checks. For each domain: (1) Run `dig +short {domain} A` for A records, (2) Run `dig +short {domain} MX` for MX records, (3) Run `curl -sI https://{domain}` and extract Server header for CDN detection. Save results as JSON to audit_output/data/{domain}_dns.json with keys: a_records, mx_records, server_header, cdn_detected. Print 'DNS complete for {domain}' after each."
  Input: Read audit_output/state.json to get the list of domains
  Expected output: One JSON file per domain in audit_output/data/

**VERIFY**: For each domain, run `ls audit_output/data/*_dns.json` and confirm files exist.

**IF BLOCKED**: dig not available → Use `nslookup {domain}` as fallback. curl fails → Skip CDN detection, set cdn_detected to "unknown".

---

### Step 4 [S4]: HTTP Performance Measurement

**DELEGATE TO SUBAGENT**:
  Task: "For each competitor URL in audit_output/state.json, measure HTTP performance. Run this curl command 3 times per URL:
  `curl -o /dev/null -s -w '{\"dns\":%{time_namelookup},\"connect\":%{time_connect},\"tls\":%{time_appconnect},\"ttfb\":%{time_starttransfer},\"total\":%{time_total},\"http_version\":\"%{http_version}\"}' {URL}`
  Average the 3 results. Save to audit_output/data/{domain}_performance.json with keys: avg_dns_ms, avg_connect_ms, avg_tls_ms, avg_ttfb_ms, avg_total_ms, http_version, compression (check Accept-Encoding response). Print the TTFB average for each domain."
  Input: URLs from audit_output/state.json
  Expected output: One JSON file per domain

**VERIFY**: Run `ls audit_output/data/*_performance.json | wc -l` and confirm count matches number of competitors.

**IF BLOCKED**: curl timing fails → Use `time curl -s {URL} > /dev/null` as rough timing fallback.

---

### Step 5 [S5]: Fetch and Parse Homepage HTML

**Action**: For EACH competitor URL (from audit_output/state.json), use WebFetch to download the homepage HTML.

**Action per competitor**: After fetching HTML, extract SEO metadata with this command:

```bash
python3 -c "
import json, re, sys
html = open(sys.argv[1]).read()
domain = sys.argv[2]
def extract(pattern, html, default=''):
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else default

seo = {
    'title': extract(r'<title>(.*?)</title>', html),
    'meta_description': extract(r'<meta[^>]*name=[\"\\']description[\"\\'][^>]*content=[\"\\']([^\"\\']*)[\"\\'\\']', html),
    'og_title': extract(r'<meta[^>]*property=[\"\\']og:title[\"\\'][^>]*content=[\"\\']([^\"\\']*)[\"\\'\\']', html),
    'og_description': extract(r'<meta[^>]*property=[\"\\']og:description[\"\\'][^>]*content=[\"\\']([^\"\\']*)[\"\\'\\']', html),
    'og_image': extract(r'<meta[^>]*property=[\"\\']og:image[\"\\'][^>]*content=[\"\\']([^\"\\']*)[\"\\'\\']', html),
    'canonical': extract(r'<link[^>]*rel=[\"\\']canonical[\"\\'][^>]*href=[\"\\']([^\"\\']*)[\"\\'\\']', html),
    'robots': extract(r'<meta[^>]*name=[\"\\']robots[\"\\'][^>]*content=[\"\\']([^\"\\']*)[\"\\'\\']', html, 'not set'),
    'h1_count': len(re.findall(r'<h1', html, re.IGNORECASE)),
    'has_jsonld': 'application/ld+json' in html.lower()
}
json.dump(seo, open(f'audit_output/data/{domain}_seo.json', 'w'), indent=2)
print(f'SEO extracted: title={seo[\"title\"][:50]}')
" "audit_output/data/{domain}_homepage.html" "{domain}"
```

**VERIFY**: Run `ls audit_output/data/*_seo.json | wc -l` and confirm count matches competitors.

**IF BLOCKED**: WebFetch fails for a URL → Use `curl -sL {URL} -o audit_output/data/{domain}_homepage.html` as fallback.

---

### Step 6 [S6]: Capture Desktop Screenshots

**Action**: For EACH competitor URL, use Playwright to capture a desktop screenshot.

```
Navigate to {URL}
Set viewport: width=1920, height=1080
Wait for network idle (max 10 seconds)
Take full-page screenshot
Save to: audit_output/screenshots/{domain}_desktop.png
```

**VERIFY**: Run `ls audit_output/screenshots/*_desktop.png | wc -l` and confirm count matches competitors.

**IF BLOCKED**: Playwright not available → Use `curl -sL {URL} -o audit_output/data/{domain}_homepage.html` and note "screenshot skipped - Playwright unavailable".

---

### Step 7 [S7]: Capture Mobile Screenshots

**Action**: For EACH competitor URL, use Playwright to capture a mobile screenshot.

```
Navigate to {URL}
Set viewport: width=375, height=812
Set user agent to iPhone Safari
Wait for network idle (max 10 seconds)
Take full-page screenshot
Save to: audit_output/screenshots/{domain}_mobile.png
```

**VERIFY**: Run `ls audit_output/screenshots/*_mobile.png | wc -l` and confirm count matches competitors.

**IF BLOCKED**: Playwright fails → Note "mobile screenshot skipped" and continue to [S8].

---

### Step 8 [S8]: JavaScript Bundle Analysis

**DELEGATE TO SUBAGENT**:
  Task: "For each competitor URL in audit_output/state.json: (1) Use Playwright to navigate to the URL, (2) Capture all network requests that are .js files, (3) Categorize each JS file as first-party (same domain) or third-party, (4) Detect framework by looking for known patterns: 'react' in any JS → React, 'vue' → Vue, 'angular' → Angular, 'svelte' → Svelte, (5) Detect analytics: 'google-analytics' or 'gtag' → GA4, 'mixpanel' → Mixpanel, 'amplitude' → Amplitude, 'segment' → Segment, (6) Calculate total JS size in KB. Save to audit_output/data/{domain}_js_analysis.json with keys: total_js_kb, first_party_count, third_party_count, framework, analytics_tools. Print summary per domain."
  Input: URLs from audit_output/state.json
  Expected output: One JSON file per domain

**VERIFY**: Run `ls audit_output/data/*_js_analysis.json | wc -l` and confirm count matches competitors.

**IF BLOCKED**: Playwright network capture fails → Parse the HTML source for `<script src=` tags instead and estimate from that.

---

### Step 9 [S9]: Pricing Page Extraction

**Action**: For EACH competitor, attempt to find and extract pricing data.

Try these URLs in order until one returns HTTP 200:

| URL Pattern | Priority |
|-------------|----------|
| `{base_url}/pricing` | Try first |
| `{base_url}/plans` | Try second |
| `{base_url}/price` | Try third |
| `{base_url}/subscribe` | Try fourth |

**Action for found pricing page**: Use Playwright to navigate and extract visible text. Then parse pricing tiers:

```bash
python3 -c "
import json, sys
# The agent should extract this data from the page text
pricing = {
    'pricing_page_url': sys.argv[1],
    'has_pricing': True,
    'tiers': [],  # Each tier: {name, monthly_price, annual_price, features: [], cta_text}
    'is_contact_sales': False,
    'notes': ''
}
json.dump(pricing, open(f'audit_output/data/{sys.argv[2]}_pricing.json', 'w'), indent=2)
print(f'Pricing extracted for {sys.argv[2]}')
" "{pricing_url}" "{domain}"
```

| Pricing Page Result | Action |
|---------------------|--------|
| Page found with visible prices | Extract tier names, prices, features |
| Page found but says "Contact Sales" | Set `is_contact_sales: true` |
| No pricing page found | Set `has_pricing: false` |

**VERIFY**: Run `ls audit_output/data/*_pricing.json | wc -l` and confirm count matches competitors.

---

### Step 10 [S10]: Technology Stack Detection

**Action**: For EACH competitor, detect technology stack from already-collected data.

```bash
python3 -c "
import json, sys
domain = sys.argv[1]

# Read from previously collected data
dns = json.load(open(f'audit_output/data/{domain}_dns.json'))
seo = json.load(open(f'audit_output/data/{domain}_seo.json'))
js = json.load(open(f'audit_output/data/{domain}_js_analysis.json'))

techstack = {
    'server': dns.get('server_header', 'unknown'),
    'cdn': dns.get('cdn_detected', 'unknown'),
    'frontend_framework': js.get('framework', 'unknown'),
    'analytics': js.get('analytics_tools', []),
    'has_jsonld': seo.get('has_jsonld', False),
    'total_js_kb': js.get('total_js_kb', 0)
}
json.dump(techstack, open(f'audit_output/data/{domain}_techstack.json', 'w'), indent=2)
print(f'Techstack: server={techstack[\"server\"]}, framework={techstack[\"frontend_framework\"]}')
" "{domain}"
```

**VERIFY**: Run `ls audit_output/data/*_techstack.json | wc -l` and confirm count matches competitors.

**IF BLOCKED**: Missing input files from prior steps → Set unknown fields to `"unavailable"` and continue.

---

### Step 11 [S11]: Core Web Vitals Estimation

**DELEGATE TO SUBAGENT**:
  Task: "For each competitor URL in audit_output/state.json: Use WebFetch to call Google PageSpeed Insights API: `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={URL}&strategy=mobile&category=performance`. Extract from the JSON response: (1) performance_score from lighthouseResult.categories.performance.score, (2) LCP from lighthouseResult.audits.largest-contentful-paint.numericValue, (3) CLS from lighthouseResult.audits.cumulative-layout-shift.numericValue, (4) TBT from lighthouseResult.audits.total-blocking-time.numericValue. Save to audit_output/data/{domain}_webvitals.json. Print score for each domain."
  Input: URLs from audit_output/state.json
  Expected output: One JSON file per domain

**VERIFY**: Run `ls audit_output/data/*_webvitals.json | wc -l` and confirm count matches competitors.

**IF BLOCKED**: PageSpeed API fails or rate limited → Set all metrics to `"unavailable"` and note "PSI API unavailable" in the file.

---

### Step 12 [S12]: Content Analysis

**DELEGATE TO SUBAGENT**:
  Task: "For each competitor, read the homepage HTML from audit_output/data/{domain}_homepage.html. Analyze: (1) word_count: count words in visible text (strip HTML tags), (2) h1_count/h2_count/h3_count: count heading tags, (3) image_count: count <img> tags, (4) images_with_alt: count <img> tags that have non-empty alt attribute, (5) internal_link_count: count <a> tags where href starts with / or contains the same domain, (6) external_link_count: count <a> tags linking to other domains. Save to audit_output/data/{domain}_content.json. Print word count and image stats per domain."
  Input: HTML files in audit_output/data/
  Expected output: One JSON file per domain

**VERIFY**: Run `ls audit_output/data/*_content.json | wc -l` and confirm count matches competitors.

**IF BLOCKED**: HTML file missing → Skip that competitor's content analysis and note "HTML not available".

---

### Step 13 [S13]: Social Media Presence Check

**Action**: For EACH competitor, check social media links in the homepage HTML:

```bash
python3 -c "
import json, re, sys
domain = sys.argv[1]
html = open(f'audit_output/data/{domain}_homepage.html').read()

platforms = {
    'twitter': r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[\w]+',
    'linkedin': r'https?://(?:www\.)?linkedin\.com/company/[\w-]+',
    'facebook': r'https?://(?:www\.)?facebook\.com/[\w.-]+',
    'instagram': r'https?://(?:www\.)?instagram\.com/[\w.]+',
    'youtube': r'https?://(?:www\.)?youtube\.com/(?:@|channel/|c/)[\w-]+',
    'github': r'https?://(?:www\.)?github\.com/[\w-]+',
    'discord': r'https?://(?:www\.)?discord\.(?:gg|com)/[\w-]+'
}

social = {}
for platform, pattern in platforms.items():
    matches = re.findall(pattern, html, re.IGNORECASE)
    social[platform] = matches[0] if matches else None

json.dump(social, open(f'audit_output/data/{domain}_social.json', 'w'), indent=2)
found = [p for p, u in social.items() if u]
print(f'{domain}: found {len(found)} social profiles: {found}')
" "{domain}"
```

**VERIFY**: Run `ls audit_output/data/*_social.json | wc -l` and confirm count matches competitors.

---

### Step 14 [S14]: Generate Comparison Matrix

**Action**: Aggregate all collected data into a comparison matrix:

```bash
python3 -c "
import json, glob, os

# Read state for competitor list
state = json.load(open('audit_output/state.json'))
domains = [c['domain'] for c in state['competitors']]

# Build comparison data
comparison = []
for domain in domains:
    row = {'domain': domain}
    for suffix in ['performance', 'seo', 'techstack', 'webvitals', 'content', 'pricing', 'social']:
        path = f'audit_output/data/{domain}_{suffix}.json'
        if os.path.exists(path):
            row[suffix] = json.load(open(path))
        else:
            row[suffix] = {'status': 'data_missing'}
    comparison.append(row)

json.dump(comparison, open('audit_output/reports/comparison_data.json', 'w'), indent=2)
print(f'Comparison matrix built for {len(comparison)} competitors')
"
```

Then write `audit_output/reports/comparison_matrix.md` with this EXACT template:

```markdown
# Competitor Comparison Matrix

| Metric | {Domain 1} | {Domain 2} | ... |
|--------|------------|------------|-----|
| TTFB (ms) | {value} | {value} | ... |
| Total Load (ms) | {value} | {value} | ... |
| JS Bundle (KB) | {value} | {value} | ... |
| Performance Score | {value} | {value} | ... |
| LCP (ms) | {value} | {value} | ... |
| CLS | {value} | {value} | ... |
| Framework | {value} | {value} | ... |
| CDN | {value} | {value} | ... |
| Pricing Model | {value} | {value} | ... |
| Social Profiles | {count} | {count} | ... |
| Word Count | {value} | {value} | ... |
| Image Alt Coverage | {%} | {%} | ... |

## Leader/Laggard
- **Best Performance**: {domain} (lowest TTFB)
- **Best SEO**: {domain} (highest content score)
- **Most Social Presence**: {domain} ({count} profiles)
```

**VERIFY**: File `audit_output/reports/comparison_matrix.md` exists and contains a markdown table.

---

### Step 15 [S15]: Final Summary and Recommendations

**Action**: Write the executive summary to `audit_output/reports/executive_summary.md` using this EXACT template:

```markdown
# Competitive Audit Executive Summary

**Date**: {YYYY-MM-DD}
**Competitors Analyzed**: {count}
**Domains**: {comma-separated list}

## Key Findings

### Top 3 Competitive Advantages
1. {advantage with supporting data}
2. {advantage with supporting data}
3. {advantage with supporting data}

### Top 3 Areas for Improvement
1. {area with competitor benchmark}
2. {area with competitor benchmark}
3. {area with competitor benchmark}

## Quick Wins (Immediate Actions)
- [ ] {action 1 with expected impact}
- [ ] {action 2 with expected impact}
- [ ] {action 3 with expected impact}

## Strategic Recommendations
| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| P0 | {action} | {low/medium/high} | {low/medium/high} |
| P1 | {action} | {low/medium/high} | {low/medium/high} |
| P2 | {action} | {low/medium/high} | {low/medium/high} |

## Files Generated
- `audit_output/reports/comparison_matrix.md` — Side-by-side comparison
- `audit_output/data/` — Raw data files ({count} files)
- `audit_output/screenshots/` — Visual evidence ({count} screenshots)
```

**Action**: Update state.json to completed:

```bash
python3 -c "
import json
from datetime import datetime, timezone
state = json.load(open('audit_output/state.json'))
state['status'] = 'completed'
state['completed_at'] = datetime.now(timezone.utc).isoformat()
state['current_step'] = 'S15'
json.dump(state, open('audit_output/state.json', 'w'), indent=2)
print('Audit completed')
"
```

**VERIFY**: Run `python3 -c "import json; print(json.load(open('audit_output/state.json'))['status'])"` and confirm it prints `completed`.

---

## Constraints

- **MUST** execute steps S1 through S15 in order
- **MUST NOT** skip any step — if a step fails, use the IF BLOCKED fallback
- **MUST** use subagent delegation for steps marked DELEGATE TO SUBAGENT
- **MUST** verify each step before proceeding to the next
- **SHOULD** process competitors in parallel within each step when possible
- **MAY** add additional competitors to state.json if discovered during analysis

## Error Recovery

| Error | Recovery |
|-------|----------|
| Network timeout on any URL | Retry once after 5 seconds. If still fails → mark as "timeout" in data |
| Playwright not available | Fall back to curl + HTML parsing for all browser steps |
| PageSpeed API rate limit | Wait 60 seconds and retry. Max 2 retries |
| Empty HTML response | Skip SEO/content analysis for that domain, note in report |
| Python script error | Print the error, save partial data, continue to next step |
