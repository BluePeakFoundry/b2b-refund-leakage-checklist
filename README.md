# B2B Refund Leakage Checklist

A static, private-by-design checklist for reviewing common B2B billing and refund leakage situations.

## Scope

The page helps finance and operations teams organize an internal review of duplicate charges, unused credits, renewal mismatches, and seat or downgrade gaps. It does not collect records, submit forms, provide legal or accounting advice, or guarantee any recovery.

## Privacy

This site is static. It does not include forms, analytics, tracking scripts, cookies, or remote runtime resources.

## Validation

Run:

```bash
python3 validate_public_site.py
python3 -m json.tool manifest.json >/dev/null
```

Expected local result after building the manifest:

```text
OK b2b refund leakage checklist files=7 money_verified_eur=0 external_actions=0
```
