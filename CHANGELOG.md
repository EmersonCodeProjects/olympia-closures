# Changelog

## Version 1.1 (October 13, 2026)
- Statistics workbook: replaced a draft copy that still flagged items for review; all checks match the final report or differ only by rounding.
- Added a dependence check for the Welch t-tests on advancement ratios (new Welch_sensitivity tab in the workbook; reproduce.py updated). Advancement ratios show little serial correlation, every K-5 result is unchanged by an effective-sample-size adjustment, and a permutation test agrees. No results changed.
- Report: Appendix A10 methods note explains the check; the Enrollment section now says the rate at which students join after kindergarten "has not fallen since COVID" rather than "is the same as before COVID," since a non-significant test shows no detectable change, not equality.

## Version 1.0 (October 12, 2026)
- First public release: full report, fact sheet, enrollment data, statistical workbook, and reproduction code.
