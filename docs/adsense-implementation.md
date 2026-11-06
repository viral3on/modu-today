# AdSense implementation

Updated: 2026-11-07 (Asia/Seoul).

`lib/adsense.mjs` owns the publisher ID, route coverage and the reading-page CSP.
`scripts/build.mjs` applies it to every emitted HTML file, including tools maintained by scheduled workflows. Do not manually insert another ad loader into individual pages.

- Enabled: home, reading index and published articles, tools index, apartment transactions, lotto, calculators, games and YouTube rankings.
- Deliberately ad-free: admin and previews, news aggregation, suspended scanner, 404 and verification files, site information/legal/contact pages, and the two archived educational guides.
- Existing calculator loader tags are normalized to one official async loader. All enabled pages include the matching `google-adsense-account` meta tag. `ads.txt` must match the same publisher; a mismatch fails the build.
- Auto ads uses the existing publisher account. No invented ad-unit IDs or empty manual slots are added. Newly published articles receive the loader automatically.

## Reading pages and CSP

These are static HTML pages, so a fixed/reused nonce is not safe. The trusted inline bootstrap has a SHA-256 hash and loads the unmodified Google script, the reading-index module (only when its search UI exists) and analytics. `strict-dynamic` permits descendant scripts without maintaining an expiring Google-domain list. The AdSense-documented `unsafe-eval` capability is permitted; arbitrary inline scripts and event handlers remain blocked in browsers supporting strict CSP. Object and base-tag restrictions remain enforced. The admin policy is unchanged.

The `vercel.json` reading policy must equal the exported `READING_CSP`; the build rejects stale hashes before deleting the previous output. If the bootstrap is edited, update that header from `READING_CSP` in the same commit. Local development serves the same configured headers.

## Account-side checks after approval

1. Confirm AdSense Sites shows modu.today as **Ready**. This repository cannot grant approval or lift policy enforcement.
2. In Ads �� By site �� modu.today, enable **Auto ads** and apply/save the settings. A site loader alone does not enable this account setting. Review formats and exclusions in the account preview.
3. Confirm the publisher ID in the account matches this repository and ads.txt, and resolve any account/payment/consent requirements reported by AdSense.
4. Test home, one reading article and one calculator in a browser without an ad blocker. Confirm a single `adsbygoogle.js` load, no site CSP violations, and actual ad requests. A pre-approval 403 is not proof of a broken site loader.
5. Check desktop/mobile placement and avoid clicking your own ads. Actual creative delivery and fill cannot be validated before the account/site are eligible.

Sources:
- https://support.google.com/adsense/answer/9261307
- https://support.google.com/adsense/answer/16283098
- https://support.google.com/adsense/answer/10858959
- https://web.dev/articles/strict-csp
