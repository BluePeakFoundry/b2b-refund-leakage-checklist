# B2B Refund Leakage Checklist

A static, private-by-design checklist for reviewing common B2B billing and refund leakage situations.

## Scope

The page helps finance and operations teams organize an internal review of duplicate charges, unused credits, renewal mismatches, and seat or downgrade gaps. It does not collect records, submit forms, provide legal or accounting advice, or guarantee any recovery.

The live page also includes a sanitized service-scope CTA for teams that want a lightweight review plan before sharing any records. Scope requests must stay public and generalized; the repository does not accept confidential data, vendor details, invoice data, account identifiers, pricing terms, tax details, contract text, or live files.

## Privacy

This site is static. It does not include data-entry forms, cookies, account requirements, or server submission of entries. Privacy-friendly aggregate analytics measure visits and non-personal CTA/download/feedback events.

## Public feedback and review requests

General workflow feedback is welcome through the public GitHub issue template: https://github.com/BluePeakFoundry/b2b-refund-leakage-checklist/issues/new?template=feedback.yml

Sanitized public checklist review requests are welcome through: https://github.com/BluePeakFoundry/b2b-refund-leakage-checklist/issues/new?template=review-request.yml

Do not share confidential data, personal data, client names, vendor names, invoice numbers, account numbers, account IDs, pricing terms, contract terms, or contract text.

The `lead:b2b:service-scope` CTA measures interest in a fixed-scope review outline without collecting private records.

## Downloadable helpers

- `downloads/refund-leakage-review.csv` — a plain CSV review sheet for internal checks.
- `downloads/vendor-message-template.md` — a neutral vendor billing correction message template.
- `downloads/ap-duplicate-invoice-checks.sql` — starter SQL for flagging duplicate invoice, same-day same-amount, and credit/cancellation review candidates inside a private AP export.
- `downloads/ap-sql-starter-guide.md` — safe-use notes, expected columns, and manual review workflow for the SQL starter pack.

## Repository signal snapshots

The workflow `.github/workflows/traffic-snapshot.yml` can be run manually or on its daily schedule to store repository-level signal snapshots under `metrics/repository-signals/`. It records GitHub Traffic API results when the workflow token can access them, records the API limitation when it cannot, and checks public availability of the page and downloadable helpers. These snapshots do not identify users.

## Validation

Run:

```bash
python3 validate_public_site.py
python3 -m json.tool manifest.json >/dev/null
```

Expected local result after building the manifest:

```text
OK b2b refund leakage checklist files=12 money_verified_eur=0 external_actions=0
```
