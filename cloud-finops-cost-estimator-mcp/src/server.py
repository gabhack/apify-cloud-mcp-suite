#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud FinOps & AI Token Cost Estimator MCP Server (Apify Standby + Standard Actor Run).
Zero external API dependencies · Real Apify Pay-Per-Event v2 billing · Strict pre-billing validation.
"""

from __future__ import annotations

import datetime
import json
import os
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

LLM_RATES_PER_1M = {
    "gemini-2.5-flash": {"in": 0.15, "out": 0.60, "provider": "Google Cloud"},
    "gemini-2.5-pro": {"in": 1.25, "out": 10.00, "provider": "Google Cloud"},
    "claude-3.7-sonnet": {"in": 3.00, "out": 15.00, "provider": "AWS Bedrock / Anthropic"},
    "nova-micro": {"in": 0.035, "out": 0.14, "provider": "AWS Bedrock"},
    "gpt-4o-mini": {"in": 0.15, "out": 0.60, "provider": "Azure Foundry / OpenAI"},
    "gpt-4o": {"in": 2.50, "out": 10.00, "provider": "Azure Foundry / OpenAI"},
}

TOOLS = [
    {
        "name": "estimate_serverless_workload",
        "description": "Estimate monthly AWS Lambda + API Gateway + DynamoDB + S3 cost and generate actionable FinOps recommendations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "monthly_requests": {"type": "integer", "minimum": 1},
                "avg_duration_ms": {"type": "integer", "minimum": 1, "default": 200},
                "memory_mb": {"type": "integer", "minimum": 128, "maximum": 10240, "default": 512},
                "storage_gb": {"type": "number", "minimum": 0, "default": 10},
            },
            "required": ["monthly_requests"],
        },
    },
    {
        "name": "estimate_llm_monthly_cost",
        "description": "Compare monthly LLM API spend across AWS Bedrock, Azure AI Foundry, and Google Cloud Gemini models with caching/batch FinOps tips.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "monthly_calls": {"type": "integer", "minimum": 1},
                "avg_input_tokens": {"type": "integer", "minimum": 1},
                "avg_output_tokens": {"type": "integer", "minimum": 1},
                "model": {"type": "string", "description": "Optional specific model id, or omit to compare all models"},
            },
            "required": ["monthly_calls", "avg_input_tokens", "avg_output_tokens"],
        },
    },
]


def charge_event(event_name: str, count: int = 1, request_id: str | None = None) -> dict[str, Any]:
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


def handle_tool_call(name: str, args: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
    if name == "estimate_serverless_workload":
        reqs = int(args.get("monthly_requests", 0))
        if reqs <= 0:
            return {"ok": False, "error": "monthly_requests must be > 0"}
        dur_ms = max(1, int(args.get("avg_duration_ms", 200)))
        mem_mb = max(128, min(10240, int(args.get("memory_mb", 512))))
        storage_gb = max(0.0, float(args.get("storage_gb", 10)))

        gb_sec = reqs * (dur_ms / 1000.0) * (mem_mb / 1024.0)
        lambda_req_cost = max(0, reqs - 1_000_000) * 0.0000002
        lambda_compute_cost = max(0.0, gb_sec - 400_000) * 0.0000166667
        apigw_http_cost = (reqs / 1_000_000.0) * 1.00
        apigw_rest_cost = (reqs / 1_000_000.0) * 3.50
        s3_cost = storage_gb * 0.023
        total_http = round(lambda_req_cost + lambda_compute_cost + apigw_http_cost + s3_cost, 2)
        total_rest = round(lambda_req_cost + lambda_compute_cost + apigw_rest_cost + s3_cost, 2)

        tips = []
        if total_rest > total_http:
            tips.append(f"Use HTTP API instead of REST API on API Gateway to save ${round(total_rest - total_http, 2)}/mo.")
        if mem_mb >= 512:
            tips.append("Switch Lambda architecture to arm64 (Graviton2) for ~20% lower compute cost + faster cold starts.")
        if storage_gb >= 100:
            tips.append("Enable S3 Intelligent-Tiering for infrequent objects to cut storage costs up to 40%.")

        return {
            "ok": True,
            "charge": charge_event("cost-estimate", 1, request_id),
            "estimate_usd": {
                "lambda_requests": round(lambda_req_cost, 2),
                "lambda_compute": round(lambda_compute_cost, 2),
                "api_gateway_http": round(apigw_http_cost, 2),
                "s3_standard": round(s3_cost, 2),
                "total_monthly_http_api": total_http,
                "total_monthly_rest_api": total_rest,
            },
            "finops_tips": tips,
        }

    if name == "estimate_llm_monthly_cost":
        calls = int(args.get("monthly_calls", 0))
        in_tok = int(args.get("avg_input_tokens", 0))
        out_tok = int(args.get("avg_output_tokens", 0))
        if calls <= 0 or in_tok <= 0 or out_tok <= 0:
            return {"ok": False, "error": "monthly_calls, avg_input_tokens, and avg_output_tokens must be > 0"}
        in_m = (calls * in_tok) / 1_000_000.0
        out_m = (calls * out_tok) / 1_000_000.0
        model_filter = (args.get("model") or "").strip().lower()

        rows = []
        for mid, rates in LLM_RATES_PER_1M.items():
            if model_filter and model_filter not in mid:
                continue
            monthly = round(in_m * rates["in"] + out_m * rates["out"], 2)
            rows.append({"model": mid, "provider": rates["provider"], "monthly_usd": monthly, "with_50pct_batch_discount_usd": round(monthly * 0.5, 2)})
        if not rows:
            return {"ok": False, "error": f"Unknown model '{model_filter}'. Supported: {', '.join(LLM_RATES_PER_1M)}"}
        rows.sort(key=lambda r: r["monthly_usd"])
        return {
            "ok": True,
            "charge": charge_event("cost-estimate", 1, request_id),
            "volume": {"input_millions": round(in_m, 3), "output_millions": round(out_m, 3)},
            "comparison": rows,
            "finops_tips": [
                "Enable prompt/context caching for static system prompts >1,024 tokens to cut input costs by 50–90%.",
                "Route classification and extraction steps to micro/flash tiers; reserve frontier models for final synthesis.",
            ],
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
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "cloud-finops-cost-estimator-mcp", "version": "1.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        res = handle_tool_call(params.get("name", ""), params.get("arguments") or {}, request_id)
        return {"jsonrpc": "2.0", "id": req_id, "result": {"isError": not res.get("ok", False), "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Mcp-Session-Id")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/health"):
            body = json.dumps({"status": "ok", "server": "cloud-finops-cost-estimator-mcp", "version": "1.1.0", "mcp_path": "/mcp"}).encode("utf-8")
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
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        resp = handle_mcp_rpc(json.loads(raw.decode("utf-8")), self.headers.get("X-Actor-Request-ID"))
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

    tool = inp.get("tool") or "estimate_llm_monthly_cost"
    arguments = inp.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {k: v for k, v in inp.items() if k != "tool"}
    if tool == "estimate_llm_monthly_cost" and not arguments.get("monthly_calls"):
        arguments = {"monthly_calls": 100000, "avg_input_tokens": 1200, "avg_output_tokens": 400}
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
        print(f"Cloud FinOps MCP v1.1.0 listening on :{port}/mcp", flush=True)
        ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
