-- AP duplicate invoice starter checks
-- Purpose: help finance and operations teams review exported accounts-payable data for likely duplicate or mismatched vendor charges.
-- Use only on your own authorized data. Do not upload or paste live bank details, personal data, confidential supplier names, contract text, account IDs, or invoice images into public systems.
-- Replace table/column names in the CTE below with names from your internal export before running.

WITH ap_export AS (
  SELECT
    vendor_name,
    vendor_id,
    invoice_number,
    invoice_date,
    due_date,
    payment_date,
    amount,
    currency,
    payment_reference,
    status
  FROM accounts_payable_export
), normalized AS (
  SELECT
    vendor_name,
    vendor_id,
    LOWER(TRIM(REGEXP_REPLACE(COALESCE(invoice_number, ''), '[^A-Za-z0-9]', '', 'g'))) AS invoice_number_key,
    invoice_number,
    invoice_date,
    payment_date,
    ROUND(amount::numeric, 2) AS amount_key,
    amount,
    currency,
    payment_reference,
    status
  FROM ap_export
), exact_duplicate_invoice AS (
  SELECT
    'exact_duplicate_invoice' AS review_query,
    vendor_id,
    vendor_name,
    invoice_number_key,
    currency,
    amount_key,
    COUNT(*) AS row_count,
    MIN(invoice_date) AS first_invoice_date,
    MAX(invoice_date) AS last_invoice_date,
    STRING_AGG(COALESCE(payment_reference, '[no payment reference]'), ', ' ORDER BY payment_reference) AS payment_references
  FROM normalized
  WHERE invoice_number_key <> ''
  GROUP BY vendor_id, vendor_name, invoice_number_key, currency, amount_key
  HAVING COUNT(*) > 1
), same_day_same_amount AS (
  SELECT
    'same_day_same_amount' AS review_query,
    vendor_id,
    vendor_name,
    NULL AS invoice_number_key,
    currency,
    amount_key,
    COUNT(*) AS row_count,
    MIN(invoice_date) AS first_invoice_date,
    MAX(invoice_date) AS last_invoice_date,
    STRING_AGG(COALESCE(invoice_number, '[no invoice number]'), ', ' ORDER BY invoice_number) AS payment_references
  FROM normalized
  GROUP BY vendor_id, vendor_name, invoice_date, currency, amount_key
  HAVING COUNT(*) > 1
), paid_after_credit_or_cancelled AS (
  SELECT
    'paid_after_credit_or_cancelled' AS review_query,
    vendor_id,
    vendor_name,
    invoice_number_key,
    currency,
    amount_key,
    COUNT(*) AS row_count,
    MIN(invoice_date) AS first_invoice_date,
    MAX(invoice_date) AS last_invoice_date,
    STRING_AGG(COALESCE(status, '[no status]'), ', ' ORDER BY status) AS payment_references
  FROM normalized
  WHERE LOWER(COALESCE(status, '')) ~ '(credit|cancel|void|refund)'
     OR amount_key < 0
  GROUP BY vendor_id, vendor_name, invoice_number_key, currency, amount_key
)
SELECT * FROM exact_duplicate_invoice
UNION ALL
SELECT * FROM same_day_same_amount
UNION ALL
SELECT * FROM paid_after_credit_or_cancelled
ORDER BY review_query, vendor_name, amount_key DESC;

-- Review output manually before contacting any supplier. A row is only a lead for internal review, not proof of overbilling or entitlement to a refund.
