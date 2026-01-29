# fatturapa-etl 

ETL pipeline for Italian electronic invoices (FatturaPA) from XML/P7M to PostgreSQL.

## Project structure

```text
fatturapa-etl/
├── invoices/
├── sql/
├── src/
└── README.md
```

## Pipeline overview

```text
XML / P7M
   ↓
Extract
   ↓
Transform
   ↓
Load
   ↓
PostgreSQL
```