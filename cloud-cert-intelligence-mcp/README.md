# Cloud Certification & Exam Blueprint Intelligence MCP Server

Standby **Model Context Protocol (MCP)** server packaged for **Apify Store Pay-Per-Event** (`$0` hosting, `80%` developer revenue share, zero social media required).

## Tools Exposed (`/mcp`)
1. `list_cloud_certifications` (`$0.002/call`) — Structured index of 9 current 2026–2027 AWS (including Dec 2026 `DVA-C03`), Microsoft Azure (`AI-901`), and Google Cloud (`GenAI Leader`) exams.
2. `get_exam_blueprint` (`$0.002/call`) — Official domain map, duration, passing threshold, and simulator deep-links.
3. `search_sample_scenarios` (`$0.005/scenario`) — Concise, context-window-safe JSON scenarios with verified answers and Exam Hacks.

## Margin & Quality Guardrails (2026 Best Practices)
- Strict input validation runs **before** `charge_apify_event()` so AI agent guessing loops never trigger bill shock.
- Compact JSON payloads (no raw HTML bloat) maximize tool reuse across Cursor, Claude, n8n, Make, and Gumloop.
- Naturally routes study agents to CloudCert Lab (`https://gabhack.github.io/cloudcert-lab/`) and Gumroad Pro (`$19.99`).
