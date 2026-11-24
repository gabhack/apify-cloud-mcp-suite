# Cloud FinOps & AI Token Cost Estimator MCP Server

Lightweight, deterministic **Model Context Protocol (MCP)** Standby server & Apify Actor for AI coding agents (**Cursor, Claude, Windsurf, n8n, Make**). Estimates monthly **AWS serverless spend** (Lambda, API Gateway HTTP vs REST, S3) and compares **Multi-Cloud LLM token spend** across **AWS Bedrock, Azure AI Foundry, and Google Cloud Gemini** with instant FinOps savings recommendations.

## Included MCP Tools (`/mcp` Streamable HTTP)

| Tool | What It Returns |
|---|---|
| `estimate_serverless_workload` | Monthly USD breakdown for Lambda requests/compute, API Gateway HTTP vs REST, S3 Standard + Graviton2/Tiering savings tips. |
| `estimate_llm_monthly_cost` | Side-by-side monthly cost comparison across Gemini 2.5 Flash/Pro, Claude 3.7 Sonnet, Amazon Nova Micro, and GPT-4o / 4o-mini (including 50% Batch discount & prompt caching guidance). |

## Pay-Per-Event Guardrails
- **Strict input validation BEFORE billing:** Invalid arguments return `isError: true` with `$0.00` charged.
- **Zero external API keys required:** Deterministic, sub-10ms responses with compact JSON payloads.
