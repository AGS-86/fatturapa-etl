# Entity Relationship Diagram (ERD)

This document describes the relational data model used to store
Italian electronic invoices (FatturaPA).

## Core entities

### companies
Represents both suppliers (cedente/prestatore) and customers (committente).

A company can appear in multiple invoices with different roles.

### invoices
Represents the invoice header.
Each invoice is linked to:
- one supplier (cedente)
- one customer (committente)

The field `invoice_type` distinguishes:
- `attiva` → issued invoices
- `passiva` → received invoices

### invoice_lines
Represents individual invoice line items.
Each invoice can contain multiple lines.

### vat_summary
Represents VAT breakdown per invoice and VAT rate.

### payments
Represents payment terms and payment-related information.

## Relationships

- companies 1 → N invoices (as cedente)
- companies 1 → N invoices (as committente)
- invoices 1 → N invoice_lines
- invoices 1 → N vat_summary
- invoices 1 → 1 payments

The model follows a normalized relational approach to avoid data duplication
and to support analytical queries.


```mermaid
erDiagram

    COMPANIES {
        int company_id PK
        varchar denominazione
        varchar partita_iva
        varchar codice_fiscale
        varchar indirizzo
        varchar cap
        varchar comune
        varchar provincia
        varchar nazione
        varchar telefono
        varchar email
    }

    INVOICES {
        int invoice_id PK
        varchar tipo_documento
        varchar divisa
        date data_documento
        varchar numero_documento
        numeric importo_totale
        varchar bollo_virtuale
        numeric importo_bollo
        varchar causale
        varchar invoice_type
        int cedente_id FK
        int committente_id FK
    }

    INVOICE_LINES {
        int line_id PK
        int invoice_id FK
        int numero_linea
        varchar codice_articolo
        varchar descrizione
        numeric quantita
        varchar unita_misura
        numeric prezzo_unitario
        numeric prezzo_totale
        numeric aliquota_iva
        varchar natura
        numeric sconto_maggiorazione
    }

    VAT_SUMMARY {
        int vat_id PK
        int invoice_id FK
        numeric aliquota_iva
        varchar natura
        numeric imponibile_importo
        numeric imposta
        varchar riferimento_normativo
    }

    PAYMENTS {
        int payment_id PK
        int invoice_id FK
        varchar condizioni_pagamento
        varchar modalita_pagamento
        date data_scadenza
        numeric importo_pagamento
        varchar iban
        varchar beneficiario
    }

    %% RELAZIONI
    COMPANIES ||--o{ INVOICES : "cedente_id"
    COMPANIES ||--o{ INVOICES : "committente_id"

    INVOICES ||--o{ INVOICE_LINES : contains
    INVOICES ||--o{ VAT_SUMMARY : summarizes
    INVOICES ||--o{ PAYMENTS : pays
```