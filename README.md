# Cloud, FinOps & Publishing MCP Server Suite (Apify Store Pay-Per-Event Ready)

[![License: MIT](https://img.shields.io/badge/License-MIT-15803d?style=for-the-badge)](./LICENSE)
[![MCP Protocol](https://img.shields.io/badge/MCP-Streamable%20HTTP%20%2Fmcp-1c69d4?style=for-the-badge)](https://modelcontextprotocol.io/)
[![CloudCert Lab](https://img.shields.io/badge/Live%20Simulator-CloudCert%20Lab-4f46e5?style=for-the-badge)](https://gabhack.github.io/cloudcert-lab/)
[![Pro Vault](https://img.shields.io/badge/Pro%20Vault-2%2C340%20Scenarios%20%2419.99-059669?style=for-the-badge)](https://gabbler407.gumroad.com/l/cloudcert-lab-pro)

Three lightweight, zero-bloat **Model Context Protocol (MCP)** Standby servers (`Streamable HTTP /mcp`, JSON-RPC 2.0) built for AI agents (**Claude Desktop, Cursor, VS Code, Windsurf, Antigravity, n8n, Make, Gumloop**) and packaged for one-click **Apify Store Pay-Per-Event** deployment (`$0` hosting · `80%` developer revenue share).

---

## Included MCP Servers & Tools (9 Tools Total)

| # | MCP Server Folder | Pricing (Apify PPE) | Exposed MCP Tools |
|---|---|---|---|
| 1 | [`cloud-cert-intelligence-mcp/`](./cloud-cert-intelligence-mcp/) | `$0.002`–`$0.005` / call | `list_cloud_certifications`, `get_exam_blueprint` (returns official domains, simulator URL, Udemy course URL, KDP ASIN & Pro Vault), `search_sample_scenarios`, `calculate_pass_readiness` |
| 2 | [`cloud-finops-cost-estimator-mcp/`](./cloud-finops-cost-estimator-mcp/) | `$0.003` / call | `estimate_aws_serverless_cost` (Lambda, API Gateway, S3, CloudWatch), `compare_llm_token_costs` (AWS Bedrock, Azure AI Foundry, Google Gemini) |
| 3 | [`indie-publishing-seo-audit-mcp/`](./indie-publishing-seo-audit-mcp/) | `$0.004` / call | `audit_kdp_backend_keywords` (7-box 50-char limit & zero duplication), `audit_udemy_course_seo` (title/subtitle limits & CTR), `audit_gumroad_cro_listing` (value-stack & trust audit) |

---

## Quick Start (Local Standby HTTP `/mcp`)

Run any server locally with Python 3.10+ (zero external pip dependencies required):

```bash
# Example: Cloud Certification Intelligence MCP on http://127.0.0.1:8080/mcp
PORT=8080 python3 cloud-cert-intelligence-mcp/src/server.py
```

### Connect from Cursor, Claude Desktop, or VS Code (`mcp.json`)

```json
{
  "mcpServers": {
    "cloud-cert-intelligence": {
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

### Verify with `curl` (JSON-RPC 2.0)

```bash
curl -s http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_exam_blueprint","arguments":{"exam":"DVA-C03"}}}'
```

---

## Built-In 2026 Agent Guardrails

- **Strict input validation BEFORE billing:** Invalid arguments return structured `isError: true` responses without invoking `POST /v2/actor-runs/:runId/charge`, preventing agent retry-loop bill shock.
- **Dual-Mode Production Execution:** Runs natively as an **Apify Standby Streamable HTTP MCP (`/mcp`)** or as a **Standard Apify Actor Run** (reading `INPUT` and pushing structured JSON to the default dataset).
- **Context-Window Friendly JSON:** Compact structured payloads (zero raw HTML dumps) so coding and research agents reuse the tools reliably.

---

## Related Multi-Cloud & AI Exam Resources (2026–2027)

- **Free Multi-Cloud Exam Simulator (9 Certifications · 135 Free Qs + Flashcards):** https://gabhack.github.io/cloudcert-lab/
- **Full Machine-Readable Reference (`llms-full.txt`):** https://gabhack.github.io/cloudcert-lab/llms-full.txt
- **Pro All-Access Vault (2,340 Scenarios · 36 Timed Mocks · 225-Hack Cheat Sheets PDF · `$19.99` One-Time):** https://gabbler407.gumroad.com/l/cloudcert-lab-pro
- **Amazon Kindle & Print Practice Exams Series (Free on Kindle Unlimited):** https://www.amazon.com/author/gabrieln
- **Official Udemy Practice Test Courses (`9/9` LIVE):**
  - [Azure AI-901](https://www.udemy.com/course/microsoft-azure-ai-fundamentals-ai-901-practice-exams-2026-j/) · [Google Cloud GenAI Leader](https://www.udemy.com/course/google-cloud-generative-ai-leader-practice-exams-2026-2027/) · [AWS DVA-C03 (New Dec 2026)](https://www.udemy.com/course/aws-certified-developer-associate-dva-c03-practice-exams-p/)
  - [AWS AIF-C01](https://www.udemy.com/course/aws-certified-ai-practitioner-aif-c01-practice-exams-2026-mf/) · [AWS MLA-C01](https://www.udemy.com/course/aws-machine-learning-engineer-associate-mla-c01-mock-tests/) · [AWS DEA-C01](https://www.udemy.com/course/aws-certified-data-engineer-associate-dea-c01-mock-exams-d/)
  - [AWS DVA-C02](https://www.udemy.com/course/aws-certified-developer-associate-dva-c02-practice-exams-dx/) · [AWS SAA-C03](https://www.udemy.com/course/aws-solutions-architect-associate-saa-c03-practice-exams-m/) · [AWS CLF-C02](https://www.udemy.com/course/aws-certified-cloud-practitioner-clf-c02-practice-exams-eg/)
