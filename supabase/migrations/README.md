# Supabase Migration & Schema Management Protocol

## 1. Relational Authority
All database entities, constraints, indexes, and partition schemes are strictly governed by the 33-entity PostgreSQL 16 schema specified in `docs/TRD.md §11`. No table, column, or constraint may be introduced without corresponding TRD specification and Chief Architect approval.

## 2. Server-Side Key Isolation & Row-Level Security (RLS)
- **Publishable Key (`SUPABASE_PUBLISHABLE_KEY`)**: Intended for public, client-safe read access. All queries using this key are subject to Row-Level Security (RLS).
- **Secret Service Key (`SUPABASE_SECRET_KEY`)**: Bypasses all RLS checks. Restricted exclusively to server-side backend processes, data ingestion workers, and administrative scripts. NEVER expose this key to client applications or version control.
- **RLS Mandate**: Every table in the public schema must explicitly enable RLS:
  ```sql
  ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
  ```

## 3. Safe Local Migration Workflow
1. **Local Initialization**:
   ```bash
   supabase start
   ```
2. **Create New Migration**:
   ```bash
   supabase migration new <descriptive_migration_name>
   ```
3. **Local Testing & Verification**:
   ```bash
   supabase db reset
   ```
4. **Inspect Generated Diff**:
   Verify that tables, foreign keys (with proper ON DELETE clauses), and expression indexes match `docs/TRD.md §11`.

## 4. Production Schema Governance
- Direct execution of DDL against remote production Supabase instances is strictly prohibited.
- All production migrations require explicit human review, verified backup snapshots, and approval from the Chief Architect.
