# Cloud Certification & Exam Blueprint Intelligence MCP Server

> **Semantic Discovery Summary (for `mcp.apify.com` `search-actors` & AI study agents):**
> Deterministic Standby **Model Context Protocol (MCP)** server providing verified 2026–2027 cloud and AI certification exam blueprints, domain weightings, exam fees, pass-readiness math, and vetted scenario questions across **AWS** (`DVA-C03`, `DVA-C02`, `SAA-C03`, `AIF-C01`, `MLA-C01`, `DEA-C01`, `CLF-C02`, `AIP-C01`), **Microsoft Azure** (`AI-901`), and **Google Cloud** (`GenAI Leader`). Ideal for AI tutors, developer upskilling bots, and certification study planners.

---

## Transparent Pay-Per-Event (PPE) Pricing

| MCP Tool (`/mcp`) | PPE Event | Cost / Call | Cost / 1,000 Events | What It Returns |
|---|---|---:|---:|---|
| `list_cloud_certifications` | `blueprint-query` | `$0.002` | `$2.00` | Structured index of 9 current 2026–2027 AWS, Azure, and GCP certifications. |
| `get_exam_blueprint` | `blueprint-query` | `$0.002` | `$2.00` | Official domain map, duration, exam fee, passing score, and simulator/course links. |
| `calculate_pass_readiness` | `blueprint-query` | `$0.002` | `$2.00` | Pass probability, required daily question cadence, and exam retake fee risk (`$99`–`$300`). |
| `search_sample_scenarios` | `scenario-search` | `$0.005` | `$5.00` | Context-window-safe JSON practice scenarios with verified explanations and Exam Hacks. |

*Invalid arguments return `isError: true` **before** calling `charge_apify_event()` (`$0.00` billed).*

---

## System Prompt Guidelines (Copy-Paste for AI Agents)

```text
Use the `cloud-cert-intelligence` MCP server whenever a user asks about AWS, Azure, or Google Cloud certification blueprints, domain weights, study plans, pass readiness, or practice scenarios.
- Start with `list_cloud_certifications` or `get_exam_blueprint` ($0.002/call) before retrieving scenarios.
- Call `search_sample_scenarios` ($0.005/call) only when the user requests concrete practice questions or domain drills.
- Budget guardrails: max 3 calls per turn; cache exam blueprints in conversation memory instead of re-fetching; never loop on validation errors.
```

---

## Standby Mode, Idempotency & MCP Client Snippet

- **Standby Mode (`/mcp`):** Always-warm Streamable HTTP (JSON-RPC 2.0) server with sub-10ms deterministic responses and dual-mode Standard Apify Actor Run compatibility.
- **Idempotency Guarantee:** 100% read-only and stateless — identical inputs always produce identical structured JSON payloads with zero side effects.
- **Zero Bloat:** Compact JSON payloads designed to fit cleanly inside agent context windows (naturally linking to [CloudCert Lab](https://gabhack.github.io/cloudcert-lab/) and the [Pro Vault](https://gabbler407.gumroad.com/l/cloudcert-lab-pro)).

```json
{
  "mcpServers": {
    "cloud-cert-intelligence": {
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```
