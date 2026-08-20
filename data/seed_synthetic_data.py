"""
Generates a realistic SYNTHETIC demo dataset for ReelLedger and loads it into
ClickHouse: one in-flight production's spend line items (with a deliberate
cost-overrun pattern in one department, so the Exposure Agent has something
interesting to find), plus a comparable-titles table for the Comps Agent.

This data is entirely synthetic. Value distributions are modeled on publicly
discussed industry patterns (typical department cost splits, typical
budget-to-box-office ratios by genre) -- not copied from any single
proprietary source. Do not treat this as real box office data.

Usage:
    python data/seed_synthetic_data.py
"""
import os
import random
import uuid
from datetime import date, timedelta
from decimal import Decimal

import clickhouse_connect
import numpy as np
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
fake = Faker()
random.seed(42)
np.random.seed(42)

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_SECURE = os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true"

DEPARTMENTS = {
    # department: (typical % of total budget, overrun-prone?)
    "Cast":        (0.22, False),
    "Camera":      (0.10, False),
    "Locations":   (0.09, False),
    "Art":         (0.08, False),
    "Wardrobe":    (0.05, False),
    "VFX":         (0.15, True),   # <- the department we'll push over budget
    "Post":        (0.10, False),
    "Catering":    (0.04, False),
    "Transport":   (0.05, False),
    "Insurance":   (0.04, False),
    "Contingency": (0.08, False),
}
CATEGORIES = ["Rental", "Labor", "Materials", "Travel", "Fees", "Purchase"]

GENRES = ["Horror", "Elevated Horror", "Comedy", "Drama", "Thriller",
          "Action", "Sci-Fi", "Romance", "Documentary", "Animation"]
BUDGET_TIERS = [("micro", 100_000, 1_000_000),
                ("low", 1_000_000, 5_000_000),
                ("mid", 5_000_000, 20_000_000),
                ("studio", 20_000_000, 150_000_000)]
CAST_TIERS = ["unknown", "rising", "established", "a-list"]
DISTRIBUTIONS = ["theatrical", "streaming", "hybrid", "festival-only"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]


def make_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        secure=CLICKHOUSE_SECURE,
    )


def seed_project_budget(client, project_id: str, project_name: str, total_budget: float):
    rows = []
    start = date.today() - timedelta(days=45)
    end = date.today() + timedelta(days=30)
    for dept, (pct, _) in DEPARTMENTS.items():
        rows.append([project_id, project_name, dept, Decimal(str(round(total_budget * pct, 2))), start, end])
    client.insert(
        "reelledger.project_budgets",
        rows,
        column_names=["project_id", "project_name", "department", "total_budget",
                      "production_start", "production_end"],
    )
    return start, end


def seed_spend_line_items(client, project_id: str, total_budget: float, start: date, end: date):
    rows = []
    today = date.today()
    days_elapsed = (today - start).days
    total_days = max((end - start).days, 1)
    progress = min(max(days_elapsed / total_days, 0.05), 0.95)

    for dept, (pct, overrun_prone) in DEPARTMENTS.items():
        dept_budget = total_budget * pct
        # base spend follows production progress; overrun-prone dept runs hot
        spend_multiplier = 1.35 if overrun_prone else np.random.uniform(0.85, 1.05)
        target_spent_so_far = dept_budget * progress * spend_multiplier

        n_line_items = random.randint(15, 40)
        remaining = target_spent_so_far
        for i in range(n_line_items):
            d = start + timedelta(days=random.randint(0, max(days_elapsed, 1)))
            share = remaining / (n_line_items - i) if (n_line_items - i) > 0 else remaining
            amount = max(round(np.random.normal(share, share * 0.3), 2), 50.0)
            remaining -= amount
            budgeted = round(amount * np.random.uniform(0.7, 1.0), 2)  # actual often exceeds budgeted line
            rows.append([
                project_id, str(uuid.uuid4()), d, dept,
                random.choice(CATEGORIES), fake.company(),
                f"{dept} - {fake.bs()}",
                Decimal(str(budgeted)), Decimal(str(round(amount, 2))),
                "USD", random.choice([0, 0, 0, 1]),
            ])

    client.insert(
        "reelledger.spend_line_items",
        rows,
        column_names=["project_id", "line_item_id", "spend_date", "department", "category",
                      "vendor", "description", "budgeted_amount", "actual_amount",
                      "currency", "is_committed"],
    )
    print(f"  inserted {len(rows)} spend line items")


def seed_comparable_titles(client, n=2000):
    rows = []
    for _ in range(n):
        genre = random.choice(GENRES)
        tier_name, lo, hi = random.choice(BUDGET_TIERS)
        budget = np.random.uniform(lo, hi)
        cast_tier = random.choices(CAST_TIERS, weights=[0.35, 0.30, 0.25, 0.10])[0]

        # rough, synthetic multiplier logic: bigger cast tier & budget -> higher
        # multiple on average, but with heavy variance (most films don't "win")
        cast_mult = {"unknown": 1.0, "rising": 1.3, "established": 1.8, "a-list": 2.6}[cast_tier]
        genre_mult = {"Horror": 3.5, "Elevated Horror": 2.8, "Comedy": 1.6, "Drama": 1.1,
                      "Thriller": 1.4, "Action": 1.9, "Sci-Fi": 1.7, "Romance": 1.3,
                      "Documentary": 0.6, "Animation": 2.0}[genre]
        noise = np.random.lognormal(mean=0, sigma=0.9)
        worldwide = budget * cast_mult * genre_mult * 0.5 * noise
        domestic = worldwide * np.random.uniform(0.35, 0.55)

        rows.append([
            fake.catch_phrase().title(), genre, tier_name, Decimal(str(round(budget, 2))),
            cast_tier, random.choice(QUARTERS), random.randint(2016, 2025),
            random.choice(DISTRIBUTIONS),
            Decimal(str(round(domestic, 2))), Decimal(str(round(worldwide, 2))),
            Decimal(str(round(np.clip(np.random.normal(65, 15), 5, 99), 1))),
            Decimal(str(round(np.clip(np.random.normal(58, 18), 5, 99), 1))),
        ])

    client.insert(
        "reelledger.comparable_titles",
        rows,
        column_names=["title_name", "genre", "budget_tier", "budget_usd", "cast_tier",
                      "release_quarter", "release_year", "distribution",
                      "domestic_gross_usd", "worldwide_gross_usd", "audience_score", "critic_score"],
    )
    print(f"  inserted {len(rows)} comparable titles")


def main():
    client = make_client()

    print("Creating schema...")
    with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
        for stmt in f.read().split(";"):
            stmt = stmt.strip()
            if stmt:
                client.command(stmt)

    print("Seeding demo project budget + spend...")
    project_id = "demo-project-001"
    start, end = seed_project_budget(client, project_id, "Midnight Signal (demo)", total_budget=8_500_000)
    seed_spend_line_items(client, project_id, total_budget=8_500_000, start=start, end=end)

    print("Seeding comparable titles (synthetic)...")
    seed_comparable_titles(client, n=2000)

    print("Done. Try querying: SELECT department, sum(actual_amount) FROM reelledger.spend_line_items GROUP BY department")


if __name__ == "__main__":
    main()
