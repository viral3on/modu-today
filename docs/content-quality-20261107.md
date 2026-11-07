# Content changes — 2026-11-07

The account screenshot identifies “low value content”; it does not identify a URL
or prove that RSS, JavaScript, or ad code caused rejection. These changes improve
the visitor experience and original content, without promising AdSense approval.

- Retire external headline aggregation permanently. Remove the home section and
  navigation entry, stop scheduled/manual collection, and stop reading its data
  during builds. The old `/news/` URL explains the change without ads and remains
  noindex; noindex is not claimed to exclude a page from AdSense review.
- Keep original articles separate from product help. Add three worked, fictional
  arithmetic examples about successive discounts, weighted averages, and
  percentage points. No claimed first-hand tests, fabricated customers or sources.
- Replace generic descriptions in five calculators and three games with usage,
  assumptions, verified examples, limits, and relevant next steps. The guide JSON
  is applied after legacy scheduled generators so they cannot restore old filler.
- Preserve functional tool code and the existing AdSense configuration. Correct
  the average-price calculator's “decrease” label when the average rises.
- Existing About, Contact, Privacy and Terms pages stay linked. The privacy
  advertising/cookie disclosure was improved in the preceding production change.
- Published articles and the apartment guide remain statically rendered, with
  canonical URLs and validated sitemap entries. Product help is not counted as a
  reading article. No arbitrary minimum article count or word quota is applied.

Validation includes the real calculator scripts against the published examples,
controls/scripts preservation when inserting guides, the full Node suite, and
production browser checks. AdSense review must be requested separately by the
owner; no review request is sent by this implementation.
