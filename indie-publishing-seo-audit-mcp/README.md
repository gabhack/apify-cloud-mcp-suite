# Indie Publishing & Programmatic SEO Auditor MCP Server

Deterministic **Model Context Protocol (MCP)** Standby server & Apify Actor built for indie authors, Udemy instructors, and digital product creators using **Claude, Cursor, n8n, and Make**.

## Included MCP Tools (`/mcp` Streamable HTTP)

| Tool | What It Audits |
|---|---|
| `audit_kdp_keywords` | Amazon KDP 7 backend keyword boxes: 50-char hard cap, zero word duplication with title/subtitle, zero cross-box duplication, and detection of Amazon-prohibited promo terms (`free`, `bestseller`, `discount`, etc.). |
| `audit_udemy_listing` | Udemy Practice Test / Course title (`<=60` chars), subtitle (`<=120` chars), and target search keyword coverage. |
| `audit_gumroad_cro_listing` | Gumroad digital product CRO score: outcome hook title, value-stack price anchor, deliverable bullet count, free-sample funnel check, and trust copy signals. |

## Pay-Per-Event Guardrails
- **Strict input validation BEFORE billing:** Invalid payloads return structured `isError: true` without invoking `Actor.charge`.
- **Context-window friendly JSON:** Compact, actionable scores and issue lists with zero HTML bloat.
