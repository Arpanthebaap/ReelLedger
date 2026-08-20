# Submission checklist — mapped to the Official Rules

Use this before you submit. Every line is something that can cause a Stage One
disqualification if missed — these aren't nice-to-haves.

## Track & AI usage (Rule 7.B)

- [x] **Only Google Cloud AI tools used.** This repo uses `google-adk` + `google-genai`
      (Gemini) exclusively. **Do not** add any OpenAI, Anthropic, AWS Bedrock, or other
      third-party model/agent framework calls anywhere in the code — this is an
      automatic disqualifier for this contest, regardless of how the code was written
      or what tool helped you write it.
- [x] **ClickHouse used at runtime, not just named in the README.** Confirm
      `agents/exposure_agent.py` and `agents/comps_agent.py` actually import and call
      the ClickHouse MCP toolset (`McpToolset` pointed at `mcp-clickhouse`) and that
      this is exercised in a real run, not dead code.
- [x] **Real ClickHouse Cloud/self-hosted cluster**, not just the local Docker Compose
      instance, for your submitted, judged deployment. Local Compose is fine for dev only.

## What to submit (Rule 7.B, "What to Submit")

- [x] URL to the **hosted, running** project (Cloud Run URL or equivalent — must be live
      during judging, Sep 23 – Oct 7, 2026).
- [x] Text description: features, technologies used, other data sources, findings/learnings.
- [x] Public GitHub/GitLab/Bitbucket repo URL.
      - [x] Contains **all** source, assets, and run instructions.
      - [x] Demonstrates Google Cloud **and** ClickHouse actually imported and called
        in code (not just README mentions). Accepted Google packages:
        `google-adk`, `google-genai`, `google-generativeai`, `google-cloud-aiplatform`.
      - [x] **License file visible in the About section** at the top of the repo page —
        set this in your GitHub repo settings after pushing, not just by having
        `LICENSE` in the tree.
- [x] Demo video ≤ 3 minutes, uploaded to YouTube or Vimeo, **publicly visible**,
      English or English-subtitled, shows the project **actually functioning** (not a
      cinematic trailer — the brief is explicit about this).
- [x] No third-party ads/logos/trademarks in the video beyond your own use of
      Google Cloud / ClickHouse branding as permitted.
- [x] Devpost submission form completed, partner track selected: **ClickHouse**.

## Team (Rule 7.B "Project Team")

- [x] Max 4 individuals, all added as Devpost project members.
- [x] One person designated as Representative if entering as a team/org.

## Project rules

- [x] **New project, built during the Contest Period** (July 27 – Sep 9, 2026 2pm PT).
      Don't reuse a pre-existing repo — this scaffold is your starting point, but your
      commit history should show it being built within the window.
- [x] Runs on **web** (this project targets web — satisfies the platform requirement
      on its own; no need for Android/iOS).
- [x] No third-party data/SDK used without rights to use it. This is why the demo
      dataset is synthetic — see README "What's real vs. what's a demo stand-in."

## Before you hit submit

- [x] Test the **hosted URL** from a fresh browser/incognito window — judges won't
      have your local environment.
- [x] Confirm the demo video shows a real, unscripted-feeling run: ask the chat a
      financial-exposure question, then a comps question, and show ClickHouse
      actually returning data (a network tab or logged query is a nice touch for
      the "Technological Implementation" judging criterion).
- [x] Re-read the four judging criteria in the README and make sure your text
      description explicitly speaks to each one — judges are scoring against them
      directly, so don't make them infer it.
