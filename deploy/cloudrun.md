# Deploying ReelLedger to Google Cloud Run

This is the path to a real hosted URL for your Devpost submission (the
Official Rules require a URL to the hosted, running project).

## 1. Set up ClickHouse Cloud

1. Create a free trial cluster at https://clickhouse.com/cloud.
2. Note the host, port (usually 8443 for HTTPS), username, and password.
3. From your local machine, point `.env` at the cloud cluster and run:
   ```bash
   python data/seed_synthetic_data.py
   ```
   This creates the schema and loads the synthetic demo dataset directly
   into ClickHouse Cloud.

## 2. Set up Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com aiplatform.googleapis.com

# Request the $100 Google Cloud credit per the contest rules if using an
# existing account (see Official Rules section 6), or use a no-cost trial.
```

Decide how you'll auth to Gemini in production:
- **Vertex AI (recommended for the hosted deployment)**: set
  `GOOGLE_GENAI_USE_VERTEXAI=true` and grant the Cloud Run service account
  the `Vertex AI User` role. No API key needed -- it uses the service's
  identity.
- **AI Studio API key**: set `GOOGLE_API_KEY` as a secret (see below). Fine
  for quick demos, less ideal for a "production-ready" story in judging.

## 3. Store secrets

```bash
echo -n "your-clickhouse-password" | gcloud secrets create clickhouse-password --data-file=-
echo -n "your-google-api-key" | gcloud secrets create google-api-key --data-file=-  # if using AI Studio auth
```

## 4. Build and deploy

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/reelledger

gcloud run deploy reelledger \
  --image gcr.io/YOUR_PROJECT_ID/reelledger \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=true,CLICKHOUSE_HOST=your-cluster.clickhouse.cloud,CLICKHOUSE_PORT=8443,CLICKHOUSE_USER=default,CLICKHOUSE_SECURE=true,CLICKHOUSE_DATABASE=reelledger" \
  --set-secrets="CLICKHOUSE_PASSWORD=clickhouse-password:latest"
```

## 5. Verify before submitting

- Open the printed `*.run.app` URL in an incognito window.
- Confirm the dashboard chart loads (proves the direct ClickHouse connection
  works).
- Ask the chat a question from each suggestion chip and confirm you get a
  real, numbers-backed answer (proves the agent → MCP → ClickHouse path
  works end to end).
- This is the URL that goes in the Devpost "hosted Project" field, and the
  one your demo video should show running live.

## Common failure points

- **MCP server subprocess can't start in the container**: `mcp-clickhouse`
  is launched via `uvx` inside the agent process. Make sure `uv` is
  installed in the container (the provided `Dockerfile` does this) and that
  the container has network egress to your ClickHouse Cloud host.
- **Cold starts**: Cloud Run's default scale-to-zero means the first request
  after idle will be slow (agent + MCP subprocess startup). Set
  `--min-instances=1` if you're demoing live to judges and want to avoid a
  slow first response.
- **CORS**: the backend currently allows all origins for demo simplicity --
  tighten `allow_origins` in `backend/main.py` if you productionize this
  beyond the hackathon.
