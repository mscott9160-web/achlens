# Federal Reserve Calendar

The calendar utility is sourced from the Federal Reserve Board's K.8 schedule:

<https://www.federalreserve.gov/aboutthefed/k8.htm>

The current embedded table covers 2026 through 2030 and was retrieved on
2026-09-12. It exposes Federal Reserve schedule dates and a helper for the next
weekday not listed in that table.

This is not a bank-specific ACH settlement calendar. Saturday and Sunday
footnotes, ACH Operator schedules, same-day ACH windows, and bank-specific
cutoffs require separate operational interpretation and are intentionally not
inferred by this utility.