"""
Reproduce the figures in "Addendum: The October 22 Enrollment Review and the Community Analysis" (Methods and calculations).

Run:  python addendum_oct22.py        (needs pandas, numpy; uses load.py and ../data)
District figures typed in below come from the OSD Student Enrollment Review (Oct. 22, 2026 board meeting),
the June 18, 2026 four-year budget, and the district's Feb. 26, 2026 OSPI financial health projections.
All results are estimates.
"""
import math
import load

# ---------------------------------------------------------------- headcount vs FTE
d = load.load_all()
sch = d['school']
hc26 = sch[sch.fall == 2026].groupby('school')['n'].sum()
FTE_OCT26 = {'Boston Harbor': 166.0, 'Centennial': 384.5, 'Garfield': 270.0, 'Hansen': 271.7, 'Lincoln': 301.5,
             'LP Brown': 303.8, 'Madison': 162.0, 'McKenny': 277.0, 'McLane': 379.1, 'Pioneer': 376.0, 'Roosevelt': 363.0}
print('Headcount and FTE. Neighborhood schools, FTE (Oct. 2026) minus headcount (Sept. 2026)')
for s, f in FTE_OCT26.items():
    print(f'  {s:14s} FTE {f:7.1f}  headcount {hc26[s]:4d}  difference {f - hc26[s]:+.1f}')
print(f'  total          FTE {sum(FTE_OCT26.values()):7.1f}  headcount {hc26.sum():4d}  difference {sum(FTE_OCT26.values()) - hc26.sum():+.1f}')

def annual_avg(df, lo, hi, fall):
    x = df[(df.g >= lo) & (df.g <= hi) & (df.fall == fall)].groupby('month')['n'].sum()
    return x.mean()
orla_k5 = d['orla'][(d['orla'].g <= 5) & (d['orla'].fall == 2026) & (d['orla'].month == 'September')]['n'].sum()
hs25 = annual_avg(d['hs'], 9, 12, 2025); orla_hs25 = annual_avg(d['orla'], 9, 12, 2025)
print(f'  ORLA K-5 headcount Sept. 2026: {orla_k5} vs district FTE 257.4')
print(f'  High school headcount 2025-26 average incl. ORLA: {hs25 + orla_hs25:.0f} vs district FTE 3,062 '
      f'(comprehensive high schools {hs25:.0f} vs {3062 - 149.2:.0f} FTE; Running Start 438)')
e = d['elem']; s19 = e[(e.fall == 2019) & (e.month == 'September')]['n'].sum(); s26 = e[(e.fall == 2026) & (e.month == 'September')]['n'].sum()
print(f'  Neighborhood K-5 headcount Sept. 2019 to Sept. 2026: {s19} to {s26} ({s26 / s19 - 1:+.1%}); district K-5 FTE 4,341 to 3,512 ({3512 / 4341 - 1:+.1%})')

# ---------------------------------------------------------------- shortfall and valuation
STATE, FULL, HALF = 10_400, 14_800, 7_400
short = 8_790 - 8_726
print(f'\nShortfall and per-student value. Shortfall: {short} FTE x ${STATE:,} to ${FULL:,} = ${short * STATE / 1e6:.2f}M to ${short * FULL / 1e6:.2f}M a year')
print(f'  Gap if it persists: ${0.41 + short * STATE / 1e6:.2f}M to ${0.41 + short * FULL / 1e6:.2f}M')
print(f'  Closure midpoint at state-only value: 1.66 + 63.5 x ({FULL}-{STATE}) = ${1.66 + 63.5 * (FULL - STATE) / 1e6:.2f}M')
print(f'  Students to cover the $0.41M gap: {0.41e6 / HALF:.0f} at half value, {0.41e6 / FULL:.0f} at full value')

# ---------------------------------------------------------------- reserve model
SPEND = {2027: 195.67, 2028: 202.93, 2029: 207.89, 2030: 212.52}   # prior-year spending, $M (denominator)
REV = {2027: 202.52, 2028: 207.52, 2029: 212.16}                   # forecast revenue, $M (score only)
GAP = {2027: 0.41, 2028: 0.37, 2029: 0.36}
YEARS = list(range(2027, 2042))
for y in YEARS:   # beyond the forecast: spending and revenue grow 2.2% a year, gap holds at 2029-30's
    if y not in SPEND: SPEND[y] = SPEND[y - 1] * 1.022
    if y not in REV: REV[y] = REV[y - 1] * 1.022
    GAP.setdefault(y, 0.36)
SHORT = short * STATE / 1e6   # about $0.67M

def path(recruit=0, closure=None, loss=lambda i: 0, shortfall=0.0, start=8.41):
    """Ending balance ($M) and yearly change for each year from 2027-28 (key 2027)."""
    b = start - shortfall; bal, chg = {}, {}
    for i, y in enumerate(YEARS):
        if closure is not None:
            inc = closure - loss(i) * FULL / 1e6
        else:
            inc = recruit * (i + 1) * HALF / 1e6
        inc -= GAP[y] + shortfall
        b += inc; bal[y], chg[y] = b, inc
    return bal, chg

# ---------------------------------------------------------------- fiscal score interpolation
W = dict(fund=0.40, exp=0.35, cash=0.15, plan=0.10)
def band_fund(r): return 0 if r < 0 else 1 if r < 0.02 else 2 if r < 0.06 else 3
def band_exp(r): return 4 if r < 1.00 else 3 if r < 1.02 else 2 if r < 1.04 else 1
def score(bal, chg, y, cash_band=0):
    deficits = sum(1 for k in range(y, y + 4) if chg[k] < 0)
    return (W['fund'] * band_fund(bal[y] / REV[y]) + W['exp'] * band_exp((REV[y] - chg[y]) / REV[y])
            + W['cash'] * cash_band + W['plan'] * {0: 4, 1: 3, 2: 2, 3: 1, 4: 0}[deficits])

CLOSURE_NET_BEFORE_LOSS = 3.14 - 0.155 - 0.305 - 0.08   # district savings less upkeep, custodial, transportation = 2.60
ROWS = [
    ('1. Shortfall persists: recruitment, 50 a year', dict(recruit=50, shortfall=SHORT)),
    ('1. Shortfall persists: closure, midpoint', dict(closure=1.66, shortfall=SHORT)),
    ('2. No action', dict()),
    ('2. Recruitment, 30 a year', dict(recruit=30)),
    ('2. Recruitment, 50 a year', dict(recruit=50)),
    ('2. Closure, our midpoint ($1.66M)', dict(closure=1.66)),
    ('2. Closure, district low end ($2.24M)', dict(closure=2.24)),
    ('2. Closure, 6883 report ($3.14M)', dict(closure=3.14)),
    ('3. Stress: staged loss of 150', dict(closure=CLOSURE_NET_BEFORE_LOSS, loss=lambda i: min(50 * (i + 1), 150))),
    ('3. Stress: staged loss of 288', dict(closure=CLOSURE_NET_BEFORE_LOSS, loss=lambda i: min(96 * (i + 1), 288))),
]
print('\nReserve model and fiscal score. Table 4: reserve % of prior-year spending (estimated score); year reaching 6%')
for label, kw in ROWS:
    bal, chg = path(**kw)
    cells = '  '.join(f'{y}-{(y + 1) % 100:02d}: {100 * bal[y] / SPEND[y]:5.1f}% ({score(bal, chg, y):.2f})' for y in (2027, 2031, 2035))
    six = next((f'{y}-{(y + 1) % 100:02d}' for y in YEARS if bal[y] / SPEND[y] >= 0.06), 'not by 2041')
    print(f'  {label:48s} {cells}   6%: {six}')

# check the interpolation against the district's own scored years (Feb. 26 model)
print('\nFiscal score check: district years, interpolated vs district score')
for yr, fb, er, dfy, dist in [('2023-24', 0.0564, 0.9964, 0, 2.60), ('2024-25', 0.0494, 1.0076, 1, 2.15)]:
    s = W['fund'] * band_fund(fb) + W['exp'] * band_exp(er) + W['plan'] * {0: 4, 1: 3, 2: 2, 3: 1}[dfy]
    print(f'  {yr}: {s:.2f} vs {dist:.2f}')

# ---------------------------------------------------------------- recruitment cost
print('\nRecruitment cost, Table 7 (estimates)')
for name, lo, hi in [('District-backed, existing staff', 35_000, 78_000), ('District-backed, 0.5 FTE lead', 80_000, 153_000),
                     ('Community-led', 10_000, 24_000)]:
    print(f'  {name:32s} ${lo:,}-{hi:,}; pays for itself at {math.ceil(lo / HALF)}-{math.ceil(hi / HALF)} students (half value)')
first_year = 50 * HALF
print(f'  Return from 50 added students: ${first_year:,.0f} a year at half value')
for name, lo, hi in [('Community-led', 10_000, 24_000), ('District-backed, existing staff', 35_000, 78_000)]:
    print(f'  {name:32s} cost is {lo / first_year:.0%}-{hi / first_year:.0%} of the first-year return')
    # subtract the recurring cost each year from 2027-28 through 2031-32 (five years)
    for c in (lo, hi):
        print(f'    recurring ${c:,}: 2031-32 reserve lower by {100 * 5 * c / 1e6 / SPEND[2031]:.2f} points')
