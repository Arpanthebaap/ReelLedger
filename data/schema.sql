-- ReelLedger ClickHouse schema
-- Run with: clickhouse-client --multiquery < data/schema.sql
-- or via clickhouse-connect from seed_synthetic_data.py

CREATE DATABASE IF NOT EXISTS reelledger;

-- ============================================================
-- spend_line_items: high-cardinality, append-mostly time series
-- of every production expense, tagged by department/vendor/day.
-- This is the table the Exposure Agent queries.
-- ============================================================
CREATE TABLE IF NOT EXISTS reelledger.spend_line_items
(
    project_id       String,
    line_item_id     UUID DEFAULT generateUUIDv4(),
    spend_date       Date,
    department       LowCardinality(String),   -- e.g. 'Camera', 'VFX', 'Locations', 'Cast', 'Catering'
    category         LowCardinality(String),   -- e.g. 'Rental', 'Labor', 'Materials', 'Travel'
    vendor           String,
    description      String,
    budgeted_amount  Decimal(12, 2),           -- amount allocated for this line item at approval
    actual_amount    Decimal(12, 2),           -- amount actually spent
    currency         LowCardinality(String) DEFAULT 'USD',
    is_committed     UInt8 DEFAULT 0,          -- 1 = PO issued/committed but not yet paid
    inserted_at      DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(spend_date)
ORDER BY (project_id, department, spend_date);

-- ============================================================
-- project_budgets: the approved top-line budget per department,
-- so the Exposure Agent has something to compare actuals against.
-- ============================================================
CREATE TABLE IF NOT EXISTS reelledger.project_budgets
(
    project_id        String,
    project_name      String,
    department        LowCardinality(String),
    total_budget      Decimal(12, 2),
    production_start  Date,
    production_end    Date,
    updated_at         DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (project_id, department);

-- ============================================================
-- comparable_titles: synthetic historical title outcomes used
-- for greenlight-style comps analysis. Modeled on publicly
-- discussed industry patterns, not scraped from any real source.
-- This is the table the Comps Agent queries.
-- ============================================================
CREATE TABLE IF NOT EXISTS reelledger.comparable_titles
(
    title_id          UUID DEFAULT generateUUIDv4(),
    title_name        String,               -- synthetic/fictional title
    genre             LowCardinality(String),
    budget_tier        LowCardinality(String), -- 'micro' <1M, 'low' 1-5M, 'mid' 5-20M, 'studio' 20M+
    budget_usd        Decimal(12, 2),
    cast_tier         LowCardinality(String), -- 'unknown', 'rising', 'established', 'a-list'
    release_quarter   LowCardinality(String), -- 'Q1'...'Q4'
    release_year      UInt16,
    distribution      LowCardinality(String), -- 'theatrical', 'streaming', 'hybrid', 'festival-only'
    domestic_gross_usd Decimal(14, 2),
    worldwide_gross_usd Decimal(14, 2),
    audience_score     Decimal(4, 1),        -- 0-100 synthetic audience score
    critic_score        Decimal(4, 1),       -- 0-100 synthetic critic score
    inserted_at         DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (genre, budget_tier, release_year);
