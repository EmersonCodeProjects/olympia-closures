"""Load the district enrollment files compiled from the OSD enrollment dashboard."""
import pandas as pd, os
DATA = os.environ.get('OSD_DATA', '../data')
GMAP = {'All Day K': 0, '1ST': 1, '2ND': 2, '3RD': 3, '4TH': 4, '5TH': 5, '6TH': 6, '7TH': 7, '8TH': 8,
        '9TH': 9, '10TH': 10, '11TH': 11, '12TH': 12}

def _fall(s):  # '2026-2027' or '2026 – 2027' -> 2026
    return int(str(s).replace('–', '-').split('-')[0].strip())

def monthly(fname, valid_grades):
    df = pd.read_excel(os.path.join(DATA, fname))
    df = df.rename(columns={'SchoolYear': 'year', 'SchoolYear Month': 'month', 'Grade': 'grade', 'Cur Year (#)': 'n'})
    df['fall'] = df['year'].map(_fall); df['g'] = df['grade'].map(GMAP)
    dropped = df[~df['g'].isin(valid_grades)]
    df = df[df['g'].isin(valid_grades)]
    return df[['fall', 'month', 'g', 'n']], dropped

def september(df):
    s = df[df['month'] == 'September'].pivot_table(index='fall', columns='g', values='n', aggfunc='sum')
    return s.sort_index()

def per_school():
    df = pd.read_excel(os.path.join(DATA, '2009_2026_OSD_Sept_per_school_enrollment.xlsx'))
    df = df.rename(columns={'Year Range': 'year', 'Entity': 'school', 'Grade': 'grade', 'Cur Year (#)': 'n'})
    df['fall'] = df['year'].map(_fall); df['g'] = df['grade'].map(GMAP)
    return df[['fall', 'school', 'g', 'n']]

def district_totals():
    df = pd.read_excel(os.path.join(DATA, '2009_2026_OSD_Enrollment.xlsx'))
    df['Year Range'] = df['Year Range'].ffill()
    df['fall'] = df['Year Range'].map(_fall)
    g = df.groupby('fall')
    out = pd.DataFrame({'months': g['Count'].count(), 'annual_avg': g['Count'].mean(),
                        'september': df[df['Month'] == 'September'].set_index('fall')['Count']})
    return out

def load_all():
    elem, _ = monthly('2009_2026_OSD_Monthly_District_enrollment.xlsx', range(0, 6))
    orla, _ = monthly('2009_2026_OSD_Orla_K_12.xlsx', range(0, 13))
    ms, ms_drop = monthly('2009_2026_OSD_6_8.xlsx', range(6, 9))
    hs, hs_drop = monthly('2009_2026_OSD_9_12.xlsx', range(9, 13))
    E5 = september(elem)                    # 11 neighborhood schools, K-5, September
    ALL = september(elem).add(september(orla), fill_value=0)
    ALL = ALL.add(september(ms), fill_value=0).add(september(hs), fill_value=0)  # all programs, K-12, September
    return dict(elem=elem, orla=orla, ms=ms, hs=hs, E5=E5, ALL=ALL, school=per_school(),
                totals=district_totals(), dropped=pd.concat([ms_drop, hs_drop]))
