# Calendar for the PMS Bersoch freshness monitor — staged, NOT ACTIVE

The monitor historically treats all Monday–Friday dates as trading sessions. This leads to false positive gaps on exchange holidays.

This change adds optional `PMS_MARKET_HOLIDAYS_CSV` support. **By default, behavior stays unchanged**. Only explicitly vetted holiday dates may be added; no speculative dates, automatic inferred holidays or external scraping.

CSV format:

```csv
date,source
YYYY-MM-DD,official exchange notice reference
```

After manually verifying holidays, store the CSV in the repository or another controlled path and set the workflow environment variable to point to it. `source` should identify an exchange calendar or notice, not a guessed weekday rule.

Tests cover skip of a holiday, omission from missing-day counts, and invalid calendar input.

## Deployment gates

1. Independently verify a full year of relevant Argentine exchange holidays and the treatment of foreign trading days.
2. Confirm whether the monitor should follow BYMA sessions, US exchange sessions, or a per-ticker market calendar. The current optional calendar represents **one explicit portfolio-level session convention**.
3. Add a source-documented CSV and set `PMS_MARKET_HOLIDAYS_CSV` in Actions only after approval.
4. Re-check 12–13 November historical gaps; no historical snapshot backfill is performed by this change.

This change is read-only and does not write to Sheets, install Apps Script or alter historical valuations.
