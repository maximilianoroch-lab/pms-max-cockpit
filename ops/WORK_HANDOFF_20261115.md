# Work handoff — public technical index (15/11/2026)

**Use the full handoff document in the owner's Google Drive** rather than treating this public repository as the home for financial data. The complete document contains the Sheets structure, required authorizations, historical-data blockers, rollout and rollback plan, and relevant safety controls. Do not add account details, private transactions, or broker reports to this public repository.

## Four release candidates (all draft / unmerged)

| Product | Repository | PR |
|---|---|---|
| Personal desktop | `maximilianoroch-lab/pms-max-cockpit` | [#45](https://github.com/maximilianoroch-lab/pms-max-cockpit/pull/45) |
| Isolated demo desktop | `maximilianoroch-lab/Demo-PMS-Max` | [#31](https://github.com/maximilianoroch-lab/Demo-PMS-Max/pull/31) |
| Personal mobile | `maximilianoroch-lab/PMS-Bersoch-mobile` | [#6](https://github.com/maximilianoroch-lab/PMS-Bersoch-mobile/pull/6) |
| Isolated demo mobile | `maximilianoroch-lab/DEMO-PMSMax-mobile` | [#5](https://github.com/maximilianoroch-lab/DEMO-PMSMax-mobile/pull/5) |

The older implementation PRs were **closed, not merged**. Verify each live HEAD SHA and CI before integration. PR success does not mean a production deployment, current quotes, or authorization to install triggers.

## Required release constraints

1. Preserve isolated real and fictitious portfolios and their independent datasets.
2. Keep Netlify automatic builds stopped, confirm current plan usage and budget in the owner's account before any manual deploy. Test locally and in GitHub Actions first. Do not enable auto recharge or spend credits on exploratory builds.
3. Inspect Apps Script triggers, current deployed source and safe backups *before* installing or editing automated captures. The capture module is read-only with respect to the certified price history and treats market timestamps as unverified unless independently sourced.
4. Never fabricate missing market closes, correct historical quotes from unmatched sources, rewrite custody or apply undated movements.
5. Respect licensing; the public repo contains only ETF source registry/metadata, not redistributed issuer holdings.
6. Validate live site versions and behavior after authorized deployment. Record rollback procedure, before/after hosting cost, and any external blockers.
7. Request user authorization before real-account financial corrections, Apps Script trigger installation or production publication.

The detailed execution checklist, exact SHAs and user-dependent blockers are kept in the owner's Drive handoff rather than here. 
