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

## Notes

- The database targets PostgreSQL.
- Data quality checks are executed on raw tables, not on analytical views.
