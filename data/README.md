# Enrollment data

Copied from the Olympia School District enrollment dashboard (PowerBI), school years 2009-10 through 2026-27. 2026-27 contains September only and is provisional.

| File | Contents |
|---|---|
| `2009_2026_OSD_Enrollment.xlsx` | District-wide headcount and FTE, all grades, by month |
| `2009_2026_OSD_Monthly_District_enrollment.xlsx` | K-5 headcount by grade and month, 11 neighborhood elementary schools (excludes ORLA) |
| `2009_2026_OSD_Sept_per_school_enrollment.xlsx` | K-5 headcount by school and grade, September |
| `2009_2026_OSD_Orla_K_12.xlsx` | ORLA (Olympia Regional Learning Academy) headcount by grade and month, K-12 |
| `2009_2026_OSD_6_8.xlsx` | Middle school headcount by grade and month, 6-8 |
| `2009_2026_OSD_9_12.xlsx` | High school headcount by grade and month, 9-12 |

Columns: school year, month, grade (or school), current-year count, prior-year count, growth.

Cleaning used in the analysis: a few stray entries of 0-3 students listed in grades outside a file's range (4th-5th grade in the middle school file, 7th-8th grade in the high school file) are omitted. School and grade analyses use September counts; district totals use the annual average of monthly counts.
