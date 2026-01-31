# fatturapa-etl 

ETL pipeline for Italian electronic invoices (FatturaPA) from XML/P7M to PostgreSQL.
The pipeline is fully configurable via YAML and designed for batch processing.

## Pipeline overview
Each step of the pipeline is implemented as a dedicated module:
- Extract: parse FatturaPA XML/P7M files
- Transform: normalize and prepare data for analytics
- Load: persist data into a relational database

The resulting database schema is designed to support analytical queries for data analysis and reporting.

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

## Project structure

```text
fatturapa-etl/
├── invoices/
├── sql/
	 ├─ schema.sql
	 └─ ERD.md
├── src/
	 ├─ extract_invoice.py
	 ├─ transform.py
	 └─ load.py
└── README.md
```


## License
This project is released under the MIT License.
