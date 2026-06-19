# dbt Core — Concepts & Reference

## What is dbt?

dbt (data build tool) handles the **T in ELT**. It takes raw data already loaded into your warehouse and transforms it using plain SQL SELECT statements. dbt compiles those SELECTs into `CREATE TABLE` or `CREATE VIEW` statements and runs them in BigQuery (or any warehouse).

You never write `CREATE TABLE` or `INSERT INTO` — you only write `SELECT`. dbt handles the rest.

---

## Two Config Files

| File | Location | Committed to git? | Purpose |
|---|---|---|---|
| `dbt_project.yml` | Inside project folder | Yes | Defines project name, model paths, materializations |
| `~/.dbt/profiles.yml` | User's home directory | Never | Your personal DB credentials and connection details |

Every developer on a team has their own `profiles.yml`. The project only ships `dbt_project.yml`.

---

## Medallion Architecture in dbt

```
BigQuery (raw)          dbt staging (silver)        dbt marts (gold)
crypto_raw.crypto_prices  →  stg_crypto_prices  →  fct_crypto_daily
     source()                    ref()
```

- **source()** — points to raw tables loaded outside dbt (by Airflow, Fivetran, etc.)
- **ref()** — points to another dbt model; creates a dependency so dbt runs models in the right order

---

## Project Folder Structure

```
crypto_pipeline/
├── dbt_project.yml        # project config
├── models/
│   ├── staging/           # silver layer — views, clean raw data
│   │   ├── source.yml     # declares external sources (BigQuery tables)
│   │   ├── schema.yml     # column descriptions + generic tests
│   │   └── stg_*.sql      # staging models
│   └── marts/             # gold layer — tables, aggregated business logic
│       ├── schema.yml
│       └── fct_*.sql / dim_*.sql
├── tests/                 # singular (custom SQL) tests
├── seeds/                 # static CSV files loaded as tables
├── snapshots/             # slowly changing dimension tracking
├── macros/                # reusable Jinja SQL functions
├── analyses/              # ad-hoc SQL, version-controlled but not materialized
└── target/                # auto-generated, never touch, add to .gitignore
```

---

## Materializations

Configured in `dbt_project.yml` under `models:`:

```yaml
models:
  crypto_pipeline:
    staging:
      +materialized: view    # silver — cheap, always fresh, no storage cost
    marts:
      +materialized: table   # gold — pre-computed, fast for dashboards
```

| Type | When to use |
|---|---|
| `view` | Staging/silver — no storage cost, query recomputes each time |
| `table` | Marts/gold — pre-aggregated, fast for BI tools like Looker Studio |
| `incremental` | Large tables — only processes new rows since last run |
| `ephemeral` | CTEs — no table/view created, inlined into downstream models |

---

## source() vs ref()

```sql
-- source() — raw data outside dbt, declared in source.yml
FROM {{ source('crypto_raw', 'crypto_prices') }}

-- ref() — another dbt model, creates dependency graph
FROM {{ ref('stg_crypto_prices') }}
```

`ref()` is how dbt knows the execution order. If `fct_crypto_daily` refs `stg_crypto_prices`, dbt always runs staging first.

---

## Declaring Sources (source.yml)

```yaml
sources:
  - name: crypto_raw              # the label you use in source()
    database: data-engineering-crypto
    schema: crypto_raw            # BigQuery dataset name
    tables:
      - name: crypto_prices
        description: "Raw hourly price data loaded by Airflow from CoinGecko"
```

---

## Tests

### Generic Tests (schema.yml) — YAML declarations
```yaml
models:
  - name: stg_crypto_prices
    columns:
      - name: coin_id
        tests:
          - not_null
          - unique
      - name: currency
        tests:
          - not_null
          - accepted_values:
              values: ['usd', 'idr', 'cny', 'jpy', 'eur', 'sgd']
      - name: price
        tests:
          - not_null
```

Built-in generic tests: `not_null`, `unique`, `accepted_values`, `relationships`

### Singular Tests (tests/ folder) — Custom SQL
```sql
-- tests/assert_price_is_positive.sql
-- Returns failing rows. If any rows returned → test fails.
select *
from {{ ref('stg_crypto_prices') }}
where price <= 0
```

Use singular tests for business logic that can't be expressed in YAML.

Run tests:
```bash
dbt test                          # all tests
dbt test --select stg_crypto_prices   # specific model
```

---

## Folder Usage in Industry

| Folder | Used in practice? | When |
|---|---|---|
| `models/` | Always | Core of every dbt project |
| `tests/` | Often | Custom data quality assertions |
| `macros/` | Very common | DRY SQL logic, surrogate key generation, reusable transformations |
| `seeds/` | Occasionally | Small lookup tables (country codes, currency maps, category labels) |
| `snapshots/` | Common in enterprise | Tracking slowly changing data (customer status, subscription changes) |
| `analyses/` | Rarely | Ad-hoc SQL you want in git but not materialized |
| `target/` | Never touch | Auto-generated compiled SQL and run artifacts |

---

## Common dbt Commands

```bash
dbt debug          # test warehouse connection
dbt run            # run all models
dbt run --select stg_crypto_prices    # run one model
dbt run --select staging.*            # run all staging models
dbt test           # run all tests
dbt build          # run + test together (recommended in production)
dbt compile        # compile Jinja to raw SQL without running
dbt docs generate  # generate documentation site
dbt docs serve     # serve docs locally in browser
```

---

## Model Naming Conventions (Industry Standard)

| Layer | Prefix | Example | Materialization |
|---|---|---|---|
| Staging (silver) | `stg_` | `stg_crypto_prices` | view |
| Fact tables (gold) | `fct_` | `fct_crypto_daily` | table |
| Dimension tables (gold) | `dim_` | `dim_coins` | table |
| Intermediate | `int_` | `int_prices_pivoted` | ephemeral or view |

---

## Key Insight

dbt is just SQL + a dependency graph + a test framework. The value isn't magic — it's structure: every transformation is version-controlled, testable, documented, and reproducible.
