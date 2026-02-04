# SQL layer

This directory contains the SQL layer of the project.

## Contents

- `schema.sql`  
  Database schema (DDL) for the analytical model.

- `ERD.md`  
  Entity Relationship Diagram and data model documentation.

- `analysis/`  
  Analytical SQL queries built on top of the ETL-loaded data.
  Includes:
  - data consistency checks

## Analytics schema

Analytical views are defined in a dedicated PostgreSQL schema named `analytics`.

This schema represents the semantic layer of the project and is intended for:
- analytical queries
- KPI calculations
- reporting and BI tools

Raw tables populated by the ETL pipeline remain in the default `public` schema.
Data quality checks are executed directly on raw tables, while KPIs and analysis
should rely on views in the `analytics` schema.


## Notes

- The database targets PostgreSQL.
- Data quality checks are executed on raw tables, not on analytical views.
