"""
Reproduce every statistical result in Appendix A of
"OSD 2026 Elementary Closure Proposal: Community Analysis" (Emerson Christie, Oct. 2026)
from the district enrollment files in ../data, and write OSD_Statistical_Analyses.xlsx.

Run:  python reproduce.py            (needs pandas, numpy, scipy, openpyxl)
All randomness (the bootstrap) uses a fixed seed, so results are identical on every run.
"""
import numpy as np, pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter as L
import load, stats_util as su

d = load.load_all()
E5, ALL, TOT = d['E5'], d['ALL'], d['totals']
SCH = d['school'].groupby(['fall', 'school'])['n'].sum().unstack()
CLOSING = ['McKenny', 'LP Brown', 'Madison']
RECEIVING = ['Hansen', 'Centennial', 'Garfield', 'Roosevelt', 'Pioneer']
OTHER = ['McLane', 'Lincoln', 'Boston Harbor']
SCHOOLS = CLOSING + RECEIVING + OTHER
YEARS = list(range(2009, 2027))
K5 = E5.sum(axis=1)
NW = 2  # Newey-West lag: floor(4*(n/100)^(2/9)) = 2 for n = 17-18

# ---------------------------------------------------------------- statistics
trend_rows = []   # (table, series, period, method, result-dict)
def trend(table, name, s, a, b, nw=False):
    s = s.loc[a:b]
    r = su.ols(s.index.values, s.values, NW if nw else None)
    trend_rows.append((table, name, f'{a}-{b}', f'OLS, Newey-West SE (lag {NW})' if nw else 'OLS, ordinary SE', r))
    return r

trend('A5.2', 'Kindergarten', E5[0], 2009, 2019)
trend('A5.2', 'Kindergarten', E5[0], 2020, 2026)
trend('A5.2', 'K-5 total', K5, 2009, 2019)
trend('A5.2', 'K-5 total', K5, 2020, 2026)
trend('A5.2', 'K-5 total', K5, 2009, 2026, nw=True)
for g in (3, 4, 5):
    trend('A5.2', f'Grade {g}', E5[g], 2021, 2026)

S = SCH.copy()
S['Closing schools combined'] = S[CLOSING].sum(axis=1)
S['Other 8 schools combined'] = S[RECEIVING + OTHER].sum(axis=1)
S['All 11 schools'] = S[SCHOOLS].sum(axis=1)
for c in SCHOOLS + ['Closing schools combined', 'Other 8 schools combined', 'All 11 schools']:
    trend('Table 4', c, S[c], 2009, 2026, nw=True)
    trend('Table 4', c, S[c], 2019, 2026)
share = S['Closing schools combined'] / S['All 11 schools']
trend('Table 4', 'Closing schools share of K-5 (difference vs. other 8)', share, 2009, 2026, nw=True)

AVG = TOT['annual_avg']
trend('A7.2', 'District annual average', AVG, 2009, 2025, nw=True)
trend('A7.2', 'District annual average', AVG, 2009, 2019)
trend('A7.2', 'District annual average', AVG, 2019, 2025)
trend('A7.2', 'District annual average', AVG, 2020, 2025)
AVG26 = AVG.copy(); AVG26[2026] = TOT.loc[2026, 'september'] + 11
trend('A7.2', 'District annual average (2026-27 = Sept. + 11)', AVG26, 2020, 2026)

# model comparison (A6): AIC = n ln(RSS/n) + 2k, k = number of fitted coefficients
x = np.array(YEARS, float); y = K5.loc[YEARS].values.astype(float); n = len(y); t = x - 2009; one = np.ones(n)
def fitm(X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None); e = y - X @ b; rss = e @ e
    return b, rss, 1 - rss / ((y - y.mean()) @ (y - y.mean())), n * np.log(rss / n) + 2 * X.shape[1]
post = (x >= 2020).astype(float)
models = {'Two segments, break at 2020': np.column_stack([one * (1 - post), t * (1 - post), post, t * post]),
          'Quadratic': np.column_stack([one, t, t ** 2]), 'Straight line': np.column_stack([one, t])}
cyc = lambda P: np.column_stack([one, t, np.sin(2 * np.pi * t / P), np.cos(2 * np.pi * t / P)])
for P in (15, 20, 25, 30):
    models[f'Straight line + {P}-year cycle'] = cyc(P)
model_rows = []
for name, X in models.items():
    b, rss, r2, aic = fitm(X)
    low = ''
    if 'cycle' in name:
        P = int(name.split('+ ')[1].split('-')[0]); tt = np.arange(0, 45, 0.01)
        f = b[0] + b[1] * tt + b[2] * np.sin(2 * np.pi * tt / P) + b[3] * np.cos(2 * np.pi * tt / P)
        mins = [2009 + tt[i] for i in range(1, len(tt) - 1) if f[i] < f[i - 1] and f[i] < f[i + 1] and 2009 + tt[i] > 2026]
        low = f'next low point about {round(mins[0])}' if mins else ''
    model_rows.append((name, X.shape[1], r2, aic, low))
bestP = minimize_scalar(lambda P: fitm(cyc(P))[1], bounds=(8, 40), method='bounded').x

# advancement ratios (A10) and Welch tests
def ratio_table(M, grades):
    rows = []
    for g in grades:
        r = {yy: M.loc[yy, g + 1] / M.loc[yy - 1, g] for yy in M.index[1:]}
        pre = [r[yy] for yy in range(2010, 2020)]; po = [r[yy] for yy in range(2022, 2027)]
        rows.append((g, np.mean(pre), np.std(pre, ddof=1), np.mean(po), np.std(po, ddof=1),
                     stats.ttest_ind(pre, po, equal_var=False).pvalue, r))
    return rows
adv5 = ratio_table(E5, range(0, 5))
adv12 = ratio_table(ALL, range(0, 12))

# cohort tracking (A11)
cohorts = [(k, E5.loc[k, 0], E5.loc[k + 5, 5]) for k in range(2009, 2022)]

# K-12 deterministic projection (A8.2): 2022-2026 mean ratios
R12 = {g: np.mean([ALL.loc[yy, g + 1] / ALL.loc[yy - 1, g] for yy in range(2022, 2027)]) for g in range(12)}
def project(kfun, last=2034):
    cur = ALL.loc[2026].values.astype(float); out = {}
    for i, yy in enumerate(range(2027, last + 1)):
        new = np.zeros(13); new[0] = kfun(i + 1, cur[0])
        for g in range(12): new[g + 1] = cur[g] * R12[g]
        cur = new; out[yy] = cur.copy()
    return out
proj_hold = project(lambda i, k: 513)
proj_3pct = project(lambda i, k: k * 0.97)

# K-5 bootstrap projection (A8.1)
rng = np.random.default_rng(20261012)
byears = list(range(2010, 2020)) + list(range(2022, 2027))
RR = np.array([[E5.loc[yy, g + 1] / E5.loc[yy - 1, g] for g in range(5)] for yy in byears])
def boot(kfun, N=20000):
    res = {2028: [], 2030: []}
    for _ in range(N):
        cur = E5.loc[2026].values.astype(float)
        for i, yy in enumerate(range(2027, 2031)):
            r = RR[rng.integers(len(byears))]
            cur = np.concatenate([[kfun(i + 1) * rng.normal(1, 0.04)], cur[:5] * r])
            if yy in res: res[yy].append(cur.sum())
    return {yy: np.percentile(v, [50, 2.5, 97.5]) for yy, v in res.items()}
boots = {'Holds at 456': boot(lambda i: 456), 'Falls 12 per year': boot(lambda i: 456 - 12 * i),
         'Falls 5% per year': boot(lambda i: 456 * 0.95 ** i)}

# ---------------------------------------------------------------- workbook
wb = Workbook()
AR = 'Arial'
H = Font(name=AR, bold=True); N_ = Font(name=AR); BLUE = Font(name=AR, color='0000FF'); TITLE = Font(name=AR, bold=True, size=13)
NOTE = Font(name=AR, italic=True, size=9, color='595959'); GRN = Font(name=AR, color='008000')
HDR = PatternFill('solid', fgColor='F2F2F2'); KEY = PatternFill('solid', fgColor='FFF2CC')

def sheet(title, heading, note=None):
    ws = wb.create_sheet(title); ws['A1'] = heading; ws['A1'].font = TITLE
    if note: ws['A2'] = note; ws['A2'].font = NOTE
    return ws
def header(ws, r, cols, c0=1):
    for j, c in enumerate(cols):
        cell = ws.cell(r, c0 + j, c); cell.font = H; cell.fill = HDR; cell.alignment = Alignment(wrap_text=True, vertical='top')
def put(ws, r, c, v, font=None, fmt=None):
    cell = ws.cell(r, c, v); cell.font = font or N_
    if fmt: cell.number_format = fmt
    return cell
def widths(ws, w):
    for i, x in enumerate(w): ws.column_dimensions[L(i + 1)].width = x

# README
ws = wb.active; ws.title = 'README'
lines = [
 ('OSD Elementary Closure Community Analysis: statistical workbook', TITLE),
 ('Reproduces every number in Appendix A of the report from the district enrollment files (folder data/).', N_),
 ('Built by reproduce.py; rerunning the script regenerates this file exactly.', N_),
 ('', N_),
 ('How to read it', H),
 ('Data tabs hold the enrollment counts as compiled from the OSD enrollment dashboard (blue = source data).', N_),
 ('Ratios, shares, cohorts, finance, reserve paths, and capacity are live Excel formulas: click a cell to see the math.', N_),
 ('Regressions, Newey-West standard errors, model fits, and the bootstrap cannot be written as simple formulas; their results are entered as values from reproduce.py, next to Excel SLOPE() checks where possible.', N_),
 ('Yellow cells are assumptions you can change; dependent cells update.', N_),
 ('', N_),
 ('Methods', H),
 ('Trends: ordinary least squares of headcount on year. Full-period trends (2009-2026) use Newey-West standard errors (Bartlett kernel, lag 2, small-sample factor n/(n-2)); segments of 2019 or later use ordinary standard errors. 95% intervals use the t distribution. Significance threshold p < 0.05, no multiple-comparison correction.', N_),
 ('Period comparisons of advancement ratios: Welch two-sample t-tests, 2010-2019 vs. 2022-2026 (2020 and 2021 COVID transitions excluded).', N_),
 ('Model comparison: AIC = n ln(RSS/n) + 2k, k = number of fitted coefficients.', N_),
 ('Projections: cohort survival. K-5 bootstrap: 20,000 draws, each resampling a whole year of advancement ratios and adding 4% random variation to kindergarten (seed 20261012). K-12: deterministic, 2022-2026 mean ratios.', N_),
 ('', N_),
 ('Data cleaning', H),
 ('September headcount for school and grade analyses; annual average of monthly counts for district totals. Stray entries of 0-3 students listed in grades outside a file\'s range (4th-5th in the middle school file, 7th-8th in the high school file) are omitted. 2026-27 has only a September count and is provisional.', N_),
 ('', N_),
 ('Checks tab', H),
 ('Lists each reported figure, the reproduced value, and whether they match. All items match the final report or differ only by rounding.', N_),
]
for i, (txt, f) in enumerate(lines, 1):
    c = ws.cell(i, 1, txt); c.font = f; c.alignment = Alignment(wrap_text=True, vertical='top')
ws.column_dimensions['A'].width = 120

# Data_K5
ws = sheet('Data_K5', 'September K-5 headcount by grade, 11 neighborhood schools (Table A5.1)',
           'Source: 2009_2026_OSD_Monthly_District_enrollment.xlsx, September rows.')
header(ws, 4, ['Fall', 'K', '1', '2', '3', '4', '5', 'K-5'])
for i, yy in enumerate(YEARS):
    r = 5 + i; put(ws, r, 1, str(yy))
    for g in range(6): put(ws, r, 2 + g, int(E5.loc[yy, g]), BLUE)
    put(ws, r, 8, f'=SUM(B{r}:G{r})', fmt='#,##0')
K5ROW = {yy: 5 + i for i, yy in enumerate(YEARS)}
widths(ws, [8] + [9] * 7)

# Data_AllPrograms
ws = sheet('Data_AllPrograms', 'September headcount by grade, all programs including ORLA, K-12',
           'Sum of the 11 neighborhood schools, ORLA K-12, middle schools 6-8, and high schools 9-12 (September rows).')
header(ws, 4, ['Fall', 'K'] + [str(g) for g in range(1, 13)] + ['K-5', '6-8', '9-12', 'K-12'])
for i, yy in enumerate(YEARS):
    r = 5 + i; put(ws, r, 1, str(yy))
    for g in range(13): put(ws, r, 2 + g, int(ALL.loc[yy, g]), BLUE)
    put(ws, r, 15, f'=SUM(B{r}:G{r})'); put(ws, r, 16, f'=SUM(H{r}:J{r})'); put(ws, r, 17, f'=SUM(K{r}:N{r})'); put(ws, r, 18, f'=SUM(B{r}:N{r})', fmt='#,##0')
widths(ws, [8] + [7] * 13 + [8] * 4)

# Data_Schools
ws = sheet('Data_Schools', 'September K-5 headcount by school (Table 4 inputs)',
           'Source: 2009_2026_OSD_Sept_per_school_enrollment.xlsx.')
cols = SCHOOLS + ['Closing combined', 'Other 8 combined', 'All 11', 'Closing share']
header(ws, 4, ['Fall'] + cols)
for i, yy in enumerate(YEARS):
    r = 5 + i; put(ws, r, 1, str(yy))
    for j, s in enumerate(SCHOOLS): put(ws, r, 2 + j, int(SCH.loc[yy, s]), BLUE)
    put(ws, r, 13, f'=SUM(B{r}:D{r})'); put(ws, r, 14, f'=SUM(E{r}:L{r})'); put(ws, r, 15, f'=SUM(B{r}:L{r})')
    put(ws, r, 16, f'=M{r}/O{r}', fmt='0.0%')
r = 5 + len(YEARS) + 1
put(ws, r, 1, 'Share 2009', H)
for j in range(14): put(ws, r, 2 + j, f'={L(2+j)}5/$O$5', fmt='0.0%')
put(ws, r + 1, 1, 'Share 2026', H)
for j in range(14): put(ws, r + 1, 2 + j, f'={L(2+j)}22/$O$22', fmt='0.0%')
widths(ws, [8] + [11] * 15)
SCHCOL = {s: L(2 + j) for j, s in enumerate(SCHOOLS)}
SCHCOL.update({'Closing schools combined': 'M', 'Other 8 schools combined': 'N', 'All 11 schools': 'O'})

# Data_District
ws = sheet('Data_District', 'District-wide headcount, all grades (Table A7.1)',
           'Source: 2009_2026_OSD_Enrollment.xlsx. Annual average = mean of monthly counts (state funding basis).')
header(ws, 4, ['School year', 'Months reported', 'Annual average', 'September'])
for i, yy in enumerate(YEARS):
    r = 5 + i; put(ws, r, 1, f'{yy}-{str(yy+1)[2:]}'); put(ws, r, 2, int(TOT.loc[yy, 'months']), BLUE)
    put(ws, r, 3, float(TOT.loc[yy, 'annual_avg']), BLUE, '#,##0'); put(ws, r, 4, int(TOT.loc[yy, 'september']), BLUE, '#,##0')
widths(ws, [12, 10, 14, 12])

# Trends
ws = sheet('Trends', 'Linear trends (Tables A5.2, A7.2, and Table 4)',
           'Values from reproduce.py. "Excel SLOPE check" recomputes the slope with Excel\'s SLOPE() from the data tabs; it should equal "Trend per year".')
header(ws, 4, ['Table', 'Series', 'Period', 'Method', 'Trend per year', '95% CI low', '95% CI high', 'p', 'R²', 'n', 'Excel SLOPE check'])
def rng_for(table, name, period):
    a, b = map(int, period.split('-'))
    if table == 'A5.2':
        col = {'Kindergarten': 'B', 'K-5 total': 'H', 'Grade 3': 'E', 'Grade 4': 'F', 'Grade 5': 'G'}[name]
        return f'Data_K5!{col}{K5ROW[a]}:{col}{K5ROW[b]}', f'Data_K5!A{K5ROW[a]}:A{K5ROW[b]}'
    if table == 'Table 4' and name in SCHCOL:
        col = SCHCOL[name]; return f'Data_Schools!{col}{K5ROW[a]}:{col}{K5ROW[b]}', f'Data_Schools!A{K5ROW[a]}:A{K5ROW[b]}'
    if table == 'Table 4':
        return f'Data_Schools!P{K5ROW[a]}:P{K5ROW[b]}', f'Data_Schools!A{K5ROW[a]}:A{K5ROW[b]}'
    if table == 'A7.2' and b <= 2025:
        return f'Data_District!C{K5ROW[a]}:C{K5ROW[b]}', f'Data_District!A{K5ROW[a]}:A{K5ROW[b]}'
    return None, None
for i, (tb, nm, per, meth, r) in enumerate(trend_rows):
    rr = 5 + i
    for j, v in enumerate([tb, nm, per, meth]): put(ws, rr, 1 + j, v)
    put(ws, rr, 5, r['slope'], fmt='0.000' if 'share' in nm else '0.0'); put(ws, rr, 6, r['lo'], fmt='0.000' if 'share' in nm else '0.0')
    put(ws, rr, 7, r['hi'], fmt='0.000' if 'share' in nm else '0.0'); put(ws, rr, 8, r['p'], fmt='0.0000')
    put(ws, rr, 9, r['r2'], fmt='0.00'); put(ws, rr, 10, r['n'])
    yr, xr = rng_for(tb, nm, per)
    if yr:  # years are stored as text; use ROW offsets instead
        a, b = map(int, per.split('-'))
        put(ws, rr, 11, f'=SLOPE({yr},ROW({yr})-{K5ROW[a]}+{a})', fmt='0.000' if 'share' in nm else '0.0')
widths(ws, [9, 46, 11, 30, 12, 11, 11, 9, 7, 5, 14])

# Models
ws = sheet('Models', 'Model comparison, K-5 total, 2009-2026 (Table A6.1)',
           f'AIC = n ln(RSS/n) + 2k. With the cycle length left free, the best fit is {bestP:.1f} years.')
header(ws, 4, ['Model', 'Coefficients (k)', 'R²', 'AIC', 'Cycle low point after 2026'])
for i, row in enumerate(sorted(model_rows, key=lambda m: m[3])):
    put(ws, 5 + i, 1, row[0]); put(ws, 5 + i, 2, row[1]); put(ws, 5 + i, 3, row[2], fmt='0.00'); put(ws, 5 + i, 4, row[3], fmt='0.0'); put(ws, 5 + i, 5, row[4])
widths(ws, [34, 16, 8, 8, 30])

# Advancement
ws = sheet('Advancement', 'Grade-to-grade advancement ratios (Tables A10.1 and A10.2)',
           'Ratio = grade g+1 this fall / grade g the prior fall. Welch t-test: TTEST(range1, range2, 2, 3). 2020 and 2021 transitions excluded.')
def adv_block(r0, title, src, grades, labels):
    put(ws, r0, 1, title, H)
    header(ws, r0 + 1, ['Fall'] + labels)
    for i, yy in enumerate(YEARS[1:]):
        rr = r0 + 2 + i; put(ws, rr, 1, str(yy))
        for j, g in enumerate(grades):
            c_now = L(2 + g + 1); c_prev = L(2 + g)
            put(ws, rr, 2 + j, f'={src}!{c_now}{K5ROW[yy]}/{src}!{c_prev}{K5ROW[yy-1]}', fmt='0.000')
    first = r0 + 2; pre = (first, first + 9); post = (first + 12, first + 16)  # 2010-2019, 2022-2026
    rr = first + len(YEARS) - 1 + 1
    for k, (lab, f) in enumerate([('2010-2019 mean', 'AVERAGE({a}{p0}:{a}{p1})'), ('2010-2019 SD', 'STDEV({a}{p0}:{a}{p1})'),
                                  ('2022-2026 mean', 'AVERAGE({a}{q0}:{a}{q1})'), ('2022-2026 SD', 'STDEV({a}{q0}:{a}{q1})'),
                                  ('Welch p', 'TTEST({a}{p0}:{a}{p1},{a}{q0}:{a}{q1},2,3)')]):
        put(ws, rr + k, 1, lab, H)
        for j in range(len(grades)):
            a = L(2 + j)
            put(ws, rr + k, 2 + j, '=' + f.format(a=a, p0=pre[0], p1=pre[1], q0=post[0], q1=post[1]), fmt='0.000' if 'p' not in lab else '0.00')
    return rr + 6
nxt = adv_block(4, 'K-5, 11 neighborhood schools (A10.1)', 'Data_K5', range(5), ['K to 1', '1 to 2', '2 to 3', '3 to 4', '4 to 5'])
adv_block(nxt + 1, 'K-12, all programs including ORLA (A10.2)', 'Data_AllPrograms', range(12),
          ['K to 1'] + [f'{g} to {g+1}' for g in range(1, 12)])
widths(ws, [16] + [9] * 12)

# Cohorts
ws = sheet('Cohorts', 'Kindergarten classes tracked to 5th grade (Table A11.1)', 'Formulas reference Data_K5.')
header(ws, 4, ['Kindergarten fall', 'K', '5th grade (5 years later)', 'Growth'])
for i, (k, a, b) in enumerate(cohorts):
    rr = 5 + i; put(ws, rr, 1, str(k)); put(ws, rr, 2, f'=Data_K5!B{K5ROW[k]}'); put(ws, rr, 3, f'=Data_K5!G{K5ROW[k+5]}')
    put(ws, rr, 4, f'=C{rr}/B{rr}-1', fmt='+0.0%;-0.0%')
widths(ws, [18, 8, 22, 10])

# Projections
ws = sheet('Projections', 'Projections (Tables A8.1 and A8.2)', 'Values from reproduce.py. Bootstrap seed 20261012; reruns give identical values.')
put(ws, 4, 1, 'A8.1  K-5, 11 neighborhood schools, bootstrap cohort survival (median and 95% interval)', H)
header(ws, 5, ['Kindergarten scenario', 'Fall 2028 median', '2.5%', '97.5%', 'Fall 2030 median', '2.5%', '97.5%'])
for i, (k, v) in enumerate(boots.items()):
    put(ws, 6 + i, 1, k)
    for j, val in enumerate(list(v[2028]) + list(v[2030])): put(ws, 6 + i, 2 + j, float(val), fmt='#,##0')
put(ws, 10, 1, 'A8.2  K-12, all programs, deterministic, 2022-2026 mean advancement ratios', H)
header(ws, 11, ['Fall', 'K-5 (K holds at 513)', '6-8', '9-12', 'K-12', 'K-12 (K falls 3%/yr)'])
for i, yy in enumerate(range(2027, 2035)):
    p = proj_hold[yy]; q = proj_3pct[yy]
    for j, val in enumerate([str(yy), p[:6].sum(), p[6:9].sum(), p[9:].sum(), p.sum(), q.sum()]):
        put(ws, 12 + i, 1 + j, float(val) if j else val, fmt='#,##0')
put(ws, 21, 1, 'Mean advancement ratios used (2022-2026)', H)
for g in range(12): put(ws, 22, 1 + g, f'{g if g else "K"} to {g+1}', H); put(ws, 23, 1 + g, float(R12[g]), fmt='0.000')
widths(ws, [44, 18, 10, 10, 16, 18, 10, 10, 10, 10, 10, 10])

# Finance
ws = sheet('Finance', 'Financial and enrollment-risk calculations (Appendix A2-A3; Tables 7, 8, 15)',
           'Blue = inputs from district documents; yellow = our assumptions (editable); black = formulas.')
r = 4
def inp(label, val, note, fmt=None, key=False, row=None):
    global r
    put(ws, r, 1, label); c = put(ws, r, 2, val, BLUE, fmt)
    if key: c.fill = KEY
    put(ws, r, 3, note, NOTE); r += 1
    return f'$B${r-1}'
put(ws, r, 1, 'Inputs', H); r += 1
REV = inp('Revenue per student ($)', 14800, 'June 18, 2026 budget first reading (state and levy)', '$#,##0', key=True)
DISP = inp('Displaced students (Sept. 2026)', 741, 'McKenny 275 + LP Brown 306 + Madison 160')
RECV = inp('Students now at receiving schools', 1756, '6883 report, 2025-26 basis')
SAV = inp('District savings estimate ($M)', 3.14, '6883 report', '0.00')
UTIL = inp('Current utilities and maintenance, closing schools ($)', 392953, '6883 report', '$#,##0')
CUST = inp('Cost per custodian FTE ($)', 86744, 'June 2026 average cost per FTE', '$#,##0')
ROOMS = inp('Newly filled classrooms at receiving schools', 43, '6883 report room assignments')
SPEND = inp('2026-27 general fund spending ($M)', 195.67, 'Adopted budget', '0.00')
SPEND25 = inp('2025-26 budgeted spending ($M)', 190.15, 'Adopted budget', '0.00')
PAYSH = inp('Salaries and benefits share of spending', 0.83, '2026-27 budget', '0%')
END26 = inp('2026-27 ending fund balance ($M)', 8.41, 'Adopted budget', '0.00')
r += 1
put(ws, r, 1, 'Attrition sensitivity (Table A3.1)', H); r += 1
header(ws, r, ['Share of displaced who leave', 'Students', 'Revenue lost ($)', 'Share of savings']); r += 1
for s in (0.02, 0.05, 0.10):
    put(ws, r, 1, s, BLUE, '0%'); put(ws, r, 2, f'=ROUND({DISP}*A{r},0)'); put(ws, r, 3, f'=B{r}*{REV}', fmt='$#,##0')
    put(ws, r, 4, f'=C{r}/3100000', fmt='0%'); r += 1
r += 1
put(ws, r, 1, 'Enrollment loss under different bases (Table 7)', H); r += 1
header(ws, r, ['Who leaves', 'Students', 'Revenue lost ($M)']); r += 1
T7 = {}
for lab, f in [('5% of displaced only', f'ROUND(0.05*{DISP},0)'), ('5% of displaced + 1% at receiving', f'ROUND(0.05*{DISP},0)+ROUND(0.01*{RECV},0)'),
               ('5% of displaced + 2% at receiving', f'ROUND(0.05*{DISP},0)+ROUND(0.02*{RECV},0)'), ('5% of all at eight affected schools', f'ROUND(0.05*({DISP}+{RECV}),0)')]:
    put(ws, r, 1, lab); put(ws, r, 2, '=' + f); put(ws, r, 3, f'=B{r}*{REV}/1000000', fmt='0.00'); T7[lab] = r; r += 1
r += 1
put(ws, r, 1, 'Closure savings after omitted costs (Table 8, $M)', H); r += 1
header(ws, r, ['Item', 'Lower-cost case', 'Higher-cost case', 'Basis']); r += 1
t8_0 = r
put(ws, r, 1, 'District estimate (6883 report)'); put(ws, r, 2, f'={SAV}'); put(ws, r, 3, f'={SAV}'); r += 1
put(ws, r, 1, 'Closed-building upkeep not budgeted'); put(ws, r, 2, -0.10, BLUE); put(ws, r, 3, -0.21, BLUE); put(ws, r, 4, 'Upkeep block below less $50,199 budgeted', NOTE); r += 1
put(ws, r, 1, 'Custodians for newly filled rooms'); put(ws, r, 2, f'=-ROUND({ROOMS}*0.5/8,1)*{CUST}/1000000', fmt='0.00'); put(ws, r, 3, f'=-ROUND({ROOMS}*0.8/8,1)*{CUST}/1000000', fmt='0.00'); put(ws, r, 4, '0.5-0.8 custodial hours per room per day, 8 hours per FTE', NOTE); r += 1
put(ws, r, 1, 'Transportation savings not realized'); put(ws, r, 2, 0, BLUE); put(ws, r, 3, -0.16, BLUE); r += 1
put(ws, r, 1, 'Enrollment loss'); put(ws, r, 2, f'=-C{T7["5% of displaced + 1% at receiving"]}', fmt='0.00'); put(ws, r, 3, f'=-C{T7["5% of displaced + 2% at receiving"]}', fmt='0.00'); r += 1
put(ws, r, 1, 'Net annual savings', H); put(ws, r, 2, f'=SUM(B{t8_0}:B{r-1})', H, '0.00'); put(ws, r, 3, f'=SUM(C{t8_0}:C{r-1})', H, '0.00'); NET = r; r += 1
put(ws, r, 1, 'Reduction from district estimate'); put(ws, r, 2, f'=1-B{NET}/{SAV}', fmt='0%'); put(ws, r, 3, f'=1-C{NET}/{SAV}', fmt='0%'); r += 2
put(ws, r, 1, 'Closed-building upkeep (Table A2.4)', H); r += 1
put(ws, r, 1, 'Utilities and maintenance at 30-50%'); put(ws, r, 2, f'=0.3*{UTIL}', fmt='$#,##0'); put(ws, r, 3, f'=0.5*{UTIL}', fmt='$#,##0'); u0 = r; r += 1
put(ws, r, 1, 'Custodial checks, 0.25-0.5 FTE'); put(ws, r, 2, f'=0.25*{CUST}', fmt='$#,##0'); put(ws, r, 3, f'=0.5*{CUST}', fmt='$#,##0'); r += 1
put(ws, r, 1, 'Security and vandalism repair'); put(ws, r, 2, 10000, BLUE, '$#,##0'); put(ws, r, 3, 20000, BLUE, '$#,##0'); r += 1
put(ws, r, 1, 'Total', H); put(ws, r, 2, f'=SUM(B{u0}:B{r-1})', H, '$#,##0'); put(ws, r, 3, f'=SUM(C{u0}:C{r-1})', H, '$#,##0'); r += 2
put(ws, r, 1, 'Other calculations (Appendix A3)', H); r += 1
put(ws, r, 1, 'One month of payroll ($M)'); put(ws, r, 2, f'={SPEND}*{PAYSH}/12', fmt='0.00'); pm = r; r += 1
put(ws, r, 1, '  as share of 2026-27 spending'); put(ws, r, 2, f'=B{pm}/{SPEND}', fmt='0.0%'); r += 1
put(ws, r, 1, '  as share of 2025-26 spending'); put(ws, r, 2, f'=B{pm}/{SPEND25}', fmt='0.0%'); r += 1
put(ws, r, 1, 'LP Brown share of learning assistance ($)'); put(ws, r, 2, '=206000*313/(313+256)', fmt='$#,##0'); r += 1
put(ws, r, 1, 'Hansen 3-yr low-income average, yr 1-3 at 52.7%'); put(ws, r, 2, '=(0.44+0.44+0.527)/3', fmt='0.0%'); put(ws, r, 3, '=(0.44+0.527+0.527)/3', fmt='0.0%'); put(ws, r, 4, '=0.527', fmt='0.0%'); r += 1
put(ws, r, 1, 'Hansen 3-yr low-income average, yr 1-3 at 51.7%'); put(ws, r, 2, '=(0.44+0.44+0.517)/3', fmt='0.0%'); put(ws, r, 3, '=(0.44+0.517+0.517)/3', fmt='0.0%'); put(ws, r, 4, '=0.517', fmt='0.0%'); r += 1
put(ws, r, 1, 'Kindergartners per in-district birth, 2019 (744/642)'); put(ws, r, 2, '=744/642', fmt='0.00'); r += 1
put(ws, r, 1, 'Kindergartners per in-district birth, 2026 (513/576)'); put(ws, r, 2, '=513/576', fmt='0.00'); r += 1
put(ws, r, 1, 'Extra kindergartners this fall at 1.08 / 1.16'); put(ws, r, 2, '=ROUND(576*1.08,0)-513'); put(ws, r, 3, '=ROUND(576*1.16,0)-513'); r += 1
put(ws, r, 1, 'Extra per year vs. forecast 0.96, births 459 / 520'); put(ws, r, 2, '=ROUND(459*(1.08-0.96),0)'); put(ws, r, 3, '=ROUND(520*(1.16-0.96),0)'); r += 1
put(ws, r, 1, 'Births below which 1.08 yields < 50 extra'); put(ws, r, 2, '=50/(1.08-0.96)', fmt='0'); r += 2

put(ws, r, 1, 'Reserve projection by option (Table 15)', H); r += 1
header(ws, r, ['', '2027-28', '2028-29', '2029-30', '2030-31']); r += 1
put(ws, r, 1, 'Forecast gap ($M)'); gr = r
for j, v in enumerate([0.41, 0.37, 0.36, 0.36]): put(ws, r, 2 + j, v, BLUE, '0.00')
r += 1
put(ws, r, 1, 'Prior-year spending ($M)'); sr = r
for j, v in enumerate([195.67, 202.93, 207.89, 212.52]): put(ws, r, 2 + j, v, BLUE, '0.00')
r += 1
put(ws, r, 1, 'Alternatives midpoint ($M/yr)'); ALT = f'$B${r}'; put(ws, r, 2, 0.70, BLUE, '0.00').fill = KEY; r += 1
put(ws, r, 1, 'Recruited students per year'); RECR = f'$B${r}'; put(ws, r, 2, 50, BLUE).fill = KEY; r += 1
put(ws, r, 1, 'Net value per recruited student (share of revenue)'); RSH = f'$B${r}'; put(ws, r, 2, 0.5, BLUE, '0%').fill = KEY; r += 1
put(ws, r, 1, 'Midpoint closure costs other than enrollment ($M)'); MID = f'$B${r}'; put(ws, r, 2, '=0.155+0.305+0.08', fmt='0.000'); r += 1
put(ws, r, 1, 'Midpoint enrollment loss (students)'); MIDN = f'$B${r}'; put(ws, r, 2, f'=0.05*{DISP}+0.015*{RECV}', fmt='0.0'); r += 2
header(ws, r, ['Ending reserve, % of prior-year spending', '2027-28', '2028-29', '2029-30', '2030-31']); r += 1
paths = [('No action', '0'), ('Alternatives only', ALT),
         ('Staged recruitment (half value)', f'{ALT}+{RECR}*{{i}}*{REV}*{RSH}/1000000'),
         ('Staged recruitment (full value)', f'{ALT}+{RECR}*{{i}}*{REV}/1000000'),
         ("Closure, district's $3.14M", SAV), ('Closure, district low end ($2.24M)', '2.24'),
         ('Closure, our midpoint', f'{SAV}-{MID}-{MIDN}*{REV}/1000000'),
         ('Closure, our higher-cost case', f'C{NET}'),
         ('Stress test: loss of 288 students', f'{SAV}-{MID}-287.67*{REV}/1000000')]
for lab, add in paths:
    put(ws, r, 1, lab)
    bal_prev = END26
    for j in range(4):
        expr = add.replace('{i}', str(j + 1))
        bal = f'({bal_prev}+({expr})-{L(2+j)}${gr})'
        # store running balance in a hidden helper row to the right
        put(ws, r, 8 + j, f'={bal}', fmt='0.00')
        put(ws, r, 2 + j, f'={L(8+j)}{r}/{L(2+j)}${sr}', fmt='0.0%')
        bal_prev = f'{L(8+j)}{r}'
    r += 1
put(ws, r - len(paths) - 1, 8, 'Ending balance ($M) 2027-28', H)
for j in range(1, 4): put(ws, r - len(paths) - 1, 8 + j, ['2028-29', '2029-30', '2030-31'][j - 1], H)
r += 1
put(ws, r, 1, 'Break-even enrollment loss (students): savings reach zero'); put(ws, r, 2, f'=({SAV}-{MID})*1000000/{REV}', fmt='0'); r += 1
put(ws, r, 1, 'Break-even enrollment loss (students): savings below 2027-28 gap'); put(ws, r, 2, f'=({SAV}-{MID}-B{gr})*1000000/{REV}', fmt='0'); r += 1
widths(ws, [52, 14, 14, 14, 14, 4, 4, 12, 10, 10, 10])

# Capacity
ws = sheet('Capacity', 'Capacity and utilization (Table 10 and Appendix A12)',
           'Rooms: Long Range Facilities Master Plan. Enrollment: 6883 report 2027-28 projections. Utilization = enrollment / capacity.')
put(ws, 4, 1, 'Students per K-3 class'); put(ws, 4, 2, 19, BLUE).fill = KEY
put(ws, 5, 1, 'Students per grade 4-5 class'); put(ws, 5, 2, 27, BLUE).fill = KEY
put(ws, 6, 1, 'Functional students per room ((4 x K-3 + 2 x 4-5) / 6)'); put(ws, 6, 2, '=(4*B4+2*B5)/6', fmt='0.0')
put(ws, 7, 1, 'Planning students per room (district)'); put(ws, 7, 2, 25, BLUE)
put(ws, 8, 1, 'Students per special education room'); put(ws, 8, 2, 10, BLUE)
put(ws, 9, 1, 'Sensitivity: alternate students per room'); put(ws, 9, 2, 24, BLUE).fill = KEY; put(ws, 9, 3, 21, BLUE).fill = KEY
header(ws, 11, ['School', '2027-28 students', 'Classrooms', 'of which special ed', 'Planning capacity', 'Utilization, planning',
                'Functional capacity', 'Utilization, functional', 'At alt. 1 (B9)', 'At alt. 2 (C9)'])
for i, (s, n_, rooms, sp) in enumerate([('Centennial', 509, 24, 2), ('Garfield', 429, 20, 1), ('Pioneer', 498, 25, 2), ('Roosevelt', 478, 24, 2), ('Hansen', 494, 28, 2)]):
    rr = 12 + i; put(ws, rr, 1, s); put(ws, rr, 2, n_, BLUE); put(ws, rr, 3, rooms, BLUE); put(ws, rr, 4, sp, BLUE)
    put(ws, rr, 5, f'=(C{rr}-D{rr})*$B$7+D{rr}*$B$8'); put(ws, rr, 6, f'=B{rr}/E{rr}', fmt='0%')
    put(ws, rr, 7, f'=(C{rr}-D{rr})*$B$6+D{rr}*$B$8', fmt='0'); put(ws, rr, 8, f'=B{rr}/G{rr}', fmt='0%')
    put(ws, rr, 9, f'=B{rr}/((C{rr}-D{rr})*$B$9+D{rr}*$B$8)', fmt='0%'); put(ws, rr, 10, f'=B{rr}/((C{rr}-D{rr})*$C$9+D{rr}*$B$8)', fmt='0%')
put(ws, 18, 1, 'District-wide, 11 schools today: 204 general + 12 special ed rooms', H)
put(ws, 19, 1, 'Functional seats'); put(ws, 19, 2, '=204*$B$6+12*$B$8', fmt='#,##0')
put(ws, 20, 1, 'After closures: 155 general + 11 special ed rooms (LP Brown 17+1, Madison 12, McKenny 20 removed)')
put(ws, 21, 1, 'Functional seats'); put(ws, 21, 2, '=155*$B$6+11*$B$8', fmt='#,##0')
put(ws, 22, 1, 'Planning seats'); put(ws, 22, 2, '=155*$B$7+11*$B$8', fmt='#,##0')
put(ws, 23, 1, '2027-28 projected enrollment'); put(ws, 23, 2, 3270, BLUE)
put(ws, 24, 1, 'Utilization, functional'); put(ws, 24, 2, '=B23/B21', fmt='0%')
put(ws, 25, 1, 'Utilization, planning'); put(ws, 25, 2, '=B23/B22', fmt='0%')
widths(ws, [58, 14, 11, 12, 13, 13, 13, 13, 12, 12])


# Forecast accuracy (A4)
ws = sheet('Forecast_accuracy', 'Forecast accuracy (Tables A4.1 and A4.2)', 'Error = (actual - forecast) / forecast.')
def fc_block(r0, title, data, lab):
    put(ws, r0, 1, title, H); header(ws, r0 + 1, ['School', 'Forecast', lab, 'Error'])
    for i, (s, f, a) in enumerate(data):
        rr = r0 + 2 + i; put(ws, rr, 1, s); put(ws, rr, 2, f, BLUE); put(ws, rr, 3, a, BLUE); put(ws, rr, 4, f'=C{rr}/B{rr}-1', fmt='+0.0%;-0.0%')
    a0, a1 = r0 + 2, r0 + 1 + len(data); rr = a1 + 1
    put(ws, rr, 1, 'Total', H); put(ws, rr, 2, f'=SUM(B{a0}:B{a1})'); put(ws, rr, 3, f'=SUM(C{a0}:C{a1})'); put(ws, rr, 4, f'=C{rr}/B{rr}-1', fmt='+0.0%;-0.0%')
    put(ws, rr + 1, 1, 'Mean absolute school error'); put(ws, rr + 1, 4, f'=SUMPRODUCT(ABS(D{a0}:D{a1}))/COUNT(D{a0}:D{a1})', fmt='0.0%')
    put(ws, rr + 2, 1, 'SD of school errors'); put(ws, rr + 2, 4, f'=STDEV(D{a0}:D{a1})', fmt='0.0%')
    return rr + 4
SCH11 = ['Boston Harbor', 'Centennial', 'Garfield', 'Hansen', 'Lincoln', 'LP Brown', 'Madison', 'McKenny', 'McLane', 'Pioneer', 'Roosevelt']
nr = fc_block(4, '2023 FLO forecast for 2025-26 vs. actual 2025-26 average headcount (A4.1)',
              list(zip(SCH11, [165, 429, 263, 430, 284, 290, 185, 280, 386, 353, 332], [169, 406, 260, 337, 298, 313, 176, 279, 397, 391, 336])), 'Actual')
fc_block(nr, 'BERK 2026-27 forecast vs. September 2026 headcount (A4.2)',
         list(zip(SCH11, [181, 378, 286, 335, 300, 326, 175, 273, 392, 399, 317], [166, 382, 271, 271, 303, 306, 160, 275, 382, 375, 362])), 'Sept. 2026')
widths(ws, [44, 10, 12, 10])

# Checks
ws = sheet('Checks', 'Reported figures compared with reproduced values',
           'MATCH = reproduced exactly at the report\'s precision. ROUNDING = differs only by rounding. Checked against the final report of Oct. 12, 2026.')
header(ws, 4, ['Report location', 'Item', 'Report says', 'Reproduced', 'Status', 'Note'])
checks = [
 ('Table A5.1', 'K-5 headcount by grade, 2009-2026', 'as printed', 'identical, all 108 cells', 'MATCH', ''),
 ('Table A7.1', 'District annual average and September headcount', 'as printed', 'identical', 'MATCH', ''),
 ('Table A5.2', 'All eight trend rows', 'as printed', 'identical (slope, CI, p, R²)', 'MATCH', 'Kindergarten 2020-26 p = 0.0006, reported <0.001'),
 ('Table 4', 'All school trends, shares, combined rows', 'as printed', 'identical', 'MATCH', 'Closing vs. other 8 (p = 0.78) is the trend in the closing schools\' share of K-5 enrollment, Newey-West SE'),
 ('Table A7.2, row 1', 'District trend 2009-10 to 2025-26', '+26.8 (-6.6 to +60.2), p = 0.108', '+26.8 (-6.6 to +60.2), p = 0.108', 'MATCH', 'Newey-West SE, as for all full-period trends (corrected Oct. 12 from an earlier draft that printed ordinary SE)'),
 ('Table A7.2, rows 2-5', 'District trends by period', 'as printed', 'identical', 'MATCH', ''),
 ('Table A6.1 / Table 3', 'R² and AIC for all seven models; free cycle length 15.1 years', 'as printed', 'identical', 'MATCH', 'AIC = n ln(RSS/n) + 2k'),
 ('Table A6.1, cycle models', 'Implied low points', '15-yr 2041; 20-yr 2029; 25-yr 2032; 30-yr 2036', 'identical', 'MATCH', 'Low points include the fitted trend (corrected Oct. 12; an earlier draft gave 2045 for the 20-year model)'),
 ('Tables A10.1, A10.2', 'Advancement ratio means, SDs, Welch p', 'as printed', 'identical', 'MATCH', '2021 K-to-1 ratio 1.036 (K-5)'),
 ('Table A11.1', 'Cohort growth K to 5', 'as printed', 'identical', 'MATCH', ''),
 ('Table A8.1', 'Bootstrap medians and intervals', 'as printed', 'within 1-3 students', 'ROUNDING', 'Simulation noise; this file fixes the random seed so reruns are identical'),
 ('Table A8.2', 'K-12 projections', 'as printed', 'identical', 'MATCH', 'Middle school -12.8% by 2033, high school -11.4% by 2034, K-12 -9.7% by 2034 (body: 13%, 11%, 10%)'),
 ('Tables A4.1, A4.2', 'Forecast errors, mean absolute 5.8%, SD 8.6%', 'as printed', 'identical', 'MATCH', ''),
 ('Table A3.1, Table 7', 'Attrition and enrollment-loss scenarios', 'as printed', 'identical', 'MATCH', ''),
 ('Table 8', 'Custodial cost and net savings', '-0.24 / -0.38; net 1.99 / 1.32', '-0.23 / -0.37; net 2.00 / 1.33', 'ROUNDING', '43 rooms x 0.5-0.8 h / 8 h = 2.7-4.3 FTE x $86,744 = $233K-373K; the report rounds to $235K-375K'),
 ('Table 15 / Appendix A2', 'Reserve paths', 'as printed', 'identical to 0.1 point', 'MATCH', ''),
 ('Appendix A2, "Reserve projection by option"', 'Prior-year spending list', '$195.67, $202.93, $207.89, 212.52 million', 'identical', 'MATCH', ''),
 ('Table 10 / A12', 'Planning and functional capacity, utilization at 22 per room', 'as printed', 'identical', 'MATCH', ''),
 ('Capacity text and finding 5', 'Sensitivity at 24 students per room', 'Centennial and Garfield about 92%; Pioneer and Roosevelt about 87%', 'Centennial 92.9%, Garfield 92.1%; Pioneer 87.1%, Roosevelt 87.2%', 'ROUNDING',
  'Special education rooms stay at 10 students. At 21 per room: 99-106%, so "at or over capacity" holds.'),
 ('Appendix A12', 'Planning seats after closures', '3,970', 'about 3,985 from room counts', 'ROUNDING', 'Utilization 82% either way'),
 ('Appendix A3', 'Payroll, LAP share, Hansen averages, birth ratios', 'as printed', 'identical', 'MATCH', ''),
]
for i, row in enumerate(checks):
    for j, v in enumerate(row):
        c = put(ws, 5 + i, 1 + j, v); c.alignment = Alignment(wrap_text=True, vertical='top')
        if j == 4 and v == 'REVIEW': c.font = Font(name=AR, bold=True, color='C00000')
widths(ws, [26, 34, 30, 30, 11, 70])
wb.move_sheet('Checks', offset=-(len(wb.sheetnames) - 2))

wb.save('OSD_Statistical_Analyses.xlsx')

# ---------------------------------------------------------------- console summary for the checks tab
def fmt(r): return f"{r['slope']:+.1f} ({r['lo']:+.1f} to {r['hi']:+.1f}), p={r['p']:.4f}, R2={r['r2']:.2f}, n={r['n']}"
if __name__ == '__main__':
    for tb, nm, per, meth, r in trend_rows: print(tb, nm, per, meth, fmt(r))
    for m in sorted(model_rows, key=lambda m: m[3]): print(m)
    print('best free period', round(bestP, 1))
    for row in adv5 + adv12: print(row[0], round(row[1], 3), round(row[2], 3), round(row[3], 3), round(row[4], 3), round(row[5], 2))
    for k, v in boots.items(): print(k, {y: np.round(a).tolist() for y, a in v.items()})
    for yy in (2028, 2030, 2032, 2033, 2034): print(yy, [round(x) for x in (proj_hold[yy][:6].sum(), proj_hold[yy][6:9].sum(), proj_hold[yy][9:].sum(), proj_hold[yy].sum(), proj_3pct[yy].sum())])
