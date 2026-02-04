-- ============================================
-- Data quality checks
-- ============================================
-- Nota: la maggior parte del cleaning viene fatto a monte (Transform).
-- Qui facciamo controlli "audit" ripetibili, senza query di debug ad hoc.
--
-- Convenzione (solo commenti):
--   DQ-S = Structural (integrità / struttura)
--   DQ-A = Accounting (quadrature / coerenze contabili)
-- ============================================


-- --------------------------------------------------------------------------
-- DQ-S-01: Fatture duplicate (stessa chiave logica: tipo+data+numero+cedente+committente)
-- Output include anche la lista degli invoice_id per agevolare eventuali rimozioni.
-- --------------------------------------------------------------------------
SELECT
  invoice_type,
  data_documento,
  numero_documento,
  cedente_id,
  committente_id,
  COUNT(*) AS dup_count,
  STRING_AGG(invoice_id::text, ' - ' ORDER BY invoice_id) AS invoices_id
FROM invoices
GROUP BY 1,2,3,4,5
HAVING COUNT(*) > 1
ORDER BY data_documento, dup_count DESC, numero_documento;


-- --------------------------------------------------------------------------
-- DQ-S-02: Fatture senza righe
-- (Non dovrebbero esistere in un load completo; spesso indica parsing incompleto)
-- --------------------------------------------------------------------------
SELECT
  i.invoice_id,
  i.invoice_type,
  i.data_documento,
  i.numero_documento,
  i.cedente_id,
  i.committente_id
FROM invoices i
LEFT JOIN invoice_lines l ON l.invoice_id = i.invoice_id
WHERE l.invoice_id IS NULL
ORDER BY i.data_documento, i.invoice_id;


-- --------------------------------------------------------------------------
-- DQ-S-03: Fatture senza data documento
-- Nota: nello schema data_documento è NOT NULL, quindi questo check è una "rete di sicurezza"
-- (utile se in futuro lo schema cambia o se esistono load parziali)
-- --------------------------------------------------------------------------
SELECT
  i.invoice_id,
  i.invoice_type,
  i.data_documento,
  i.numero_documento,
  i.cedente_id,
  i.committente_id
FROM invoices i
WHERE i.data_documento IS NULL
ORDER BY i.invoice_id;


-- --------------------------------------------------------------------------
-- DQ-S-04: numero_linea duplicato nella stessa fattura
-- (Per analisi a livello riga è un problema serio: si rischiano duplicazioni di importi)
-- --------------------------------------------------------------------------
WITH double_line AS (
  SELECT
    invoice_id,
    numero_linea,
    COUNT(*) AS dup_count
  FROM invoice_lines
  GROUP BY 1,2
  HAVING COUNT(*) > 1
)
SELECT
  l.invoice_id,
  i.invoice_type,
  i.tipo_documento,
  i.data_documento,
  i.numero_documento,
  l.line_id,
  l.numero_linea,
  l.descrizione,
  l.quantita,
  l.prezzo_unitario,
  l.prezzo_totale
FROM invoice_lines l
JOIN double_line d
  ON d.invoice_id = l.invoice_id
 AND d.numero_linea = l.numero_linea
JOIN invoices i
  ON i.invoice_id = l.invoice_id
ORDER BY l.invoice_id, l.numero_linea, l.line_id;


-- --------------------------------------------------------------------------
-- DQ-A-01: Riconciliazione imponibile - invoice_lines vs vat_summary
-- Confronto per fattura e per "bucket IVA" (aliquota_iva + natura).
--
-- Assunzione: invoice_lines.prezzo_totale rappresenta l'imponibile (netto IVA) a livello riga.
-- Tolleranza: 0.10 per arrotondamenti / differenze minime.
-- --------------------------------------------------------------------------
WITH lines AS (
  SELECT
    invoice_id,
    COALESCE(aliquota_iva, -1) AS aliquota_iva_key,
    COALESCE(natura, '')       AS natura_key,
    ROUND(SUM(COALESCE(prezzo_totale, 0)), 2) AS imponibile_lines
  FROM invoice_lines
  GROUP BY 1,2,3
),
vat AS (
  SELECT
    invoice_id,
    COALESCE(aliquota_iva, -1) AS aliquota_iva_key,
    COALESCE(natura, '')       AS natura_key,
    ROUND(SUM(COALESCE(imponibile_importo, 0)), 2) AS imponibile_vat
  FROM vat_summary
  GROUP BY 1,2,3
),
recon AS (
  SELECT
    COALESCE(l.invoice_id, v.invoice_id) AS invoice_id,
    COALESCE(l.aliquota_iva_key, v.aliquota_iva_key) AS aliquota_iva_key,
    COALESCE(l.natura_key, v.natura_key) AS natura_key,
    l.imponibile_lines,
    v.imponibile_vat,
    ROUND(COALESCE(l.imponibile_lines, 0) - COALESCE(v.imponibile_vat, 0), 2) AS delta
  FROM lines l
  FULL JOIN vat v
    ON l.invoice_id = v.invoice_id
   AND l.aliquota_iva_key = v.aliquota_iva_key
   AND l.natura_key = v.natura_key
)
SELECT
  r.invoice_id,
  i.invoice_type,
  i.tipo_documento,
  i.data_documento,
  i.numero_documento,
  i.importo_bollo,
  NULLIF(r.aliquota_iva_key, -1) AS aliquota_iva,
  NULLIF(r.natura_key, '')       AS natura,
  r.imponibile_lines,
  r.imponibile_vat,
  r.delta
FROM recon r
LEFT JOIN invoices i
  ON i.invoice_id = r.invoice_id
WHERE ABS(COALESCE(r.imponibile_lines, 0) - COALESCE(r.imponibile_vat, 0)) > 0.10
ORDER BY ABS(COALESCE(r.imponibile_lines, 0) - COALESCE(r.imponibile_vat, 0)) DESC,
         r.invoice_id;
