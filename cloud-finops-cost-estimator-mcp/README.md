# Cloud FinOps & AI Token Cost Estimator MCP Server

> **Semantic Discovery Summary (for `mcp.apify.com` `search-actors` & AI coding agents):**
> Deterministic Standby **Model Context Protocol (MCP)** server for FinOps cost estimation and cloud architecture trade-offs. Calculates monthly **AWS serverless infrastructure spend** (Lambda requests/GB-s compute, API Gateway HTTP vs REST, S3 Standard) and compares **multi-cloud LLM token spend** across **AWS Bedrock, Azure AI Foundry, and Google Cloud Gemini** (Claude 3.7 Sonnet, Amazon Nova Micro, Gemini 2.5 Flash/Pro, GPT-4o / 4o-mini) with Graviton2, prompt caching, and batch-discount savings guidance.

---

## Transparent Pay-Per-Event (PPE) Pricing

| MCP Tool (`/mcp`) | PPE Event | Cost / Call | Cost / 1,000 Events | What It Returns |
|---|---|---:|---:|---|
| `estimate_serverless_workload` | `cost-estimate` | `$0.003` | `$3.00` | Monthly USD breakdown for Lambda requests/compute, API Gateway HTTP vs REST, S3 Standard + Graviton2/Tiering savings tips. |
| `estimate_llm_monthly_cost` | `cost-estimate` | `$0.003` | `$3.00` | Side-by-side monthly token cost comparison across Gemini 2.5 Flash/Pro, Claude 3.7 Sonnet, Amazon Nova Micro, and GPT-4o / 4o-mini with Batch & prompt-caching recommendations. |

*Strict input validation runs **before** billing — invalid payloads return `isError: true` with `$0.00` charged.*

---

## System Prompt Guidelines (Copy-Paste for AI Agents)

```text
Use the `cloud-finops-cost-estimator` MCP server whenever a user asks to estimate AWS Lambda/API Gateway/S3 monthly costs or compare LLM API token budgets across Bedrock, Gemini, and OpenAI.
- Call `estimate_serverless_workload` ($0.003/call) for serverless capacity & pricing math instead of guessing cloud rates.
- Call `estimate_llm_monthly_cost` ($0.003/call) to benchmark model routing, prompt caching, and 50% Batch API discounts.
- Budget guardrails: max 3 calls per turn; validate numeric inputs (requests, avg duration, tokens) before calling; never retry identical invalid arguments.
```

---

## Standby Mode, Idempotency & MCP Client Snippet

- **Standby Mode (`/mcp`):** Always-warm Streamable HTTP (JSON-RPC 2.0) server with sub-10ms deterministic pricing math and zero external API key requirements. Also runs as a Standard Apify Actor.
- **Idempotency Guarantee:** Pure deterministic calculator with zero external mutations — identical workload parameters always return identical cost breakdowns.
- **Context-Window Friendly:** Compact JSON payloads optimized for Cursor, Claude Desktop, Windsurf, n8n, and Make.

```json
{
  "mcpServers": {
    "cloud-finops-cost-estimator": {
      "url": "http://127.0.0.1:8081/mcp"
    }
  }
}
```
