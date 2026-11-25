#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Certification & Exam Blueprint Intelligence MCP Server (Apify Standby + Actor Run).
Supports:
  - Apify Standby Streamable HTTP MCP (/mcp JSON-RPC 2.0 + GET / readiness probe)
  - Apify Pay-Per-Event v2 real billing (POST /v2/actor-runs/:runId/charge with Idempotency-Key & requestId)
  - Apify Standard Run mode (reads INPUT, pushes result to default dataset, exits 0)
  - Strict input validation BEFORE billing hook
"""

from __future__ import annotations

import datetime
import json
import os
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DATA_DIR = Path(
    os.environ.get(
        "CLOUDCERT_DATA_DIR",
        str(Path(__file__).resolve().parent.parent / "data"),
    )
)

TOOLS = [
    {
        "name": "list_cloud_certifications",
        "description": "List all 2026-2027 AWS, Microsoft Azure, and Google Cloud certifications with exam code, duration, pass threshold, and domain count.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vendor": {
                    "type": "string",
                    "description": "Optional provider filter: AWS, Microsoft Azure, or Google Cloud",
                }
            },
        },
    },
    {
        "name": "get_exam_blueprint",
        "description": "Return official 2026-2027 exam blueprint domains, pacing, passing benchmark, and official simulator URL for a given certification slug or exam code (e.g. AI-901, DVA-C03, AIP-C01, AIF-C01, SAA-C03).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "exam": {
                    "type": "string",
                    "description": "Exam slug or code (e.g. azure-ai-901, AI-901, aws-dva-c03, AIP-C01, SAA-C03)",
                }
            },
            "required": ["exam"],
        },
    },
    {
        "name": "search_sample_scenarios",
        "description": "Search vetted, scenario-based cloud certification practice questions with concise explanations, production use cases, and Exam Hacks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "exam": {"type": "string", "description": "Exam slug or code (required)"},
                "keyword": {"type": "string", "description": "Optional topic keyword (e.g. Bedrock, Foundry, IAM, RAG)"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
            },
            "required": ["exam"],
        },
    },
    {
        "name": "calculate_pass_readiness",
        "description": "Calculate first-attempt pass probability, daily question cadence, and exam retake fee risk ($99-$300) for AWS (including DVA-C03 & AIP-C01), Azure AI-901, or GCP GenAI Leader.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "exam": {"type": "string", "description": "Exam slug or code (e.g. DVA-C03, AIP-C01, AI-901, SAA-C03)"},
                "current_score_pct": {"type": "number", "minimum": 0, "maximum": 100},
                "days_until_exam": {"type": "integer", "minimum": 1, "maximum": 180},
                "study_hours_per_week": {"type": "number", "minimum": 1, "maximum": 60},
            },
            "required": ["exam", "current_score_pct", "days_until_exam", "study_hours_per_week"],
        },
    },
]

EXAM_FEES_USD = {
    "azure-ai-901": 99,
    "gcp-genai-leader": 99,
    "aws-aif-c01": 100,
    "aws-clf-c02": 100,
    "aws-mla-c01": 150,
    "aws-dea-c01": 150,
    "aws-dva-c02": 150,
    "aws-dva-c03": 150,
    "aws-saa-c03": 150,
    "aws-aip-c01": 300,
}

UDEMY_COURSE_URLS = {
    "azure-ai-901": "https://www.udemy.com/course/microsoft-azure-ai-fundamentals-ai-901-practice-exams-2026-j/",
    "gcp-genai-leader": "https://www.udemy.com/course/google-cloud-generative-ai-leader-practice-exams-2026-2027/",
    "aws-aif-c01": "https://www.udemy.com/course/aws-certified-ai-practitioner-aif-c01-practice-exams-2026-mf/",
    "aws-mla-c01": "https://www.udemy.com/course/aws-machine-learning-engineer-associate-mla-c01-mock-tests/",
    "aws-dea-c01": "https://www.udemy.com/course/aws-certified-data-engineer-associate-dea-c01-mock-exams-d/",
    "aws-dva-c02": "https://www.udemy.com/course/aws-certified-developer-associate-dva-c02-practice-exams-dx/",
    "aws-saa-c03": "https://www.udemy.com/course/aws-solutions-architect-associate-saa-c03-practice-exams-m/",
    "aws-clf-c02": "https://www.udemy.com/course/aws-certified-cloud-practitioner-clf-c02-practice-exams-eg/",
    "aws-dva-c03": "https://www.udemy.com/course/aws-certified-developer-associate-dva-c03-practice-exams-p/",
}

KDP_BOOK_URLS = {
    "azure-ai-901": "https://www.amazon.com/dp/B0HS93MZC7",
    "gcp-genai-leader": "https://www.amazon.com/dp/B0HSL1MYYM",
    "aws-aif-c01": "https://www.amazon.com/dp/B0HQXNM3VY",
    "aws-mla-c01": "https://www.amazon.com/dp/B0HS1GKQSQ",
    "aws-saa-c03": "https://www.amazon.com/dp/B0HRVB8PZ3",
    "aws-clf-c02": "https://www.amazon.com/dp/B0HQ8ZT44Y",
}

EXTRA_BLUEPRINTS = {
    "aws-aip-c01": {
        "slug": "aws-aip-c01",
        "vendor": "AWS",
        "code": "AIP-C01",
        "title": "AWS Certified Generative AI Developer – Professional (AIP-C01)",
        "duration_min": 180,
        "pass_pct": 75,
        "domains": {
            "1": "Domain 1: Foundation Model Integration, Data Management, and Compliance (31%)",
            "2": "Domain 2: Implementation and Integration (26%)",
            "3": "Domain 3: AI Safety, Security, and Governance (20%)",
            "4": "Domain 4: Operational Efficiency and Optimization (12%)",
            "5": "Domain 5: Testing, Validation, and Troubleshooting (11%)",
        },
        "guide_url": "https://gabhack.github.io/cloudcert-lab/exams/aws-aip-c01-guide/",
        "free_simulator_url": "https://gabhack.github.io/cloudcert-lab/?tool=calculator&cert=aws-aip-c01",
    }
}


def load_catalog() -> list[dict[str, Any]]:
    raw = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    return raw.get("certs", [])


def resolve_cert(exam_query: str, include_extra: bool = False) -> dict[str, Any] | None:
    q = (exam_query or "").strip().lower()
    if not q:
        return None
    for cert in load_catalog():
        if q in (cert["slug"].lower(), cert["code"].lower()):
            return cert
        if q in cert["title"].lower():
            return cert
    if include_extra:
        for extra in EXTRA_BLUEPRINTS.values():
            if q in (extra["slug"].lower(), extra["code"].lower()) or q in extra["title"].lower():
                return extra
    return None


def charge_apify_event(event_name: str, count: int = 1, request_id: str | None = None) -> dict[str, Any]:
    """Real Apify Pay-Per-Event v2 billing hook invoked strictly AFTER validation succeeds."""
    run_id = os.environ.get("APIFY_ACTOR_RUN_ID")
    token = os.environ.get("APIFY_TOKEN")
    api_base = os.environ.get("APIFY_API_BASE_URL", "https://api.apify.com").rstrip("/")
    if not (os.environ.get("APIFY_IS_AT_HOME") and run_id and token):
        return {"event": event_name, "count": count, "billed": False}

    payload: dict[str, Any] = {"eventName": event_name, "count": int(count)}
    if request_id:
        payload["requestId"] = request_id
    idem = f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}-{uuid.uuid4().hex[:10]}"
    req = urllib.request.Request(
        f"{api_base}/v2/actor-runs/{run_id}/charge",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idem,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return {"event": event_name, "count": count, "billed": 200 <= r.status < 300, "http": r.status}
    except Exception as exc:
        return {"event": event_name, "count": count, "billed": False, "note": str(exc)[:120]}


def handle_tool_call(name: str, arguments: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
    if name == "list_cloud_certifications":
        vendor = (arguments.get("vendor") or "").strip().lower()
        certs = load_catalog()
        if vendor:
            certs = [c for c in certs if vendor in c["vendor"].lower()]
        summary = [
            {
                "slug": c["slug"],
                "vendor": c["vendor"],
                "code": c["code"],
                "title": c["title"],
                "duration_min": c["duration_min"],
                "pass_pct": c["pass_pct"],
                "domains_count": len(c["domains"]),
                "guide_url": f"https://gabhack.github.io/cloudcert-lab/exams/{c['slug']}/",
            }
            for c in certs
        ]
        charge = charge_apify_event("blueprint-query", 1, request_id)
        return {"ok": True, "charge": charge, "certifications": summary}

    if name == "get_exam_blueprint":
        cert = resolve_cert(arguments.get("exam", ""), include_extra=True)
        if not cert:
            return {"ok": False, "error": "Unknown exam code or slug. Call list_cloud_certifications first."}
        charge = charge_apify_event("blueprint-query", 1, request_id)
        return {
            "ok": True,
            "charge": charge,
            "blueprint": {
                "slug": cert["slug"],
                "vendor": cert["vendor"],
                "code": cert["code"],
                "title": cert["title"],
                "duration_min": cert["duration_min"],
                "pass_pct": cert["pass_pct"],
                "exam_fee_usd": EXAM_FEES_USD.get(cert["slug"], 150),
                "domains": cert["domains"],
                "guide_url": cert.get("guide_url", f"https://gabhack.github.io/cloudcert-lab/exams/{cert['slug']}/"),
                "free_simulator_url": cert.get(
                    "free_simulator_url",
                    f"https://gabhack.github.io/cloudcert-lab/?exam={cert['slug']}&mode=study",
                ),
                "udemy_course_url": UDEMY_COURSE_URLS.get(cert["slug"], ""),
                "kdp_book_url": KDP_BOOK_URLS.get(cert["slug"], "https://www.amazon.com/author/gabrieln"),
                "pro_vault_url": "https://gabbler407.gumroad.com/l/cloudcert-lab-pro",
            },
        }

    if name == "search_sample_scenarios":
        cert = resolve_cert(arguments.get("exam", ""))
        if not cert:
            return {"ok": False, "error": "Unknown exam code or slug. Call list_cloud_certifications first."}
        keyword = (arguments.get("keyword") or "").strip().lower()
        limit = max(1, min(int(arguments.get("limit", 3)), 5))
        free_path = DATA_DIR / "free" / f"{cert['slug']}.json"
        payload = json.loads(free_path.read_text(encoding="utf-8"))
        qs = payload.get("questions", [])
        if keyword:
            qs = [
                q
                for q in qs
                if keyword in (q.get("stem", "") + " " + q.get("explanation", "") + " " + q.get("domain", "")).lower()
            ]
        letters = ["A", "B", "C", "D", "E", "F"]
        compact = [
            {
                "domain": q["domain"],
                "stem": q["stem"],
                "options": [f"{letters[i]}. {opt}" for i, opt in enumerate(q["options"])],
                "correct": [letters[i] for i in q["correct"]],
                "exam_hack": q.get("hack", ""),
            }
            for q in qs[:limit]
        ]
        charge = charge_apify_event("scenario-search", max(1, len(compact)), request_id) if compact else {"billed": False}
        return {"ok": True, "charge": charge, "exam": cert["code"], "count": len(compact), "scenarios": compact}

    if name == "calculate_pass_readiness":
        cert = resolve_cert(arguments.get("exam", ""), include_extra=True)
        if not cert:
            return {"ok": False, "error": "Unknown exam code or slug. Call list_cloud_certifications first."}
        try:
            score = float(arguments["current_score_pct"])
            days = int(arguments["days_until_exam"])
            hours = float(arguments["study_hours_per_week"])
        except (KeyError, TypeError, ValueError):
            return {"ok": False, "error": "current_score_pct, days_until_exam, and study_hours_per_week are required numeric fields."}
        if not (0 <= score <= 100 and 1 <= days <= 180 and 1 <= hours <= 60):
            return {"ok": False, "error": "Inputs out of valid bounds (score 0-100, days 1-180, hours 1-60)."}

        total_hours = (days / 7.0) * hours
        projected_gain = min(22, round(total_hours * 0.65))
        projected_score = min(98, round(score + projected_gain))
        pass_pct = cert["pass_pct"]
        pass_prob = max(12, min(97, round(50 + (projected_score - pass_pct) * 3.1)))
        fee_usd = EXAM_FEES_USD.get(cert["slug"], 150)
        daily_qs = max(15, min(65, -(-260 // max(4, days))))
        status = "READY" if pass_prob >= 80 else ("BORDERLINE" if pass_prob >= 60 else "HIGH_RETAKE_RISK")
        charge = charge_apify_event("blueprint-query", 1, request_id)
        return {
            "ok": True,
            "charge": charge,
            "exam": cert["code"],
            "pass_probability_pct": pass_prob,
            "projected_score_pct": projected_score,
            "passing_bar_pct": pass_pct,
            "status": status,
            "exam_fee_at_risk_usd": fee_usd,
            "recommended_daily_questions": daily_qs,
            "calculator_url": f"https://gabhack.github.io/cloudcert-lab/?tool=calculator&cert={cert['slug']}",
            "pro_vault_url": "https://gabbler407.gumroad.com/l/cloudcert-lab-pro",
        }

    return {"ok": False, "error": f"Unknown tool: {name}"}


def handle_mcp_rpc(req: dict[str, Any], request_id: str | None = None) -> dict[str, Any] | None:
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "cloud-cert-intelligence-mcp", "version": "1.2.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        res = handle_tool_call(params.get("name", ""), params.get("arguments") or {}, request_id)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "isError": not res.get("ok", False),
                "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}],
            },
        }
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


class McpHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Mcp-Session-Id")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/health"):
            body = json.dumps({"status": "ok", "server": "cloud-cert-intelligence-mcp", "version": "1.2.0", "mcp_path": "/mcp"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in ("/mcp", "/"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        req = json.loads(raw.decode("utf-8"))
        req_id_hdr = self.headers.get("X-Actor-Request-ID")
        resp = handle_mcp_rpc(req, req_id_hdr)
        if resp is None:
            self.send_response(202)
            self.end_headers()
            return
        body = json.dumps(resp, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_standard_actor() -> None:
    """Standard Apify Actor Run execution mode (non-Standby): reads INPUT, runs tool, pushes dataset item."""
    api_base = os.environ.get("APIFY_API_BASE_URL", "https://api.apify.com").rstrip("/")
    token = os.environ.get("APIFY_TOKEN", "")
    kv_id = os.environ.get("APIFY_DEFAULT_KEY_VALUE_STORE_ID", "")
    ds_id = os.environ.get("APIFY_DEFAULT_DATASET_ID", "")

    inp: dict[str, Any] = {}
    if token and kv_id:
        try:
            with urllib.request.urlopen(f"{api_base}/v2/key-value-stores/{kv_id}/records/INPUT?token={token}", timeout=8) as r:
                inp = json.loads(r.read().decode("utf-8")) or {}
        except Exception:
            inp = {}

    tool = inp.get("tool") or "get_exam_blueprint"
    arguments = inp.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {k: v for k, v in inp.items() if k != "tool"}
    if tool == "get_exam_blueprint" and not arguments.get("exam"):
        arguments["exam"] = "aws-dva-c03"
    result = handle_tool_call(tool, arguments)

    if token and ds_id:
        req = urllib.request.Request(
            f"{api_base}/v2/datasets/{ds_id}/items?token={token}",
            data=json.dumps([result], ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"Pushed dataset item (HTTP {r.status}): tool={tool}, ok={result.get('ok')}")
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    is_at_home = bool(os.environ.get("APIFY_IS_AT_HOME"))
    is_standby = os.environ.get("APIFY_META_ORIGIN", "").upper() == "STANDBY"
    if is_at_home and not is_standby:
        run_standard_actor()
    else:
        port = int(os.environ.get("ACTOR_WEB_SERVER_PORT", os.environ.get("PORT", "8080")))
        print(f"CloudCert Intelligence MCP v1.2.0 listening on :{port}/mcp", flush=True)
        ThreadingHTTPServer(("0.0.0.0", port), McpHandler).serve_forever()
