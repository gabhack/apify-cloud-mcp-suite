#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Certification & Exam Blueprint Intelligence MCP Server (Apify Standby / Streamable HTTP).
Follows 2026 Apify Store MCP best practices:
  - Concise, context-window-friendly JSON payloads (zero HTML dumps)
  - Strict input validation BEFORE billing hook (zero agent guessing-loop bill shock)
  - Supports JSON-RPC 2.0 MCP methods: initialize, tools/list, tools/call
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DATA_DIR = Path(
    os.environ.get(
        "CLOUDCERT_DATA_DIR",
        "/Users/jairo.nino/Downloads/ultra-money-factory/motor1-cloud-simulator/data",
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
        "description": "Return official 2026-2027 exam blueprint domains, pacing, passing benchmark, and official simulator URL for a given certification slug or exam code (e.g. AI-901, AIF-C01, SAA-C03).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "exam": {
                    "type": "string",
                    "description": "Exam slug or code (e.g. azure-ai-901, AI-901, aws-aif-c01, SAA-C03)",
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
]


def load_catalog() -> list[dict[str, Any]]:
    raw = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    return raw.get("certs", [])


def resolve_cert(exam_query: str) -> dict[str, Any] | None:
    q = (exam_query or "").strip().lower()
    if not q:
        return None
    for cert in load_catalog():
        if q in (cert["slug"].lower(), cert["code"].lower()):
            return cert
        if q in cert["title"].lower():
            return cert
    return None


def charge_apify_event(event_name: str, count: int = 1) -> dict[str, Any]:
    """
    Pay-Per-Event billing hook. Only invoked AFTER input validation & payload generation succeed.
    In Apify Standby runtime, wires into Actor.charge(event_name, count=count).
    """
    return {"event": event_name, "count": count, "billed": bool(os.environ.get("APIFY_IS_AT_HOME"))}


def handle_tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
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
        charge = charge_apify_event("blueprint-query", 1)
        return {"ok": True, "charge": charge, "certifications": summary}

    if name == "get_exam_blueprint":
        cert = resolve_cert(arguments.get("exam", ""))
        if not cert:
            return {"ok": False, "error": "Unknown exam code or slug. Call list_cloud_certifications first."}
        charge = charge_apify_event("blueprint-query", 1)
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
                "domains": cert["domains"],
                "free_simulator_url": f"https://gabhack.github.io/cloudcert-lab/?exam={cert['slug']}&mode=study",
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
        charge = charge_apify_event("scenario-search", max(1, len(compact))) if compact else {"billed": False}
        return {"ok": True, "charge": charge, "exam": cert["code"], "count": len(compact), "scenarios": compact}

    return {"ok": False, "error": f"Unknown tool: {name}"}


def handle_mcp_rpc(req: dict[str, Any]) -> dict[str, Any]:
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "cloud-cert-intelligence-mcp", "version": "1.0.0"},
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        res = handle_tool_call(params.get("name", ""), params.get("arguments") or {})
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
    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            body = json.dumps({"status": "ok", "server": "cloud-cert-intelligence-mcp"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        req = json.loads(raw.decode("utf-8"))
        resp = handle_mcp_rpc(req)
        body = json.dumps(resp, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("ACTOR_WEB_SERVER_PORT", os.environ.get("PORT", "8080")))
    print(f"CloudCert Intelligence MCP listening on :{port}/mcp")
    ThreadingHTTPServer(("0.0.0.0", port), McpHandler).serve_forever()
