# ReelLedger

**Real-time financial exposure and comparable-title intelligence for productions that can't afford an enterprise analytics desk.**

Built for the **Agentic Cinema: The Blockbuster Hackathon** (Google Cloud x ClickHouse track).

---

## The problem

Two things are true about the film & TV industry right now, and they compound:

1. **Production finance is still fragmented across spreadsheets.** Industry coverage on production accounting in 2026 is unanimous that studios want *live* budget visibility — not a reconciliation at the end of the month — but most productions below the studio tentpole tier are still stitching this together from disconnected sheets and PDFs. By the time a department head realizes they're 20% over on a line item, the money is already spent.
2. **Predictive "will this get made / will this perform" analytics is a studio-only luxury.** Tools like Cinelytic exist, but they're built and priced for major studios. Indie and mid-budget productions — the ones who most need to know whether a project is financially viable before they commit — have no equivalent. One industry software directory we researched explicitly separates "studio-grade software that uses intelligent analysis to boost financing and greenlight chances" from the commodity call-sheet and budgeting tools everyone else uses.

Nobody has combined **live financial exposure tracking** with **comparable-title outcome intelligence** in a single natural-language interface, built on infrastructure that can actually handle the query volume real productions generate (thousands of spend line items, tens of thousands of comparable-title data points, queried ad hoc, in plain English, by non-technical producers and financiers).

## The solution

ReelLedger is a small agent network — a **Producer Agent** orchestrating an **Exposure Agent** and a **Comps Agent** — built on **Google Cloud Agent Builder / ADK with Gemini**, backed by **ClickHouse** for the actual analytical heavy lifting, exposed to the agents through the official **ClickHouse MCP server** (`mcp-clickhouse`).

- **Exposure Agent** — watches burn rate against budget per department, in real time, and flags which department is trending over before it becomes a problem.
- **Comps Agent** — given a project's genre, budget tier, and cast tier, finds comparable historical titles and shows the realistic outcome distribution (not a single point estimate — a range, like a real financier would want).
- **Producer Agent** — the one thing a producer actually talks to. Routes the question, calls the right specialist agent(s), and answers in plain language with the numbers behind it.

Why ClickHouse specifically: both data shapes here — high-cardinality time-series spend events and large comparable-title outcome tables — are exactly the workload ClickHouse's columnar engine is built for. A producer asking "which department is about to blow budget" or "show me every $5–15M horror film released in Q4 for the last 8 years" needs sub-second aggregation over data that a row-store or a spreadsheet just can't give them.

## Architecture

```
Producer chat UI (web)
        │
        ▼
Google Cloud Agent Builder (Gemini + ADK)
        │
   Producer Agent  ──────────────┐
        │                        │
        ▼                        ▼
  Exposure Agent            Comps Agent
        │                        │
        ▼                        ▼
  ClickHouse MCP server    ClickHouse MCP server
        │                        │
        └───────────┬────────────┘
                     ▼
            ClickHouse Cloud
   (spend_line_items, comparable_titles)
```

## Repo layout

```
reelledger/
├── agents/                  # ADK agent definitions — the actual AI logic
│   ├── orchestrator.py      # Producer Agent (root agent) + sub-agent wiring
│   ├── exposure_agent.py    # Financial exposure specialist
│   ├── comps_agent.py       # Comparable-title specialist
│   └── prompts.py           # System prompts, kept out of code for iteration
├── backend/
│   └── main.py              # FastAPI app: serves the dashboard + /chat endpoint
├── frontend/
│   └── index.html            # Single-page dashboard + chat (vanilla JS, no build step)
├── data/
│   ├── schema.sql            # ClickHouse table definitions
│   └── seed_synthetic_data.py  # Generates a realistic synthetic demo dataset
├── deploy/
│   └── cloudrun.md           # Step-by-step Cloud Run deployment
├── Dockerfile
├── docker-compose.yml         # Local ClickHouse for development/testing
├── requirements.txt
├── .env.example
├── LICENSE                    # MIT
└── SUBMISSION_CHECKLIST.md    # Maps every hard hackathon requirement to where it's satisfied
```

## Quickstart (local development)

```bash
# 1. Start a local ClickHouse instance for development
docker compose up -d clickhouse

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Seed synthetic demo data (spend line items + comparable titles)
python data/seed_synthetic_data.py

# 4. Set environment variables
cp .env.example .env
# Fill in: GOOGLE_CLOUD_PROJECT, GOOGLE_API_KEY (or ADC), CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD

# 5. Run the backend
uvicorn backend.main:app --reload --port 8080

# 6. Open frontend/index.html in a browser, or serve it statically
```

For a production deployment against real ClickHouse Cloud, see `deploy/cloudrun.md`.

## What's real vs. what's a demo stand-in

Being upfront about this because judges will check:

- **The agent orchestration, the ClickHouse MCP integration, and the Gemini calls are real, runnable code** — not mocked.
- **The demo dataset is synthetic**, generated by `data/seed_synthetic_data.py`. We chose synthetic data deliberately over scraping real box-office numbers or using a real production's actual budget, to avoid any third-party rights or licensing complications in a submission that must be open source under an OSI license. The schema and value distributions are modeled on publicly discussed industry patterns (e.g., typical department cost splits, typical budget-to-box-office ratios by genre), not copied from any single proprietary source.
- If you want to point this at TMDB for real comparable-title metadata, there's a commented-out integration path in `data/seed_synthetic_data.py` — but note TMDB's API terms require attribution and don't permit bulk redistribution, so treat it as a live lookup, not something to bake into the committed dataset.

## License

MIT — see `LICENSE`. This repo contains no proprietary or copyrighted third-party content; the demo dataset is synthetic.
