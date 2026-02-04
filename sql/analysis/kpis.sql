-- ============================================
-- KPI queries (semantic layer: analytics.*)
-- ============================================
-- Nota:
-- - Tutti gli importi "fatturato" sono basati su imponibile/netto IVA.
-- - Le KPI qui sono query ripetibili (niente debug / niente filtri hardcoded su anni fissi).


-- ------------------------------------------------------------
-- KPI 1: Volume fatture e totale netto per mese e tipo (ultimi 3 anni rolling)
-- ------------------------------------------------------------
SELECT
  doc_month,
  invoice_type,
  COUNT(DISTINCT invoice_id) AS n_invoices,
  SUM(invoice_net_amount)    AS total_net_amount
FROM analytics.invoice_header_fact
WHERE doc_date >= (CURRENT_DATE - INTERVAL '3 years')
GROUP BY 1,2
ORDER BY 1 DESC, 2;


-- ------------------------------------------------------------
-- KPI 2: Top 10 clienti per valore (ultimi 24 mesi) - solo fatture attive
-- KPI "serio": totale netto e ticket medio per fattura (non media per riga)
-- ------------------------------------------------------------
SELECT
  counterparty_name,
  counterparty_vat,
  COUNT(DISTINCT invoice_id)              AS n_invoices,
  SUM(net_amount)                         AS total_net_amount,
  ROUND(SUM(net_amount) / NULLIF(COUNT(DISTINCT invoice_id),0), 2) AS avg_net_per_invoice,
  ROUND(AVG(net_amount), 2) AS avg_net_per_line
FROM analytics.invoice_lines_fact
WHERE invoice_type = 'attiva'
  AND doc_date >= (CURRENT_DATE - INTERVAL '24 months')
GROUP BY 1,2
ORDER BY total_net_amount DESC
LIMIT 10;


-- ------------------------------------------------------------
-- KPI 3: Top 10 fornitori per valore (ultimi 24 mesi) - solo fatture passive
-- ------------------------------------------------------------
SELECT
  counterparty_name,
  counterparty_vat,
  COUNT(DISTINCT invoice_id)              AS n_invoices,
  SUM(net_amount)                         AS total_net_amount,
  ROUND(SUM(net_amount) / NULLIF(COUNT(DISTINCT invoice_id),0), 2) AS avg_net_per_invoice
FROM analytics.invoice_lines_fact
WHERE invoice_type = 'passiva'
  AND doc_date >= (CURRENT_DATE - INTERVAL '24 months')
GROUP BY 1,2
ORDER BY total_net_amount DESC
LIMIT 10;


-- ------------------------------------------------------------
-- KPI 4: Distribuzione aliquote IVA (linee) - imponibile totale e numero righe
-- ------------------------------------------------------------
SELECT
  aliquota_iva,
  COUNT(*)           AS n_lines,
  SUM(net_amount)    AS total_taxable_net
FROM analytics.invoice_lines_fact
GROUP BY 1
ORDER BY 1;


-- ------------------------------------------------------------
-- KPI 5: Importo netto per fattura (distribuzione per tipo)
-- ------------------------------------------------------------
SELECT
  invoice_type,
  ROUND(AVG(invoice_net_amount), 2) AS avg_invoice_net,
  MIN(invoice_net_amount)           AS min_invoice_net,
  MAX(invoice_net_amount)           AS max_invoice_net
FROM analytics.invoice_header_fact
GROUP BY 1
ORDER BY 1;


-- ------------------------------------------------------------
-- KPI 6: Fatturato netto per trimestre e azienda gestita (ultimi 3 anni rolling)
-- Include:
-- - media trimestrale dell'anno (year_avg)
-- - moving average su 2 trimestri (moving_avg_2q)
-- - progressivo anno (ytd_amount)
-- ------------------------------------------------------------
WITH revenue_q AS (
  SELECT
    cedente_company_id,
    cedente_name,
    EXTRACT(YEAR FROM doc_date)::int AS year,
    date_trunc('quarter', doc_date)::date AS quarter_start,
    SUM(invoice_net_amount) AS quarter_net_amount
  FROM analytics.invoice_header_fact
  WHERE invoice_type = 'attiva'
    AND doc_date >= (CURRENT_DATE - INTERVAL '3 years')
  GROUP BY 1,2,3,4
)
SELECT
  cedente_company_id,
  cedente_name,
  year,
  quarter_start,
  quarter_net_amount,

  -- Media trimestrale dell'anno (stabile, non "running")
  ROUND(AVG(quarter_net_amount) OVER (
    PARTITION BY cedente_company_id, year
  ), 2) AS year_avg_quarter_net,

  -- Moving average su 2 trimestri (per anno)
  ROUND(AVG(quarter_net_amount) OVER (
    PARTITION BY cedente_company_id, year
    ORDER BY quarter_start
    ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
  ), 2) AS moving_avg_2q_net,

  -- Progressivo anno (YTD)
  SUM(quarter_net_amount) OVER (
    PARTITION BY cedente_company_id, year
    ORDER BY quarter_start
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS ytd_net_amount

FROM revenue_q
ORDER BY cedente_company_id, year DESC, quarter_start DESC;
