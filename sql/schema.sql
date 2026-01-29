-- ============================================
-- SCHEMA: Electronic Invoice Analytical Model
-- ============================================

-- Drop tables (for development only)
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS vat_summary CASCADE;
DROP TABLE IF EXISTS invoice_lines CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

-- ============================================
-- COMPANIES (Cedente / Committente)
-- ============================================
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    denominazione VARCHAR(300) NOT NULL,
    partita_iva VARCHAR(20) UNIQUE NOT NULL,
    codice_fiscale VARCHAR(20),
    indirizzo VARCHAR(200),
    cap VARCHAR(20),
    comune VARCHAR(100),
    provincia VARCHAR(100),
    nazione VARCHAR(100),
    telefono VARCHAR(100),
    email VARCHAR(100)
);

-- ============================================
-- INVOICES (Active / Passive)
-- ============================================
CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    tipo_documento VARCHAR(10) NOT NULL,    
    divisa VARCHAR(10) DEFAULT 'EUR',
    data_documento DATE NOT NULL,
    numero_documento VARCHAR(200) NOT NULL,
    importo_totale NUMERIC(12,2),
    bollo_virtuale VARCHAR(10),
    importo_bollo NUMERIC(12,2),
    causale VARCHAR(300),
    invoice_type VARCHAR(20) NOT NULL CHECK (invoice_type IN ('attiva', 'passiva')),

    cedente_id INT NOT NULL REFERENCES companies(company_id),
    committente_id INT NOT NULL REFERENCES companies(company_id)

    
);

-- ============================================
-- INVOICE LINES
-- ============================================
CREATE TABLE invoice_lines (
    line_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    numero_linea INT NOT NULL,
    codice_articolo VARCHAR(500),
    descrizione VARCHAR(500),
    quantita NUMERIC(12,2),
    unita_misura VARCHAR(20),
    prezzo_unitario NUMERIC(12,2),
    prezzo_totale NUMERIC(12,2),
    aliquota_iva NUMERIC(5,2),
    natura VARCHAR(50),
    sconto_maggiorazione NUMERIC(12,2)
);

-- ============================================
-- VAT SUMMARY
-- ============================================
CREATE TABLE vat_summary (
    vat_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    aliquota_iva NUMERIC(5,2),
    natura VARCHAR(50),
    imponibile_importo NUMERIC(12,2),
    imposta NUMERIC(12,2),
    riferimento_normativo VARCHAR(300)
);

-- ============================================
-- PAYMENTS
-- ============================================
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    condizioni_pagamento VARCHAR(100),
    modalita_pagamento VARCHAR(100),
    data_scadenza DATE,
    importo_pagamento NUMERIC(12,2),
    iban VARCHAR(50),
    beneficiario VARCHAR(200)
);

-- ============================================
-- INDEXES (Performance for analytics)
-- ============================================
CREATE INDEX idx_invoices_date ON invoices(data_documento);
CREATE INDEX idx_invoices_type ON invoices(invoice_type);
CREATE INDEX idx_invoice_lines_invoice ON invoice_lines(invoice_id);
CREATE INDEX idx_vat_summary_invoice ON vat_summary(invoice_id);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
