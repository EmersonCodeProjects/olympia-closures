# Changelog

## Version 1.2 (October 20, 2026)
- Added an addendum responding to the district's Oct. 22, 2026 Student Enrollment Review (`OSD_Enrollment_Addendum_Oct22.pdf`): headcount and FTE compared school by school, the October enrollment shortfall, the new transfer data, and whether recruitment alone is financially sufficient.
- Added `analysis/addendum_oct22.py`, which reproduces every figure in the addendum's Methods and calculations section.
- Web page: dated notice and download link for the addendum. The report, fact sheet, data, and statistical workbook are unchanged.

## Version 1.1 (October 13, 2026)
- Statistics workbook: replaced a draft copy that still flagged items for review; all checks match the final report or differ only by rounding.
- Added a dependence check for the Welch t-tests on advancement ratios (new Welch_sensitivity tab in the workbook; reproduce.py updated). Advancement ratios show little serial correlation, every K-5 result is unchanged by an effective-sample-size adjustment, and a permutation test agrees. No results changed.
- Report: Appendix A10 methods note explains the check; the Enrollment section now says the rate at which students join after kindergarten "has not fallen since COVID" rather than "is the same as before COVID," since a non-significant test shows no detectable change, not equality.

## Version 1.0 (October 12, 2026)
- First public release: full report, fact sheet, enrollment data, statistical workbook, and reproduction code.
