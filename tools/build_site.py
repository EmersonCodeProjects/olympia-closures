"""Build the web version of the report from the final .docx.
Usage: python build_site.py report.docx out_dir
Writes out_dir/index.html (full page for GitHub Pages)."""
import sys, re, subprocess, html
from bs4 import BeautifulSoup

src, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(['pandoc', src, '-t', 'html5', '--wrap=none'], capture_output=True, text=True, check=True).stdout
s = BeautifulSoup(raw, 'html.parser')

# 1. drop title, byline, and the Word table of contents (we build our own)
h1 = s.find('h1'); byline = h1.find_next_sibling('p'); title = h1.get_text(' ', strip=True); byline_txt = byline.get_text(' ', strip=True)
h1.decompose(); byline.decompose()
for p in s.find_all(['p', 'h1', 'h2']):
    if p.get_text(strip=True) == 'Contents':
        nxt = p.find_next_sibling()
        p.decompose()
        while nxt is not None and nxt.name == 'p' and nxt.find('span') and re.fullmatch(r'\d+', nxt.find_all('span')[-1].get_text(strip=True)):
            n2 = nxt.find_next_sibling(); nxt.decompose(); nxt = n2
        break

# 1b. the About paragraphs are bold text, not Word headings; show them as headings on the web
for p in s.find_all('p'):
    t = p.get_text(strip=True)
    if t in ('About this report', 'About the author') and p.find('strong'):
        p.name = 'h2' if t == 'About this report' else 'h3'; p.string = t

# 2. tables: header row -> thead/th, strip widths, wrap for horizontal scroll
for t in s.find_all('table'):
    cg = t.find('colgroup')
    if cg: cg.decompose()
    for tag in t.find_all(style=True): del tag['style']
    for tr in t.find_all('tr'): tr.attrs.pop('class', None)
    tb = t.find('tbody'); thead = t.find('thead')
    if tb and not thead:
        first = tb.find('tr')
        if first:
            thead = s.new_tag('thead'); first.extract()
            for td in first.find_all('td'): td.name = 'th'; td['scope'] = 'col'
            thead.append(first); t.insert(0, thead)
    for tr in t.find_all('tr'):
        cells = tr.find_all(['td', 'th'])
        if cells and all(c.find('strong') and c.get_text(strip=True) == c.find('strong').get_text(strip=True) for c in cells if c.get_text(strip=True)):
            tr['class'] = 'total'
        for c in cells:
            if re.fullmatch(r'[\s$€+\-−–~≈<>()0-9.,%/→×]+', c.get_text(' ', strip=True) or 'x') and c.name == 'td':
                c['class'] = 'num'
    ncol = max(len(tr.find_all(['td', 'th'])) for tr in t.find_all('tr'))
    wrap = s.new_tag('div', attrs={'class': 'tbl' + (' wide' if ncol >= 6 else ''), 'tabindex': '0', 'role': 'region'})
    cap = t.find_previous_sibling()
    if cap is not None and cap.name == 'p' and re.match(r'\s*Table [A-Z]?[0-9.]+\.', cap.get_text()):
        cap['class'] = 'caption'; wrap['aria-label'] = cap.get_text(' ', strip=True)[:80]
    t.wrap(wrap)

# 3. headings: clean ids, collect navigation
nav = []
for h in s.find_all(['h2', 'h3']):
    hid = re.sub(r'[^a-z0-9]+', '-', h.get_text(' ', strip=True).lower()).strip('-')[:60]
    h['id'] = hid
    if h.name == 'h2': nav.append([h.get_text(' ', strip=True), hid, []])
    elif nav: nav[-1][2].append((h.get_text(' ', strip=True), hid))
# fix in-document links that pointed at old pandoc ids
ids = {h['id'] for h in s.find_all(['h2', 'h3'])}
for a in s.find_all('a', href=True):
    if a['href'].startswith('#') and a['href'][1:] not in ids:
        a.unwrap()
    elif a['href'].startswith('http'):
        a['target'] = '_blank'; a['rel'] = 'noopener'

# 4. wrap each h2 section so long sections can be styled
body_html = str(s)

def nav_html():
    out = []
    for t_, hid, subs in nav:
        sub = ''.join(f'<li><a href="#{i}">{html.escape(x)}</a></li>' for x, i in subs)
        out.append(f'<li><a href="#{hid}">{html.escape(t_)}</a>' + (f'<ul>{sub}</ul>' if sub else '') + '</li>')
    return '<ul>' + ''.join(out) + '</ul>'

date = re.search(r'([A-Z][a-z]{2,8}\.? \d{1,2}, \d{4})', byline_txt)
author = byline_txt.split('·')[-1].strip() if '·' in byline_txt else byline_txt

BOARD = [('Jess Tourtellotte-Palumbo', 'jtourtellottepalumbo@osd.wednet.edu'), ('Maria Flores', 'mflores@osd.wednet.edu'),
         ('Renee Fullerton', 'rfullerton@osd.wednet.edu'), ('Gilbert Lamont', 'glamont@osd.wednet.edu'), ('Hilary Seidel', 'hseidel@osd.wednet.edu')]

STYLE = open('site.css').read()
SCRIPT = open('site.js').read()
page = f'''<title>Olympia Elementary Closures Analysis</title>
<meta name="description" content="Independent community analysis of the Olympia School District proposal to close McKenny, Madison, and LP Brown elementary schools.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<style>{STYLE}</style>
<a class="skip" href="#main">Skip to the report</a>
<header class="bar">
  <div class="bar-inner">
    <a class="brand" href="#top">Olympia Elementary Closures <span>Community Analysis</span></a>
    <details class="sections" id="sections-menu"><summary>Sections</summary><nav aria-label="Sections">{nav_html()}</nav></details>
  </div>
</header>
<div class="layout" id="top">
  <aside class="toc" aria-label="Contents"><p class="toc-label">Contents</p>{nav_html()}</aside>
  <main id="main">
    <section class="hero">
      <p class="eyebrow">Independent analysis · Olympia School District · {html.escape(date.group(1) if date else '')}</p>
      <p class="update"><strong>Update, Oct. 20:</strong> <a href="OSD_Enrollment_Addendum_Oct22.pdf">Addendum on the district’s Oct. 22 enrollment review</a> <small>PDF</small>. The report below is unchanged.</p>
      <h1>The proposal to close McKenny, Madison, and LP Brown</h1>
      <p class="thesis">Recruitment, not closure, is the answer.</p>
      <p class="byline">By {html.escape(author)} · Community analysis, version 1.0</p>
      <dl class="facts">
        <div><dt>Board vote</dt><dd>Thursday, Nov. 12</dd></div>
        <div><dt>Public hearings, 6 p.m.</dt><dd>McKenny Oct. 12<br>LP Brown Oct. 15<br>Madison Oct. 19</dd></div>
        <div><dt>Forecast gap</dt><dd>about $0.4M a year</dd></div>
        <div><dt>Closure savings</dt><dd>Claimed $3.1M a year; <span class="nw">likely $1.3–2.0M</span></dd></div>
      </dl>
      <div class="downloads">
        <a class="dl primary" href="OSD_Closure_Community_Analysis.pdf">Full report <small>PDF</small></a>
        <a class="dl" href="OSD_Closure_Fact_Sheet.pdf">Two-page fact sheet <small>PDF</small></a>
        <a class="dl" href="OSD_Enrollment_Addendum_Oct22.pdf">Oct. 22 enrollment addendum <small>PDF</small></a>
        <a class="dl" href="analysis/OSD_Statistical_Analyses.xlsx">Statistics workbook <small>Excel</small></a>
        <a class="dl" href="https://github.com/EmersonCodeProjects/olympia-closures">Data and code <small>GitHub</small></a>
      </div>
    </section>
    <article class="report">
{body_html}
    </article>
    <section class="involve" id="get-involved">
      <h2>How to be heard</h2>
      <p>Speak at a hearing, or email all five board members before November 12 and ask that your comments be included in the record of the closure decision.</p>
      <ul class="board">
        {''.join(f'<li><span class="who">{n}</span><span class="addr">{e}</span><button type="button" class="copy" data-copy="{e}" aria-label="Copy {n}\'s email">Copy</button></li>' for n, e in BOARD)}
      </ul>
      <button type="button" class="copy all" data-copy="{', '.join(e for _, e in BOARD)}">Copy all five addresses</button>
    </section>
    <footer class="foot">
      <p>Independent analysis by {html.escape(author)}. Figures marked as estimates are the author's; all others come from the sources cited. The data, the statistical workbook, and the code that reproduces every number are published with this page.</p>
    </footer>
  </main>
</div>
<script>{SCRIPT}</script>
'''
full = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + \
       page.split('<a class="skip"')[0] + '</head>\n<body>\n<a class="skip"' + page.split('<a class="skip"', 1)[1] + '</body>\n</html>\n'
open(f'{out}/index.html', 'w').write(full)
print('sections', len(nav), 'tables', len(s.find_all('table')))
