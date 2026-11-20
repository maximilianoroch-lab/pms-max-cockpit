# Legacy close correction — PREPARED, NOT INSTALLED

Based on the installed `AutomatizacionesPMS.gs` supplied by Max on 2026-11-18.
This is a separate handler, `pmsLegacySnapshotSafe`, for the personal application.
It is not Capture V3, does not certify quote freshness, and has no trigger installer.

The old writer appends detail before the total. A failure on the second write can
leave detail without a total; the old retry checks only detail count and returns
success. This candidate checks both persisted parts, unique tickers and their sum.
Partial or inconsistent data stops without writing or repairing history.

Run offline: `node --test ops/apps_script/test_legacy_snapshot_safe.cjs`.
Tests use synthetic positions, injected failures and no network or credentials.

## Conditions before production approval

- Export all installed project files, manifest, Script Properties names (secrets
  kept private), and actual trigger configuration under the correct owner.
- Verify `PMS_PERSONAL_SPREADSHEET_ID` privately against the bound personal base.
  Missing or mismatched configuration blocks this handler, including DEMO use.
- Recheck actual column headers, expected count and read-only reconciliation.
- Test on an isolated staging spreadsheet with this ID explicitly configured;
  never point test fixtures or a DEMO project at the personal production base.
- Obtain specific approval to install code, set configuration and replace the
  existing close trigger with exactly one trigger for this handler. Preserve the
  three existing MEP handlers. Do not run any legacy trigger installer.
- Changing the handler is not authorized by preparation or passing local tests.
- The old wrapper remains unchanged until the approved controlled switch.

## Limits and rollback

Two `setValues` calls are not a transaction. An uncertain write produces a clear
error; the next invocation checks both sheets before any further write. There is
no automatic deletion, compensation or repair. A complete prior snapshot is
checked against persisted totals, not repriced against current positions.
The 17:00 threshold preserves the old eligibility rule; this is not proof of EOD.
Market holidays, quote timestamps and flow reconciliation remain separate work.

If the controlled installation fails, stop the new close trigger and restore the
backed-up code/configuration and previous trigger only under the approved rollback.
Do not delete or overwrite appended rows. Inspect both histories and request
specific patrimonial approval for any correction. Application rollback and data
rollback are separate decisions.

No production, historical data, remote branch or Netlify build was changed by
preparing these files. Integrate into the existing consolidated candidate only;
do not create another parallel PR.
