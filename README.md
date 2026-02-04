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
├── invoices/				# input invoice files
├── sql/
│   ├── README.md			
│   ├── schema.sql			# database schema
│	├── ERD.md				# entity relationship diagram
│	└── analysis/
│		├── data_quality.sql
│		├── views.md
│		└── kpis.sql
│
├── src/
│   ├── extract_invoice.py
│   ├── transform.py
│   └── load_postgres.py
├── batch_loader.py			# ETL entry point
├── config.yaml.example		# configuration template
├── .gitignore
├── LICENSE
└── README.md
```
## Database and schema

The ETL pipeline currently targets PostgreSQL.
The database schema is defined in sql/schema.sql.

With minimal adaptations (mainly data types and constraints), the schema can be ported to other relational databases such as MySQL or SQL Server.

The database must be created manually on the target server before running the pipeline.

The schema is optimized for analytical workloads, enabling downstream reporting and data analysis use cases.

## Configuration

The pipeline is configured via a YAML file.

A configuration template is provided in config.yaml.example.
Sensitive values (such as database passwords) are expected to be provided via environment variables.

Main configuration sections include:

- database connection parameters

- company VAT numbers to process

- filesystem paths for input, processed and error files

- logging configuration

The batch loader expects the configuration file to be named `config.yaml`
and located in the project root.

The `config.yaml` file is intentionally excluded from version control.

## Batch execution and error handling

The ETL process is orchestrated by a batch loader that coordinates all pipeline steps.

Invalid or malformed invoice files are automatically:

- logged

- moved to a dedicated error directory

This ensures traceability and robustness during batch execution.

## SQL analytics

The project includes an SQL analytics layer built on top of the ETL-loaded data.

### Structure

- Raw tables populated by the ETL pipeline are stored in the default `public` schema.
- Analytical views are defined in a dedicated `analytics` schema.
- Data quality checks and KPI queries are provided as SQL scripts under `sql/analysis/`.

### Data quality

The file `sql/analysis/data_quality.sql` contains repeatable audit queries to validate:
- structural integrity (e.g. duplicates, missing lines)
- accounting consistency (e.g. invoice lines vs VAT summary)

Data cleaning and normalization are intentionally handled upstream during the ETL transform phase.

### KPIs

The file `sql/analysis/kpis.sql` contains a curated set of analytical KPI queries
(e.g. revenue trends, top customers/suppliers, VAT distribution).

KPIs are provided as SQL queries rather than database views.
Depending on downstream needs, these queries can be promoted to views
(e.g. `analytics.kpi_*`) to simplify integration with BI tools.

## License
This project is released under the MIT License.
