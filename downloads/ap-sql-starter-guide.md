# AP duplicate invoice SQL starter guide

This small pack helps finance or operations teams turn an internal accounts-payable export into a first-pass review queue for duplicate invoices, same-day repeated charges, and possible credit or cancellation mismatches.

## Safe use

- Use only data you are authorized to review.
- Run the SQL inside your own analytics database or a private local copy.
- Do not use live bank details, personal data, confidential supplier names, invoice images, contract text, account IDs, or customer records in public issues, examples, or support requests.
- Treat every result as a review lead. The query does not prove overbilling, refund rights, or legal entitlement.

## Expected input columns

The starter SQL assumes an `accounts_payable_export` table with these columns. Rename them in the first CTE if your export differs:

- `vendor_name`
- `vendor_id`
- `invoice_number`
- `invoice_date`
- `due_date`
- `payment_date`
- `amount`
- `currency`
- `payment_reference`
- `status`

## Review queries included

1. `exact_duplicate_invoice` — same vendor, normalized invoice number, currency, and amount appears more than once.
2. `same_day_same_amount` — same vendor, invoice date, currency, and amount appears more than once even if invoice numbers differ.
3. `paid_after_credit_or_cancelled` — records with credit, cancelled, void, refund, or negative-amount signals that may need manual matching.

## Suggested workflow

1. Export AP records for a bounded period such as a quarter.
2. Load the export into a temporary private table.
3. Run `ap-duplicate-invoice-checks.sql` after mapping column names.
4. Remove false positives caused by legitimate split billing, tax-only corrections, or reissued invoices.
5. Verify against contracts, vendor statements, credit memos, and payment records before contacting any vendor.
6. Use the vendor message template only through the safest official supplier channel.

No refund, saving, recovery, response, or outcome is guaranteed.
