# Indie Publishing & Programmatic SEO Auditor MCP Server

> **Semantic Discovery Summary (for `mcp.apify.com` `search-actors` & AI marketing/publishing agents):**
> Deterministic Standby **Model Context Protocol (MCP)** server for indie authors, Udemy instructors, and digital product creators. Audits **Amazon KDP 7 backend keyword boxes** (50-char hard cap, zero title/subtitle/cross-box duplication, Amazon-prohibited promo term detection), **Udemy course/practice-test SEO** (`<=60`-char title, `<=120`-char subtitle, keyword coverage), and **Gumroad listing CRO** (outcome hook, price-anchor value stack, deliverable bullets, free-sample funnel, trust signals).

---

## Transparent Pay-Per-Event (PPE) Pricing

| MCP Tool (`/mcp`) | PPE Event | Cost / Call | Cost / 1,000 Events | What It Audits |
|---|---|---:|---:|---|
| `audit_kdp_keywords` | `seo-audit` | `$0.004` | `$4.00` | Amazon KDP 7 backend keyword boxes: 50-char cap, deduplication vs title/subtitle, and prohibited promo-term detection (`free`, `bestseller`, `discount`, etc.). |
| `audit_udemy_listing` | `seo-audit` | `$0.004` | `$4.00` | Udemy Practice Test / Course title (`<=60` chars), subtitle (`<=120` chars), and target search keyword coverage. |
| `audit_gumroad_cro_listing` | `seo-audit` | `$0.004` | `$4.00` | Gumroad digital product CRO score: outcome hook title, value-stack price anchor, deliverable bullet count, free-sample funnel check, and trust copy signals. |

*Strict input validation runs **before** billing — invalid payloads return structured `isError: true` without invoking `Actor.charge` (`$0.00` charged).*

---

## System Prompt Guidelines (Copy-Paste for AI Agents)

```text
Use the `indie-publishing-seo-audit` MCP server before finalizing metadata for Amazon KDP books, Udemy courses/practice tests, or Gumroad product listings.
- Call `audit_kdp_keywords` ($0.004/call) to verify all 7 KDP backend boxes stay <=50 chars with zero duplicate or prohibited words.
- Call `audit_udemy_listing` ($0.004/call) to check title/subtitle character limits and primary keyword coverage.
- Call `audit_gumroad_cro_listing` ($0.004/call) to score conversion-rate optimization signals before launch.
- Budget guardrails: max 2 audit passes per listing (initial audit + post-fix verification); never submit empty fields or retry unchanged failing payloads.
```

---

## Standby Mode, Idempotency & MCP Client Snippet

- **Standby Mode (`/mcp`):** Always-warm Streamable HTTP (JSON-RPC 2.0) server delivering sub-10ms deterministic audits, plus full Standard Apify Actor Run support (`INPUT` -> default dataset).
- **Idempotency Guarantee:** 100% pure, read-only rule engine — identical listing metadata always produces identical scores and issue lists with zero side effects.
- **Context-Window Friendly:** Compact JSON scores and actionable issue arrays with zero raw HTML bloat.

```json
{
  "mcpServers": {
    "indie-publishing-seo-audit": {
      "url": "http://127.0.0.1:8082/mcp"
    }
  }
}
```
