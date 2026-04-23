# Memory Migrations

This directory stores versioned SQLite migrations for pmgo long-term memory.

## Rules

- Keep migration files immutable once committed.
- Use zero-padded numeric prefixes (`0001_*.sql`, `0002_*.sql`, ...).
- Every migration should be idempotent where possible.
- Record applied versions in `schema_migrations`.

## Relationship with `memory/schema.sql`

- `memory/schema.sql` is the latest full schema snapshot.
- `memory/migrations/*.sql` are append-only history for upgrades.

## Apply migrations

Run from repo root:

```bash
npm run memory:migrate
```

Behavior:

- Applies pending migrations in filename order.
- Tracks applied versions in `schema_migrations`.
- Skips already applied migrations.
