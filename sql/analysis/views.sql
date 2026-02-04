-- ============================================
-- Views for analytics (semantic layer)
-- ============================================
-- NB:
-- - Importi NON "signed": eventuali note di credito / storni non sono gestiti come segno.
-- - net_amount = imponibile (netto IVA) a livello riga, derivato da invoice_lines.prezzo_totale.

CREATE SCHEMA IF NOT EXISTS analytics;

-- ------------------------------------------------------------
-- 1) Intestazione fattura arricchita (header + metrica netta)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.invoice_header_fact AS
WITH tot_lines AS (
  SELECT
    invoice_id,
    ROUND(SUM(COALESCE(prezzo_totale, 0)), 2) AS invoice_net_amount
  FROM invoice_lines
  GROUP BY invoice_id
)
SELECT
  i.invoice_id,
  i.invoice_type,                  -- 'attiva' | 'passiva'
  i.tipo_documento,
  i.divisa,
  i.data_documento AS doc_date,
  EXTRACT(YEAR FROM i.data_documento)::int AS doc_year,
  date_trunc('month', i.data_documento)::date AS doc_month,
  i.numero_documento,
  t.invoice_net_amount,
  i.importo_totale,                -- lordo IVA (non KPI fatturato, utile per riconciliazioni)
  i.importo_bollo,
  i.causale,

  -- Cedente / committente (anagrafica)
  c_ced.company_id    AS cedente_company_id,
  c_ced.denominazione AS cedente_name,
  c_ced.partita_iva   AS cedente_vat,

  c_com.company_id    AS committente_company_id,
  c_com.denominazione AS committente_name,
  c_com.partita_iva   AS committente_vat

FROM invoices i
JOIN companies c_ced ON c_ced.company_id = i.cedente_id
JOIN companies c_com ON c_com.company_id = i.committente_id
LEFT JOIN tot_lines t ON t.invoice_id = i.invoice_id;


-- ------------------------------------------------------------
-- 2) Fact a livello riga: base per KPI (evita join ripetuti)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.invoice_lines_fact AS
SELECT
  i.invoice_id,
  i.invoice_type,
  i.data_documento AS doc_date,
  EXTRACT(YEAR FROM i.data_documento)::int AS doc_year,
  date_trunc('month', i.data_documento)::date AS doc_month,
  i.tipo_documento,
  i.numero_documento,
  i.divisa,

  -- Controparte "unica" in base al tipo fattura
  CASE WHEN i.invoice_type = 'attiva'  THEN i.committente_id ELSE i.cedente_id END AS counterparty_id,
  CASE WHEN i.invoice_type = 'attiva'  THEN c_com.denominazione ELSE c_ced.denominazione END AS counterparty_name,
  CASE WHEN i.invoice_type = 'attiva'  THEN c_com.partita_iva   ELSE c_ced.partita_iva   END AS counterparty_vat,

  -- Line
  l.line_id,
  l.numero_linea,
  l.codice_articolo,
  l.descrizione,
  l.quantita,
  l.unita_misura,
  l.prezzo_unitario,
  l.prezzo_totale AS net_amount,        -- alias chiaro (imponibile / netto IVA)
  l.aliquota_iva,
  l.natura,
  l.sconto_maggiorazione

FROM invoice_lines l
JOIN invoices i      ON i.invoice_id = l.invoice_id
JOIN companies c_ced ON c_ced.company_id = i.cedente_id
JOIN companies c_com ON c_com.company_id = i.committente_id;
